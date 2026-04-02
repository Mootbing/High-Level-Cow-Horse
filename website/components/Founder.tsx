"use client";

import { useEffect, useRef, useState, useCallback } from "react";

function PortraitCard({ className }: { className?: string }) {
  const cardRef = useRef<HTMLDivElement>(null);
  const [tilt, setTilt] = useState({ x: 0, y: 0 });
  const [hovered, setHovered] = useState(false);

  const handleMouseMove = useCallback((e: React.MouseEvent) => {
    const el = cardRef.current;
    if (!el) return;
    const rect = el.getBoundingClientRect();
    const x = (e.clientX - rect.left) / rect.width - 0.5;
    const y = (e.clientY - rect.top) / rect.height - 0.5;
    setTilt({ x: y * -12, y: x * 12 });
  }, []);

  return (
    <div
      ref={cardRef}
      className={`reveal delay-3 ${className || ""}`}
      onMouseEnter={() => setHovered(true)}
      onMouseMove={handleMouseMove}
      onMouseLeave={() => { setHovered(false); setTilt({ x: 0, y: 0 }); }}
      style={{ perspective: "1000px" }}
    >
      <div
        style={{
          position: "relative",
          width: "100%",
          aspectRatio: "3 / 4",
          borderRadius: "var(--radius-lg)",
          overflow: "hidden",
          background: "var(--bg-alt)",
          border: `1px solid ${hovered ? "var(--accent)" : "var(--border)"}`,
          transform: hovered
            ? `rotateX(${tilt.x}deg) rotateY(${tilt.y}deg) scale(1.02)`
            : "rotateX(0) rotateY(0) scale(1)",
          transition: hovered
            ? "transform 0.1s ease, border-color 0.3s ease, box-shadow 0.3s ease"
            : "transform 0.5s cubic-bezier(0.16, 1, 0.3, 1), border-color 0.3s ease, box-shadow 0.3s ease",
          transformStyle: "preserve-3d",
          boxShadow: hovered
            ? "0 25px 60px rgba(0,0,0,0.1), 0 0 0 1px rgba(124,92,252,0.1)"
            : "0 4px 20px rgba(0,0,0,0.04)",
          willChange: "transform",
        }}
      >
        <img
          src="/assets/jason-xu/portrait.png"
          alt="Jason Xu, Founder of Clarmi Design Studio"
          style={{
            width: "100%",
            height: "100%",
            objectFit: "cover",
            filter: "grayscale(100%) contrast(1.1)",
            pointerEvents: "none",
          }}
        />

        <div style={{
          position: "absolute", bottom: 0, left: 0, right: 0, height: "40%",
          background: "linear-gradient(to top, rgba(250,250,248,0.95) 0%, transparent 100%)",
          pointerEvents: "none",
        }} />

        <div style={{ position: "absolute", bottom: "clamp(1rem, 2vw, 1.5rem)", left: "clamp(1rem, 2vw, 1.5rem)", right: "clamp(1rem, 2vw, 1.5rem)" }}>
          <div style={{ fontFamily: '"Instrument Serif", Georgia, serif', fontSize: "clamp(1.2rem, 1.8vw, 1.5rem)", color: "var(--text)", lineHeight: 1.2 }}>
            Jason Xu
          </div>
          <div style={{ fontSize: "clamp(0.72rem, 0.82vw, 0.78rem)", color: "var(--text-muted)", marginTop: "0.15rem" }}>
            Founder &amp; CTO (Engineering &amp; Design)
          </div>
        </div>

      </div>
    </div>
  );
}

