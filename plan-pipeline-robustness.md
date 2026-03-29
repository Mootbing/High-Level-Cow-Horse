# Pipeline Robustness Improvement Plan

Audit of the OpenClaw multi-agent pipeline. Each section identifies a concrete bug,
cites the exact file and line, and provides the fix.

---

## 1. RACE CONDITION: Push fires BEFORE Vercel project is linked

### Problem

In `scaffold_nextjs`, the engineer creates a GitHub repo (step 2), pushes code
(step 3), then creates the Vercel project (step 4). Because the Vercel project
does not exist at push time, the GitHub webhook that Vercel installs cannot fire.
The initial scaffold commit never triggers a Vercel build. The site is dark until
the *next* push, which may never come if the engineer considers scaffolding complete.

### Location

`src/openclaw/agents/engineer.py`, lines 139-157 inside the `scaffold_nextjs` branch
of `handle_tool_call`.

Current order:
```python
# 2. Create GitHub repo                      (line 141)
repo_data = await create_repo(...)
# 3. Push initial scaffold                   (line 148)
push_result = await push_directory(...)
# 4. Create Vercel project linked to GitHub  (line 155)
vercel_project = await create_project_from_github(...)
```

### Fix

Swap steps 3 and 4 so Vercel is linked before the first push. Then, if the
webhook-based deploy still has not started after the push (race with Vercel
provisioning the webhook), explicitly trigger a deployment as a fallback.

```python
        if tool_name == "scaffold_nextjs":
            # 1. Copy template
            template_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..", "templates", "nextjs-base")
            template_dir = os.path.normpath(template_dir)
            if os.path.exists(template_dir):
                shutil.copytree(template_dir, project_dir, dirs_exist_ok=True)
            else:
                os.makedirs(project_dir, exist_ok=True)

            # 2. Create GitHub repo
            from openclaw.integrations.github_client import create_repo, push_directory
            repo_data = await create_repo(
                name=project_name,
                description=tool_input.get("description", f"Website for {project_name} — built by OpenClaw"),
            )
            repo_full_name = repo_data["full_name"]

            # 3. Create Vercel project linked to GitHub BEFORE any push
            from openclaw.integrations.vercel_client import create_project_from_github, get_latest_deployment, trigger_deployment
            vercel_project = await create_project_from_github(project_name, repo_full_name)
            vercel_linked = bool(vercel_project.get("link"))

            # 4. Push initial scaffold (Vercel webhook is now active)
            push_result = await push_directory(
                repo_full_name,
                project_dir,
                commit_message="Initial scaffold: Next.js 15 + GSAP + Lenis + Tailwind",
            )

            # 5. Fallback: if Vercel did not pick up the push, trigger manually
            import asyncio
            await asyncio.sleep(5)  # give webhook a moment
            deployment = await get_latest_deployment(project_name)
            if not deployment:
                logger.warning("vercel_webhook_missed_push, triggering manual deploy", project=project_name)
                await trigger_deployment(project_name)

            return {
                "status": "scaffolded",
                "path": project_dir,
                "github_repo": repo_full_name,
                "github_url": f"https://github.com/{repo_full_name}",
                "vercel_project": vercel_project.get("name"),
                "vercel_auto_deploy": vercel_linked,
                "commit": push_result.get("commit_sha", "")[:8],
                "note": "Vercel linked before push; auto-deploy active" if vercel_linked else "Vercel created but not linked to GitHub — manual deploy triggered",
            }
```

---

## 2. DUPLICATE WORK: CEO and PM both delegate the same task

### Problem

When the owner says "build a website for X", the CEO delegates to
`project_manager` (ceo.py:158-167). The PM then delegates to `engineer`
(project_manager.py:58-68). But the auto-report logic in worker.py:64-97 sends
the PM's result back to the CEO, and the CEO's system prompt (ceo.py:119-127)
tells it to "delegate to project_manager with the brand data" again, creating a
duplicate project. There is no dedup key on published messages.

Additionally, neither the CEO nor PM track what has already been delegated. Two
concurrent inbound messages about the same project both get fanned out.

### Location

