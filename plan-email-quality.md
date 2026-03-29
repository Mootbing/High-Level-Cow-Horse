# Email Quality Improvement Plan -- OpenClaw Outbound Agent

**Date:** 2026-03-28
**Scope:** `src/openclaw/agents/outbound.py`, delegation pipeline from CEO/PM agents

---

## Problem Statement

The current outbound agent produces generic, templated-feeling emails because:

1. **The system prompt is vague.** It says "reference their current branding" but gives no structure, tone guidance, or word-count constraint. Claude will default to a sales-pitch format.
2. **The prospect data never reaches the outbound agent.** When the CEO agent delegates to outbound, it passes only `{"prompt": tool_input["task_description"], ...}` -- a freeform string. None of the structured fields from the `Prospect` model (company_name, brand_colors, tagline, industry, tech_stack, fonts, contact_emails) are included.
3. **No subject-line strategy.** The prompt says nothing about subject lines. Claude picks whatever it wants, often generic ("Transform Your Web Presence").
4. **No email structure constraint.** Without explicit structure, Claude rambles or front-loads a sales pitch before establishing any relevance.

---

## 1. PERSONALIZATION -- System Prompt Rewrite Principles

The new system prompt must instruct Claude to:

| Requirement | Current State | Target State |
|---|---|---|
| Use prospect's company name | Mentioned vaguely | Mandatory -- first sentence |
| Reference brand colors | Not mentioned | Cite specific hex values and suggest improvements |
| Reference tagline / positioning | Not mentioned | Mirror their language back to them |
| Reference industry | Not mentioned | Tailor value prop to their vertical |
| Mention specific website weaknesses | "reference specific details" (no guidance) | Call out concrete UX/design/speed issues from scraped data |
| Tone | "professional, non-spammy" | Warm, consultative, peer-to-peer -- like a designer friend pointing something out |
| Length | No constraint | Hard cap at 150 words body (excluding signature) |
| CTA | Not defined | Soft CTA -- question, not demand |

---

## 2. CONTEXT PASSING -- Bridging Inbound Data to Outbound

### Current Data Flow (broken)

```
Owner: "send outreach to example.com"
  -> CEO agent delegates to outbound with:
     { "prompt": "Send outreach email to example.com", "source": "ceo" }
  -> Outbound agent receives a bare URL -- no prospect data
  -> Claude has to hallucinate or write generically
```

### Target Data Flow (fixed)

```
Owner: "send outreach to example.com"
  -> CEO agent (or outbound agent itself) queries DB for Prospect where url = example.com
  -> Outbound agent receives:
     {
       "prompt": "Draft a cold outreach email for this prospect.",
       "prospect": {
         "company_name": "Acme Corp",
         "url": "https://acme.com",
         "tagline": "Better widgets for a better world",
         "industry": "Manufacturing",
         "brand_colors": ["#1a2b3c", "#ff6600"],
         "fonts": ["Inter", "Georgia"],
         "tech_stack": ["WordPress", "WooCommerce"],
         "contact_emails": ["hello@acme.com"],
         "website_issues": "Slow load time, no mobile optimization, outdated hero section"
       }
     }
```

### Implementation (in outbound.py)

The outbound agent should **look up the prospect from the database itself** when it receives a URL or company name. This keeps the delegation interface simple and makes outbound self-sufficient.

Add a `lookup_prospect` tool so Claude can pull the data:

```python
LOOKUP_PROSPECT_TOOL = {
    "name": "lookup_prospect",
    "description": "Look up scraped prospect data from the database by URL or company name. ALWAYS call this before drafting an email.",
    "input_schema": {
        "type": "object",
        "properties": {
            "url": {"type": "string", "description": "Prospect website URL."},
            "company_name": {"type": "string", "description": "Company name to search for."},
        },
    },
}
```

This way, even if the CEO just passes a bare URL, the outbound agent can hydrate all the prospect fields itself.

---

## 3. PROMPT ENGINEERING -- New OUTBOUND_SYSTEM_PROMPT

