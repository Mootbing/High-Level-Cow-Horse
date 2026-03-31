"use client";

import { useEffect, useRef } from "react";
import Link from "next/link";
import type { Project } from "@/lib/projects";

export default function CaseStudyClient({ project }: { project: Project }) {
  const pageRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = pageRef.current;
    if (!el) return;
    el.querySelectorAll(".reveal").forEach((r, i) => {
      setTimeout(() => r.classList.add("active"), 100 + i * 80);
    });
  }, []);

  return (
    <div ref={pageRef} style={{ minHeight: "100vh", background: "var(--bg)" }}>
      {/* Nav bar */}
      <nav
        style={{
          position: "fixed",
          top: 0,
          left: 0,
          right: 0,
          zIndex: 100,
          padding: "0.8rem 0",
          background: "rgba(250,250,248,0.9)",
          backdropFilter: "blur(16px) saturate(180%)",
          borderBottom: "1px solid var(--border)",
        }}
      >
        <div
          className="container"
          style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}
        >
          <Link
            href="/"
            style={{
              fontFamily: '"Instrument Serif", Georgia, serif',
              fontSize: "clamp(1.3rem, 1.8vw, 1.6rem)",
              color: "var(--text)",
            }}
          >
            Clarmi
          </Link>
          <Link
            href="/#work"
            style={{
              display: "flex",
              alignItems: "center",
              gap: "0.4rem",
              fontSize: "0.88rem",
              color: "var(--text-muted)",
              transition: "color 0.3s",
            }}
          >
            <svg
              width="16"
              height="16"
              viewBox="0 0 16 16"
              fill="none"
              style={{ transform: "rotate(180deg)" }}
            >
              <line
                x1="3"
                y1="8"
                x2="13"
                y2="8"
                stroke="currentColor"
                strokeWidth="1.2"
                strokeLinecap="round"
              />
              <polyline
                points="9,4 13,8 9,12"
                stroke="currentColor"
                strokeWidth="1.2"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
            All Work
          </Link>
        </div>
      </nav>

      {/* Hero */}
      <section
        style={{
          paddingTop: "clamp(8rem, 18vh, 14rem)",
          paddingBottom: "clamp(3rem, 6vh, 5rem)",
          position: "relative",
          overflow: "hidden",
        }}
      >
        {/* Gradient background */}
        <div
          style={{
            position: "absolute",
            top: 0,
            left: 0,
            right: 0,
            height: "60%",
            background: project.gradient,
            opacity: 0.15,
            pointerEvents: "none",
          }}
        />

        <div className="container" style={{ position: "relative", zIndex: 2 }}>
          <div className="reveal" style={{ display: "flex", alignItems: "center", gap: "0.6rem", marginBottom: "clamp(1rem, 2vh, 1.5rem)" }}>
            <span
              style={{
                width: 8,
                height: 8,
                borderRadius: "50%",
                background: project.color,
              }}
            />
            <span className="text-label">{project.industry}</span>
          </div>

          <h1
            className="text-display-lg reveal delay-1"
            style={{ maxWidth: "800px" }}
          >
            {project.name}
          </h1>

          <p
            className="text-body-lg reveal delay-2"
            style={{
              maxWidth: "600px",
              marginTop: "clamp(1rem, 2vh, 1.5rem)",
            }}
          >
            {project.brief}
          </p>

          {/* Stats bar */}
          <div
            className="reveal delay-3"
            style={{
              display: "flex",
              gap: "clamp(2rem, 4vw, 3rem)",
              marginTop: "clamp(2rem, 4vh, 3rem)",
              flexWrap: "wrap",
            }}
          >
            <div>
              <div
                style={{
                  fontFamily: '"Instrument Serif", Georgia, serif',
                  fontSize: "clamp(1.3rem, 2vw, 1.6rem)",
                  color: project.color,
                }}
              >
                {project.improvement}
              </div>
              <div style={{ fontSize: "clamp(0.72rem, 0.82vw, 0.78rem)", color: "var(--text-light)", marginTop: "0.15rem" }}>
                Key Result
              </div>
            </div>
            <div>
              <div
                style={{
                  fontFamily: '"Instrument Serif", Georgia, serif',
                  fontSize: "clamp(1.3rem, 2vw, 1.6rem)",
                  color: "var(--text)",
                }}
              >
                48hrs
              </div>
              <div style={{ fontSize: "clamp(0.72rem, 0.82vw, 0.78rem)", color: "var(--text-light)", marginTop: "0.15rem" }}>
                Delivery Time
              </div>
            </div>
          </div>

          {/* Tech tags */}
          <div
            className="reveal delay-4"
            style={{
              display: "flex",
              gap: "0.4rem",
              marginTop: "clamp(1.5rem, 3vh, 2rem)",
              flexWrap: "wrap",
            }}
          >
            {project.tech.map((t) => (
              <span
                key={t}
                style={{
                  padding: "0.3rem 0.7rem",
                  background: "var(--bg-card)",
                  border: "1px solid var(--border)",
                  borderRadius: "var(--radius-full)",
                  fontSize: "clamp(0.72rem, 0.82vw, 0.78rem)",
                  fontWeight: 500,
                  color: "var(--text-muted)",
                }}
              >
                {t}
              </span>
            ))}
          </div>
        </div>
      </section>

      <div className="section-divider"><div style={{ height: 1, background: "var(--border)" }} /></div>

      {/* Challenge */}
      <section className="section">
        <div
          className="container"
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(min(100%, 350px), 1fr))",
            gap: "clamp(3rem, 6vw, 6rem)",
          }}
        >
          <div>
            <span className="text-label reveal">The Challenge</span>
            <h2
              className="text-display-md reveal delay-1"
              style={{ marginTop: "clamp(0.6rem, 1vh, 0.8rem)" }}
            >
              What was <em className="font-serif" style={{ fontStyle: "italic" }}>broken</em>
            </h2>
          </div>
          <p className="text-body-lg reveal delay-2">{project.challenge}</p>
        </div>
      </section>

      {/* Solution */}
      <section
        className="section"
        style={{
          background: "var(--bg-alt)",
          borderTop: "1px solid var(--border)",
          borderBottom: "1px solid var(--border)",
        }}
      >
        <div
          className="container"
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(min(100%, 350px), 1fr))",
            gap: "clamp(3rem, 6vw, 6rem)",
          }}
        >
          <div>
            <span className="text-label reveal">The Solution</span>
            <h2
              className="text-display-md reveal delay-1"
              style={{ marginTop: "clamp(0.6rem, 1vh, 0.8rem)" }}
            >
              What we <em className="font-serif" style={{ fontStyle: "italic" }}>built</em>
            </h2>
          </div>
          <p className="text-body-lg reveal delay-2">{project.solution}</p>
        </div>
      </section>

      {/* Results */}
      <section className="section">
        <div className="container">
          <div style={{ textAlign: "center", marginBottom: "clamp(2.5rem, 5vh, 4rem)" }}>
            <span className="text-label reveal">The Results</span>
            <h2
              className="text-display-md reveal delay-1"
              style={{ marginTop: "clamp(0.6rem, 1vh, 0.8rem)" }}
            >
              The <em className="font-serif" style={{ fontStyle: "italic" }}>numbers</em>
            </h2>
          </div>

          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(min(100%, 240px), 1fr))",
              gap: "clamp(0.75rem, 1.5vw, 1rem)",
              maxWidth: "900px",
              margin: "0 auto",
            }}
          >
            {project.results.map((result, i) => (
              <div
                key={i}
                className={`card reveal delay-${i + 2}`}
                style={{
                  display: "flex",
                  alignItems: "flex-start",
                  gap: "0.75rem",
                }}
              >
                <svg
                  width="18"
                  height="18"
                  viewBox="0 0 18 18"
                  fill="none"
                  style={{ flexShrink: 0, marginTop: "3px" }}
                >
                  <path
                    d="M4 9L7.5 12.5L14 5.5"
                    stroke={project.color}
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                </svg>
                <p
                  style={{
                    fontSize: "clamp(0.9rem, 1.05vw, 1rem)",
                    lineHeight: 1.6,
                    color: "var(--text-muted)",
                  }}
                >
                  {result}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section
        className="section"
        style={{
          background: "var(--bg-alt)",
          borderTop: "1px solid var(--border)",
          textAlign: "center",
        }}
      >
        <div className="container reveal">
          <h2 className="text-display-md">
            Want results like{" "}
            <em className="font-serif" style={{ fontStyle: "italic" }}>these</em>?
          </h2>
          <p
            className="text-body-lg"
            style={{
              maxWidth: "420px",
              margin: "clamp(0.8rem, 1.5vh, 1.2rem) auto clamp(1.5rem, 3vh, 2rem)",
            }}
          >
            Drop your URL and we&apos;ll show you what&apos;s possible.
          </p>
          <Link href="/#cta" className="btn-primary">
            Get Your Free Audit
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer
        style={{
          borderTop: "1px solid var(--border)",
          padding: "clamp(1.5rem, 3vh, 2rem) 0",
        }}
      >
        <div
          className="container"
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
          }}
        >
          <p style={{ fontSize: "clamp(0.72rem, 0.82vw, 0.78rem)", color: "var(--text-light)" }}>
            &copy; {new Date().getFullYear()} Clarmi Design Studio
          </p>
          <Link
            href="/"
            style={{
              fontFamily: '"Instrument Serif", Georgia, serif',
              fontSize: "clamp(1rem, 1.3vw, 1.2rem)",
              color: "var(--text)",
            }}
          >
            Clarmi
          </Link>
        </div>
      </footer>
    </div>
  );
}
