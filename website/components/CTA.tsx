"use client";

import { useEffect, useRef } from "react";

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

  const handleClick = () => {
    window.scrollTo({ top: 0, behavior: "smooth" });
    setTimeout(() => {
      const input = document.querySelector<HTMLInputElement>(".url-input-wrapper input");
      input?.focus();
    }, 600);
  };

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
          <br /><em className="font-serif" style={{ fontStyle: "italic", color: "var(--accent)" }}>yours</em>
        </h2>

        <button
          onClick={handleClick}
          className="btn-primary reveal delay-2"
          style={{ marginTop: "clamp(1.5rem, 3vh, 2.5rem)" }}
        >
          Get Started
        </button>
      </div>
    </section>
  );
}
