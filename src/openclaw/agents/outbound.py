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
- If prospect data is missing or incomplete, do NOT make things up. Write a shorter, more general email based on what you know from the task description.
- You MUST ALWAYS save a draft using gmail_draft, even if data is limited. Use "?" as the to address if you don't have a contact email. The owner will fill it in.
- NEVER refuse to draft. NEVER say you need more info. Just draft the best email you can with what you have.
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
