"use client";

import { useEffect, useRef } from "react";

type FeatureValue = boolean | "partial";
interface Feature {
  label: string;
  agency: FeatureValue;
  local: FeatureValue;
  clarmi: FeatureValue;
  tips?: { agency?: string; local?: string; clarmi?: string };
  info?: string;
}

const FEATURES: Feature[] = [
  { label: "Custom Design", agency: true, local: "partial", clarmi: true,
    tips: { agency: "6-12 weeks, $10k+", local: "Template with your colors", clarmi: "Custom from day 1" } },
  { label: "48-hour delivery", agency: false, local: false, clarmi: true,
    tips: { agency: "6-12 weeks typical", local: "2-4 weeks minimum", clarmi: "Website drafted in less than 24 hours" } },
  { label: "Mobile-responsiveness", agency: true, local: "partial", clarmi: true,
    tips: { local: "Depends on the template", clarmi: "Every breakpoint tested" } },
  { label: "SEO-optimization", agency: true, local: "partial", clarmi: true,
    tips: { local: "Basic SEO, no structured data", clarmi: "Structured data, sitemap, sub-second loads" } },
  { label: "AI SEO", info: "ChatGPT, Perplexity, Claude, etc.", agency: "partial", local: false, clarmi: true,
    tips: { agency: "Very preliminary", local: "Won't bother", clarmi: "MCP Server hosted with site" } },
  { label: "SSL, hosting & analytics included", agency: false, local: false, clarmi: true,
    tips: { agency: "Billed separately, $50-200/mo", local: "You manage your own", clarmi: "All included" } },
  { label: "Unlimited revisions", agency: false, local: false, clarmi: true,
    tips: { agency: "$150-300/hr, capped rounds", local: "Flat fee per change", clarmi: "No limits, ever" } },
  { label: "Competitor tracking", agency: true, local: false, clarmi: true,
    tips: { agency: "Add-on retainer", local: "Not offered", clarmi: "Monitored & updated" } },
  { label: "Uptime monitoring", agency: false, local: false, clarmi: true,
    tips: { agency: "Extra cost", local: "You're on your own", clarmi: "24/7 monitoring included" } },
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
      <div className="container" style={{ maxWidth: 1200, margin: "0 auto" }}>
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
            overflow: "visible",
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
                Early Bird
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
                  {feature.info && (
                    <span className="pricing-info-wrap">
                      <span className="pricing-info-icon">?</span>
                      <span className="pricing-tip">{feature.info}</span>
                    </span>
                  )}
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
            Custom design. Don&apos;t pay until you&apos;re happy.
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

        .pricing-info-wrap {
          position: relative;
          cursor: pointer;
          display: inline-flex;
          margin-left: 0.35rem;
          vertical-align: middle;
        }

        .pricing-info-icon {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          width: 16px;
          height: 16px;
          border-radius: 50%;
          border: 1px solid var(--text-light);
          font-size: 0.6rem;
          font-weight: 600;
          color: var(--text-light);
          opacity: 0.5;
          transition: opacity 0.2s ease;
        }

        .pricing-info-wrap:hover .pricing-info-icon {
          opacity: 0.85;
        }

        .pricing-info-wrap:hover .pricing-tip,
        .pricing-info-wrap:active .pricing-tip {
          opacity: 1;
          transform: translateX(-50%) translateY(0);
        }

        .pricing-tip-wrap {
          position: relative;
          cursor: pointer;
          display: inline-flex;
        }

        .pricing-tip {
          position: absolute;
          bottom: calc(100% + 10px);
          left: 50%;
          transform: translateX(-50%) translateY(6px);
          background: rgba(20, 20, 25, 0.95);
          backdrop-filter: blur(12px);
          -webkit-backdrop-filter: blur(12px);
          color: #f0f0f0;
          font-size: 0.8rem;
          line-height: 1.55;
          padding: 0.7rem 0.9rem;
          border-radius: 10px;
          pointer-events: none;
          opacity: 0;
          transition: opacity 0.25s ease, transform 0.25s ease;
          z-index: 100;
          width: max-content;
          max-width: 200px;
          text-align: center;
          box-shadow: 0 8px 30px rgba(0,0,0,0.25), 0 0 0 1px rgba(255,255,255,0.08);
          letter-spacing: 0.01em;
        }

        .pricing-tip::after {
          content: "";
          position: absolute;
          top: 100%;
          left: 50%;
          transform: translateX(-50%);
          border: 6px solid transparent;
          border-top-color: rgba(20, 20, 25, 0.95);
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
