"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { PROJECTS } from "@/lib/projects";

function PolaroidCard({
  project,
  index,
}: {
  project: (typeof PROJECTS)[number];
  index: number;
}) {
  const [hovered, setHovered] = useState(false);
  const [tilt, setTilt] = useState({ x: 0, y: 0 });
  const cardRef = useRef<HTMLAnchorElement>(null);

  const handleMouseMove = (e: React.MouseEvent) => {
    const el = cardRef.current;
    if (!el) return;
    const rect = el.getBoundingClientRect();
    const x = (e.clientX - rect.left) / rect.width - 0.5;
    const y = (e.clientY - rect.top) / rect.height - 0.5;
    setTilt({ x: y * -8, y: x * 8 });
  };

  const handleMouseLeave = () => {
    setHovered(false);
    setTilt({ x: 0, y: 0 });
  };

  return (
    <Link
      ref={cardRef}
      href={`/work/${project.slug}`}
      className={`reveal delay-${index + 2}`}
      onMouseEnter={() => setHovered(true)}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      style={{
        display: "block",
        textDecoration: "none",
        cursor: "pointer",
        perspective: "800px",
      }}
    >
      <div
        style={{
          background: "#fff",
          padding: "clamp(10px, 1.5vw, 14px)",
          paddingBottom: "clamp(44px, 6vw, 60px)",
          borderRadius: "4px",
          boxShadow: hovered
            ? "0 20px 50px rgba(0,0,0,0.12), 0 4px 12px rgba(0,0,0,0.08)"
            : "0 4px 14px rgba(0,0,0,0.08), 0 1px 3px rgba(0,0,0,0.06)",
          transform: hovered
            ? `rotate(0deg) scale(1.04) rotateX(${tilt.x}deg) rotateY(${tilt.y}deg)`
            : `rotate(${project.rotation}deg) scale(1)`,
          transition: hovered
            ? "box-shadow 0.3s ease, transform 0.1s ease"
            : "box-shadow 0.4s ease, transform 0.5s cubic-bezier(0.16, 1, 0.3, 1)",
          transformStyle: "preserve-3d",
          position: "relative",
        }}
      >
        {/* Image area */}
        <div
          style={{
            width: "100%",
            aspectRatio: "1 / 1",
            borderRadius: "2px",
            overflow: "hidden",
            background: project.gradient,
            position: "relative",
          }}
        >
          {/* Project preview mockup */}
          <div
            style={{
              position: "absolute",
              inset: 0,
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              justifyContent: "center",
              gap: "clamp(0.5rem, 1vw, 0.8rem)",
            }}
          >
            {/* Browser mockup */}
            <div
              style={{
                width: "80%",
                height: "65%",
                background: project.darkPreview ? "rgba(15,15,15,0.95)" : "rgba(255,255,255,0.95)",
                borderRadius: "8px",
                boxShadow: "0 8px 32px rgba(0,0,0,0.18)",
                overflow: "hidden",
                display: "flex",
                flexDirection: "column",
              }}
            >
              {/* Browser bar */}
              <div
                style={{
                  height: "clamp(16px, 2vw, 22px)",
                  background: project.darkPreview ? "#1a1a1a" : "#f5f5f5",
                  borderBottom: `1px solid ${project.darkPreview ? "#2a2a2a" : "#e5e5e5"}`,
                  display: "flex",
                  alignItems: "center",
                  padding: "0 8px",
                  gap: "4px",
                }}
              >
                <span style={{ width: 6, height: 6, borderRadius: "50%", background: "#ff5f57" }} />
                <span style={{ width: 6, height: 6, borderRadius: "50%", background: "#ffbd2e" }} />
                <span style={{ width: 6, height: 6, borderRadius: "50%", background: "#28c840" }} />
              </div>
              {/* Content area */}
              <div style={{ flex: 1, padding: "clamp(6px, 1vw, 12px)", display: "flex", flexDirection: "column", gap: "clamp(3px, 0.5vw, 6px)" }}>
                <div style={{ width: "60%", height: "clamp(6px, 1vw, 10px)", borderRadius: 3, background: project.color, opacity: 0.8 }} />
                <div style={{ width: "80%", height: "clamp(4px, 0.6vw, 6px)", borderRadius: 2, background: project.darkPreview ? "#2a2a2a" : "#e5e5e5" }} />
                <div style={{ width: "70%", height: "clamp(4px, 0.6vw, 6px)", borderRadius: 2, background: project.darkPreview ? "#2a2a2a" : "#e5e5e5" }} />
                <div style={{ flex: 1, borderRadius: 4, background: `${project.color}15`, marginTop: "clamp(2px, 0.3vw, 4px)" }} />
              </div>
            </div>
            {/* Industry badge */}
            <div
              style={{
                padding: "3px 10px",
                background: "rgba(255,255,255,0.85)",
                borderRadius: "100px",
                fontSize: "clamp(0.6rem, 0.75vw, 0.7rem)",
                fontWeight: 600,
                color: project.color,
                letterSpacing: "0.05em",
                backdropFilter: "blur(4px)",
              }}
            >
              {project.industry}
            </div>
          </div>
        </div>

        {/* Caption (handwritten) */}
        <div
          style={{
            position: "absolute",
            bottom: "clamp(10px, 1.5vw, 16px)",
            left: 0,
            right: 0,
            textAlign: "center",
          }}
        >
          <span
            style={{
              fontFamily: '"Caveat", cursive',
              fontSize: "clamp(1rem, 1.4vw, 1.2rem)",
              fontWeight: 600,
              color: "#333",
              letterSpacing: "0.01em",
            }}
          >
            {project.caption}
          </span>
        </div>

        {/* Improvement badge (appears on hover) */}
        <div
          style={{
            position: "absolute",
            top: "clamp(16px, 2.5vw, 22px)",
            right: "clamp(16px, 2.5vw, 22px)",
            padding: "4px 10px",
            background: "rgba(255,255,255,0.92)",
            borderRadius: "100px",
            fontSize: "clamp(0.65rem, 0.75vw, 0.72rem)",
            fontWeight: 600,
            color: project.color,
            backdropFilter: "blur(8px)",
            opacity: hovered ? 1 : 0,
            transform: hovered ? "translateY(0)" : "translateY(-6px)",
            transition: "all 0.3s ease",
            pointerEvents: "none",
          }}
        >
          {project.improvement}
        </div>
      </div>
    </Link>
  );
}