export default function Founder() {
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
      { threshold: 0.12 }
    );
    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  return (
    <section ref={ref} className="section" id="founder">
      <div className="container">
        <div
          className="founder-grid"
          style={{
            display: "grid",
            gap: "clamp(3rem, 6vw, 6rem)",
            alignItems: "center",
          }}
        >
          {/* Left: Letter */}
          <div>
            <h2
              className="text-display-md reveal delay-1"
              style={{ marginTop: "clamp(0.8rem, 1.5vh, 1.2rem)" }}
            >
              A letter from{" "}
              <em className="font-serif" style={{ fontStyle: "italic" }}>the founder</em>
            </h2>

            {/* Mobile portrait — shown after title on small screens */}
            <div className="hide-desktop" style={{ marginTop: "clamp(1.5rem, 3vh, 2rem)", maxWidth: 280 }}>
              <PortraitCard />
            </div>

            {/* Letter-style body */}
            <div
              className="reveal delay-2"
              style={{
                marginTop: "clamp(1.5rem, 3vh, 2.5rem)",
                maxWidth: "540px",
              }}
            >
              <p
                style={{
                  fontFamily: '"Instrument Serif", Georgia, serif',
                  fontSize: "clamp(1.05rem, 1.3vw, 1.2rem)",
                  lineHeight: 1.75,
                  color: "var(--text-muted)",
                  display: "flex",
                  alignItems: "center",
                  gap: "0.6rem",
                  flexWrap: "wrap",
                }}
              >
                Hi, I&apos;m Jason!
                <span style={{ display: "inline-flex", gap: "0.45rem", alignItems: "center" }}>
                  {[
                    {
                      href: "https://www.linkedin.com/in/xj1",
                      label: "LinkedIn",
                      icon: (
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                          <path d="M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-2-2 2 2 0 0 0-2 2v7h-4v-7a6 6 0 0 1 6-6z" />
                          <rect x="2" y="9" width="4" height="12" />
                          <circle cx="4" cy="4" r="2" />
                        </svg>
                      ),
                    },
                    {
                      href: "https://github.com/mootbing",
                      label: "GitHub",
                      icon: (
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                          <path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22" />
                        </svg>
                      ),
                    },
                    {
                      href: "https://jasonxu.me",
                      label: "Website",
                      icon: (
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                          <circle cx="12" cy="12" r="10" />
                          <ellipse cx="12" cy="12" rx="4" ry="10" />
                          <path d="M2 12h20" />
                        </svg>
                      ),
                    },
                    {
                      href: "https://instagram.com/x.json1",
                      label: "Instagram",
                      icon: (
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                          <rect x="2" y="2" width="20" height="20" rx="5" ry="5" />
                          <circle cx="12" cy="12" r="5" />
                          <circle cx="17.5" cy="6.5" r="1.5" fill="currentColor" stroke="none" />
                        </svg>
                      ),
                    },
                  ].map((social) => (
                    <a
                      key={social.label}
                      href={social.href}
                      target="_blank"
                      rel="noopener noreferrer"
                      aria-label={social.label}
                      style={{
                        display: "inline-flex",
                        color: "var(--text-light)",
                        transition: "color 0.2s ease",
                      }}
                      onMouseEnter={(e) => { e.currentTarget.style.color = "var(--accent)"; }}
                      onMouseLeave={(e) => { e.currentTarget.style.color = "var(--text-light)"; }}
                    >
                      {social.icon}
                    </a>
                  ))}
                </span>
              </p>
              {[
                "I've been obsessed with building things on the internet since I was 14. By 16, something I made got acquired by the United Nations. At 17, I won international design awards. At 19, I joined a startup as the 2nd engineer and helped scale it past $12M ARR.",
                "I'm at UPenn now, and I started Clarmi because it kept bugging me — small businesses with amazing products, stuck behind websites that don't do them justice. The design and engineering that VC-funded startups get shouldn't cost $10,000. So I built a studio where it doesn't.",
                "If your website doesn't make you proud, send me the URL. I'll show you what it could be.",
              ].map((text, i) => (
                <p
                  key={i}
                  style={{
                    fontFamily: '"Instrument Serif", Georgia, serif',
                    fontSize: "clamp(1.05rem, 1.3vw, 1.2rem)",
                    lineHeight: 1.75,
                    color: "var(--text-muted)",
                    marginTop: "clamp(0.8rem, 1.5vh, 1rem)",
                  }}
                >
                  {text}
                </p>
              ))}
            </div>

            {/* Signature */}
            <div
              className="reveal delay-4"
              style={{ marginTop: "clamp(2rem, 4vh, 3rem)" }}
            >
              <div
                style={{
                  fontFamily: '"Caveat", cursive',
                  fontSize: "clamp(1.8rem, 2.5vw, 2.2rem)",
                  color: "var(--text)",
                  lineHeight: 1,
                  marginBottom: "0.25rem",
                }}
              >
                Jason Xu
              </div>
              <div
                style={{
                  fontSize: "clamp(0.72rem, 0.82vw, 0.78rem)",
                  color: "var(--text-light)",
                }}
              >
                Founder, Clarmi Design Studio
              </div>
                            <div
                style={{
                  fontSize: "clamp(0.72rem, 0.82vw, 0.78rem)",
                  color: "var(--text-light)",
                }}
              >
                jason@clarmi.studio
              </div>
            </div>

            {/* Award badges */}
            <div
              className="reveal delay-5"
              style={{
                marginTop: "clamp(1.5rem, 3vh, 2rem)",
                display: "flex",
                flexWrap: "wrap",
                gap: "0.4rem",
              }}
            >
              {[
                { label: "CSS Design Awards — Special Kudos", url: "https://www.cssdesignawards.com/sites/my-life-story-at-17-jason-xu/44020/" },
                { label: "Awwwards — Honorable Mention", url: "https://www.awwwards.com/sites/my-life-story-at-17-jason-xu" },
                { label: "CSSFox — Featured", url: "https://cssfox.co/=jason-xu" },
              ].map((award) => (
                <a
                  key={award.label}
                  href={award.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  style={{
                    display: "inline-flex",
                    alignItems: "center",
                    gap: "0.45rem",
                    padding: "0.4rem 0.75rem",
                    background: "var(--accent-soft)",
                    borderRadius: "var(--radius-full)",
                    border: "1px solid rgba(124,92,252,0.12)",
                    fontSize: "clamp(0.68rem, 0.78vw, 0.74rem)",
                    fontWeight: 500,
                    color: "var(--accent)",
                    textDecoration: "none",
                    transition: "all 0.3s ease",
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.background = "rgba(124,92,252,0.12)";
                    e.currentTarget.style.borderColor = "var(--accent)";
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.background = "var(--accent-soft)";
                    e.currentTarget.style.borderColor = "rgba(124,92,252,0.12)";
                  }}
                >
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" style={{ flexShrink: 0 }}>
                    <circle cx="12" cy="9" r="6" stroke="currentColor" strokeWidth="1.5" />
                    <path d="M8 15L6.5 22L12 19L17.5 22L16 15" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                  {award.label}
                  <svg width="10" height="10" viewBox="0 0 10 10" fill="none" style={{ flexShrink: 0, opacity: 0.5 }}>
                    <path d="M3 1H9V7" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round" />
                    <path d="M9 1L1 9" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" />
                  </svg>
                </a>
              ))}
            </div>
          </div>

          {/* Right: Portrait with 3D tilt — desktop only */}
          <PortraitCard className="hide-mobile" />
        </div>
      </div>

      <style>{`
        .founder-grid {
          grid-template-columns: 1fr clamp(260px, 35vw, 420px);
        }
        @media (max-width: 768px) {
          .founder-grid {
            grid-template-columns: 1fr !important;
          }
        }
      `}</style>
    </section>
  );
}