- `src/openclaw/agents/worker.py`, lines 64-97 (auto-report loop)
- `src/openclaw/agents/ceo.py`, lines 109-127 (result handler re-delegates)
- `src/openclaw/agents/base.py`, line 171 (`delegate` has no idempotency key)

### Fix

**A. Add a `task_id` dedup key to every delegation and check it before processing.**

In `base.py`, generate a deterministic task ID when delegating:

```python
    async def delegate(
        self,
        target_agent: str,
        payload: dict,
        project_id: str | None = None,
        task_id: str | None = None,
    ) -> str:
        """Delegate a task to another agent via Redis Streams."""
        # Generate a deterministic dedup key if none provided
        if not task_id:
            import hashlib
            dedup_input = f"{self.agent_type}:{target_agent}:{payload.get('prompt', '')[:200]}"
            task_id = hashlib.sha256(dedup_input.encode()).hexdigest()[:16]

        message = AgentMessage(
            type="task",
            source_agent=self.agent_type,
            target_agent=target_agent,
            project_id=project_id,
            task_id=task_id,
            payload=payload,
        )
        entry_id = await publish(target_agent, message.to_publish_dict())
        self.log.info(
            "delegated_task",
            target=target_agent,
            entry_id=entry_id,
            task_id=task_id,
            payload_preview=str(payload)[:200],
        )
        return entry_id
```

**B. Check for duplicate `task_id` in the worker loop before processing.**

In `worker.py`, add a Redis SET-based dedup check around line 57:

```python
                try:
                    # Dedup: skip if this task_id was already processed
                    task_id = data.get("task_id")
                    if task_id:
                        dedup_key = f"openclaw:dedup:{agent_type}:{task_id}"
                        already_done = await consumer.redis.set(
                            dedup_key, "1", nx=True, ex=3600  # 1-hour TTL
                        )
                        if not already_done:
                            logger.info("duplicate_task_skipped", agent=agent_type, task_id=task_id)
                            await consumer.ack(entry_id)
                            continue

                    result = await agent.process_task(data)
                    await consumer.ack(entry_id)
```

**C. Stop the CEO from re-delegating completed work.**

In `ceo.py`, amend the result-handling prompt (lines 109-127) to be explicit:

```python
        elif msg_type == "result":
            source = message.get("source_agent", "unknown")
            payload = message.get("payload", {})
            result_text = payload.get("result", "")
            original = payload.get("original_prompt", "")
            prompt = (
                f"The {source} agent has completed a task and is reporting results back to you.\n"
                f"Original task: {original}\n\n"
                f"Result:\n{result_text[:4000]}\n\n"
                f"IMPORTANT: This task is ALREADY COMPLETE. Do NOT re-delegate it.\n"
                f"Just summarize the result and send a status update to the owner via whatsapp_send with to='owner'.\n"
                f"Only delegate NEW follow-up work if the result explicitly requires it (e.g., QA failed and needs a fix)."
            )
```

---

## 3. TURN LIMIT: Engineer exhausts 10 turns on generate_code, never deploys

### Problem

The base agent run loop (`base.py:57-60`) hard-caps at 10 turns. The engineer's
system prompt lists a workflow: scaffold -> generate_code (per section) ->
commit_and_deploy -> get_deploy_url. With 10 sections of code to generate, the
engineer burns all 10 turns on `generate_code` calls and never reaches
`commit_and_deploy`. The site is never deployed.

Worse, each `generate_code` call itself invokes a *nested* `self.run()`
(engineer.py:173), which uses its own 10-turn budget internally. But the outer
loop still counts each `generate_code` tool call as one turn, so with 10+ sections
the outer loop silently terminates.

### Location

- `src/openclaw/agents/base.py`, lines 57-60 (`max_turns = 10`)
- `src/openclaw/agents/engineer.py`, line 173 (nested `self.run()` inside `generate_code`)

### Fix

**A. Give the engineer a higher turn budget.** Override `max_turns` on the
EngineerAgent class (not globally, to protect other agents from runaway loops):

