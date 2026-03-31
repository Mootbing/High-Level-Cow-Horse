"use client";

import { useEffect, useRef, useState } from "react";

const PROJECTS = [
  {
    name: "Bella Vista Ristorante",
    industry: "Restaurant",
    improvement: "4.2s \u2192 1.1s load time",
    description: "Full rebrand and site rebuild. Replaced a 6-year-old WordPress site with a scroll-driven showcase of their menu, ambiance, and story.",
    gradient: "linear-gradient(135deg, #1a0a00 0%, #2d1800 50%, #0d0d0d 100%)",
    accent: "#ff8c42",
  },
  {
    name: "Summit Legal Group",
    industry: "Law Firm",
    improvement: "312% more contact form submissions",
    description: "Transformed a generic template site into a trust-building experience. Case results, attorney bios, and practice areas — all above the fold.",
    gradient: "linear-gradient(135deg, #000a1a 0%, #001a3d 50%, #0d0d0d 100%)",
    accent: "#4da6ff",
  },
  {
    name: "Pure Glow Aesthetics",
    industry: "Medical Spa",
    improvement: "First page of Google in 3 weeks",
    description: "Cinematic hero video, before/after gallery, and online booking integration. Every section designed to build confidence and drive bookings.",
    gradient: "linear-gradient(135deg, #1a0012 0%, #2d0020 50%, #0d0d0d 100%)",
    accent: "#ff4da6",
  },
];

export default function Work() {
  const sectionRef = useRef<HTMLElement>(null);
  const [hoveredIndex, setHoveredIndex] = useState<number | null>(null);

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
      { threshold: 0.1 }
    );

    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  return (
    <section ref={sectionRef} className="section" id="work">
      <div className="container">
        {/* Header */}
        <div
          style={{
            display: "flex",
            alignItems: "flex-end",
            justifyContent: "space-between",
            marginBottom: "clamp(3rem, 6vh, 5rem)",
            flexWrap: "wrap",
            gap: "1.5rem",
          }}
        >
          <div>
            <span className="text-label reveal">Selected Work</span>
            <h2
              className="text-display-lg reveal delay-1"
              style={{ marginTop: "clamp(0.8rem, 1.5vh, 1.2rem)" }}
            >
              Sites we&apos;ve
              <br />
              <span style={{ color: "var(--accent)" }}>shipped</span>
            </h2>
          </div>
          <p className="text-body reveal delay-2" style={{ maxWidth: "400px" }}>
            Real businesses. Real results. Every project built from scratch with
            AI-powered precision.
          </p>
        </div>

        {/* Projects */}
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            gap: "clamp(1rem, 2vw, 1.5rem)",
          }}
        >
          {PROJECTS.map((project, i) => (
            <div
              key={project.name}
              className={`reveal delay-${i + 3}`}
              onMouseEnter={() => setHoveredIndex(i)}
              onMouseLeave={() => setHoveredIndex(null)}
              style={{
                position: "relative",
                borderRadius: "var(--radius-lg)",
                overflow: "hidden",
                border: `1px solid ${hoveredIndex === i ? project.accent + "40" : "var(--gray-700)"}`,
                background: project.gradient,
                transition: "all 0.5s cubic-bezier(0.16, 1, 0.3, 1)",
                transform: hoveredIndex === i ? "scale(1.01)" : "scale(1)",
                cursor: "pointer",
              }}
            >
              {/* Decorative SVG pattern */}
              <svg
                style={{
                  position: "absolute",
                  right: "clamp(-40px, -3vw, -20px)",
                  top: "50%",
                  transform: "translateY(-50%)",
                  width: "clamp(200px, 30vw, 400px)",
                  height: "clamp(200px, 30vw, 400px)",
                  opacity: 0.05,
                }}
                viewBox="0 0 400 400"
                fill="none"
              >
                <circle cx="200" cy="200" r="180" stroke={project.accent} strokeWidth="1" />
                <circle cx="200" cy="200" r="130" stroke={project.accent} strokeWidth="1" />
                <circle cx="200" cy="200" r="80" stroke={project.accent} strokeWidth="1" />
                <line x1="200" y1="20" x2="200" y2="380" stroke={project.accent} strokeWidth="0.5" />
                <line x1="20" y1="200" x2="380" y2="200" stroke={project.accent} strokeWidth="0.5" />
              </svg>

              <div
                style={{
                  position: "relative",
                  zIndex: 2,
                  padding: "clamp(2rem, 4vw, 3.5rem)",
                  display: "grid",
                  gridTemplateColumns: "1fr auto",
                  alignItems: "center",
                  gap: "clamp(1.5rem, 3vw, 3rem)",
                }}
              >
                <div>
                  {/* Industry tag */}
                  <span
                    style={{
                      display: "inline-block",
                      padding: "0.3rem 0.75rem",
                      background: `${project.accent}15`,
                      border: `1px solid ${project.accent}30`,
                      borderRadius: "100px",
                      fontFamily: '"Space Grotesk", sans-serif',
                      fontSize: "clamp(0.7rem, 0.85vw, 0.8rem)",
                      fontWeight: 600,
                      color: project.accent,
                      letterSpacing: "0.05em",
                      marginBottom: "clamp(0.8rem, 1.5vh, 1.2rem)",
                    }}
                  >
                    {project.industry}
                  </span>

                  {/* Project Name */}
                  <h3
                    style={{
                      fontFamily: '"Syne", sans-serif',
                      fontWeight: 700,
                      fontSize: "clamp(1.5rem, 3vw, 2.5rem)",
                      color: "var(--white)",
                      lineHeight: 1.1,
                      marginBottom: "clamp(0.5rem, 1vh, 0.8rem)",
                    }}
                  >
                    {project.name}
                  </h3>

                  <p
                    className="text-body"
                    style={{ maxWidth: "550px", marginBottom: "clamp(0.8rem, 1.5vh, 1.2rem)" }}
                  >
                    {project.description}
                  </p>

                  {/* Improvement stat */}
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: "0.5rem",
                    }}
                  >
                    <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                      <path d="M2 14L8 4L14 14" stroke={project.accent} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                    </svg>
                    <span
                      style={{
                        fontFamily: '"Space Grotesk", sans-serif',
                        fontSize: "clamp(0.85rem, 1vw, 0.95rem)",
                        fontWeight: 600,
                        color: project.accent,
                      }}
                    >
                      {project.improvement}
                    </span>
                  </div>
                </div>

                {/* Arrow */}
                <div
                  className="hide-mobile"
                  style={{
                    width: 56,
                    height: 56,
                    borderRadius: "50%",
                    border: `1px solid ${hoveredIndex === i ? project.accent : "var(--gray-600)"}`,
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    transition: "all 0.4s ease",
                    transform: hoveredIndex === i ? "rotate(-45deg)" : "none",
                    flexShrink: 0,
                  }}
                >
                  <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                    <line x1="4" y1="10" x2="16" y2="10" stroke={hoveredIndex === i ? project.accent : "var(--gray-400)"} strokeWidth="1.5" strokeLinecap="round" />
                    <polyline points="11,5 16,10 11,15" stroke={hoveredIndex === i ? project.accent : "var(--gray-400)"} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
