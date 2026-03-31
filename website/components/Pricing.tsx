"use client";

import { useEffect, useRef } from "react";

const PLANS = [
  {
    name: "Launch",
    price: "$500",
    period: "one-time",
    monthly: "$50/mo",
    monthlyLabel: "maintenance",
    description: "Everything you need to replace your outdated site with something that actually works.",
    features: [
      "Custom design from scratch",
      "Mobile-responsive on all devices",
      "SEO-optimized from day one",
      "Analytics dashboard",
      "1 content revision per month",
      "SSL + hosting included",
      "48-hour delivery",
    ],
    highlighted: false,
  },
  {
    name: "Growth",
    price: "$500",
    period: "one-time",
    monthly: "$100/mo",
    monthlyLabel: "everything",
    description: "For businesses that want their website to be an active growth engine, not just a brochure.",
    features: [
      "Everything in Launch",
      "Priority support (same-day)",
      "Weekly content updates",
      "A/B testing for conversions",
      "Blog management",
      "Monthly performance reports",
      "Dedicated account manager",
    ],
    highlighted: true,
  },
];

export default function Pricing() {
  const sectionRef = useRef<HTMLElement>(null);

  useEffect(() => {
    const el = sectionRef.current;
    if (!el) return;

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            const reveals = el.querySelectorAll(".reveal");
            reveals.forEach((r, i) => {
              setTimeout(() => r.classList.add("active"), i * 100);
            });
            observer.disconnect();
          }
        });
      },
      { threshold: 0.15 }
    );

    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  return (
    <section ref={sectionRef} className="section" id="pricing">
      <div className="container">
        {/* Header */}
        <div style={{ textAlign: "center", marginBottom: "clamp(3rem, 6vh, 5rem)" }}>
          <span className="text-label reveal">Pricing</span>
          <h2
            className="text-display-lg reveal delay-1"
            style={{ marginTop: "clamp(0.8rem, 1.5vh, 1.2rem)" }}
          >
            Honest pricing.
            <br />
            <span style={{ color: "var(--accent)" }}>No surprises.</span>
          </h2>
          <p className="text-body-lg reveal delay-2" style={{ maxWidth: "550px", margin: "clamp(1rem, 2vh, 1.5rem) auto 0" }}>
            Agencies charge $10,000+. Local designers charge $5,000+.
            We charge $500 because AI lets us work faster, not cheaper.
          </p>
        </div>

        {/* Comparison strike-throughs */}
        <div
          className="reveal delay-2"
          style={{
            display: "flex",
            justifyContent: "center",
            gap: "clamp(1.5rem, 4vw, 3rem)",
            marginBottom: "clamp(2rem, 4vh, 3rem)",
            flexWrap: "wrap",
          }}
        >
          <div style={{ textAlign: "center", opacity: 0.4 }}>
            <div
              style={{
                fontFamily: '"Syne", sans-serif',
                fontWeight: 700,
                fontSize: "clamp(1.2rem, 2vw, 1.6rem)",
                textDecoration: "line-through",
                textDecorationColor: "#ff4444",
                color: "var(--gray-400)",
              }}
            >
              $10,000+
            </div>
            <div style={{ fontSize: "clamp(0.7rem, 0.85vw, 0.8rem)", color: "var(--gray-600)", marginTop: "0.2rem" }}>
              Traditional Agency
            </div>
          </div>
          <div style={{ textAlign: "center", opacity: 0.4 }}>
            <div
              style={{
                fontFamily: '"Syne", sans-serif',
                fontWeight: 700,
                fontSize: "clamp(1.2rem, 2vw, 1.6rem)",
                textDecoration: "line-through",
                textDecorationColor: "#ff4444",
                color: "var(--gray-400)",
              }}
            >
              $5,000+
            </div>
            <div style={{ fontSize: "clamp(0.7rem, 0.85vw, 0.8rem)", color: "var(--gray-600)", marginTop: "0.2rem" }}>
              Local Designer
            </div>
          </div>
          <div style={{ textAlign: "center" }}>
            <div
              style={{
                fontFamily: '"Syne", sans-serif',
                fontWeight: 800,
                fontSize: "clamp(1.2rem, 2vw, 1.6rem)",
                color: "var(--accent)",
              }}
            >
              $500
            </div>
            <div style={{ fontSize: "clamp(0.7rem, 0.85vw, 0.8rem)", color: "var(--accent)", marginTop: "0.2rem", fontWeight: 600 }}>
              Clarmi
            </div>
          </div>
        </div>

        {/* Pricing Cards */}
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(min(100%, 360px), 1fr))",
            gap: "clamp(1rem, 2vw, 1.5rem)",
            maxWidth: "860px",
            margin: "0 auto",
          }}
        >
          {PLANS.map((plan, i) => (
            <div
              key={plan.name}
              className={`${plan.highlighted ? "card-accent" : "card"} reveal delay-${i + 3}`}
              style={{
                display: "flex",
                flexDirection: "column",
                gap: "clamp(1.2rem, 2vh, 1.8rem)",
              }}
            >
              {/* Plan badge */}
              {plan.highlighted && (
                <span
                  style={{
                    alignSelf: "flex-start",
                    padding: "0.3rem 0.85rem",
                    background: "var(--accent)",
                    color: "var(--black)",
                    borderRadius: "100px",
                    fontFamily: '"Space Grotesk", sans-serif',
                    fontSize: "0.75rem",
                    fontWeight: 700,
                    letterSpacing: "0.05em",
                    textTransform: "uppercase",
                  }}
                >
                  Most Popular
                </span>
              )}

              {/* Plan name */}
              <h3
                style={{
                  fontFamily: '"Syne", sans-serif',
                  fontWeight: 700,
                  fontSize: "clamp(1.3rem, 2vw, 1.6rem)",
                  color: "var(--white)",
                }}
              >
                {plan.name}
              </h3>

              {/* Price */}
              <div>
                <div style={{ display: "flex", alignItems: "baseline", gap: "0.5rem" }}>
                  <span className="price-tag">{plan.price}</span>
                  <span className="price-period">{plan.period}</span>
                </div>
                <div
                  style={{
                    marginTop: "0.3rem",
                    display: "flex",
                    alignItems: "baseline",
                    gap: "0.4rem",
                  }}
                >
                  <span
                    style={{
                      fontFamily: '"Syne", sans-serif',
                      fontWeight: 700,
                      fontSize: "clamp(1.1rem, 1.5vw, 1.3rem)",
                      color: "var(--white)",
                    }}
                  >
                    + {plan.monthly}
                  </span>
                  <span className="price-period">{plan.monthlyLabel}</span>
                </div>
              </div>

              <p className="text-body">{plan.description}</p>

              {/* Divider */}
              <div style={{ height: 1, background: "var(--gray-700)" }} />

              {/* Features */}
              <ul style={{ listStyle: "none", display: "flex", flexDirection: "column", gap: "0.65rem", flex: 1 }}>
                {plan.features.map((feature) => (
                  <li
                    key={feature}
                    style={{
                      display: "flex",
                      alignItems: "flex-start",
                      gap: "0.6rem",
                      fontFamily: '"Space Grotesk", sans-serif',
                      fontSize: "clamp(0.85rem, 0.95vw, 0.9rem)",
                      color: "var(--gray-300)",
                      fontWeight: 400,
                      lineHeight: 1.4,
                    }}
                  >
                    <svg
                      width="16"
                      height="16"
                      viewBox="0 0 16 16"
                      fill="none"
                      style={{ flexShrink: 0, marginTop: "2px" }}
                    >
                      <path
                        d="M3 8L6.5 11.5L13 4.5"
                        stroke="var(--accent)"
                        strokeWidth="1.5"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                      />
                    </svg>
                    {feature}
                  </li>
                ))}
              </ul>

              {/* CTA */}
              <a
                href="#cta"
                className={plan.highlighted ? "btn-primary" : "btn-outline"}
                style={{ textAlign: "center", marginTop: "auto" }}
              >
                Get Started
              </a>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
