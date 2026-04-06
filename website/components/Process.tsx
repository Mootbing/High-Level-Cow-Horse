"use client";

import { useEffect, useRef } from "react";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";

gsap.registerPlugin(ScrollTrigger);

const STEPS = [
  {
    number: "01",
    title: "Send Us Your URL",
    desc: "Drop your link. We run a full audit — design, performance, SEO, mobile — and a detailed report lands in your inbox.",
    detail: "4 min audit",
  },
  {
    number: "02",
    title: "We Research Everything",
    desc: "We crawl your competitors, extract your brand identity, and learn your business so the new site feels like yours.",
    detail: "Competitor analysis",
  },
  {
    number: "03",
    title: "See It Before You Pay",
    desc: "You get a full audit and a live preview of your redesigned site first. No upfront risk. Pay only when you approve.",
    detail: "No commitment",
  },
  {
    number: "04",
    title: "Go Live",
    desc: "Say the word and we push it live to your domain. SSL, hosting, analytics, and updates are covered in one flat monthly fee.",
    detail: "$500 to launch",
  },
];

const BG_WORDS = ["DESIGN", "BUILD", "LAUNCH", "SHIP"];

export default function Process() {
  const ref = useRef<HTMLElement>(null);
  const scrollRowsRef = useRef<(HTMLDivElement | null)[]>([]);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;

    const ctx = gsap.context(() => {
      scrollRowsRef.current.forEach((row, i) => {
        if (!row) return;
        const direction = i % 2 === 0 ? 1 : -1;
        const angleDeg = direction === 1 ? -12 : 12;
        const angleRad = (angleDeg * Math.PI) / 180;
        const dist = 400;
        gsap.to(row, {
          x: () => direction * Math.cos(angleRad) * dist,
          y: () => direction * Math.sin(angleRad) * dist,
          ease: "none",
          scrollTrigger: {
            trigger: el,
            start: "top bottom",
            end: "bottom top",
            scrub: 0.5,
          },
        });
      });
    }, el);

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            el.querySelectorAll(".reveal").forEach((r, i) => {
              setTimeout(() => r.classList.add("active"), i * 120);
            });
            observer.disconnect();
          }
        });
      },
      { threshold: 0.1 }
    );
    observer.observe(el);

    return () => {
      ctx.revert();
      observer.disconnect();
    };
  }, []);

  return (
    <section
      ref={ref}
      className="section"
      id="process"
      style={{
        position: "relative",
        overflow: "hidden",
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
      }}
    >
      {/* Background scroll-driven text */}
      <div style={{
        position: "absolute",
        inset: 0,
        overflow: "hidden",
        pointerEvents: "none",
        zIndex: 0,
      }}>
        {BG_WORDS.map((word, i) => {
          const direction = i % 2 === 0;
          return (
            <div
              key={word}
              ref={(el) => { scrollRowsRef.current[i] = el; }}
              style={{
                position: "absolute",
                fontFamily: '"Inter", system-ui, sans-serif',
                fontSize: "clamp(4rem, 8vw, 7rem)",
                fontWeight: 900,
                color: "var(--text)",
                opacity: 0.011,
                whiteSpace: "nowrap",
                transform: `rotate(${direction ? -12 : 12}deg) translateX(${direction ? "-200px" : "0px"})`,
                top: `${i * 25 - 5}%`,
                left: "-20%",
                letterSpacing: "0.05em",
                userSelect: "none",
                textTransform: "uppercase",
              }}
            >
              {`${word} · `.repeat(10)}
            </div>
          );
        })}
      </div>

      <div className="container" style={{ position: "relative", zIndex: 1 }}>
        {/* Header — matches Work/Pricing pattern */}
        <div style={{ textAlign: "center", marginBottom: "clamp(3rem, 6vh, 5rem)" }}>
          <h2 className="text-display-lg reveal delay-1">
            The <em className="font-serif" style={{ fontStyle: "italic" }}>Clarmi Way</em>
          </h2>
          <p className="text-body-lg reveal delay-1" style={{ maxWidth: "420px", margin: "clamp(0.8rem, 1.5vh, 1rem) auto 0" }}>
            From audit to launch in 36 hours.
          </p>
        </div>

        {/* 4-column grid */}
        <div className="process-grid" style={{
          display: "grid",
          gridTemplateColumns: "repeat(4, 1fr)",
          gap: "clamp(1.5rem, 3vw, 2.5rem)",
          maxWidth: 1200,
          margin: "0 auto",
        }}>
          {STEPS.map((step, i) => (
            <div
              key={step.number}
              className={`reveal delay-${i + 2}`}
              style={{
                display: "flex",
                flexDirection: "column",
                gap: "clamp(0.4rem, 0.8vh, 0.6rem)",
              }}
            >
              {/* Number */}
              <span style={{
                fontFamily: '"Instrument Serif", Georgia, serif',
                fontSize: "clamp(2.5rem, 4vw, 3.5rem)",
                lineHeight: 1,
                color: "var(--accent)",
                opacity: 0.2,
              }}>
                {step.number}
              </span>

              {/* Title */}
              <h3 style={{
                fontFamily: '"Instrument Serif", Georgia, serif',
                fontSize: "clamp(1.15rem, 1.6vw, 1.45rem)",
                color: "var(--text)",
                lineHeight: 1.2,
              }}>
                {step.title}
              </h3>

              {/* Description */}
              <p style={{
                fontSize: "clamp(0.82rem, 0.92vw, 0.9rem)",
                color: "var(--text-muted)",
                lineHeight: 1.6,
              }}>
                {step.desc}
              </p>

              {/* Badge */}
              <span style={{
                display: "inline-block",
                alignSelf: "flex-start",
                marginTop: "auto",
                padding: "0.3rem 0.75rem",
                background: "var(--accent-soft)",
                borderRadius: "var(--radius-full)",
                fontSize: "clamp(0.7rem, 0.8vw, 0.76rem)",
                fontWeight: 500,
                color: "var(--accent)",
              }}>
                {step.detail}
              </span>
            </div>
          ))}
        </div>
      </div>

      <style>{`
        @media (max-width: 768px) {
          .process-grid { grid-template-columns: repeat(2, 1fr) !important; }
        }
        @media (max-width: 480px) {
          .process-grid { grid-template-columns: 1fr !important; }
        }
      `}</style>
    </section>
  );
}
