"use client";

import { useEffect, useRef } from "react";

const STATS = [
  {
    number: "88%",
    label: "of visitors won't return after a bad website experience",
  },
  {
    number: "75%",
    label: "judge credibility by website design alone",
  },
  {
    number: "8.7s",
    label: "average load time for small business WordPress sites",
  },
];

export default function Problem() {
  const sectionRef = useRef<HTMLElement>(null);

  useEffect(() => {
    const el = sectionRef.current;
    if (!el) return;
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            el.querySelectorAll(".reveal").forEach((r, i) => {
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
    <section ref={sectionRef} className="section" id="problem">
      <div className="container">
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(min(100%, 450px), 1fr))", gap: "clamp(3rem, 6vw, 6rem)", alignItems: "start" }}>
          {/* Left: Editorial text */}
          <div>
            <span className="text-label reveal">The Hard Truth</span>
            <h2 className="text-display-lg reveal delay-1" style={{ marginTop: "clamp(0.8rem, 1.5vh, 1.2rem)" }}>
              Your website is{" "}
              <em className="font-serif" style={{ fontStyle: "italic", textDecoration: "line-through", textDecorationColor: "var(--accent)", textDecorationThickness: "2px" }}>
                fine
              </em>.
            </h2>
            <p className="text-body-lg reveal delay-2" style={{ marginTop: "clamp(1rem, 2vh, 1.5rem)", maxWidth: "500px" }}>
              Fine doesn&apos;t convert. Most small business websites were built
              years ago on platforms that now cost more than they earn. Your
              competitors already upgraded.
            </p>
          </div>

          {/* Right: Stat cards */}
          <div style={{ display: "flex", flexDirection: "column", gap: "clamp(0.75rem, 1.5vw, 1rem)" }}>
            {STATS.map((stat, i) => (
              <div
                key={i}
                className={`card reveal delay-${i + 3}`}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "clamp(1rem, 2vw, 1.5rem)",
                }}
              >
                <span
                  style={{
                    fontFamily: '"Instrument Serif", Georgia, serif',
                    fontSize: "clamp(2rem, 3.5vw, 2.8rem)",
                    color: "var(--accent)",
                    letterSpacing: "-0.03em",
                    lineHeight: 1,
                    flexShrink: 0,
                    minWidth: "clamp(60px, 8vw, 80px)",
                  }}
                >
                  {stat.number}
                </span>
                <p style={{ fontSize: "clamp(0.88rem, 1vw, 0.95rem)", lineHeight: 1.5, color: "var(--text-muted)" }}>
                  {stat.label}
                </p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
