"use client";

import { useEffect, useRef } from "react";

const TESTIMONIALS = [
  {
    quote:
      "We went from a WordPress site that took 8 seconds to load to a custom build that scores 98 on Lighthouse. Our booking inquiries doubled in the first month.",
    name: "Maria Chen",
    title: "Owner, Pure Glow Aesthetics",
    initials: "MC",
  },
  {
    quote:
      "I was skeptical about the $500 price. Then I saw the pitch deck they sent within an hour of me submitting my URL. These people actually looked at my site and told me exactly what was wrong. Nobody else does that.",
    name: "David Okafor",
    title: "Partner, Summit Legal Group",
    initials: "DO",
  },
  {
    quote:
      "48 hours. That\u2019s how long it took from \u2018yes\u2019 to a live site. My old developer quoted me 6 weeks. The new site has already paid for itself in catering orders.",
    name: "Sarah Bellini",
    title: "Owner, Bella Vista Ristorante",
    initials: "SB",
  },
];

export default function Testimonials() {
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
              setTimeout(() => r.classList.add("active"), i * 120);
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
    <section ref={sectionRef} className="section">
      <div className="container">
        {/* Header */}
        <div style={{ textAlign: "center", marginBottom: "clamp(3rem, 6vh, 5rem)" }}>
          <span className="text-label reveal">Client Stories</span>
          <h2
            className="text-display-lg reveal delay-1"
            style={{ marginTop: "clamp(0.8rem, 1.5vh, 1.2rem)" }}
          >
            Don&apos;t take our
            <br />
            <span style={{ color: "var(--accent)" }}>word for it</span>
          </h2>
        </div>

        {/* Testimonial grid */}
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(min(100%, 320px), 1fr))",
            gap: "clamp(1rem, 2vw, 1.5rem)",
          }}
        >
          {TESTIMONIALS.map((t, i) => (
            <div
              key={t.name}
              className={`card reveal delay-${i + 2}`}
              style={{
                display: "flex",
                flexDirection: "column",
                justifyContent: "space-between",
                gap: "clamp(1.5rem, 3vh, 2rem)",
              }}
            >
              {/* Quote icon */}
              <svg
                width="32"
                height="24"
                viewBox="0 0 32 24"
                fill="none"
                style={{ opacity: 0.15 }}
              >
                <path
                  d="M0 24V14.4C0 6.4 4.8 1.6 14.4 0L16 3.2C10.4 4.8 8 8 7.2 11.2H12.8V24H0ZM16 24V14.4C16 6.4 20.8 1.6 30.4 0L32 3.2C26.4 4.8 24 8 23.2 11.2H28.8V24H16Z"
                  fill="var(--accent)"
                />
              </svg>

              {/* Quote text */}
              <p
                style={{
                  fontFamily: '"Space Grotesk", sans-serif',
                  fontSize: "clamp(0.95rem, 1.1vw, 1.05rem)",
                  lineHeight: 1.65,
                  color: "var(--gray-300)",
                  fontWeight: 400,
                  flex: 1,
                }}
              >
                &ldquo;{t.quote}&rdquo;
              </p>

              {/* Author */}
              <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
                <div
                  style={{
                    width: 40,
                    height: 40,
                    borderRadius: "50%",
                    background: "rgba(200, 255, 0, 0.1)",
                    border: "1px solid rgba(200, 255, 0, 0.2)",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    fontFamily: '"Syne", sans-serif',
                    fontWeight: 700,
                    fontSize: "0.75rem",
                    color: "var(--accent)",
                    letterSpacing: "0.02em",
                    flexShrink: 0,
                  }}
                >
                  {t.initials}
                </div>
                <div>
                  <div
                    style={{
                      fontFamily: '"Space Grotesk", sans-serif',
                      fontWeight: 600,
                      fontSize: "clamp(0.85rem, 1vw, 0.9rem)",
                      color: "var(--white)",
                    }}
                  >
                    {t.name}
                  </div>
                  <div
                    style={{
                      fontFamily: '"Space Grotesk", sans-serif',
                      fontSize: "clamp(0.75rem, 0.85vw, 0.8rem)",
                      color: "var(--gray-500)",
                    }}
                  >
                    {t.title}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