```
OUTBOUND_SYSTEM_PROMPT = """You are the Outbound Email Writer for OpenClaw, a premium digital design agency that builds high-end scrolling websites.

YOUR WORKFLOW -- follow these steps in order, every time:
1. Use lookup_prospect to pull the prospect's full profile from the database.
2. Study their data: company name, tagline, industry, brand colors, fonts, tech stack, and any website issues noted in raw_data.
3. Draft one email using the structure and rules below.
4. Use gmail_draft to save it. Do NOT send it -- the agency owner reviews and approves every email.

EMAIL STRUCTURE (follow this exactly):
- SUBJECT LINE: Personalized, under 60 characters. Reference their company name or a specific observation about their site. No clickbait. No ALL CAPS.
- GREETING: "Hi [First Name]," -- if you only have a generic email like info@ or hello@, use "Hi [Company Name] team,".
- HOOK (1-2 sentences): Reference something specific and positive about their business -- their tagline, a product, their mission, a recent post. Show you actually looked at their site.
- OBSERVATION (1-2 sentences): Point out ONE concrete thing about their website that could be better. Be specific: slow load time, dated design, missing mobile optimization, weak hero section, no scroll animations. Do NOT be insulting -- frame it as an opportunity.
- VALUE PROP (1-2 sentences): Explain what OpenClaw does and why it matters for their specific industry. Connect it to the observation. Mention a concrete outcome (faster load, higher conversions, modern feel).
- CTA (1 sentence): Ask a low-commitment question. Examples: "Would it be worth a quick look at what a refreshed [company name] site could look like?" or "Want me to put together a free mockup?" Never say "book a call" or "schedule a demo" in a cold email.
- SIGN-OFF: "Best," followed by the sender name on the next line.

RULES:
- Total email body MUST be under 150 words. Shorter is better. Every sentence must earn its place.
- Tone: Warm, direct, human. Write like a skilled designer who genuinely noticed something -- not a salesperson working a list.
- NEVER use these phrases: "I hope this email finds you well", "I came across your website", "I wanted to reach out", "in today's digital landscape", "take your brand to the next level", "synergy", "leverage", "circle back".
- NEVER use exclamation marks in the subject line.
- Reference at least ONE specific detail from the prospect data (brand color, tech stack, tagline, industry).
- If the prospect uses WordPress or an older tech stack, note that a modern Next.js build would be significantly faster -- but frame it as an upgrade, not a criticism.
- If brand colors are available, you may suggest how a refined palette using those colors could modernize their look.
- Write the body as clean HTML. Use <p> tags for paragraphs. No inline styles, no images, no fancy formatting. Plain and readable.
- If prospect data is missing or incomplete, do NOT make things up. Write a shorter, more general email and note in your response that data was limited.
"""
```

---

## 4. SUBJECT LINES -- 5 Personalized Templates with High Open Rates

These templates use variables from the prospect data. Each is under 60 characters.

| # | Template | Example | Why It Works |
|---|---|---|---|
| 1 | `Quick thought on {company_name}'s site` | "Quick thought on Bloom Bakery's site" | Curiosity + specificity. Not salesy. Feels like a peer observation. |
| 2 | `{company_name} + faster load times` | "Acme Corp + faster load times" | Names a concrete benefit. The "+" format is concise and scannable. |
| 3 | `Your {industry} site deserves better UX` | "Your fitness site deserves better UX" | Flattering (says the business deserves more), industry-specific. |
| 4 | `Noticed something on {url_domain}` | "Noticed something on bloomcoffee.com" | Triggers curiosity. Feels personal, not mass-mailed. |
| 5 | `One idea for {company_name}` | "One idea for Riverview Dental" | Low-commitment framing. "One idea" signals brevity and respect for their time. |

**Anti-patterns to avoid:**
- "Transform Your Digital Presence" (generic, salesy)
- "EXCLUSIVE OFFER Inside!" (spam trigger)
- "Let's Connect!" (vapid, no value signal)
- Anything over 60 characters (gets truncated on mobile)

---

## 5. EMAIL STRUCTURE -- The Ideal Anatomy

