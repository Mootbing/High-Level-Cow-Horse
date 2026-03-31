"use client";

import { useEffect, useRef } from "react";

const STATS = [
  {
    number: "88%",
    label: "of visitors won\u2019t return after a bad website experience",
    icon: (
      <svg width="32" height="32" viewBox="0 0 32 32" fill="none">
        <path d="M16 4L4 28H28L16 4Z" stroke="var(--accent)" strokeWidth="2" strokeLinejoin="round" />
        <line x1="16" y1="13" x2="16" y2="20" stroke="var(--accent)" strokeWidth="2" strokeLinecap="round" />
        <circle cx="16" cy="24" r="1.5" fill="var(--accent)" />
      </svg>
    ),
  },
  {
    number: "75%",
    label: "of consumers judge a company\u2019s credibility by its website design",
    icon: (
      <svg width="32" height="32" viewBox="0 0 32 32" fill="none">
        <circle cx="16" cy="16" r="12" stroke="var(--accent)" strokeWidth="2" />
        <circle cx="16" cy="16" r="5" stroke="var(--accent)" strokeWidth="2" />
        <circle cx="16" cy="16" r="1.5" fill="var(--accent)" />
      </svg>
    ),
  },
  {
    number: "8.7s",
    label: "is the average load time of a small business WordPress site",
    icon: (
      <svg width="32" height="32" viewBox="0 0 32 32" fill="none">
        <circle cx="16" cy="16" r="12" stroke="var(--accent)" strokeWidth="2" />
        <polyline points="16,8 16,16 22,20" stroke="var(--accent)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    ),
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
            const reveals = el.querySelectorAll(".reveal");
            reveals.forEach((r, i) => {
              setTimeout(() => r.classList.add("active"), i * 120);
            });
            observer.disconnect();
          }
        });
      },
      { threshold: 0.2 }
    );

    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  return (
    <section ref={sectionRef} className="section" id="problem">
      <div className="container">
        {/* Section header */}
        <div
          style={{
            maxWidth: "900px",
            marginBottom: "clamp(3rem, 6vh, 5rem)",
          }}
        >
          <span className="text-label reveal">The Hard Truth</span>
          <h2
            className="text-display-lg reveal delay-1"
            style={{ marginTop: "clamp(0.8rem, 1.5vh, 1.2rem)" }}
          >
            Your website is{" "}
            <span
              style={{
                textDecoration: "line-through",
                textDecorationColor: "var(--accent)",
                textDecorationThickness: "3px",
              }}
            >
              fine
            </span>
            .
            <br />
            Fine doesn&apos;t convert.
          </h2>
          <p className="text-body-lg reveal delay-2" style={{ marginTop: "clamp(1rem, 2vh, 1.5rem)", maxWidth: "650px" }}>
            Most small business websites were built five years ago on a
            platform that\u2019s now costing more than it\u2019s earning. Slow loads,
            dated design, zero mobile optimization. Your competitors already
            upgraded.
          </p>
        </div>

        {/* Stats Grid */}
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(min(100%, 300px), 1fr))",
            gap: "clamp(1rem, 2vw, 1.5rem)",
          }}
        >
          {STATS.map((stat, i) => (
            <div
              key={i}
              className={`card reveal delay-${i + 3}`}
              style={{
                display: "flex",
                flexDirection: "column",
                gap: "clamp(1rem, 2vh, 1.5rem)",
              }}
            >
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                {stat.icon}
                <span
                  style={{
                    fontFamily: '"Syne", sans-serif',
                    fontWeight: 800,
                    fontSize: "clamp(2.5rem, 5vw, 3.5rem)",
                    color: "var(--accent)",
                    letterSpacing: "-0.03em",
                    lineHeight: 1,
                  }}
                >
                  {stat.number}
                </span>
              </div>
              <p
                style={{
                  fontFamily: '"Space Grotesk", sans-serif',
                  fontSize: "clamp(0.9rem, 1.1vw, 1.05rem)",
                  lineHeight: 1.5,
                  color: "var(--gray-300)",
                }}
              >
                {stat.label}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
