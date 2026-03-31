"use client";

import { useEffect, useRef } from "react";

const TESTIMONIALS = [
  {
    quote: "We went from a WordPress site that took 8 seconds to load to a custom build scoring 98 on Lighthouse. Our booking inquiries doubled in the first month.",
    name: "Maria Chen",
    title: "Owner, Pure Glow Aesthetics",
    initials: "MC",
  },
  {
    quote: "I was skeptical about the price. Then I saw the pitch deck they sent within an hour. They actually looked at my site and told me exactly what was wrong.",
    name: "David Okafor",
    title: "Partner, Summit Legal Group",
    initials: "DO",
  },
  {
    quote: "48 hours from 'yes' to a live site. My old developer quoted me 6 weeks. The new site has already paid for itself in catering orders.",
    name: "Sarah Bellini",
    title: "Owner, Bella Vista Ristorante",
    initials: "SB",
  },
];

export default function Testimonials() {
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
      { threshold: 0.1 }
    );
    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  return (
    <section ref={ref} className="section">
      <div className="container">
        <div style={{ textAlign: "center", marginBottom: "clamp(3rem, 6vh, 5rem)" }}>
          <span className="text-label reveal">Client Stories</span>
          <h2 className="text-display-lg reveal delay-1" style={{ marginTop: "clamp(0.8rem, 1.5vh, 1.2rem)" }}>
            Don&apos;t take our <em className="font-serif" style={{ fontStyle: "italic" }}>word</em> for it
          </h2>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(min(100%, 320px), 1fr))", gap: "clamp(0.75rem, 1.5vw, 1rem)" }}>
          {TESTIMONIALS.map((t, i) => (
            <div key={t.name} className={`card reveal delay-${i + 2}`} style={{ display: "flex", flexDirection: "column", justifyContent: "space-between", gap: "clamp(1.5rem, 3vh, 2rem)" }}>
              <div>
                <svg width="24" height="18" viewBox="0 0 24 18" fill="none" style={{ opacity: 0.12, marginBottom: "clamp(0.75rem, 1.5vh, 1rem)" }}>
                  <path d="M0 18V10.8C0 4.8 3.6 1.2 10.8 0L12 2.4C7.8 3.6 6 6 5.4 8.4H9.6V18H0ZM12 18V10.8C12 4.8 15.6 1.2 22.8 0L24 2.4C19.8 3.6 18 6 17.4 8.4H21.6V18H12Z" fill="var(--text)" />
                </svg>
                <p style={{ fontSize: "clamp(0.95rem, 1.1vw, 1.05rem)", lineHeight: 1.7, color: "var(--text-muted)" }}>
                  &ldquo;{t.quote}&rdquo;
                </p>
              </div>

              <div style={{ display: "flex", alignItems: "center", gap: "0.65rem" }}>
                <div style={{
                  width: 36, height: 36, borderRadius: "50%",
                  background: "var(--bg-alt)", border: "1px solid var(--border)",
                  display: "flex", alignItems: "center", justifyContent: "center",
                  fontFamily: '"Instrument Serif", Georgia, serif',
                  fontSize: "0.75rem", color: "var(--text-muted)", flexShrink: 0,
                }}>
                  {t.initials}
                </div>
                <div>
                  <div style={{ fontWeight: 500, fontSize: "clamp(0.85rem, 0.95vw, 0.9rem)", color: "var(--text)" }}>{t.name}</div>
                  <div style={{ fontSize: "clamp(0.75rem, 0.82vw, 0.8rem)", color: "var(--text-light)" }}>{t.title}</div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