```
SUBJECT: Quick thought on {company_name}'s site

Hi {first_name or company_name team},

[HOOK -- 1-2 sentences]
I was looking at {company_name} and really liked {specific positive detail -- their
tagline, a product line, their mission statement}. {Brief genuine compliment.}

[OBSERVATION -- 1-2 sentences]
One thing I noticed: {specific website issue -- e.g., "your homepage takes about
6 seconds to load on mobile" or "the hero section doesn't have any scroll
animations, which is a missed opportunity for a brand as visual as yours"}.

[VALUE PROP -- 1-2 sentences]
At OpenClaw, we build fast, modern scrolling websites specifically for
{industry} brands. {Concrete outcome tied to the observation -- e.g.,
"A Next.js rebuild could cut that load time to under 2 seconds and give
visitors a reason to keep scrolling."}.

[CTA -- 1 sentence, question format]
Would it be worth putting together a quick mockup to show what a refreshed
{company_name} site could look like?

Best,
{Sender name}
```

**Word count target:** 100-150 words. The email above is ~120 words.

**Why this structure works:**
- **Hook first, pitch last.** The recipient sees you actually looked at their business before you ask for anything.
- **One observation, not a laundry list.** Multiple criticisms feel like an attack. One focused point feels like helpful advice.
- **Question CTA, not demand CTA.** "Would it be worth..." is deferential and easy to say yes to. "Book a call" is a commitment most cold prospects will refuse.
- **No filler.** Every sentence either builds trust or delivers value. Nothing is there just to be polite.

---

## 6. COMPLETE UPDATED `outbound.py`

This is the full replacement for `src/openclaw/agents/outbound.py`:

