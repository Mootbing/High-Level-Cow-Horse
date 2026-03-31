"use client";

import { useEffect, useRef } from "react";

const STEPS = [
  {
    number: "01",
    title: "Send Us Your URL",
    description:
      "Drop your current website URL into the form. Our AI audits your site in minutes \u2014 design, performance, SEO, mobile experience, content quality. You get a detailed report for free.",
    detail: "Average audit time: 4 minutes",
  },
  {
    number: "02",
    title: "See Your Future Site",
    description:
      "We send you a personalized pitch deck showing exactly what we\u2019ll build. Specific problems we found, specific solutions we\u2019re proposing. No generic templates.",
    detail: "Delivered within 1 hour",
  },
  {
    number: "03",
    title: "We Build It",
    description:
      "Custom design, AI-generated assets, hand-tuned animations. Your real content, your brand colors, your story. Built on Next.js for speed and SEO. Deployed to a preview URL for your review.",
    detail: "Average build time: 48 hours",
  },
  {
    number: "04",
    title: "You Go Live",
    description:
      "Review the preview, request changes, and when you\u2019re happy \u2014 we push it live. Domain, hosting, SSL, analytics all configured. Your new site is earning from day one.",
    detail: "Unlimited revisions before launch",
  },
];

export default function Process() {
  const sectionRef = useRef<HTMLElement>(null);
  const lineRef = useRef<HTMLDivElement>(null);
  const stepsRef = useRef<(HTMLDivElement | null)[]>([]);

  useEffect(() => {
    const el = sectionRef.current;
    if (!el) return;

    // Reveal animations
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
      { threshold: 0.1 }
    );
    observer.observe(el);

    // Scroll-driven line fill
    const handleScroll = () => {
      if (!lineRef.current || !sectionRef.current) return;

      const rect = sectionRef.current.getBoundingClientRect();
      const sectionTop = rect.top;
      const sectionHeight = rect.height;
      const windowHeight = window.innerHeight;

      // Calculate progress through the section
      const start = sectionTop - windowHeight * 0.6;
      const end = sectionTop + sectionHeight - windowHeight * 0.4;
      const progress = Math.max(0, Math.min(1, -start / (end - start)));

      const fillEl = lineRef.current.querySelector(".process-line-fill") as HTMLElement;
      if (fillEl) {
        fillEl.style.height = `${progress * 100}%`;
      }

      // Activate dots based on progress
      stepsRef.current.forEach((step, i) => {
        if (!step) return;
        const stepProgress = (i + 0.5) / STEPS.length;
        const dot = step.querySelector(".process-dot");
        if (dot) {
          if (progress >= stepProgress) {
            dot.classList.add("active");
          } else {
            dot.classList.remove("active");
          }
        }
      });
    };

    window.addEventListener("scroll", handleScroll, { passive: true });
    handleScroll();

    return () => {
      observer.disconnect();
      window.removeEventListener("scroll", handleScroll);
    };
  }, []);

  return (
    <section ref={sectionRef} className="section" id="process">
      <div className="container">
        {/* Header */}
        <div style={{ textAlign: "center", marginBottom: "clamp(3rem, 6vh, 5rem)" }}>
          <span className="text-label reveal">How It Works</span>
          <h2
            className="text-display-lg reveal delay-1"
            style={{ marginTop: "clamp(0.8rem, 1.5vh, 1.2rem)" }}
          >
            From <span style={{ color: "var(--accent)" }}>outdated</span> to
            <br />outstanding in 4 steps
          </h2>
        </div>

        {/* Timeline */}
        <div
          style={{
            maxWidth: "800px",
            margin: "0 auto",
            position: "relative",
            paddingLeft: "clamp(40px, 6vw, 60px)",
          }}
        >
          {/* Vertical line track */}
          <div
            ref={lineRef}
            className="process-line"
            style={{ left: "clamp(4px, 1vw, 8px)" }}
          >
            <div className="process-line-fill" />
          </div>

          {/* Steps */}
          <div style={{ display: "flex", flexDirection: "column", gap: "clamp(3rem, 6vh, 5rem)" }}>
            {STEPS.map((step, i) => (
              <div
                key={step.number}
                ref={(el) => { stepsRef.current[i] = el; }}
                className={`reveal delay-${i + 2}`}
                style={{
                  display: "flex",
                  gap: "clamp(1rem, 2.5vw, 2rem)",
                  position: "relative",
                }}
              >
                {/* Dot */}
                <div
                  className="process-dot"
                  style={{
                    position: "absolute",
                    left: `calc(-1 * clamp(40px, 6vw, 60px) + clamp(-2px, -0.3vw, 0px))`,
                  }}
                />

                {/* Content */}
                <div style={{ flex: 1 }}>
                  {/* Number + Title */}
                  <div
                    style={{
                      display: "flex",
                      alignItems: "baseline",
                      gap: "clamp(0.5rem, 1.5vw, 1rem)",
                      marginBottom: "clamp(0.5rem, 1vh, 0.75rem)",
                    }}
                  >
                    <span
                      style={{
                        fontFamily: '"Syne", sans-serif',
                        fontWeight: 800,
                        fontSize: "clamp(0.8rem, 1vw, 0.95rem)",
                        color: "var(--accent)",
                        letterSpacing: "0.05em",
                      }}
                    >
                      {step.number}
                    </span>
                    <h3
                      style={{
                        fontFamily: '"Syne", sans-serif',
                        fontWeight: 700,
                        fontSize: "clamp(1.3rem, 2.5vw, 1.8rem)",
                        color: "var(--white)",
                        lineHeight: 1.2,
                      }}
                    >
                      {step.title}
                    </h3>
                  </div>

                  <p className="text-body" style={{ marginBottom: "clamp(0.5rem, 1vh, 0.75rem)" }}>
                    {step.description}
                  </p>

                  {/* Detail tag */}
                  <span
                    style={{
                      display: "inline-block",
                      padding: "0.35rem 0.85rem",
                      background: "rgba(200, 255, 0, 0.06)",
                      border: "1px solid rgba(200, 255, 0, 0.12)",
                      borderRadius: "100px",
                      fontFamily: '"Space Grotesk", sans-serif',
                      fontSize: "clamp(0.7rem, 0.85vw, 0.8rem)",
                      fontWeight: 500,
                      color: "var(--accent)",
                    }}
                  >
                    {step.detail}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
