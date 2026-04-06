"use client";

import { useEffect, useRef } from "react";
import AuditForm from "@/components/AuditForm";

export default function CTA() {
  const ref = useRef<HTMLElement>(null);

  useEffect(() => {
    const el = ref.current;
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
      { threshold: 0.2 }
    );
    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  return (
    <section
      ref={ref}
      id="cta"
      className="section"
      style={{
        position: "relative",
        overflow: "hidden",
        background: "var(--bg-alt)",
        borderTop: "1px solid var(--border)",
      }}
    >
      {/* Soft gradient orbs */}
      <div style={{
        position: "absolute", top: "30%", left: "15%",
        width: "clamp(200px, 30vw, 400px)", height: "clamp(200px, 30vw, 400px)",
        borderRadius: "50%", background: "radial-gradient(circle, rgba(96,165,250,0.06) 0%, transparent 70%)",
        pointerEvents: "none",
      }} />
      <div style={{
        position: "absolute", bottom: "20%", right: "10%",
        width: "clamp(250px, 35vw, 450px)", height: "clamp(250px, 35vw, 450px)",
        borderRadius: "50%", background: "radial-gradient(circle, rgba(232,121,168,0.05) 0%, transparent 70%)",
        pointerEvents: "none",
      }} />

      <div className="container" style={{ position: "relative", zIndex: 2, display: "flex", flexDirection: "column", alignItems: "center", textAlign: "center" }}>
        <h2 className="text-display-hero reveal delay-1" style={{ color: "var(--text)" }}>
          Let&apos;s build
          <br /><em className="font-serif" style={{ fontStyle: "italic", color: "var(--accent)" }}>together</em>
        </h2>

        <div className="reveal delay-2 cta-actions" style={{ marginTop: "clamp(1.5rem, 3vh, 2.5rem)", width: "100%", maxWidth: 620, display: "flex", alignItems: "flex-start", gap: "clamp(0.6rem, 1vw, 0.8rem)" }}>
          <div style={{ flex: 1, minWidth: 0 }}>
            <AuditForm />
          </div>
          <a
            href="https://calendar.app.google/1R6HGErUx6kvbgSa9"
            target="_blank"
            rel="noopener noreferrer"
            className="btn-outline cta-talk-btn"
            style={{
              marginTop: 0,
              whiteSpace: "nowrap",
              padding: "clamp(0.9rem, 1.3vw, 1.1rem) clamp(1.2rem, 1.8vw, 1.5rem)",
              fontSize: "clamp(0.85rem, 0.95vw, 0.9rem)",
              flexShrink: 0,
              background: "#FFFFFF",
              border: "1px solid var(--border)",
              color: "#0A0A0A",
              boxShadow: "0 2px 12px rgba(0, 0, 0, 0.04)",
            }}
          >
            Let&apos;s Talk
          </a>
        </div>
      </div>
    </section>
  );
}