```python
@register_agent("engineer")
class EngineerAgent(BaseAgent):
    agent_type = "engineer"
    system_prompt = ENGINEER_SYSTEM_PROMPT
    max_turns = 30  # Needs more turns: scaffold + N sections + commit + deploy
    tools = [SCAFFOLD_TOOL, GENERATE_CODE_TOOL, COMMIT_AND_DEPLOY_TOOL, GET_DEPLOY_URL_TOOL]
```

And make `max_turns` a class attribute that the run loop reads (in `base.py`):

```python
class BaseAgent:
    agent_type: str = "base"
    system_prompt: str = "You are a helpful assistant."
    model: str = ""
    max_context_messages: int = 50
    max_turns: int = 10  # Default safety limit; subclasses can override
    tools: list[dict] = []
```

Then in the `run` method, replace the hardcoded `10`:

```python
    async def run(self, prompt: str, context: list[dict] | None = None) -> str:
        messages = []
        if context:
            messages.extend(context[-self.max_context_messages :])
        messages.append({"role": "user", "content": prompt})

        await self._persist_log("user", prompt)

        final_text_parts = []

        for turn in range(self.max_turns):
```

**B. Add a turn-budget warning to the system prompt so the LLM prioritizes deploy.**

Append to `ENGINEER_SYSTEM_PROMPT`:

```
CRITICAL CONSTRAINT:
You have a limited number of tool-call turns. ALWAYS call commit_and_deploy
before your budget runs out. A generated but undeployed site is worthless.
Prioritize: scaffold -> generate 3-5 key sections -> commit_and_deploy -> get_deploy_url.
You can do additional sections in a follow-up task.
```

**C. Add a "last-chance" deploy guard at the end of the run loop.** In `base.py`,
after the for-loop exits, check if the engineer never deployed:

```python
        full_response = "\n".join(final_text_parts)

        # Safety net: if engineer hit turn limit, warn
        if turn >= self.max_turns - 1:
            self.log.warning(
                "turn_limit_reached",
                agent=self.agent_type,
                turns_used=turn + 1,
            )

        await self._persist_log("assistant", full_response, response.usage.output_tokens)
        return full_response
```

---

## 4. CONTEXT LOSS: generate_code's nested self.run() loses project context

### Problem

When the engineer calls the `generate_code` tool, `handle_tool_call` invokes
`self.run()` with only the code-generation prompt (engineer.py:173):

```python
code = await self.run(
    f"Generate ONLY the code (no markdown, no explanation) for: {tool_input['description']}"
)
```

This creates a fresh `messages` list with zero context about the project, brand
data, existing components, file structure, or design spec. The generated code
cannot reference other components, use the correct brand colors, or import shared
utilities because it has no knowledge of the project.

Additionally, the nested `run()` call creates its own LLM conversation which
accumulates tool calls, but none of that context flows back to the outer run loop.

### Location

`src/openclaw/agents/engineer.py`, lines 171-178

### Fix

**Replace the nested `self.run()` with a direct single-shot Claude API call** that
includes project context but does NOT enter a tool-use loop:

```python
        elif tool_name == "generate_code":
            filepath = os.path.join(project_dir, tool_input["file_path"])
            os.makedirs(os.path.dirname(filepath), exist_ok=True)

            # Build project context from existing files
            project_context = self._gather_project_context(project_dir)

            # Single-shot generation (no tool loop, no nested run)
            gen_response = await self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                system=(
                    "You are a code generator. Output ONLY valid source code. "
                    "No markdown fences, no explanation, no commentary. "
                    "Match the project's existing style, imports, and brand."
                ),
                messages=[
                    {
                        "role": "user",
                        "content": (
                            f"Project files for context:\n{project_context}\n\n"
                            f"Generate the code for: {tool_input['description']}\n"
                            f"Target file: {tool_input['file_path']}"
                        ),
                    }
                ],
            )
            code = gen_response.content[0].text

            with open(filepath, "w") as f:
                f.write(code)
            return {"status": "written", "path": tool_input["file_path"], "size": len(code)}
```

Add the helper method to `EngineerAgent`:

```python
    def _gather_project_context(self, project_dir: str, max_chars: int = 20000) -> str:
        """Read key project files to build context for code generation."""
        context_parts = []
        total = 0
        priority_files = [
            "package.json",
            "tailwind.config.ts",
            "src/app/layout.tsx",
            "src/app/page.tsx",
            "src/app/globals.css",
        ]
        for rel_path in priority_files:
            full_path = os.path.join(project_dir, rel_path)
            if os.path.isfile(full_path):
                with open(full_path, "r", errors="ignore") as f:
                    content = f.read()
                if total + len(content) > max_chars:
                    break
                context_parts.append(f"--- {rel_path} ---\n{content}")
                total += len(content)

        # Also list all existing component files
        components_dir = os.path.join(project_dir, "src", "components")
        if os.path.isdir(components_dir):
            for fname in sorted(os.listdir(components_dir)):
                context_parts.append(f"[existing component] src/components/{fname}")

        return "\n\n".join(context_parts) if context_parts else "(empty project)"
```

---

## 5. STORE_PROSPECT DUPLICATE: Fails on unique constraint for URL

### Problem

`store_prospect` (inbound.py:163-182) always does a blind `session.add(Prospect(...))`
followed by `session.commit()`. The `Prospect.url` column has a `unique=True`
constraint (models/prospect.py:24). If the inbound agent scrapes the same URL
twice (common when the CEO re-triggers research), the commit raises
`IntegrityError` and the task fails.

Note: `firecrawl_scrape` (inbound.py:100-121) already does a proper
select-then-update upsert for `raw_data`. But `store_prospect` does not.

### Location

`src/openclaw/agents/inbound.py`, lines 163-182

### Fix

Replace the blind insert with an upsert pattern using `select` + merge:

```python
        elif tool_name == "store_prospect":
            from openclaw.db.session import async_session_factory
            from openclaw.models.prospect import Prospect
            from sqlalchemy import select

            async with async_session_factory() as session:
                # Upsert: update if URL already exists, insert otherwise
                result = await session.execute(
                    select(Prospect).where(Prospect.url == tool_input["url"])
                )
                prospect = result.scalar_one_or_none()

                if prospect:
                    # Update existing fields (only overwrite with non-None values)
                    for field in (
                        "company_name", "tagline", "logo_url", "industry",
                    ):
                        val = tool_input.get(field)
                        if val is not None:
                            setattr(prospect, field, val)
                    for field in (
                        "contact_emails", "brand_colors", "fonts", "tech_stack",
                    ):
                        val = tool_input.get(field)
                        if val:  # non-empty list
                            setattr(prospect, field, val)
                    social = tool_input.get("social_links")
                    if social:
                        prospect.social_links = social
                    prospect.raw_data = tool_input
                    status = "updated"
                else:
                    prospect = Prospect(
                        url=tool_input["url"],
                        company_name=tool_input.get("company_name"),
                        tagline=tool_input.get("tagline"),
                        contact_emails=tool_input.get("contact_emails", []),
                        brand_colors=tool_input.get("brand_colors", []),
                        fonts=tool_input.get("fonts", []),
                        logo_url=tool_input.get("logo_url"),
                        social_links=tool_input.get("social_links", {}),
                        industry=tool_input.get("industry"),
                        tech_stack=tool_input.get("tech_stack", []),
                        raw_data=tool_input,
                    )
                    session.add(prospect)
                    status = "created"

                await session.commit()
                return {"status": status, "url": tool_input["url"]}
```

---

## 6. VERCEL AUTO-DEPLOY TIMING: Identical root cause to Issue 1, plus fallback gap

### Problem

This is the same ordering bug as Issue 1, but there is a second failure mode.
Even after reordering, `create_project_from_github` in `vercel_client.py:60-101`
can fail to attach the GitHub integration (the Vercel GitHub App may not be
installed on the repo yet, or the installation ID is missing). When this happens,
the function falls back to creating a Vercel project *without* the git link
(lines 85-98). This unlinked project will NEVER auto-deploy from pushes.

The `commit_and_deploy` tool (engineer.py:180-199) also assumes auto-deploy and
does not check whether Vercel is actually linked. If it is not linked, the push
goes to GitHub but nothing deploys.

### Location

- `src/openclaw/integrations/vercel_client.py`, lines 83-98 (silent fallback to no-git project)
- `src/openclaw/agents/engineer.py`, lines 180-199 (`commit_and_deploy` has no fallback deploy)

