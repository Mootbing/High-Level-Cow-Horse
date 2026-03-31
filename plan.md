# Clarmi Design Studio — Exhaustive Client-Direct Automation Flows

## Current System Inventory

Before detailing the flows, here is what exists today and where the gaps are.

**Existing MCP tools**: `create_project`, `get_project_status`, `update_project_status`, `list_projects`, `store_prospect`, `lookup_prospect`, `scaffold_nextjs`, `list_files`, `read_code`, `edit_code`, `write_code`, `verify_build`, `deploy`, `deploy_preview`, `approve_preview`, `generate_image`, `generate_video`, `take_screenshot`, `run_lighthouse`, `verify_url`, `draft_email`, `send_email`, `store_knowledge`, `analyze_project`, `log_metrics`

**Existing integrations**: GitHub (repos, branches, PRs, file push), Vercel (projects, deployments, protection), Gmail (OAuth2 send), WhatsApp (send text/image, receive webhooks), Google AI (image gen via Nano Banana, video gen via Veo 3)

**Existing DB models**: Project, Prospect, Task, Message, EmailLog, Asset, Deployment, AgentLog, KnowledgeBase, PromptVersion, ImprovementMetric

**What does NOT exist yet**: Any payment integration, any client self-service portal, any inbound lead capture, any automated follow-up sequences, any analytics reporting to clients, any referral mechanism, any formal sign-off workflow, any content collection forms, any scheduled content updates, any uptime monitoring, any cancellation flow.

---

## FLOW 1: Inbound Lead Capture via Landing Page

**Trigger**: Prospect visits clarmi.studio (or any marketing page) and submits a contact form or enters their website URL.

**Client interaction**: Prospect sees a landing page with a single input field: "Enter your website URL for a free audit." They submit the URL and optionally their email/phone. Within minutes, they receive a WhatsApp message or email containing a link to their personalized pitch deck.

**Agent actions**:
1. A webhook endpoint receives the form submission (URL, email, phone)
2. Agent calls `store_prospect(url, contact_emails, ...)` to create the prospect record
3. Agent calls `create_project(name, brief, client_phone)` to provision the project
4. Agent runs the full Research pipeline (WebFetch, extract branding, audit problems)
5. Agent runs the Pitch pipeline (generate HTML slide deck at `/pitch/`)
6. Agent calls `deploy(project_name, ...)` to publish the pitch
7. Agent calls `draft_email(to, subject, body)` with the pitch link -- this email can be auto-sent (no owner approval needed for inbound leads)
8. If phone provided, agent sends WhatsApp message with pitch link

**Owner involvement**: Notification only. Owner gets a WhatsApp summary: "New inbound lead: [Company] -- pitch deployed at [URL]. Prospect notified."

**Revenue impact**: Generates new leads without any owner prospecting effort. Converts passive traffic into qualified prospects. The speed of response (minutes vs days) dramatically increases conversion rates.

**Implementation complexity**: Medium

**New tools/infrastructure needed**:
- A public-facing landing page/form (could be a static Next.js page deployed to Vercel under clarmi.studio)
- A webhook endpoint MCP tool: `handle_inbound_lead(url, email, phone)` that orchestrates the full pipeline
- A new cron entry or OpenClaw session type for processing inbound leads from a queue
- New config: `INBOUND_AUTO_SEND: bool` to control whether emails to inbound leads skip owner approval
- New DB model or field: `Prospect.source` (inbound vs outbound) to track lead origin

---

## FLOW 2: Automated Lead Qualification and Scoring

**Trigger**: A new prospect record is created (either from inbound form or owner-initiated research).

**Client interaction**: None directly -- this is a background scoring step. However, the score determines what happens next (auto-pitch vs manual review).

**Agent actions**:
1. After `store_prospect` completes, agent evaluates qualification criteria:
   - Tech stack (WordPress/Wix/Squarespace = high opportunity; already on modern stack = lower)
   - Number and severity of `site_problems`
   - Industry (restaurants, salons, contractors = ideal; enterprise = wrong fit)
   - Existing site quality (poor Lighthouse score = high opportunity)
   - Business signals (social presence, reviews, Google Business listing)
2. Agent calls a new tool `score_prospect(prospect_id, criteria)` that saves a numeric score and tier (hot/warm/cold)
3. Hot leads: auto-generate pitch + deploy + send email (full pipeline, no owner)
4. Warm leads: auto-generate pitch + deploy, notify owner to review before outreach
5. Cold leads: store data, notify owner, do nothing else

**Owner involvement**: None for hot leads. Notification for warm. Review required for cold (owner decides whether to pursue).

**Revenue impact**: Focuses effort on highest-probability prospects. Prevents wasting compute and API costs on poor-fit leads.

**Implementation complexity**: Low

**New tools needed**:
- `score_prospect(prospect_id, tech_stack_score, problem_severity, industry_fit, overall_score, tier)` MCP tool
- New DB fields on Prospect: `qualification_score: Float`, `qualification_tier: String` (hot/warm/cold)
- Scoring logic can live entirely in the system prompt or as a new service

---

## FLOW 3: Self-Service Client Onboarding Questionnaire

**Trigger**: Prospect accepts the pitch (responds to email/WhatsApp saying "yes" or "interested").

**Client interaction**: Agent sends a structured onboarding message via WhatsApp (or a link to a simple form page). The questionnaire collects:
- Business name, tagline, description
- Target audience
- Key pages needed (Home, About, Services, Contact, Menu, etc.)
- Preferred style/vibe (modern, classic, bold, minimal)
- Must-have features (booking, menu, gallery, testimonials)
- Content readiness ("Do you have logo files, photos, copy ready?")
- Timeline expectations
- Budget confirmation

The client responds conversationally via WhatsApp, and the agent parses each answer, asks follow-ups if needed, and marks the onboarding as complete when all required fields are filled.

**Agent actions**:
1. Detect "interested" / "yes" intent from client message
2. Send onboarding questionnaire via WhatsApp as a series of messages (or a single structured message with numbered questions)
3. Parse each client response, store in a new `ClientOnboarding` record
4. If a response is ambiguous, ask a clarifying question
5. Once all required fields are filled, call `update_project_status(project_id, "onboarded")` and notify owner
6. Automatically populate the project brief with onboarding data

**Owner involvement**: Notification only when onboarding completes. Owner gets a summary: "Onboarding complete for [Company]. Brief: [summary]. Ready to start design."

