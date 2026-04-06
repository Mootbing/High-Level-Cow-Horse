"""HTML email template for website audit results.

Uses inline styles and tables for maximum email client compatibility.
Claude provides personalized copy; this template provides reliable HTML rendering.
"""

from __future__ import annotations

import html as _html

from openclaw.services.website_audit import AuditResult


def _score_color(score: float) -> str:
    """Return hex color based on score."""
    if score >= 8:
        return "#22c55e"
    elif score >= 6:
        return "#7C5CFC"
    elif score >= 4:
        return "#f59e0b"
    else:
        return "#ef4444"


def _score_label(score: float) -> str:
    if score >= 8:
        return "Great"
    elif score >= 6:
        return "Good"
    elif score >= 4:
        return "Needs Work"
    else:
        return "Critical"


def render_audit_email(
    audit: AuditResult,
    recipient_email: str,
    personalized_intro: str | None = None,
    personalized_cta: str | None = None,
) -> str:
    """Render the full HTML audit email.

    Args:
        audit: Structured audit data (scores, problems, tech stack)
        recipient_email: Who we're sending to
        personalized_intro: Claude-written opening paragraph (specific to this site)
        personalized_cta: Claude-written call-to-action copy (specific recommendations)
    """

    # Score breakdown rows
    dimensions = [
        ("Visual Design", audit.scores.get("visual_design", 5)),
        ("UX & Navigation", audit.scores.get("ux_navigation", 5)),
        ("Content Quality", audit.scores.get("content_quality", 5)),
        ("Technical", audit.scores.get("technical", 5)),
        ("Mobile Friendly", audit.scores.get("mobile_friendly", 5)),
    ]

    score_rows = ""
    for name, score in dimensions:
        color = _score_color(score)
        bar_width = score * 10
        score_rows += f"""
        <tr>
          <td style="padding: 8px 0; font-size: 14px; color: #374151; width: 140px;">{name}</td>
          <td style="padding: 8px 0;">
            <div style="background: #f3f4f6; border-radius: 999px; height: 8px; overflow: hidden;">
              <div style="background: {color}; width: {bar_width}%; height: 100%; border-radius: 999px;"></div>
            </div>
          </td>
          <td style="padding: 8px 0 8px 12px; font-size: 14px; font-weight: 600; color: {color}; text-align: right; width: 50px;">{score}/10</td>
        </tr>"""

    # Problems list
    problems_html = ""
    if audit.site_problems:
        items = ""
        for problem in audit.site_problems[:6]:
            items += f'<li style="padding: 6px 0; font-size: 14px; color: #374151;">{_html.escape(str(problem))}</li>'
        problems_html = f"""
        <div style="margin-top: 32px;">
          <h2 style="font-size: 18px; color: #0a0a0a; margin: 0 0 16px;">Issues We Found</h2>
          <ul style="margin: 0; padding-left: 20px;">{items}</ul>
        </div>"""

    # Tech stack chips
    tech_html = ""
    if audit.tech_stack:
        chips = " ".join(
            f'<span style="display: inline-block; padding: 4px 10px; background: #f3f4f6; border-radius: 999px; font-size: 12px; color: #6b7280; margin: 2px;">{_html.escape(str(t))}</span>'
            for t in audit.tech_stack
        )
        tech_html = f"""
        <div style="margin-top: 24px;">
          <p style="font-size: 13px; color: #9a9a9a; margin: 0 0 8px;">Detected technology</p>
          {chips}
        </div>"""

    overall_color = _score_color(audit.overall)
    overall_label = _score_label(audit.overall)

    # HTML-escape all external data
    safe_url = _html.escape(audit.final_url)

    # Personalized intro from Claude (or generic fallback)
    if personalized_intro:
        intro_html = f"""
      <div style="margin-bottom: 24px;">
        <p style="font-size: 15px; color: #374151; line-height: 1.6; margin: 0;">
          {_html.escape(personalized_intro)}
        </p>
      </div>"""
    else:
        intro_html = ""

    # Personalized CTA from Claude (or generic fallback)
    if personalized_cta:
        cta_text = _html.escape(personalized_cta)
    else:
        cta_text = "Want a redesign that fixes these issues?<br>We build it free &mdash; you only pay when you love it."

    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
<body style="margin: 0; padding: 0; background: #f9fafb; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
  <div style="max-width: 600px; margin: 0 auto; padding: 40px 20px;">

    <!-- Header -->
    <div style="text-align: center; margin-bottom: 32px;">
      <h1 style="font-size: 24px; color: #0a0a0a; margin: 0;">Clarmi Design Studio</h1>
      <p style="font-size: 14px; color: #9a9a9a; margin: 8px 0 0;">Your website audit report</p>
    </div>

    <!-- Main card -->
    <div style="background: #ffffff; border-radius: 16px; padding: 32px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">

      {intro_html}

      <!-- Overall Score -->
      <div style="text-align: center; margin-bottom: 32px;">
        <div style="display: inline-block; width: 80px; height: 80px; border-radius: 50%; border: 4px solid {overall_color}; line-height: 80px; text-align: center;">
          <span style="font-size: 28px; font-weight: 700; color: {overall_color};">{audit.overall}</span>
        </div>
        <p style="font-size: 16px; color: {overall_color}; font-weight: 600; margin: 8px 0 0;">{overall_label}</p>
        <p style="font-size: 13px; color: #9a9a9a; margin: 4px 0 0;">{safe_url}</p>
      </div>

      <!-- Score Breakdown -->
      <h2 style="font-size: 18px; color: #0a0a0a; margin: 0 0 16px;">Score Breakdown</h2>
      <table style="width: 100%; border-collapse: collapse;">{score_rows}</table>

      {problems_html}

      {tech_html}

      <!-- CTA -->
      <div style="margin-top: 40px; text-align: center;">
        <p style="font-size: 15px; color: #374151; margin: 0 0 16px;">
          {cta_text}
        </p>
        <a href="https://calendar.app.google/1R6HGErUx6kvbgSa9" style="display: inline-block; padding: 14px 32px; background: #7C5CFC; color: #ffffff; text-decoration: none; border-radius: 999px; font-weight: 600; font-size: 15px;">
          Let&rsquo;s Talk
        </a>
      </div>
    </div>

    <!-- Footer -->
    <div style="text-align: center; margin-top: 32px;">
      <p style="font-size: 12px; color: #9a9a9a;">
        Clarmi Design Studio &middot; Modern web design<br>
        You received this because you requested an audit at clarmi.com
      </p>
    </div>
  </div>
</body>
</html>"""