```python
from __future__ import annotations

import json
import structlog

from openclaw.agents.base import BaseAgent
from openclaw.agents.registry import register_agent

logger = structlog.get_logger()

OUTBOUND_SYSTEM_PROMPT = """\
You are the Outbound Email Writer for OpenClaw, a premium digital design agency that builds high-end scrolling websites.

YOUR WORKFLOW -- follow these steps in order, every time:
1. Use lookup_prospect to pull the prospect's full profile from the database.
2. Study their data: company name, tagline, industry, brand colors, fonts, tech stack, and any website issues noted in raw_data.
3. Draft one email using the structure and rules below.
4. Use gmail_draft to save it. Do NOT send it -- the agency owner reviews and approves every email.

EMAIL STRUCTURE (follow this exactly):
- SUBJECT LINE: Personalized, under 60 characters. Reference their company name or a specific observation about their site. No clickbait. No ALL CAPS.
- GREETING: "Hi [First Name]," -- if you only have a generic email like info@ or hello@, use "Hi [Company Name] team,".
- HOOK (1-2 sentences): Reference something specific and positive about their business -- their tagline, a product, their mission, a recent post. Show you actually looked at their site.
- OBSERVATION (1-2 sentences): Point out ONE concrete thing about their website that could be better. Be specific: slow load time, dated design, missing mobile optimization, weak hero section, no scroll animations. Do NOT be insulting -- frame it as an opportunity.
- VALUE PROP (1-2 sentences): Explain what OpenClaw does and why it matters for their specific industry. Connect it to the observation. Mention a concrete outcome (faster load, higher conversions, modern feel).
- CTA (1 sentence): Ask a low-commitment question. Examples: "Would it be worth a quick look at what a refreshed [company name] site could look like?" or "Want me to put together a free mockup?" Never say "book a call" or "schedule a demo" in a cold email.
- SIGN-OFF: "Best," followed by the sender name on the next line.

RULES:
- Total email body MUST be under 150 words. Shorter is better. Every sentence must earn its place.
- Tone: Warm, direct, human. Write like a skilled designer who genuinely noticed something -- not a salesperson working a list.
- NEVER use these phrases: "I hope this email finds you well", "I came across your website", "I wanted to reach out", "in today's digital landscape", "take your brand to the next level", "synergy", "leverage", "circle back".
- NEVER use exclamation marks in the subject line.
- Reference at least ONE specific detail from the prospect data (brand color, tech stack, tagline, industry).
- If the prospect uses WordPress or an older tech stack, note that a modern Next.js build would be significantly faster -- but frame it as an upgrade, not a criticism.
- If brand colors are available, you may suggest how a refined palette using those colors could modernize their look.
- Write the body as clean HTML. Use <p> tags for paragraphs. No inline styles, no images, no fancy formatting. Plain and readable.
- If prospect data is missing or incomplete, do NOT make things up. Write a shorter, more general email and note in your response that data was limited.
"""

LOOKUP_PROSPECT_TOOL = {
    "name": "lookup_prospect",
    "description": (
        "Look up scraped prospect data from the database by URL or company name. "
        "ALWAYS call this FIRST before drafting any email."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "Prospect website URL (full or partial).",
            },
            "company_name": {
                "type": "string",
                "description": "Company name to search for.",
            },
        },
    },
}

GMAIL_DRAFT_TOOL = {
    "name": "gmail_draft",
    "description": (
        "Save an email as a draft for owner review. The email will NOT be sent "
        "immediately -- it will appear in the dashboard for approval."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "to": {"type": "string", "description": "Recipient email address."},
            "subject": {"type": "string", "description": "Email subject line (under 60 chars, personalized)."},
            "body": {"type": "string", "description": "Email body in clean HTML (under 150 words)."},
        },
        "required": ["to", "subject", "body"],
    },
}


@register_agent("outbound")
class OutboundAgent(BaseAgent):
    agent_type = "outbound"
    system_prompt = OUTBOUND_SYSTEM_PROMPT
    tools = [LOOKUP_PROSPECT_TOOL, GMAIL_DRAFT_TOOL]

    async def handle_tool_call(self, tool_name: str, tool_input: dict) -> dict:
        if tool_name == "lookup_prospect":
            return await self._lookup_prospect(tool_input)
        elif tool_name == "gmail_draft":
            return await self._save_draft(tool_input)
        return await super().handle_tool_call(tool_name, tool_input)

    async def _lookup_prospect(self, tool_input: dict) -> dict:
        """Query the prospects table and return structured data for email personalization."""
        from openclaw.db.session import async_session_factory
        from openclaw.models.prospect import Prospect
        from sqlalchemy import select, or_

        url = tool_input.get("url", "").strip()
        company_name = tool_input.get("company_name", "").strip()

        if not url and not company_name:
            return {"error": "Provide at least a url or company_name to look up."}

        async with async_session_factory() as session:
            conditions = []
            if url:
                # Match on exact URL or URL containing the input (handles partial matches)
                conditions.append(Prospect.url.ilike(f"%{url}%"))
            if company_name:
                conditions.append(Prospect.company_name.ilike(f"%{company_name}%"))

            result = await session.execute(
                select(Prospect).where(or_(*conditions)).limit(1)
            )
            prospect = result.scalar_one_or_none()

        if not prospect:
            return {
                "found": False,
                "message": (
                    f"No prospect found for url='{url}' company_name='{company_name}'. "
                    "The inbound agent may not have scraped this prospect yet. "
                    "Write a shorter, more general email and note that data was limited."
                ),
            }

        # Build a rich context object for Claude to use in personalization
        raw = prospect.raw_data or {}
        metadata = raw.get("metadata", {}) if isinstance(raw, dict) else {}
        markdown_preview = ""
        if isinstance(raw, dict) and raw.get("markdown"):
            # Give Claude the first 3000 chars of site content for additional context
            markdown_preview = raw["markdown"][:3000]

        return {
            "found": True,
            "prospect_id": str(prospect.id),
            "url": prospect.url,
            "company_name": prospect.company_name or "Unknown",
            "tagline": prospect.tagline or "",
            "industry": prospect.industry or "Unknown",
            "contact_emails": prospect.contact_emails or [],
            "brand_colors": prospect.brand_colors or [],
            "fonts": prospect.fonts or [],
            "logo_url": prospect.logo_url or "",
            "social_links": prospect.social_links or {},
            "tech_stack": prospect.tech_stack or [],
            "page_title": metadata.get("title", ""),
            "page_description": metadata.get("description", ""),
            "content_preview": markdown_preview,
        }

    async def _save_draft(self, tool_input: dict) -> dict:
        """Save the email as a draft and link it to the prospect record."""
        from openclaw.db.session import async_session_factory
        from openclaw.models.email_log import EmailLog
        from openclaw.models.prospect import Prospect
        from openclaw.tools.messaging import publish_dashboard_event
        from sqlalchemy import select

        to_email = tool_input["to"]
        subject = tool_input["subject"]
        body = tool_input["body"]

        async with async_session_factory() as session:
            # Try to link the draft to a prospect by matching the recipient email
            prospect_id = None
            result = await session.execute(
                select(Prospect).where(
                    Prospect.contact_emails.op("@>")(f'["{to_email}"]')
                ).limit(1)
            )
            prospect = result.scalar_one_or_none()
            if prospect:
                prospect_id = prospect.id

            log = EmailLog(
                prospect_id=prospect_id,
                to_email=to_email,
                subject=subject,
                body=body,
                status="draft",
            )
            session.add(log)
            await session.commit()
            await session.refresh(log)
            draft_id = str(log.id)

        # Notify dashboard that a new draft is ready for review
        await publish_dashboard_event({
            "type": "email_draft",
            "draft_id": draft_id,
            "to": to_email,
            "subject": subject,
            "prospect_id": str(prospect_id) if prospect_id else None,
        })

        logger.info(
            "email_draft_saved",
            draft_id=draft_id,
            to=to_email,
            prospect_id=str(prospect_id) if prospect_id else None,
        )
        return {
            "status": "draft_saved",
            "draft_id": draft_id,
            "to": to_email,
            "prospect_linked": prospect_id is not None,
            "message": "Email saved as draft. Owner will review and approve from the dashboard.",
        }
```

