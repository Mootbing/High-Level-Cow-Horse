"use client";

import { useEffect, useRef, useCallback } from "react";

const SERVICES = [
  {
    title: "Design",
    description: "Custom designs built from your real content, colors, and voice. Not a template with your logo slapped on.",
    features: ["Brand-aligned visuals", "Mobile-first layouts", "Conversion-optimized UX"],
  },
  {
    title: "Build",
    description: "Lightning-fast sites on Next.js. No WordPress, no page builders, no 47 plugins. Just clean code that loads in under 2 seconds.",
    features: ["Next.js + React", "Sub-2s load times", "97+ Lighthouse score"],
  },
  {
    title: "Launch",
    description: "Live URL within 48 hours of approval. Hosting, SSL, domain setup, and analytics from day one.",
    features: ["48hr turnaround", "Free SSL + hosting", "Analytics included"],
  },
  {
    title: "Maintain",
    description: "Your site stays fast, secure, and current. Monthly revisions and performance monitoring included.",
    features: ["Monthly updates", "Performance monitoring", "Priority support"],
  },
];

function SpotlightCard({ children, className, style }: { children: React.ReactNode; className?: string; style?: React.CSSProperties }) {
  const cardRef = useRef<HTMLDivElement>(null);

  const handleMouseMove = useCallback((e: React.MouseEvent) => {
    const el = cardRef.current;
    if (!el) return;
    const rect = el.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    el.style.setProperty("--spotlight-x", `${x}px`);
    el.style.setProperty("--spotlight-y", `${y}px`);
  }, []);

  return (
    <div
      ref={cardRef}
      className={`spotlight-card ${className || ""}`}
      style={{
        ...style,
        "--spotlight-x": "50%",
        "--spotlight-y": "50%",
      } as React.CSSProperties}
      onMouseMove={handleMouseMove}
    >
      <div
        style={{
          position: "absolute",
          width: 300,
          height: 300,
          borderRadius: "50%",
          background: "radial-gradient(circle, var(--accent-soft) 0%, transparent 70%)",
          left: "var(--spotlight-x)",
          top: "var(--spotlight-y)",
          transform: "translate(-50%, -50%)",
          pointerEvents: "none",
          opacity: 0,
          transition: "opacity 0.4s ease",
        }}
        className="spotlight-glow"
      />
      <div style={{ position: "relative", zIndex: 1 }}>{children}</div>
    </div>
  );
}

export default function Services() {
  const sectionRef = useRef<HTMLElement>(null);

  useEffect(() => {
    const el = sectionRef.current;
    if (!el) return;
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            el.querySelectorAll(".reveal").forEach((r, i) => {
              setTimeout(() => r.classList.add("active"), i * 80);
            });
            observer.disconnect();
          }
        });
      },
      { threshold: 0.1 }
    );
    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    // Activate spotlight glow on hover via CSS
    const style = document.createElement("style");
    style.textContent = `.spotlight-card:hover .spotlight-glow { opacity: 1 !important; }`;
    document.head.appendChild(style);
    return () => { document.head.removeChild(style); };
  }, []);

  return (
    <section ref={sectionRef} className="section" id="services">
      <div className="container">
        <div style={{ textAlign: "center", marginBottom: "clamp(3rem, 6vh, 5rem)" }}>
          <span className="text-label reveal">What We Do</span>
          <h2 className="text-display-lg reveal delay-1" style={{ marginTop: "clamp(0.8rem, 1.5vh, 1.2rem)" }}>
            Everything your website
            <br />
            <em className="font-serif" style={{ fontStyle: "italic" }}>should already have</em>
          </h2>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(min(100%, 280px), 1fr))", gap: "clamp(0.75rem, 1.5vw, 1rem)" }}>
          {SERVICES.map((service, i) => (
            <SpotlightCard
              key={service.title}
              className={`reveal delay-${i + 2}`}
              style={{ display: "flex", flexDirection: "column", gap: "clamp(1rem, 2vh, 1.5rem)" }}
            >
              {/* Number */}
              <span
                style={{
                  fontFamily: '"Instrument Serif", Georgia, serif',
                  fontSize: "clamp(2.5rem, 4vw, 3.5rem)",
                  color: "var(--border)",
                  lineHeight: 1,
                  letterSpacing: "-0.04em",
                }}
              >
                0{i + 1}
              </span>

              <h3 style={{ fontFamily: '"Instrument Serif", Georgia, serif', fontSize: "clamp(1.4rem, 2vw, 1.7rem)", color: "var(--text)" }}>
                {service.title}
              </h3>

              <p className="text-body" style={{ flex: 1 }}>{service.description}</p>

              <ul style={{ listStyle: "none", display: "flex", flexDirection: "column", gap: "0.4rem" }}>
                {service.features.map((f) => (
                  <li key={f} style={{ display: "flex", alignItems: "center", gap: "0.5rem", fontSize: "clamp(0.82rem, 0.9vw, 0.88rem)", color: "var(--text-muted)" }}>
                    <svg width="12" height="12" viewBox="0 0 12 12" fill="none" style={{ flexShrink: 0 }}>
                      <path d="M2.5 6L5 8.5L9.5 3.5" stroke="var(--accent)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                    </svg>
                    {f}
                  </li>
                ))}
              </ul>
            </SpotlightCard>
          ))}
        </div>
      </div>
    </section>
  );
}
