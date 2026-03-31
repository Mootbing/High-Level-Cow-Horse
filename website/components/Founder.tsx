"use client";

import { useEffect, useRef } from "react";

const MILESTONES = [
  {
    age: "16",
    title: "App Acquired by the United Nations",
    description:
      "Built and launched an application that caught the attention of the UN, leading to an acquisition before finishing high school.",
  },
  {
    age: "17",
    title: "CSS Design Awards \u2014 Special Kudos",
    description:
      "Recognized internationally with a 7.92/10 judges\u2019 score across UI, UX, and Innovation. Praised for parallax design and animated graphics by 13 industry judges.",
  },
  {
    age: "18",
    title: "2nd Founding Engineer at $12M+ ARR Startup",
    description:
      "Joined as the second engineer at a high-growth startup, helping scale the product and engineering team from early stage to over $12M in annual recurring revenue.",
  },
];

export default function Founder() {
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
    <section ref={sectionRef} className="section" id="founder">
      <div className="container">
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(min(100%, 400px), 1fr))",
            gap: "clamp(3rem, 6vw, 6rem)",
            alignItems: "start",
          }}
        >
          {/* Left: Story */}
          <div>
            <span className="text-label reveal">The Founder</span>
            <h2
              className="text-display-md reveal delay-1"
              style={{ marginTop: "clamp(0.8rem, 1.5vh, 1.2rem)" }}
            >
              Built by someone who&apos;s been{" "}
              <span style={{ color: "var(--accent)" }}>shipping since 16</span>
            </h2>
            <p
              className="text-body-lg reveal delay-2"
              style={{ marginTop: "clamp(1rem, 2vh, 1.5rem)" }}
            >
              Clarmi was founded by Jason Xu \u2014 an engineer and designer who had
              an app acquired by the United Nations at 16, won international
              design recognition at 17, and helped scale a startup past $12M ARR
              as the 2nd founding engineer.
            </p>
            <p
              className="text-body reveal delay-3"
              style={{ marginTop: "clamp(0.75rem, 1.5vh, 1rem)" }}
            >
              Clarmi is the result of that experience distilled into a single
              mission: give every small business access to the same caliber of
              design and engineering that funded startups and Fortune 500s get \u2014
              at a price that makes sense.
            </p>

            {/* Award badge */}
            <div
              className="reveal delay-4"
              style={{
                marginTop: "clamp(1.5rem, 3vh, 2rem)",
                display: "inline-flex",
                alignItems: "center",
                gap: "0.75rem",
                padding: "0.75rem 1.25rem",
                background: "rgba(200, 255, 0, 0.05)",
                border: "1px solid rgba(200, 255, 0, 0.15)",
                borderRadius: "var(--radius)",
              }}
            >
              <svg width="28" height="28" viewBox="0 0 28 28" fill="none">
                <circle cx="14" cy="11" r="8" stroke="var(--accent)" strokeWidth="1.5" />
                <path d="M10 19L8 26L14 23L20 26L18 19" stroke="var(--accent)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                <path d="M11 10L13 8L15 12L17 7" stroke="var(--accent)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
              <div>
                <div
                  style={{
                    fontFamily: '"Space Grotesk", sans-serif',
                    fontWeight: 600,
                    fontSize: "clamp(0.8rem, 0.95vw, 0.9rem)",
                    color: "var(--accent)",
                  }}
                >
                  CSS Design Awards \u2014 Special Kudos 2023
                </div>
                <div
                  style={{
                    fontFamily: '"Space Grotesk", sans-serif',
                    fontSize: "clamp(0.7rem, 0.8vw, 0.75rem)",
                    color: "var(--gray-400)",
                  }}
                >
                  7.92/10 Judges Score \u00b7 UI 7.91 \u00b7 UX 7.85 \u00b7 Innovation 8.01
                </div>
              </div>
            </div>
          </div>

          {/* Right: Milestones */}
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              gap: "clamp(1.5rem, 3vh, 2rem)",
            }}
          >
            {MILESTONES.map((m, i) => (
              <div
                key={m.age}
                className={`card reveal delay-${i + 2}`}
                style={{
                  display: "flex",
                  gap: "clamp(1rem, 2vw, 1.5rem)",
                  alignItems: "flex-start",
                }}
              >
                {/* Age badge */}
                <div
                  style={{
                    width: "clamp(48px, 6vw, 60px)",
                    height: "clamp(48px, 6vw, 60px)",
                    borderRadius: "var(--radius)",
                    background: "rgba(200, 255, 0, 0.08)",
                    border: "1px solid rgba(200, 255, 0, 0.15)",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    flexShrink: 0,
                  }}
                >
                  <span
                    style={{
                      fontFamily: '"Syne", sans-serif',
                      fontWeight: 800,
                      fontSize: "clamp(1.1rem, 1.5vw, 1.4rem)",
                      color: "var(--accent)",
                    }}
                  >
                    {m.age}
                  </span>
                </div>

                <div>
                  <h3
                    style={{
                      fontFamily: '"Syne", sans-serif',
                      fontWeight: 700,
                      fontSize: "clamp(1rem, 1.4vw, 1.2rem)",
                      color: "var(--white)",
                      lineHeight: 1.2,
                      marginBottom: "0.4rem",
                    }}
                  >
                    {m.title}
                  </h3>
                  <p
                    style={{
                      fontFamily: '"Space Grotesk", sans-serif',
                      fontSize: "clamp(0.85rem, 0.95vw, 0.9rem)",
                      lineHeight: 1.5,
                      color: "var(--gray-400)",
                    }}
                  >
                    {m.description}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