---

## 7. MIGRATION CHECKLIST

These are the concrete code changes required, in priority order:

- [ ] **Replace `src/openclaw/agents/outbound.py`** with the code in Section 6 above.
- [ ] **Verify the JSON containment query** for `contact_emails` works with your database (PostgreSQL `@>` operator on JSON columns). If using SQLite for dev, replace with a LIKE-based fallback.
- [ ] **No changes needed to `ceo.py` or `project_manager.py`.** The delegation payload stays the same -- the outbound agent now self-serves its own data via `lookup_prospect`.
- [ ] **Recommended workflow change:** Before delegating to outbound, the CEO agent should ensure inbound has already scraped the prospect. If not, delegate to inbound first, then outbound. Add this to the CEO system prompt:
  ```
  When the owner asks to send outreach to a prospect:
  1. First delegate to inbound to scrape the prospect's website (if not already done).
  2. Then delegate to outbound to draft the email.
  Do NOT delegate to outbound without scraping first -- the email quality depends on having prospect data.
  ```
- [ ] **Test with a real prospect URL** to verify the full pipeline: inbound scrape -> outbound lookup -> personalized draft -> dashboard review.

---

## 8. BEFORE / AFTER COMPARISON

### BEFORE (current system output, typical)

```
Subject: Transform Your Web Presence with OpenClaw

Hi there,

I hope this email finds you well. I came across your website and was impressed
by what you've built. However, I noticed there are some opportunities to enhance
your digital presence.

At OpenClaw, we specialize in creating premium scrolling websites that captivate
visitors and drive conversions. We'd love to help take your brand to the next level.

Would you be open to a quick call to discuss how we can help? I'd be happy to
share some examples of our recent work.

Looking forward to hearing from you!

Best regards,
OpenClaw Team
```

**Problems:** Generic greeting, no company name, no specific observation, banned phrases everywhere ("I hope this email finds you well", "take your brand to the next level"), no industry relevance, vague CTA ("quick call"), 120+ words of filler.

### AFTER (expected output with new system)

```
Subject: Quick thought on Bloom Bakery's site

Hi Bloom Bakery team,

Your "Baked fresh, delivered faster" tagline is great -- it immediately tells me
what you're about. The product photography on your homepage is strong too.

One thing: your site takes about 5 seconds to load on mobile, and the menu page
doesn't scroll smoothly on smaller screens. For a food brand where people are
ordering on their phones, that's leaving sales on the table.

We build fast, modern websites for food and hospitality brands. A Next.js rebuild
with your existing warm palette (#D4A373, #FEFAE0) could cut load time to under
2 seconds and make browsing your menu feel effortless.

Would it be worth putting together a quick mockup for Bloom Bakery?

Best,
James
```

**Improvements:** Uses company name (3x), references tagline verbatim, cites specific brand colors, identifies a concrete problem (mobile load time), ties the value prop to their industry (food/ordering), soft CTA, 130 words, zero filler.
