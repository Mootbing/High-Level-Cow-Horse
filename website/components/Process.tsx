"use client";

import { useEffect, useRef } from "react";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";

gsap.registerPlugin(ScrollTrigger);

const STEPS = [
  {
    number: "01",
    title: "Send Us Your URL",
    detail: "4 min audit",
    desc: "Drop your link and we run a full audit — design, performance, SEO, mobile. A detailed report lands in your inbox in minutes.",
  },
  {
    number: "02",
    title: "We Research Everything",
    detail: "Competitor analysis",
    desc: "We crawl your competitors, extract your brand identity, colors, fonts, and content. We learn your business so the new site feels like yours.",
  },
  {
    number: "03",
    title: "Audit + Website, Free",
    detail: "No commitment",
    desc: "You get a full audit and a live preview of your redesigned site — completely free. No payment until you say \"deploy it.\"",
  },
  {
    number: "04",
    title: "Go Live",
    detail: "$250 to launch",
    desc: "Say the word and we push it live to your domain. SSL, hosting, analytics — all included. You're live in minutes, not weeks.",
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
      // Scroll-driven text rows — move along rotation axis
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

      // Reveal animations
      const observer = new IntersectionObserver(
        (entries) => {
          entries.forEach((entry) => {
            if (entry.isIntersecting) {
              el.querySelectorAll(".reveal").forEach((r, idx) => {
                setTimeout(() => r.classList.add("active"), idx * 120);
              });
              observer.disconnect();
            }
          });
        },
        { threshold: 0.08 }
      );
      observer.observe(el);
    }, el);

    return () => ctx.revert();
  }, []);

  return (
    <section ref={ref} className="section" id="process" style={{ position: "relative", overflow: "hidden" }}>
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
                opacity: 0.022,
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
        {/* Header */}
        <div style={{ textAlign: "center", marginBottom: "clamp(3rem, 6vh, 5rem)" }}>
          <h2 className="text-display-lg reveal">
            From <em className="font-serif" style={{ fontStyle: "italic" }}>outdated</em>
            <br />To <em className="font-serif" style={{ fontStyle: "italic" }}>outstanding</em>
          </h2>
        </div>

        {/* 2x2 Bento grid */}
        <div style={{
          display: "grid",
          gridTemplateColumns: "repeat(2, 1fr)",
          gap: "clamp(0.75rem, 1.5vw, 1.25rem)",
          maxWidth: 880,
          margin: "0 auto",
        }}>
          {STEPS.map((step, i) => (
            <div
              key={step.number}
              className={`reveal delay-${i + 1}`}
              style={{
                background: "var(--bg-card)",
                border: "1px solid var(--border)",
                borderRadius: "var(--radius-lg)",
                padding: "clamp(1.5rem, 3vw, 2.5rem)",
                display: "flex",
                flexDirection: "column",
                gap: "clamp(0.6rem, 1.2vh, 1rem)",
                transition: "border-color 0.3s ease, box-shadow 0.3s ease",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.borderColor = "var(--accent)";
                e.currentTarget.style.boxShadow = "0 8px 30px rgba(124,92,252,0.08)";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.borderColor = "var(--border)";
                e.currentTarget.style.boxShadow = "none";
              }}
            >
              {/* Number */}
              <span style={{
                fontFamily: '"Instrument Serif", Georgia, serif',
                fontSize: "clamp(2.5rem, 4.5vw, 3.5rem)",
                lineHeight: 1,
                color: "var(--accent)",
                opacity: 0.2,
              }}>
                {step.number}
              </span>

              {/* Title */}
              <h3 style={{
                fontFamily: '"Instrument Serif", Georgia, serif',
                fontSize: "clamp(1.3rem, 2vw, 1.7rem)",
                color: "var(--text)",
                lineHeight: 1.15,
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
        @media (max-width: 600px) {
          #process .container > div:last-child {
            grid-template-columns: 1fr !important;
          }
        }
      `}</style>
    </section>
  );
}