**Revenue impact**: Eliminates 3-5 back-and-forth conversations the owner currently has with each new client. Saves 30-60 minutes per project.

**Implementation complexity**: Medium

**New tools needed**:
- `send_onboarding_questionnaire(project_id, client_phone)` MCP tool
- `save_onboarding_response(project_id, field, value)` MCP tool
- `get_onboarding_status(project_id)` MCP tool
- New DB model: `ClientOnboarding` with fields for each questionnaire answer, linked to Project
- System prompt additions for the conversational onboarding flow

---

## FLOW 4: WhatsApp-Based Content Collection

**Trigger**: Agent determines that content/assets are needed from the client (after onboarding, or when building the site).

**Client interaction**: Agent sends specific, actionable requests via WhatsApp:
- "Can you send me your logo? A PNG or SVG with a transparent background works best."
- "I need 5-10 photos of your restaurant/shop/team. Just drop them here."
- "What are your current business hours?"
- "Can you share your menu/price list?"

Client responds with text, images, PDFs, or documents directly in WhatsApp. Agent processes each.

**Agent actions**:
1. Agent sends targeted content requests via WhatsApp (`send_text_message`)
2. When client sends images: agent receives via webhook, downloads media using WhatsApp Media API, stores in project assets
3. When client sends text: agent parses and stores (hours, menu items, pricing, etc.) into project metadata
4. When client sends documents (PDF menu, price list): agent downloads, extracts text (OCR/parsing), stores structured data
5. Agent tracks which content has been received vs still pending
6. Agent sends reminders if content is outstanding after 24/48 hours
7. Once all content is collected, agent notifies that the build can proceed

**Owner involvement**: None. Agent handles the entire content collection loop.

**Revenue impact**: Eliminates the biggest time sink in web design -- chasing clients for content. Saves hours per project and prevents projects from stalling.

**Implementation complexity**: Medium-High

**New tools needed**:
- `download_whatsapp_media(media_id)` MCP tool (WhatsApp Media API)
- `store_client_asset(project_id, asset_type, content_bytes, filename)` MCP tool
- `get_content_checklist(project_id)` MCP tool -- returns what has been received and what is still needed
- `send_content_reminder(project_id)` MCP tool
- New DB model: `ContentItem` (project_id, item_type [logo, photos, menu, hours, etc.], status [pending, received], content_data)
- New cron: content reminder cron that checks for stale content requests

---

## FLOW 5: Interactive Design Direction Selection

**Trigger**: Research is complete, design phase is about to begin.

**Client interaction**: Agent generates 2-3 design direction options (different color palettes, typography pairings, mood references) and sends them to the client via WhatsApp as image collages or styled HTML pages. Client responds with their preference: "I like option 2" or "Can we mix the colors from 1 with the layout from 3?"

**Agent actions**:
1. Agent uses `generate_image` to create 2-3 mood board / style tile images showing different design directions
2. Agent sends images to client via `send_media_message` with descriptions
3. Agent parses client preference and stores the chosen direction in project metadata
4. If client wants a mix, agent creates a refined option and sends for confirmation
5. Once approved, the chosen direction informs all subsequent `generate_image` and build prompts

**Owner involvement**: None.

**Revenue impact**: Reduces revision cycles later (client has buy-in on direction from the start). Makes the client feel involved. Prevents the "this isn't what I wanted" problem.

**Implementation complexity**: Medium

**New tools needed**:
- `generate_style_tiles(project_id, num_options)` MCP tool -- generates 2-3 mood boards using Google AI
- `store_design_direction(project_id, chosen_option, notes)` MCP tool
- System prompt additions for handling design preference conversations

---

## FLOW 6: Structured Build Feedback via Annotated Screenshots

**Trigger**: Initial build is deployed and shared with client for review.