### Fix

**A. Make `create_project_from_github` return a clear `linked` flag:**

Already returns `link` in the response object, but the fallback path (line 97)
returns a project with no `link` key. Add an explicit flag:

```python
        if resp2.status_code in (200, 201):
            data = resp2.json()
            logger.warning("vercel_project_created_no_git", name=data.get("name"))
            await _disable_protection(client, project_name)
            data["_openclaw_git_linked"] = False  # Explicit flag
            return data

    # ...and in the success path (line 78):
        if resp.status_code == 200 or resp.status_code == 201:
            data = resp.json()
            logger.info("vercel_project_created", name=data.get("name"), id=data.get("id"))
            await _disable_protection(client, project_name)
            data["_openclaw_git_linked"] = True
            return data
```

**B. Make `commit_and_deploy` fall back to direct Vercel deploy when not git-linked.**

In `engineer.py`, replace the `commit_and_deploy` handler:

```python
        elif tool_name == "commit_and_deploy":
            from openclaw.integrations.github_client import get_authenticated_user, push_directory
            from openclaw.integrations.vercel_client import get_latest_deployment, deploy_directory

            # Push to GitHub
            user = await get_authenticated_user()
            repo_full_name = f"{user}/{project_name}"

            push_result = await push_directory(
                repo_full_name,
                project_dir,
                commit_message=tool_input["commit_message"],
            )

            # Wait briefly for webhook-triggered deploy
            import asyncio
            await asyncio.sleep(5)
            deployment = await get_latest_deployment(project_name)

            if deployment and deployment.get("readyState") in ("BUILDING", "READY", "QUEUED"):
                return {
                    "status": "committed_and_deploying",
                    "commit": push_result.get("commit_sha", "")[:8],
                    "deploy_url": f"https://{deployment.get('url', '')}",
                    "deploy_state": deployment.get("readyState"),
                    "note": "Vercel auto-deployed from GitHub push",
                }

            # Fallback: upload directly to Vercel
            logger.warning("vercel_auto_deploy_missed", project=project_name)
            direct_deploy = await deploy_directory(project_name, project_dir)
            return {
                "status": "committed_and_deployed_directly",
                "commit": push_result.get("commit_sha", "")[:8],
                "deploy_url": direct_deploy.get("url", ""),
                "deploy_state": direct_deploy.get("readyState"),
                "files_deployed": direct_deploy.get("files_deployed"),
                "note": "Vercel webhook did not fire; deployed via direct upload fallback",
            }
```

---

## Summary of changes by file

| File | Changes |
|------|---------|
| `src/openclaw/agents/base.py` | Make `max_turns` a class attribute (default 10), use `self.max_turns` in run loop, add turn-limit warning log |
| `src/openclaw/agents/engineer.py` | Reorder scaffold (Vercel before push), add fallback deploy trigger, replace nested `self.run()` with single-shot API call + project context, set `max_turns = 30`, add `_gather_project_context` helper, add deploy fallback in `commit_and_deploy` |
| `src/openclaw/agents/ceo.py` | Rewrite result-handler prompt to forbid re-delegation of completed tasks |
| `src/openclaw/agents/worker.py` | Add Redis SET dedup check before `process_task`, skip duplicates |
| `src/openclaw/agents/inbound.py` | Replace `store_prospect` blind insert with select-then-upsert |
| `src/openclaw/integrations/vercel_client.py` | Add `_openclaw_git_linked` flag to both success and fallback paths |

## Execution order

1. Fix Issue 1 + 6 together (both are scaffold ordering)
2. Fix Issue 5 (standalone DB fix, low risk)
3. Fix Issue 4 (context loss, standalone engineer change)
4. Fix Issue 3 (turn limits, base + engineer change)
5. Fix Issue 2 (dedup, touches worker + ceo + base)

Issues 1+6 and 5 are the highest-severity bugs (silent deployment failure and
data loss respectively). Issues 3 and 4 are high severity (sites never deploy,
code quality is wrong). Issue 2 is medium severity (wasted compute, but
eventually converges).
