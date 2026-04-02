"use client";

import { useEffect, useRef } from "react";

type FeatureValue = boolean | "partial";
interface Feature {
  label: string;
  agency: FeatureValue;
  local: FeatureValue;
  clarmi: FeatureValue;
  tips?: { agency?: string; local?: string; clarmi?: string };
}

const FEATURES: Feature[] = [
  { label: "Custom design from scratch", agency: true, local: "partial", clarmi: true,
    tips: { agency: "Custom, but expect 6-12 weeks and $10k+ budgets", local: "Most use WordPress templates with your colors swapped in", clarmi: "Custom designs since day 1" } },
  { label: "48-hour delivery", agency: false, local: false, clarmi: true,
    tips: { agency: "Typical agency timeline is 6-12 weeks", local: "Usually 2-4 weeks minimum", clarmi: "From brief to live site in under 48 hours" } },
  { label: "Mobile-responsive on every device", agency: true, local: "partial", clarmi: true,
    tips: { local: "Heavily dependent on the template used", clarmi: "Tested across every breakpoint from phones, tablets, ultrawide" } },
  { label: "SEO-optimized from day one", agency: true, local: "partial", clarmi: true,
    tips: { local: "Basic SEO at best. No structured data or performance tuning", clarmi: "Structured data, meta tags, sitemap, and sub-second load times" } },
  { label: "Agent Search Optimization (ChatGPT, Perplexity)", agency: "partial", local: false, clarmi: true,
    tips: { agency: "Very preliminary", local: "Won't bother", clarmi: "MCP Server hosted & updated with site" } },
  { label: "SSL, hosting & analytics included", agency: false, local: false, clarmi: true,
    tips: { agency: "Hosting and SSL billed separately, $50-200/mo", local: "You manage your own hosting and domain", clarmi: "SSL, global CDN hosting, and analytics dashboard — all included" } },
  { label: "Monthly revisions & monitoring", agency: false, local: false, clarmi: true,
    tips: { agency: "Revisions billed hourly at $150-300/hr", local: "Usually a flat fee per change request", clarmi: "Ongoing tweaks and uptime monitoring every month" } },
  { label: "Unlimited pre-launch revisions", agency: false, local: false, clarmi: true,
    tips: { agency: "Most cap at 2-3 revision rounds", local: "Typically 1-2 rounds included", clarmi: "We iterate until you love it — no limits" } },
  { label: "Competitor tracking", agency: true, local: false, clarmi: true,
    tips: { agency: "Available, but usually an add-on retainer", local: "Not offered", clarmi: "We monitor your competitors' sites and keep you ahead" } },
  { label: "Monthly analytics", agency: false, local: false, clarmi: true,
    tips: { agency: "Reports available at extra cost", local: "You're on your own with Google Analytics", clarmi: "Monthly performance reports delivered to your inbox" } },
];

function CheckIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
      <circle cx="9" cy="9" r="8" fill="var(--accent-soft)" stroke="var(--accent)" strokeWidth="1" />
      <path d="M5.5 9L8 11.5L12.5 6.5" stroke="var(--accent)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function XIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
      <circle cx="9" cy="9" r="8" fill="rgba(180,180,180,0.08)" stroke="rgba(180,180,180,0.3)" strokeWidth="1" />
      <path d="M6.5 6.5L11.5 11.5M11.5 6.5L6.5 11.5" stroke="var(--text-light)" strokeWidth="1.3" strokeLinecap="round" />
    </svg>
  );
}

function PartialIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
      <circle cx="9" cy="9" r="8" fill="rgba(200,170,80,0.08)" stroke="rgba(200,170,80,0.35)" strokeWidth="1" />
      <path d="M6 9H12" stroke="rgba(200,170,80,0.7)" strokeWidth="1.5" strokeLinecap="round" />
    </svg>
  );
}

function StatusIcon({ value, tip }: { value: boolean | string; tip?: string }) {
  const icon = value === true ? <CheckIcon /> : value === "partial" ? <PartialIcon /> : <XIcon />;
  if (!tip) return icon;
  return (
    <span className="pricing-tip-wrap">
      {icon}
      <span className="pricing-tip">{tip}</span>
    </span>
  );
}