**Client interaction**: Agent sends the client a link to the deployed preview plus screenshots at multiple viewports. Client can respond via WhatsApp with specific feedback. Agent parses feedback into actionable items. For example:
- "The phone number is wrong, it should be 555-1234"
- "Can you make the header bigger?"
- "I don't like the blue, can we try green?"
- Client can also send annotated screenshots (draw on them with WhatsApp's markup tool)

**Agent actions**:
1. After `deploy_preview`, agent calls `take_screenshot` at multiple viewports
2. Agent sends screenshots to client via `send_media_message` with captions: "Here's how your site looks on desktop / tablet / mobile"
3. Agent sends preview URL: "You can also view the live preview here: [URL]"
4. When client responds with feedback, agent parses it into structured change requests
5. For each change request, agent runs the revision cycle: `read_code` -> `edit_code` -> `verify_build` -> `deploy_preview`
6. Agent sends updated screenshots and asks "How does this look?"
7. Loop until client says it looks good
8. Agent calls `approve_preview` to merge to production

**Owner involvement**: None. This is the existing Client Funnel, enhanced with proactive screenshot sharing.

**Revenue impact**: Faster feedback cycles. Client feels in control. Reduces miscommunication.

**Implementation complexity**: Low (mostly system prompt refinements, slight enhancements to existing flow)

**New tools needed**:
- `send_preview_with_screenshots(project_id, preview_url)` -- convenience tool that takes screenshots and sends them via WhatsApp
- `parse_feedback(client_message)` -- could be a prompt/system-prompt capability rather than a tool

---

## FLOW 7: Formal QA Sign-Off and Contract Acceptance

**Trigger**: Build feedback cycle is complete; site is ready for launch.

**Client interaction**: Agent sends a formal sign-off message:
> "Your site is ready for launch. Here's a final summary:
> - Live preview: [URL]
> - Lighthouse scores: Performance 92, Accessibility 96, SEO 94
> - Pages: Home, About, Services, Contact, Gallery
> - Mobile-optimized and tested across 4 viewport sizes
>
> Reply 'APPROVE' to launch it live, or let me know if there are any final changes."

Client replies "approve" (or similar affirmative). Agent records the sign-off timestamp, merges to production, and sends confirmation.

**Agent actions**:
1. Agent compiles a sign-off summary: deployed URL, Lighthouse scores, page list, screenshot links
2. Agent sends via WhatsApp
3. Agent waits for "APPROVE" or equivalent
4. On approval: `approve_preview` -> merge to main -> deploy to production
5. Store sign-off record: `record_signoff(project_id, client_phone, approved_at)`
6. Send confirmation: "Your site is live at [URL]. Welcome aboard."
7. Transition project status to "launched"

**Owner involvement**: Notification only: "Client [Name] approved final site. Deployed to production."

**Revenue impact**: Creates a formal approval record (useful for disputes). Gives the client a professional experience. Clear handoff point from "build" to "maintenance."

**Implementation complexity**: Low

**New tools needed**:
- `record_signoff(project_id, approved_by, channel, notes)` MCP tool
- New DB model or new fields on Project: `signed_off_at: datetime`, `signed_off_by: str`
- New project status: "launched" (distinct from "deployed")

---

## FLOW 8: Automated Payment Collection via Stripe

**Trigger**: Client approves sign-off (Flow 7), or on a recurring monthly schedule for maintenance fees.

**Client interaction**: Agent sends a payment link via WhatsApp or email:
> "Here's your invoice for the initial build: $500
> Payment link: [Stripe Checkout URL]
>
> Your $50/month maintenance starts next month and will be billed automatically."

For recurring payments, Stripe handles the billing automatically via subscription. Client receives Stripe-generated receipts.

**Agent actions**:
1. After sign-off approval, agent calls `create_payment_link(project_id, amount, description)` to generate a Stripe Checkout session for the one-time build fee
2. Agent sends the payment link to client via WhatsApp
3. Stripe webhook fires when payment succeeds -> agent updates project status to "paid" and records the payment
4. Agent calls `create_subscription(project_id, client_email, plan)` to set up recurring billing
5. For payment failures: Stripe handles dunning; agent receives webhook and sends a gentle WhatsApp reminder
6. Agent can generate invoices on demand: `generate_invoice(project_id)`

**Owner involvement**: None for standard payments. Notification for payment failures after 3 dunning attempts.

**Revenue impact**: Direct revenue collection without owner intervention. Eliminates "forgetting to invoice" and "chasing payments." Recurring revenue is collected automatically. This is a critical bottleneck -- currently all payments are handled offline.

**Implementation complexity**: High

**New tools needed**:
- Stripe integration client: `src/openclaw/integrations/stripe_client.py`
  - `create_checkout_session(amount, currency, description, client_email, project_id)`
  - `create_subscription(client_email, price_id, metadata)`
  - `get_payment_status(session_id)`
  - `cancel_subscription(subscription_id)`
  - `create_invoice(project_id)`
- MCP tools: `create_payment_link`, `check_payment_status`, `create_subscription`, `cancel_subscription`
- Stripe webhook handler (new endpoint or integration with OpenClaw gateway)
- New DB model: `Payment` (project_id, stripe_session_id, amount, currency, status, paid_at)
- New DB model: `Subscription` (project_id, stripe_subscription_id, plan, status, current_period_end)
- New config: `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `STRIPE_PRICE_ID_MONTHLY`

---

## FLOW 9: Automated Post-Launch Uptime Monitoring

**Trigger**: Cron job (runs every 5 minutes for all "launched" projects).

**Client interaction**: If the site goes down, client receives a WhatsApp message:
> "We detected that your site [URL] may be experiencing issues. Our team is already investigating. We'll let you know as soon as it's resolved."

When resolved:
> "Your site is back online. The issue lasted approximately 12 minutes. No action needed on your end."

**Agent actions**:
1. Cron triggers: agent calls `list_projects(status="launched")` to get all live sites
2. For each site: `verify_url(deployed_url)` to check HTTP status
3. If a site returns non-200 or is unreachable:
   - Store incident: `create_incident(project_id, type="downtime", details)`
   - Check Vercel deployment status for errors
   - Attempt auto-recovery: `trigger_deployment(project_name)` to redeploy
   - Notify client via WhatsApp (if configured)
   - Notify owner via WhatsApp
4. On recovery: update incident, notify client and owner
5. Log uptime metrics: `log_uptime(project_id, status, response_time)`

**Owner involvement**: Notification only. Owner is informed of incidents but agent handles detection, attempted recovery, and client communication.

**Revenue impact**: Client retention -- clients feel their site is actively monitored. Prevents churn from undetected outages. Justifies the monthly maintenance fee.

**Implementation complexity**: Medium

**New tools needed**:
- `check_uptime(project_id)` MCP tool
- `create_incident(project_id, incident_type, details)` MCP tool
- `resolve_incident(incident_id, resolution_notes)` MCP tool
- New DB model: `Incident` (project_id, type, detected_at, resolved_at, duration_minutes, status)
- New DB model: `UptimeCheck` (project_id, checked_at, status_code, response_time_ms)
- New cron entry in `openclaw.json`: uptime check every 5 minutes

---

## FLOW 10: Automated Monthly Analytics Reports

**Trigger**: Cron job (1st of every month for all "launched" projects).

**Client interaction**: Client receives a WhatsApp message or email with a monthly report:
> "Here's your monthly site report for March 2026:
> - Lighthouse Performance: 94 (+2 from last month)
> - Lighthouse Accessibility: 97 (unchanged)
> - Lighthouse SEO: 96 (+1)
> - Site uptime: 99.97%
> - [If Vercel Analytics enabled] Unique visitors: 1,247 (+15%)
>
> Everything looks great. Your site continues to perform well."

**Agent actions**:
1. Cron triggers on the 1st of each month
2. For each launched project: `run_lighthouse(deployed_url)` for fresh scores
3. Query `UptimeCheck` records for the month to calculate uptime percentage
4. If Vercel Analytics API is integrated, pull visitor/pageview data
5. Compare to previous month's metrics (stored in `ImprovementMetric` or new `MonthlyReport` table)
6. Generate report text
7. Send to client via WhatsApp or email
8. Store report in DB for history

**Owner involvement**: None. Owner receives a summary of all client reports sent.

**Revenue impact**: Justifies the monthly fee. Clients see tangible value. Reduces churn. Creates upsell opportunities (when metrics are bad, agent can suggest improvements).

**Implementation complexity**: Medium

**New tools needed**:
- `generate_monthly_report(project_id, month, year)` MCP tool
- `send_client_report(project_id, report_content, channel)` MCP tool
- Vercel Analytics API integration (optional): `get_analytics(project_name, start_date, end_date)`
- New DB model: `MonthlyReport` (project_id, month, year, lighthouse_scores, uptime_pct, visitor_count, sent_at)
- New cron entry: monthly reporting on the 1st

---

## FLOW 11: Seasonal and Scheduled Content Updates

**Trigger**: Client sends a WhatsApp message like "We're changing our hours for the holidays" or "New summer menu starting June 1" -- OR a pre-scheduled date triggers automatically.

**Client interaction**:
- **Reactive**: Client sends content update via WhatsApp, agent processes it immediately using the existing Client Funnel
- **Proactive**: Agent sends a WhatsApp message before known events: "The holiday season is coming up -- do you have updated hours or a special menu you'd like on your site?"
- **Scheduled**: Client tells agent "On December 1st, switch to the winter menu" -- agent schedules the change and executes it automatically

**Agent actions**:
1. For proactive reminders: cron checks upcoming holidays/seasons and sends reminders to clients in relevant industries (restaurants, retail)
2. For scheduled changes: agent stores the scheduled update in a new `ScheduledUpdate` table
3. A cron job checks for due scheduled updates and executes them: `read_code` -> `edit_code` -> `verify_build` -> `deploy`
4. After execution, agent notifies client: "Your site has been updated with the winter menu as requested. Take a look: [URL]"

**Owner involvement**: None.

**Revenue impact**: Ongoing engagement keeps clients from forgetting about Clarmi. Demonstrates ongoing value. Could be an upsell: "Content update package: $20/month for up to 4 updates."

**Implementation complexity**: Medium

**New tools needed**:
- `schedule_content_update(project_id, description, execute_at, changes)` MCP tool
- `list_scheduled_updates(project_id)` MCP tool
- `cancel_scheduled_update(update_id)` MCP tool
- `send_seasonal_reminder(project_id, season)` MCP tool
- New DB model: `ScheduledUpdate` (project_id, description, execute_at, changes_json, status, executed_at)
- New cron: check for due scheduled updates (every hour)
- New cron: seasonal reminder check (weekly, compares date to holiday calendar)

---

## FLOW 12: Automated SEO Optimization Cycle

**Trigger**: Cron job (weekly for all launched projects).

**Client interaction**: Mostly invisible. If significant improvements are made, client gets a message:
> "We've optimized your site's SEO this week: added missing meta descriptions, improved image alt text, and updated your sitemap. Your SEO score improved from 88 to 95."

**Agent actions**:
1. Weekly cron triggers for all launched projects
2. Agent runs `run_lighthouse(deployed_url)` focusing on SEO category
3. Agent reads current site code: `list_files` -> `read_code` for key pages
4. Agent identifies SEO improvements:
   - Missing or poor `<meta>` descriptions
   - Missing `alt` text on images
   - Missing `<title>` tags or poor title structure
   - Missing structured data (JSON-LD for local business, restaurant, etc.)
   - Missing sitemap.xml or robots.txt
   - Missing Open Graph / Twitter card tags
   - Poor heading hierarchy
5. Agent makes improvements: `edit_code` for each fix
6. Agent runs `verify_build` -> `deploy`
7. Agent runs Lighthouse again to confirm improvement
8. If score improved meaningfully (5+ points), notify client

**Owner involvement**: None for small fixes. Notification for significant changes.

**Revenue impact**: Genuine ongoing value that justifies the monthly fee. Clients rank higher on Google. Creates a measurable, reportable improvement.

**Implementation complexity**: Medium

**New tools needed**:
- `audit_seo(project_id)` MCP tool -- runs Lighthouse + reads code to identify specific issues
- `generate_structured_data(project_id, business_type)` MCP tool -- creates JSON-LD schema markup
- `generate_sitemap(project_id)` MCP tool -- creates/updates sitemap.xml
- New cron: weekly SEO optimization

---

## FLOW 13: AI-Driven Upselling

**Trigger**: Multiple triggers: monthly report reveals opportunities, client site traffic plateaus, competitor analysis shows gaps, or after a set period post-launch.

**Client interaction**: Agent sends a targeted, data-backed upsell via WhatsApp:
> "I noticed your site doesn't have a booking/reservation system yet. Restaurants like yours typically see a 25% increase in reservations when they add online booking. Would you like me to add one? It's a $200 add-on."

Or:
> "Your site is 6 months old and performing well. I can add a blog section to help with SEO -- consistent content can increase your search traffic by 30-50% over 6 months. The add-on is $300 for setup + $30/month for content updates."

**Agent actions**:
1. After monthly report, agent analyzes the site for missing features common in the client's industry
2. Agent calls `lookup_prospect(url)` to check industry and original site problems
3. Agent identifies upsell opportunities:
   - Missing features: booking, e-commerce, blog, newsletter, chat widget, gallery, testimonials section
   - Performance upgrades: CDN optimization, image optimization, lazy loading
   - New pages: FAQ, careers, events, menu (seasonal)
   - Ongoing services: blog writing, social media integration, email marketing
4. Agent crafts a personalized upsell message with data backing
5. Agent sends via WhatsApp
6. If client accepts, agent provisions a new task and begins work

**Owner involvement**: Owner can configure which upsells are auto-suggested vs require approval. Notification when an upsell is accepted.

**Revenue impact**: Direct incremental revenue. A single $200 upsell per quarter per client adds significant revenue at scale.

**Implementation complexity**: Medium

**New tools needed**:
- `identify_upsell_opportunities(project_id)` MCP tool
- `send_upsell_proposal(project_id, proposal)` MCP tool
- `accept_upsell(project_id, upsell_type, amount)` MCP tool
- New DB model: `Upsell` (project_id, type, description, amount, status [proposed, accepted, rejected, completed], proposed_at, accepted_at)
- Configuration for upsell rules per industry

---

## FLOW 14: Automated Referral Program

**Trigger**: 30 days after site launch (client has had time to be satisfied), or after a positive interaction (client approves a revision and says something enthusiastic).

**Client interaction**: Agent sends a referral request:
> "Glad you're happy with your site! If you know any other business owners who could use a website upgrade, I'd love to help them too. For every referral that signs up, you'll get one month of maintenance free ($50 value). Just have them mention your name, or share this link: [referral link]"

When a referred prospect signs up:
> "Great news! [Referred Company] just signed up thanks to your referral. Your next month of maintenance is on us."

**Agent actions**:
1. Timer-based trigger: 30 days post-launch, agent sends referral message
2. Agent generates a unique referral code/link for the client
3. When a new prospect arrives with a referral code: agent links the referral, credits the referrer
4. Agent notifies the referrer and applies the credit (discount on next Stripe invoice, or free month)
5. Track referral metrics: referrals sent, converted, credits issued

**Owner involvement**: None. Owner gets a monthly summary of referral activity.

**Revenue impact**: Free marketing. Each referral is a warm lead (much higher conversion than cold outreach). The $50 credit costs less than acquiring a new client through cold outreach.

**Implementation complexity**: Medium

**New tools needed**:
- `generate_referral_link(project_id)` MCP tool
- `track_referral(referrer_project_id, referred_prospect_id)` MCP tool
- `apply_referral_credit(referrer_project_id)` MCP tool
- New DB model: `Referral` (referrer_project_id, referred_prospect_id, referral_code, status, credit_applied, created_at)
- Integration with Stripe for credit/coupon application

---

## FLOW 15: Graceful Cancellation and Offboarding

**Trigger**: Client messages "I want to cancel" or stops paying (Stripe subscription lapses).

**Client interaction**:
- **Voluntary cancellation**: Agent responds empathetically and offers alternatives:
  > "I'm sorry to hear that. Before we cancel, I'd like to understand -- is there something we can improve? If it's about cost, we can discuss a reduced plan. If you're sure, I'll proceed with the offboarding process."
- **If client confirms cancellation**: Agent provides clear next steps:
  > "Your site will remain live for 30 more days. After that, we'll take it offline. If you'd like to transfer the domain or get your site files, let me know and I'll package everything up."
- **Involuntary (payment failure)**: Agent sends escalating reminders before eventual offboarding.

**Agent actions**:
1. Detect cancellation intent from client message
2. Run retention attempt: offer discount, ask for feedback, propose alternative plan
3. If client confirms: `update_project_status(project_id, "cancelling")`
4. Cancel Stripe subscription: `cancel_subscription(subscription_id)`
5. Schedule site takedown 30 days out: `schedule_offboarding(project_id, takedown_date)`
6. On takedown date: export site files (zip), share with client, then remove from Vercel
7. Record cancellation reason for analytics

**Owner involvement**: Notification when cancellation is requested. Owner can intervene if desired.

**Revenue impact**: Retention attempts can save 10-20% of cancellations. Graceful offboarding preserves reputation (client may return or refer others). Cancellation reason data informs product improvements.

**Implementation complexity**: Medium

**New tools needed**:
- `initiate_offboarding(project_id, reason)` MCP tool
- `export_site_files(project_id)` MCP tool -- packages all code/assets into a downloadable zip
- `schedule_offboarding(project_id, takedown_date)` MCP tool
- `execute_offboarding(project_id)` MCP tool -- removes from Vercel, archives repo
- New DB model: `CancellationRecord` (project_id, reason, requested_at, retention_attempted, final_action, executed_at)
- New project statuses: "cancelling", "cancelled", "archived"

---

## FLOW 16: Emergency Support (Site Down / Broken Page / Urgent Fix)

**Trigger**: Client sends an urgent message via WhatsApp: "My site is down!" or "There's a broken page!" -- OR the uptime monitor (Flow 9) detects an issue.

**Client interaction**: Agent immediately acknowledges:
> "I see the issue. I'm looking into it right now -- I'll have an update for you within 5 minutes."

Then resolves and confirms:
> "Fixed! The issue was [brief explanation]. Your site is back up. Sorry for the inconvenience."

**Agent actions**:
1. Detect urgency keywords in client message (down, broken, error, urgent, emergency, not working)
2. Immediately run diagnostics:
   - `verify_url(deployed_url)` -- check if site is reachable
   - Check Vercel deployment status via `get_latest_deployment`
   - If reachable but broken: `take_screenshot` to see current state
3. Attempt auto-fix based on diagnosis:
   - **Deployment failed**: trigger redeployment `trigger_deployment(project_name)`
   - **Code error**: read build logs, identify and fix the code issue, redeploy
   - **Vercel outage**: nothing to fix, inform client it's a hosting-wide issue
   - **Protection re-enabled**: `ensure_protection_disabled`
4. Verify fix: `verify_url` + `take_screenshot`
5. Notify client with resolution

**Owner involvement**: Notification of incident and resolution. Owner only involved if agent cannot auto-resolve.

**Revenue impact**: Client retention and trust. A quick response to a site emergency cements the relationship. This is the single highest-impact moment for client satisfaction.

**Implementation complexity**: Low-Medium (mostly orchestration logic in system prompt, using existing tools)

**New tools needed**:
- `diagnose_issue(project_id)` MCP tool -- runs a suite of checks and returns a structured diagnosis
- The `Incident` model from Flow 9 covers tracking
- System prompt additions for emergency handling priority and tone

---

## FLOW 17: Multi-Revision Complex Redesign Workflow

**Trigger**: Client requests a major change that requires multiple steps: "I want to completely redo the about page" or "Add an online ordering system" or "Redesign the navigation."

**Client interaction**: Agent breaks the work into milestones and communicates progress:
> "That's a bigger change -- here's my plan:
> 1. New page layout with updated content (I'll send a preview)
> 2. New images to match the updated design
> 3. Mobile optimization pass
>
> I'll send you a preview after each step. Ready to start?"

Client approves each milestone before the next begins.

**Agent actions**:
1. Parse the complex request and break it into sub-tasks
2. Create a task hierarchy: `create_task(project_id, parent_task, title, description)` for each sub-task
3. Execute sub-tasks sequentially, sending a preview (`deploy_preview`) after each milestone
4. Wait for client approval before proceeding to the next milestone
5. If client wants changes to a milestone, iterate on that milestone before moving on
6. After all milestones approved, merge everything to production via `approve_preview`
7. Track the full revision as a single billable event (if applicable)

**Owner involvement**: None for standard redesigns. Notification if the scope suggests it should be billed as an add-on.

**Revenue impact**: Handles complex requests that would otherwise require owner involvement. Structured milestones prevent scope creep.

**Implementation complexity**: Medium

**New tools needed**:
- `create_revision_plan(project_id, description, milestones)` MCP tool
- `get_revision_plan(project_id)` MCP tool
- Enhancements to Task model: use existing `parent_task_id` for milestone hierarchy
- System prompt additions for multi-step revision planning

---

## FLOW 18: Automated Follow-Up Email Sequences

**Trigger**: After outreach email is sent (Flow 6 in the existing pipeline), or after a pitch is deployed.

**Client interaction**: If prospect does not respond to the initial email within 3 days, agent sends a follow-up. Sequence:
- **Day 0**: Initial outreach email (existing)
- **Day 3**: Follow-up 1: "Just wanted to make sure you saw the proposal I put together for [Company]"
- **Day 7**: Follow-up 2: "Quick update -- I made some improvements to the demo site. Take a look: [URL]"
- **Day 14**: Follow-up 3: Final gentle nudge, different angle (e.g., focus on a competitor, or a seasonal opportunity)
- **Day 21**: Close: "I'll leave this in your hands. The proposal is still available at [URL] whenever you're ready."

Sequence stops immediately if the prospect responds (positive or negative).

**Agent actions**:
1. After initial email is sent, agent schedules follow-up sequence entries in a new `FollowUpSequence` table
2. Cron job runs daily, checks for due follow-ups
3. For each due follow-up: check if prospect has responded (check Gmail for reply, or WhatsApp for inbound)
4. If no response: `draft_email` with the follow-up, then auto-send (or queue for owner approval depending on config)
5. If prospect responds: cancel remaining follow-ups, route to appropriate handler (interested -> onboarding, not interested -> archive)

**Owner involvement**: Configurable. Could be fully autonomous or owner-approved for each follow-up.

**Revenue impact**: Massive. Most deals are won on follow-ups, not initial contact. Industry data shows 80% of sales require 5+ touches. Currently Clarmi sends one email and stops.

**Implementation complexity**: Medium

**New tools needed**:
- `schedule_followup_sequence(prospect_id, project_id, email_id)` MCP tool
- `check_email_reply(email_id)` MCP tool -- checks Gmail for replies to a sent email
- `cancel_followup_sequence(prospect_id)` MCP tool
- New DB model: `FollowUpEntry` (prospect_id, project_id, sequence_position, scheduled_for, status [pending, sent, cancelled], email_id)
- New cron: daily follow-up check

---

## FLOW 19: Prospect Pipeline Auto-Discovery (Lead Generation)

**Trigger**: Cron job (daily or configurable) -- agent proactively finds prospects.

**Client interaction**: None directly -- prospects receive cold outreach (existing Flow 6) after being researched.

**Agent actions**:
1. Agent uses WebSearch/WebFetch to find businesses in target verticals and geographies:
   - Search: "restaurants in [city] with bad websites"
   - Search: "salons in [city] wordpress site"
   - Scrape Google Maps for businesses with websites
   - Scrape Yelp for businesses with outdated or no websites
2. For each discovered prospect: run Research pipeline (scrape, audit, score)
3. High-scoring prospects: auto-generate pitch + outreach email
4. Store all discovered prospects in the database

**Owner involvement**: Owner configures target verticals, geographies, and daily prospecting limits. After that, fully autonomous.

**Revenue impact**: The owner currently initiates every project manually. This flow generates a constant stream of qualified leads without any owner input.

**Implementation complexity**: High

**New tools needed**:
- `discover_prospects(industry, location, max_results)` MCP tool
- `search_google_maps(query, location)` MCP tool (or use WebSearch)
- New config: `PROSPECTING_ENABLED`, `PROSPECTING_INDUSTRIES`, `PROSPECTING_LOCATIONS`, `PROSPECTING_DAILY_LIMIT`
- New cron: daily prospect discovery

---

## FLOW 20: Client Self-Service Portal (Web Dashboard)

**Trigger**: Client visits their portal URL (e.g., portal.clarmi.studio/[project-slug]).

**Client interaction**: A simple web dashboard where the client can:
- View their site's current Lighthouse scores and uptime
- Submit revision requests via a form (instead of WhatsApp)
- View revision history and their status
- Upload content/assets via drag-and-drop
- View and pay invoices
- Approve pending previews
- Download site files/backups
- View monthly reports

**Agent actions**:
1. The portal is a lightweight Next.js app (deployed once, serves all clients)
2. Authentication: magic link sent via email/WhatsApp (no passwords)
3. Portal reads data from the PostgreSQL database (project status, Lighthouse scores, etc.)
4. Form submissions create tasks/messages in the DB, which trigger the agent via webhook
5. File uploads go to the project's asset storage
6. Preview approvals call `approve_preview` via an API endpoint

**Owner involvement**: None for portal usage. Owner builds/deploys the portal once.

**Revenue impact**: Reduces WhatsApp back-and-forth. Some clients prefer web interfaces. Makes Clarmi look more professional. Could justify higher pricing.

**Implementation complexity**: High

**New tools needed**:
- An entirely new Next.js application (`portal/`) with:
  - Authentication (magic link via email)
  - Dashboard page (project status, scores, uptime)
  - Revision request form
  - File upload component
  - Invoice/payment view (Stripe integration)
  - Preview approval button
  - Monthly report viewer
- API endpoints (or webhook handlers) that bridge portal actions to agent tools
- New config: portal URL, authentication secrets

---

## FLOW 21: Automated Competitor Monitoring

**Trigger**: Cron job (monthly for all launched projects) or client request.

**Client interaction**: Agent sends insights:
> "I checked your top competitor [Competitor Name]'s website this month. They recently added online ordering and updated their design. Your site is still outperforming theirs on speed (94 vs 72), but you might want to consider adding online ordering too. Want me to look into it?"

**Agent actions**:
1. During onboarding (Flow 3), agent collects 1-3 competitor URLs
2. Monthly cron: agent scrapes competitor sites using WebFetch
3. Agent compares: design quality, features present, Lighthouse scores, content freshness
4. If competitor made significant changes: notify client with actionable insights
5. Frame insights as upsell opportunities (Flow 13)

**Owner involvement**: None.

**Revenue impact**: Keeps clients engaged and aware of competitive pressure. Creates upsell opportunities. Demonstrates ongoing value.

**Implementation complexity**: Medium

**New tools needed**:
- `store_competitors(project_id, competitor_urls)` MCP tool
- `analyze_competitor(project_id, competitor_url)` MCP tool
- New DB field on Project metadata: `competitors: list[str]`
- New cron: monthly competitor analysis

---

## FLOW 22: Automated Domain Management

**Trigger**: Post-launch, when client needs a custom domain connected, or domain is about to expire.

**Client interaction**:
> "Your site is currently at [vercel-url]. Would you like to connect a custom domain? If you already have one, send it to me and I'll set it up. If you need to buy one, I can help with that too."

**Agent actions**:
1. After launch, agent offers domain connection
2. If client provides a domain: agent configures it via Vercel Domains API
3. Agent sends DNS instructions: "Point these DNS records to Vercel: [records]"
4. Agent monitors DNS propagation and confirms when live
5. For domain expiration monitoring: cron checks WHOIS data, alerts client 30 days before expiry

**Owner involvement**: Notification only.

**Revenue impact**: Premium add-on service. Completes the offering. Prevents clients from needing to go elsewhere for domain management.

**Implementation complexity**: Medium

**New tools needed**:
- Vercel Domains API integration: `add_domain(project_name, domain)`, `check_domain_config(domain)`, `remove_domain(project_name, domain)`
- `check_domain_expiry(domain)` MCP tool (WHOIS lookup)
- New cron: domain expiry monitoring (monthly)

---

## FLOW 23: Automated A/B Testing for Client Sites

**Trigger**: Agent identifies an optimization opportunity (e.g., CTA button color, hero headline, layout variant), or client requests "I want to test two versions of my hero."

**Client interaction**:
> "I'd like to test two versions of your hero section to see which gets more clicks. Version A keeps the current design; Version B uses a different headline and button color. I'll run the test for 2 weeks and show you the results."

After test completes:
> "Results are in! Version B got 23% more clicks on the CTA button. I've made it the default. Here's the full breakdown: [report]"

**Agent actions**:
1. Agent creates two variants of a section using `edit_code`/`write_code`
2. Agent adds simple A/B testing logic (cookie-based or random split) to the Next.js page
3. Agent deploys and monitors using Vercel Analytics or a lightweight custom tracking pixel
4. After the test period, agent analyzes results and applies the winner
5. Reports results to client

**Owner involvement**: None for standard tests. Owner configurable for which sites get A/B testing.

**Revenue impact**: Premium service add-on. Demonstrates data-driven value. Improves client site performance.

**Implementation complexity**: High

**New tools needed**:
- `create_ab_test(project_id, element, variant_a, variant_b, duration_days)` MCP tool
- `check_ab_test_results(test_id)` MCP tool
- `apply_ab_test_winner(test_id)` MCP tool
- Tracking mechanism (analytics snippet or custom pixel)
- New DB model: `ABTest` (project_id, element, variants, start_date, end_date, results, winner, status)

---

## FLOW 24: Proactive Outreach Timing Optimization

**Trigger**: Intelligence-driven timing for when to send outreach emails.

**Client interaction**: Same as standard outreach, but timed for maximum impact.

**Agent actions**:
1. Agent analyzes email engagement data from past campaigns (open rates by day/time)
2. Agent checks prospect timezone (inferred from location/area code)
3. Agent schedules outreach emails for optimal times (e.g., Tuesday 10am local time)
4. Agent avoids sending during holidays, weekends, or known low-engagement periods
5. Over time, agent learns which timing works best for which industries

**Owner involvement**: None.

**Revenue impact**: Higher email open and response rates. Industry data shows timing can improve open rates by 20-40%.

**Implementation complexity**: Low-Medium

**New tools needed**:
- `schedule_email_send(email_id, send_at)` MCP tool
- Email scheduling cron (checks every 15 minutes for due emails)
- New DB fields on EmailLog: `scheduled_for: datetime`, `timezone: str`

---

## FLOW 25: Client Satisfaction Check-Ins

**Trigger**: Cron job at specific intervals post-launch: 7 days, 30 days, 90 days.

**Client interaction**:
- **Day 7**: "How are you liking your new site? Any changes you'd like?"
- **Day 30**: "Your site has been live for a month! Lighthouse scores are strong. Anything you'd like to tweak?"
- **Day 90**: "Quick check-in -- everything working well with your site? Let me know if you need anything."

**Agent actions**:
1. Cron checks for projects at 7/30/90 day milestones post-launch
2. Agent sends personalized check-in via WhatsApp
3. If client responds with feedback: route to Client Funnel for revisions
4. If client responds positively: trigger referral request (Flow 14) if not already sent
5. If client reports issues: trigger emergency support flow
6. Track NPS-style satisfaction scores

**Owner involvement**: None. Owner gets a weekly summary of satisfaction scores.

**Revenue impact**: Retention. Early intervention if a client is unhappy. Natural lead-in to referral requests.

**Implementation complexity**: Low

**New tools needed**:
- `send_checkin(project_id, milestone)` MCP tool
- `record_satisfaction(project_id, score, notes)` MCP tool
- New cron: daily check for milestone dates
- New DB model or fields: `last_checkin_at`, `satisfaction_score`

---

## FLOW 26: WhatsApp Broadcast for Multiple Clients

**Trigger**: Owner or agent needs to communicate with all clients (e.g., scheduled maintenance, new feature announcement, holiday message).

**Client interaction**: All clients receive a personalized message:
> "Hi [Name], just a heads up -- we're rolling out a performance update to all our sites tonight between 2-4am. Your site [URL] will be even faster afterward. No action needed on your end."

**Agent actions**:
1. Owner or cron triggers a broadcast
2. Agent queries all active projects with `client_phone`
3. Agent personalizes each message with the client's name, project name, and deployed URL
4. Agent sends via WhatsApp in batches (respecting rate limits)
5. Log all sent messages

**Owner involvement**: Owner initiates (unless it's an automated announcement). Agent handles personalization and delivery.

**Revenue impact**: Professional communication at scale. Keeps clients informed. Low effort, high perception of value.

**Implementation complexity**: Low

**New tools needed**:
- `broadcast_message(template, filter_status)` MCP tool
- Rate limiting logic in WhatsApp client

---

## FLOW 27: Automated Site Backup and Version History

**Trigger**: Before every deployment, and on a weekly cron schedule.

**Client interaction**: Mostly invisible. Client can request: "Can you revert my site to how it looked last week?" Agent handles it.

**Agent actions**:
1. Before every `deploy`: agent tags the current Git commit as a version point
2. Weekly cron: agent creates a tagged backup (Git tag with date)
3. If client requests rollback: agent identifies the correct version, deploys that commit
4. Agent can list versions: "Your site has 12 saved versions. The most recent is from yesterday."

**Owner involvement**: None.

**Revenue impact**: Safety net. Builds trust. Prevents catastrophic mistakes from being permanent.

**Implementation complexity**: Low (Git already provides this, just needs orchestration)

**New tools needed**:
- `create_backup(project_id, label)` MCP tool (creates a Git tag)
- `list_backups(project_id)` MCP tool
- `rollback_to_backup(project_id, backup_label)` MCP tool (deploys a specific tag)

---

## FLOW 28: Gmail Inbox Monitoring for Client Replies

**Trigger**: Continuous or cron-based polling of the Gmail inbox.

**Client interaction**: Client replies to a Clarmi email (outreach, report, invoice). The agent detects the reply and routes it appropriately.

**Agent actions**:
1. Cron or webhook monitors Gmail inbox for new messages
2. Agent matches incoming email to a known prospect/project using sender email
3. Routes the message:
   - Reply to outreach: prospect is interested -> trigger onboarding (Flow 3)
   - Reply to report: client has feedback -> route to Client Funnel
   - Reply with "unsubscribe" or negative: mark prospect as do-not-contact
4. Agent responds appropriately via email or WhatsApp

**Owner involvement**: None for standard routing. Notification for unusual messages.

**Revenue impact**: Captures leads that respond via email (currently these responses may be missed or require owner to check manually). Eliminates the "forgot to check my email" problem.

**Implementation complexity**: Medium

**New tools needed**:
- Gmail inbox monitoring integration: `check_inbox(since_timestamp)` using Gmail API
- `route_email_reply(email_thread_id, sender, content)` MCP tool
- New config in gmail_client.py: inbox watch / polling
- New cron: email inbox check (every 5-15 minutes)

---

## Priority Ranking and Implementation Roadmap

Ordered by impact-to-effort ratio:

| Priority | Flow | Impact | Effort | Revenue Type |
|----------|------|--------|--------|-------------|
| 1 | Flow 8: Stripe Payments | Critical | High | Revenue collection |
| 2 | Flow 18: Follow-Up Sequences | Very High | Medium | Lead conversion |
| 3 | Flow 1: Inbound Lead Capture | Very High | Medium | Lead generation |
| 4 | Flow 4: Content Collection | High | Medium | Time savings |
| 5 | Flow 3: Onboarding Questionnaire | High | Medium | Time savings |
| 6 | Flow 7: Formal Sign-Off | High | Low | Process quality |
| 7 | Flow 25: Client Check-Ins | High | Low | Retention |
| 8 | Flow 6: Build Feedback (enhanced) | Medium | Low | Time savings |
| 9 | Flow 9: Uptime Monitoring | High | Medium | Retention |
| 10 | Flow 10: Monthly Reports | High | Medium | Retention |
| 11 | Flow 16: Emergency Support | High | Low-Medium | Retention |
| 12 | Flow 15: Cancellation/Offboarding | Medium | Medium | Retention |
| 13 | Flow 12: SEO Optimization | High | Medium | Ongoing value |
| 14 | Flow 11: Seasonal Content | Medium | Medium | Engagement |
| 15 | Flow 14: Referral Program | High | Medium | Lead generation |
| 16 | Flow 13: Upselling | High | Medium | Revenue growth |
| 17 | Flow 2: Lead Scoring | Medium | Low | Efficiency |
| 18 | Flow 28: Gmail Monitoring | Medium | Medium | Lead capture |
| 19 | Flow 24: Outreach Timing | Medium | Low-Medium | Conversion |
| 20 | Flow 5: Design Direction | Medium | Medium | Quality |
| 21 | Flow 17: Complex Redesigns | Medium | Medium | Capability |
| 22 | Flow 27: Site Backups | Medium | Low | Trust |
| 23 | Flow 26: Broadcast Messages | Low-Medium | Low | Engagement |
| 24 | Flow 19: Auto-Discovery | Very High | High | Lead generation |
| 25 | Flow 22: Domain Management | Medium | Medium | Completeness |
| 26 | Flow 21: Competitor Monitoring | Medium | Medium | Engagement |
| 27 | Flow 20: Client Portal | High | High | Professionalism |
| 28 | Flow 23: A/B Testing | Low-Medium | High | Premium service |

---

## Summary of New Infrastructure Required

**New integrations (files in `src/openclaw/integrations/`):**
- `stripe_client.py` -- payment processing, subscriptions, invoices
- Gmail inbox reading (extend existing `gmail_client.py`)
- Vercel Domains API (extend existing `vercel_client.py`)
- Vercel Analytics API (extend existing `vercel_client.py`)

**New DB models (files in `src/openclaw/models/`):**
- `client_onboarding.py` -- onboarding questionnaire responses
- `content_item.py` -- content collection tracking
- `payment.py` -- payment records
- `subscription.py` -- recurring billing
- `scheduled_update.py` -- timed content changes
- `follow_up.py` -- email follow-up sequences
- `incident.py` -- uptime incidents
- `uptime_check.py` -- uptime monitoring records
- `monthly_report.py` -- client reports
- `referral.py` -- referral tracking
- `cancellation.py` -- offboarding records
- `upsell.py` -- upsell proposals and conversions

**New MCP tool modules (files in `src/openclaw/mcp_server/tools/`):**
- `payments.py` -- Stripe payment tools
- `onboarding.py` -- client onboarding tools
- `content.py` -- content collection tools
- `monitoring.py` -- uptime and incident tools
- `reporting.py` -- monthly report tools
- `scheduling.py` -- scheduled updates and follow-ups
- `referrals.py` -- referral program tools
- `offboarding.py` -- cancellation and archival tools

**New cron entries in `openclaw.json`:**
- Uptime check (every 5 minutes)
- Follow-up sequence check (daily)
- Monthly report generation (1st of month)
- SEO optimization (weekly)
- Satisfaction check-ins (daily, checks for milestone dates)
- Competitor analysis (monthly)
- Seasonal reminders (weekly)
- Prospect discovery (daily, if enabled)
- Scheduled update execution (hourly)
- Email inbox monitoring (every 15 minutes)
- Domain expiry check (monthly)

**System prompt additions (`CLAUDE.md`):**
- Onboarding conversation flow
- Content collection conversation flow
- Emergency support priority handling
- Upsell messaging guidelines
- Cancellation retention scripting
- Satisfaction check-in templates
- Formal sign-off process
- Follow-up email templates

### Critical Files for Implementation
- `/home/mootbing/code/High-Level-Cow-Horse/CLAUDE.md` -- system prompt that governs all agent behavior; every new flow requires additions here
- `/home/mootbing/code/High-Level-Cow-Horse/openclaw.json` -- agent configuration including cron jobs; all new scheduled flows are registered here
- `/home/mootbing/code/High-Level-Cow-Horse/src/openclaw/mcp_server/server.py` -- MCP server registry; every new tool module must be imported here
- `/home/mootbing/code/High-Level-Cow-Horse/src/openclaw/models/project.py` -- Project model is the central entity; new fields (signed_off_at, satisfaction_score, competitors) and relationships attach here
- `/home/mootbing/code/High-Level-Cow-Horse/src/openclaw/integrations/whatsapp_client.py` -- WhatsApp client is the primary client-facing channel; needs media download, rate limiting, and template message support for most flows
