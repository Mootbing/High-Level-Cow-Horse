"use client";

import { useEffect, useRef } from "react";

const TIERS = [
  {
    label: "Traditional Agency",
    price: "$10,000+",
    monthly: "+ $200/mo retainer",
    verdict: "6–12 week timelines. Bloated teams. You're paying for their office rent.",
  },
  {
    label: "Local Designer",
    price: "$5,000+",
    monthly: "+ $150/mo maintenance",
    verdict: "WordPress under the hood. A template with your colors swapped in.",
  },
];

const CLARMI = {
  description: "Custom design. 48-hour delivery. Don't pay until you're happy.",
  features: [
    "Custom design from scratch — no templates",
    "Next.js build — sub-2s loads, 97+ Lighthouse",
    "48-hour delivery, not 6 weeks",
    "Mobile-responsive on every device",
    "SEO-optimized from day one",
    "SSL, hosting, analytics included",
    "Monthly revisions & performance monitoring",
    "Unlimited pre-launch revisions",
  ],
};

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
      { threshold: 0.15, rootMargin: "0px 0px -60px 0px" }
    );

    reveals.forEach((r) => observer.observe(r));
    return () => observer.disconnect();
  }, []);

  return (
    <section ref={ref} className="section" id="pricing">
      <div className="container" style={{ maxWidth: 680, margin: "0 auto" }}>
        {/* Header */}
        <div className="pricing-reveal" style={{ textAlign: "center", marginBottom: "clamp(3rem, 6vh, 5rem)", opacity: 0, transform: "translateY(30px)", transition: "opacity 0.9s cubic-bezier(0.16,1,0.3,1), transform 0.9s cubic-bezier(0.16,1,0.3,1)" }}>
          <h2 className="text-display-lg">
            Honest pricing. <em className="font-serif" style={{ fontStyle: "italic" }}>No surprises.</em>
          </h2>
        </div>

        {/* Competitor tiers — stacked, revealed on scroll */}
        {TIERS.map((tier, i) => (
          <div key={tier.label}>
            {/* Competitor row */}
            <div
              className="pricing-reveal"
              style={{
                opacity: 0,
                transform: "translateY(40px)",
                transition: "opacity 0.8s cubic-bezier(0.16,1,0.3,1), transform 0.8s cubic-bezier(0.16,1,0.3,1)",
                transitionDelay: `${i * 0.1}s`,
                display: "flex",
                alignItems: "center",
                gap: "clamp(1.2rem, 3vw, 2rem)",
                padding: "clamp(0.6rem, 1.2vw, 0.8rem) 0",
              }}
            >
              {/* Price */}
              <div style={{ flexShrink: 0, minWidth: "clamp(120px, 20vw, 180px)" }}>
                <span style={{
                  fontFamily: '"Instrument Serif", Georgia, serif',
                  fontSize: "clamp(2rem, 4vw, 3rem)",
                  color: "var(--text-light)",
                  lineHeight: 1,
                }}>
                  {tier.price}
                </span>
                <div style={{
                  fontSize: "clamp(0.75rem, 0.85vw, 0.82rem)",
                  color: "var(--text-light)",
                  marginTop: "0.25rem",
                }}>
                  {tier.monthly}
                </div>
              </div>

              {/* Label + verdict */}
              <div style={{ flex: 1 }}>
                <div style={{
                  fontSize: "clamp(0.88rem, 1vw, 0.95rem)",
                  fontWeight: 500,
                  color: "var(--text-muted)",
                  marginBottom: "0.25rem",
                }}>
                  {tier.label}
                </div>
                <div style={{
                  fontSize: "clamp(0.78rem, 0.88vw, 0.85rem)",
                  color: "var(--text-light)",
                  lineHeight: 1.5,
                }}>
                  {tier.verdict}
                </div>
              </div>
            </div>

            {/* Arrow connector */}
            <div
              className="pricing-reveal"
              style={{
                opacity: 0,
                transform: "translateY(20px)",
                transition: "opacity 0.6s cubic-bezier(0.16,1,0.3,1), transform 0.6s cubic-bezier(0.16,1,0.3,1)",
                transitionDelay: `${i * 0.1 + 0.15}s`,
                display: "flex",
                justifyContent: "center",
                padding: "clamp(0.2rem, 0.5vh, 0.3rem) 0",
              }}
            >
              <div style={{ width: 1, height: "clamp(20px, 3vh, 32px)", background: "var(--text-light)", opacity: 0.5 }} />
            </div>
          </div>
        ))}

        {/* Clarmi — the reveal payoff */}
        <div
          className="pricing-reveal"
          style={{
            opacity: 0,
            transform: "translateY(50px) scale(0.97)",
            transition: "opacity 1s cubic-bezier(0.16,1,0.3,1), transform 1s cubic-bezier(0.16,1,0.3,1)",
            background: "var(--bg-card)",
            border: "1px solid var(--accent)",
            borderRadius: "var(--radius-lg)",
            padding: "clamp(2rem, 4vw, 3rem)",
            position: "relative",
            boxShadow: "0 8px 40px rgba(124,92,252,0.08)",
            marginTop: "clamp(0.5rem, 1vh, 0.8rem)",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "clamp(0.8rem, 1.5vh, 1rem)" }}>
            <span className="text-label" style={{ color: "var(--accent)", letterSpacing: "0.15em" }}>Clarmi</span>
            <span style={{
              padding: "0.2rem 0.6rem",
              background: "var(--accent-soft)",
              color: "var(--accent)",
              borderRadius: "var(--radius-full)",
              fontSize: "0.68rem",
              fontWeight: 600,
              letterSpacing: "0.03em",
              border: "1px solid rgba(124, 92, 252, 0.15)",
            }}>
              Inauguration Discount
            </span>
          </div>

          {/* Price */}
          <div>
            <span style={{
              fontFamily: '"Instrument Serif", Georgia, serif',
              fontSize: "clamp(3rem, 6vw, 4.5rem)",
              lineHeight: 1,
              color: "var(--accent)",
            }}>
              $250
            </span>
            <div style={{ marginTop: "0.25rem" }}>
              <span className="price-period">+ $50/mo for a limited time</span>
            </div>
          </div>

          <p className="text-body" style={{ marginTop: "clamp(0.6rem, 1vh, 0.8rem)" }}>
            {CLARMI.description}
          </p>

          <div style={{ height: 1, background: "var(--border)", margin: "clamp(1rem, 2vh, 1.5rem) 0" }} />

          <ul style={{ listStyle: "none", display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(min(100%, 250px), 1fr))", gap: "0.4rem 1.5rem" }}>
            {CLARMI.features.map((f) => (
              <li key={f} style={{
                display: "flex", alignItems: "flex-start", gap: "0.5rem",
                fontSize: "clamp(0.8rem, 0.88vw, 0.85rem)", color: "var(--text-muted)", lineHeight: 1.5,
              }}>
                <svg width="12" height="12" viewBox="0 0 12 12" fill="none" style={{ flexShrink: 0, marginTop: "3px" }}>
                  <path d="M2.5 6L5 8.5L9.5 3.5" stroke="var(--accent)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
                {f}
              </li>
            ))}
          </ul>

        </div>
      </div>

      <style>{`
        .pricing-reveal.active {
          opacity: 1 !important;
          transform: translateY(0) scale(1) !important;
        }
      `}</style>
    </section>
  );
}