export default function Work() {
  const sectionRef = useRef<HTMLElement>(null);

  useEffect(() => {
    const el = sectionRef.current;
    if (!el) return;
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
    return () => observer.disconnect();
  }, []);

  return (
    <section ref={sectionRef} className="section" id="work">
      <div className="container">
        <div style={{ textAlign: "center", marginBottom: "clamp(3rem, 6vh, 5rem)" }}>
          <h2
            className="text-display-lg reveal delay-1"
            style={{ marginTop: "clamp(0.8rem, 1.5vh, 1.2rem)" }}
          >
            Sites we&apos;ve <em className="font-serif" style={{ fontStyle: "italic" }}>shipped</em>
          </h2>
          <p className="text-body-lg reveal delay-1" style={{ maxWidth: "420px", margin: "clamp(0.8rem, 1.5vh, 1rem) auto 0" }}>
            Real businesses. Real results. Real stories.
          </p>
        </div>

        {/* Polaroid grid */}
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(min(100%, 280px), 1fr))",
            gap: "clamp(2.5rem, 5vw, 4rem)",
            maxWidth: "720px",
            margin: "0 auto",
            padding: "1rem 0",
          }}
        >
          {PROJECTS.map((project, i) => (
            <PolaroidCard key={project.slug} project={project} index={i} />
          ))}
        </div>
      </div>
    </section>
  );
}