export default function Pricing() {
  const ref = useRef<HTMLElement>(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;

    const reveals = el.querySelectorAll(".pricing-reveal");
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("active");
          }
        });
      },
      { threshold: 0.1, rootMargin: "0px 0px -40px 0px" }
    );

    reveals.forEach((r) => observer.observe(r));
    return () => observer.disconnect();
  }, []);

  return (
    <section ref={ref} className="section" id="pricing">
      <div className="container" style={{ maxWidth: 960, margin: "0 auto" }}>
        {/* Header */}
        <div className="pricing-reveal" style={{ textAlign: "center", marginBottom: "clamp(3rem, 6vh, 5rem)", opacity: 0, transform: "translateY(30px)", transition: "opacity 0.9s cubic-bezier(0.16,1,0.3,1), transform 0.9s cubic-bezier(0.16,1,0.3,1)" }}>
          <h2 className="text-display-lg">
            Honest pricing. <em className="font-serif" style={{ fontStyle: "italic" }}>No surprises.</em>
          </h2>
        </div>

        {/* Comparison grid */}
        <div
          className="pricing-reveal pricing-grid-wrapper"
          style={{
            opacity: 0,
            transform: "translateY(40px)",
            transition: "opacity 1s cubic-bezier(0.16,1,0.3,1), transform 1s cubic-bezier(0.16,1,0.3,1)",
            transitionDelay: "0.1s",
            borderRadius: "var(--radius-lg)",
            border: "1px solid var(--border)",
            overflow: "hidden",
          }}
        >
          <div className="pricing-grid">
            {/* Column headers */}
            <div className="pricing-cell pricing-corner" />

            {/* Agency header */}
            <div className="pricing-cell pricing-header">
              <div className="pricing-header-label">Traditional Agency</div>
              <div className="pricing-header-price" style={{ color: "var(--text-light)" }}>
                $10,000+
              </div>
              <div className="pricing-header-monthly">+ $200/mo</div>
            </div>

            {/* Local header */}
            <div className="pricing-cell pricing-header">
              <div className="pricing-header-label">Local Designer</div>
              <div className="pricing-header-price" style={{ color: "var(--text-light)" }}>
                $5,000+
              </div>
              <div className="pricing-header-monthly">+ $150/mo</div>
            </div>

            {/* Clarmi header */}
            <div className="pricing-cell pricing-header pricing-header-clarmi">
              <span style={{
                padding: "0.15rem 0.5rem",
                background: "var(--accent-soft)",
                color: "var(--accent)",
                borderRadius: "var(--radius-full)",
                fontSize: "0.62rem",
                fontWeight: 600,
                letterSpacing: "0.05em",
                border: "1px solid rgba(124, 92, 252, 0.15)",
                marginBottom: "0.3rem",
                display: "inline-block",
              }}>
                Inauguration Discount
              </span>
              <div className="pricing-header-label" style={{ color: "var(--accent)" }}>Clarmi</div>
              <div style={{ display: "flex", alignItems: "baseline", gap: "0.35rem", justifyContent: "center" }}>
                <div className="pricing-header-price" style={{ color: "var(--accent)" }}>
                  $250
                </div>
                <span style={{
                  fontFamily: '"Instrument Serif", Georgia, serif',
                  fontSize: "clamp(0.9rem, 1.2vw, 1.1rem)",
                  color: "var(--text-light)",
                  textDecoration: "line-through",
                  opacity: 0.4,
                }}>
                  $500
                </span>
              </div>
              <div style={{ display: "flex", alignItems: "baseline", gap: "0.3rem", justifyContent: "center" }}>
                <span className="pricing-header-monthly" style={{ color: "var(--accent)", opacity: 0.8 }}>+ $25/mo</span>
                <span style={{
                  fontSize: "clamp(0.65rem, 0.72vw, 0.7rem)",
                  color: "var(--text-light)",
                  textDecoration: "line-through",
                  opacity: 0.35,
                }}>
                  $50/mo
                </span>
              </div>
            </div>

            {/* Feature rows */}
            {FEATURES.map((feature, i) => (
              <>
                <div key={`label-${i}`} className="pricing-cell pricing-feature-label">
                  {feature.label}
                </div>
                <div key={`agency-${i}`} className="pricing-cell pricing-check">
                  <StatusIcon value={feature.agency} tip={feature.tips?.agency} />
                </div>
                <div key={`local-${i}`} className="pricing-cell pricing-check">
                  <StatusIcon value={feature.local} tip={feature.tips?.local} />
                </div>
                <div key={`clarmi-${i}`} className="pricing-cell pricing-check pricing-check-clarmi">
                  <StatusIcon value={feature.clarmi} tip={feature.tips?.clarmi} />
                </div>
              </>
            ))}
          </div>
        </div>

        {/* CTA line */}
        <div
          className="pricing-reveal"
          style={{
            opacity: 0,
            transform: "translateY(20px)",
            transition: "opacity 0.8s cubic-bezier(0.16,1,0.3,1), transform 0.8s cubic-bezier(0.16,1,0.3,1)",
            transitionDelay: "0.25s",
            textAlign: "center",
            marginTop: "clamp(1.5rem, 3vh, 2rem)",
          }}
        >
          <p className="text-body" style={{ color: "var(--text-muted)" }}>
            Custom design. 48-hour delivery. Don&apos;t pay until you&apos;re happy.
          </p>
        </div>
      </div>

      <style>{`
        .pricing-reveal.active {
          opacity: 1 !important;
          transform: translateY(0) scale(1) !important;
        }

        .pricing-grid {
          display: grid;
          grid-template-columns: 1.6fr 1fr 1fr 1fr;
        }

        .pricing-cell {
          padding: clamp(0.6rem, 1.2vw, 0.85rem) clamp(0.8rem, 1.5vw, 1.2rem);
          display: flex;
          align-items: center;
        }

        .pricing-corner {
          background: var(--bg);
          border-bottom: 1px solid var(--border);
        }

        .pricing-header {
          flex-direction: column;
          justify-content: flex-end;
          text-align: center;
          padding: clamp(1.2rem, 2.5vw, 1.8rem) clamp(0.6rem, 1vw, 1rem);
          background: var(--bg);
          border-bottom: 1px solid var(--border);
          border-left: 1px solid var(--border);
          gap: 0.1rem;
        }

        .pricing-header-clarmi {
          background: rgba(124, 92, 252, 0.03);
          border-bottom: 1.5px solid var(--accent);
        }

        .pricing-header-label {
          font-size: clamp(0.78rem, 0.88vw, 0.85rem);
          font-weight: 500;
          color: var(--text-muted);
          margin-bottom: 0.15rem;
        }

        .pricing-header-price {
          font-family: "Instrument Serif", Georgia, serif;
          font-size: clamp(1.6rem, 3vw, 2.2rem);
          line-height: 1.1;
        }

        .pricing-header-monthly {
          font-size: clamp(0.68rem, 0.78vw, 0.75rem);
          color: var(--text-light);
        }

        .pricing-feature-label {
          font-size: clamp(0.78rem, 0.88vw, 0.85rem);
          color: var(--text-muted);
          line-height: 1.4;
          border-bottom: 1px solid var(--border);
          background: var(--bg);
        }

        .pricing-check {
          justify-content: center;
          border-bottom: 1px solid var(--border);
          border-left: 1px solid var(--border);
          background: var(--bg);
        }

        .pricing-check-clarmi {
          background: rgba(124, 92, 252, 0.02);
        }

        .pricing-grid > .pricing-cell:nth-last-child(-n+4) {
          border-bottom: none;
        }

        .pricing-tip-wrap {
          position: relative;
          cursor: pointer;
          display: inline-flex;
        }

        .pricing-tip {
          position: absolute;
          bottom: calc(100% + 8px);
          left: 50%;
          transform: translateX(-50%) translateY(4px);
          background: var(--text);
          color: var(--bg);
          font-size: 0.72rem;
          line-height: 1.4;
          padding: 0.4rem 0.65rem;
          border-radius: 6px;
          white-space: nowrap;
          pointer-events: none;
          opacity: 0;
          transition: opacity 0.2s ease, transform 0.2s ease;
          z-index: 10;
          max-width: 220px;
          white-space: normal;
          text-align: center;
        }

        .pricing-tip::after {
          content: "";
          position: absolute;
          top: 100%;
          left: 50%;
          transform: translateX(-50%);
          border: 5px solid transparent;
          border-top-color: var(--text);
        }

        .pricing-tip-wrap:hover .pricing-tip,
        .pricing-tip-wrap:active .pricing-tip {
          opacity: 1;
          transform: translateX(-50%) translateY(0);
        }

        /* Mobile: stack into cards */
        @media (max-width: 640px) {
          .pricing-grid {
            grid-template-columns: 1fr 1fr 1fr;
          }

          .pricing-corner {
            display: none;
          }

          .pricing-feature-label {
            grid-column: 1 / -1;
            justify-content: center;
            text-align: center;
            background: var(--bg-alt);
            font-weight: 500;
            padding: clamp(0.5rem, 1vw, 0.7rem) clamp(0.6rem, 1vw, 0.8rem);
          }

          .pricing-header {
            padding: clamp(1rem, 2vw, 1.4rem) clamp(0.4rem, 0.8vw, 0.6rem);
          }

          .pricing-header:first-child {
            border-left: none;
          }

          .pricing-check:first-of-type {
            border-left: none;
          }

          .pricing-grid > .pricing-feature-label + .pricing-check {
            border-left: none;
          }
        }
      `}</style>
    </section>
  );
}
