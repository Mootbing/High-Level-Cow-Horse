"use client";

import { useEffect, useRef } from "react";

const SERVICES = [
  {
    title: "Design",
    description:
      "Custom designs that capture your brand\u2019s personality. Built from scratch using your real content, colors, and voice. Not a Squarespace template with your logo pasted on.",
    icon: (
      <svg width="48" height="48" viewBox="0 0 48 48" fill="none" className="service-icon">
        <rect x="6" y="6" width="36" height="36" rx="4" stroke="var(--accent)" strokeWidth="2" />
        <circle cx="18" cy="18" r="4" stroke="var(--accent)" strokeWidth="2" />
        <path d="M6 34L16 24L24 32L32 22L42 34" stroke="var(--accent)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    ),
    features: ["Brand-aligned visuals", "Mobile-first layouts", "Conversion-optimized UX"],
  },
  {
    title: "Build",
    description:
      "Lightning-fast sites built on Next.js with modern architecture. No WordPress, no page builders, no 47 plugins. Just clean code that loads in under 2 seconds.",
    icon: (
      <svg width="48" height="48" viewBox="0 0 48 48" fill="none" className="service-icon">
        <polyline points="18,12 6,24 18,36" stroke="var(--accent)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
        <polyline points="30,12 42,24 30,36" stroke="var(--accent)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
        <line x1="22" y1="8" x2="26" y2="40" stroke="var(--accent)" strokeWidth="2" strokeLinecap="round" />
      </svg>
    ),
    features: ["Next.js + React", "Sub-2s load times", "97+ Lighthouse score"],
  },
  {
    title: "Launch",
    description:
      "Deployed in days, not months. You get a live URL within 48 hours of approval. We handle hosting, SSL, domain setup, and analytics from day one.",
    icon: (
      <svg width="48" height="48" viewBox="0 0 48 48" fill="none" className="service-icon">
        <path d="M24 6L24 42" stroke="var(--accent)" strokeWidth="2" strokeLinecap="round" />
        <polyline points="16,14 24,6 32,14" stroke="var(--accent)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
        <path d="M8 28C8 28 12 20 24 20C36 20 40 28 40 28" stroke="var(--accent)" strokeWidth="2" strokeLinecap="round" />
        <circle cx="24" cy="38" r="4" stroke="var(--accent)" strokeWidth="2" />
      </svg>
    ),
    features: ["48hr turnaround", "Free SSL + hosting", "Analytics built in"],
  },
  {
    title: "Maintain",
    description:
      "Your site stays fast, secure, and up-to-date. Monthly revisions, performance monitoring, and content updates included. $50/mo covers everything.",
    icon: (
      <svg width="48" height="48" viewBox="0 0 48 48" fill="none" className="service-icon">
        <circle cx="24" cy="24" r="16" stroke="var(--accent)" strokeWidth="2" />
        <path d="M24 14V24L30 28" stroke="var(--accent)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
        <path d="M38 10L42 6" stroke="var(--accent)" strokeWidth="2" strokeLinecap="round" />
        <circle cx="42" cy="6" r="3" stroke="var(--accent)" strokeWidth="2" />
      </svg>
    ),
    features: ["Monthly updates", "Performance monitoring", "Priority support"],
  },
];

export default function Services() {
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
    <section ref={sectionRef} className="section" id="services">
      <div className="container">
        {/* Header */}
        <div style={{ textAlign: "center", marginBottom: "clamp(3rem, 6vh, 5rem)" }}>
          <span className="text-label reveal">What We Do</span>
          <h2
            className="text-display-lg reveal delay-1"
            style={{ marginTop: "clamp(0.8rem, 1.5vh, 1.2rem)" }}
          >
            Everything your website
            <br />
            <span style={{ color: "var(--accent)" }}>should already have</span>
          </h2>
        </div>

        {/* Services Grid */}
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(min(100%, 300px), 1fr))",
            gap: "clamp(1rem, 2vw, 1.5rem)",
          }}
        >
          {SERVICES.map((service, i) => (
            <div
              key={service.title}
              className={`card reveal delay-${i + 2}`}
              style={{
                display: "flex",
                flexDirection: "column",
                gap: "clamp(1.2rem, 2vh, 1.8rem)",
              }}
            >
              {/* Icon */}
              <div
                style={{
                  width: "clamp(56px, 7vw, 72px)",
                  height: "clamp(56px, 7vw, 72px)",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  borderRadius: "var(--radius)",
                  background: "rgba(200, 255, 0, 0.05)",
                  border: "1px solid rgba(200, 255, 0, 0.1)",
                }}
              >
                {service.icon}
              </div>

              {/* Title */}
              <h3
                style={{
                  fontFamily: '"Syne", sans-serif',
                  fontWeight: 700,
                  fontSize: "clamp(1.3rem, 2vw, 1.6rem)",
                  color: "var(--white)",
                }}
              >
                {service.title}
              </h3>

              {/* Description */}
              <p className="text-body" style={{ flex: 1 }}>
                {service.description}
              </p>

              {/* Features list */}
              <ul
                style={{
                  listStyle: "none",
                  display: "flex",
                  flexDirection: "column",
                  gap: "0.5rem",
                }}
              >
                {service.features.map((feature) => (
                  <li
                    key={feature}
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: "0.6rem",
                      fontFamily: '"Space Grotesk", sans-serif',
                      fontSize: "clamp(0.8rem, 0.95vw, 0.9rem)",
                      color: "var(--gray-300)",
                      fontWeight: 500,
                    }}
                  >
                    <svg width="14" height="14" viewBox="0 0 14 14" fill="none" style={{ flexShrink: 0 }}>
                      <path
                        d="M3 7L6 10L11 4"
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
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
