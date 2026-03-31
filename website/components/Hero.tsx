"use client";

import { useEffect, useRef, useState } from "react";

function AnimatedGrid() {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let animationId: number;
    let time = 0;

    const resize = () => {
      const dpr = window.devicePixelRatio || 1;
      canvas.width = window.innerWidth * dpr;
      canvas.height = window.innerHeight * dpr;
      canvas.style.width = window.innerWidth + "px";
      canvas.style.height = window.innerHeight + "px";
      ctx.scale(dpr, dpr);
    };

    resize();
    window.addEventListener("resize", resize);

    const spacing = 40;
    const dotRadius = 1.2;

    const animate = () => {
      time += 0.008;
      const w = window.innerWidth;
      const h = window.innerHeight;

      ctx.clearRect(0, 0, w, h);

      const cols = Math.ceil(w / spacing) + 1;
      const rows = Math.ceil(h / spacing) + 1;

      for (let row = 0; row < rows; row++) {
        for (let col = 0; col < cols; col++) {
          const x = col * spacing;
          const y = row * spacing;

          // Wave-based opacity
          const dist = Math.sqrt(
            Math.pow(x - w / 2, 2) + Math.pow(y - h / 2, 2)
          );
          const wave = Math.sin(dist * 0.008 - time * 2) * 0.5 + 0.5;
          const opacity = 0.03 + wave * 0.08;

          ctx.beginPath();
          ctx.arc(x, y, dotRadius, 0, Math.PI * 2);
          ctx.fillStyle = `rgba(200, 255, 0, ${opacity})`;
          ctx.fill();
        }
      }

      // Draw some connecting lines near center
      ctx.strokeStyle = "rgba(200, 255, 0, 0.03)";
      ctx.lineWidth = 0.5;
      for (let row = 0; row < rows; row++) {
        for (let col = 0; col < cols - 1; col++) {
          const x = col * spacing;
          const y = row * spacing;
          const dist = Math.sqrt(
            Math.pow(x - w / 2, 2) + Math.pow(y - h / 2, 2)
          );
          if (dist < 300) {
            const lineOpacity = (1 - dist / 300) * 0.06;
            ctx.strokeStyle = `rgba(200, 255, 0, ${lineOpacity})`;
            ctx.beginPath();
            ctx.moveTo(x, y);
            ctx.lineTo(x + spacing, y);
            ctx.stroke();
            ctx.beginPath();
            ctx.moveTo(x, y);
            ctx.lineTo(x, y + spacing);
            ctx.stroke();
          }
        }
      }

      animationId = requestAnimationFrame(animate);
    };

    animate();

    return () => {
      cancelAnimationFrame(animationId);
      window.removeEventListener("resize", resize);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      style={{
        position: "absolute",
        inset: 0,
        zIndex: 0,
        pointerEvents: "none",
      }}
    />
  );
}

function FloatingShapes() {
  return (
    <div style={{ position: "absolute", inset: 0, zIndex: 0, overflow: "hidden", pointerEvents: "none" }}>
      {/* Large blurred accent circle */}
      <div
        style={{
          position: "absolute",
          top: "10%",
          right: "-10%",
          width: "clamp(300px, 50vw, 700px)",
          height: "clamp(300px, 50vw, 700px)",
          borderRadius: "50%",
          background: "radial-gradient(circle, rgba(200,255,0,0.06) 0%, transparent 70%)",
          animation: "float 8s ease-in-out infinite",
        }}
      />
      {/* Smaller secondary glow */}
      <div
        style={{
          position: "absolute",
          bottom: "5%",
          left: "-5%",
          width: "clamp(200px, 30vw, 500px)",
          height: "clamp(200px, 30vw, 500px)",
          borderRadius: "50%",
          background: "radial-gradient(circle, rgba(200,255,0,0.04) 0%, transparent 70%)",
          animation: "float 10s ease-in-out infinite reverse",
        }}
      />
      {/* Geometric accent */}
      <svg
        style={{
          position: "absolute",
          top: "20%",
          left: "8%",
          width: "clamp(60px, 8vw, 120px)",
          height: "clamp(60px, 8vw, 120px)",
          opacity: 0.08,
          animation: "rotate-slow 40s linear infinite",
        }}
        viewBox="0 0 100 100"
        fill="none"
      >
        <rect x="10" y="10" width="80" height="80" rx="8" stroke="var(--accent)" strokeWidth="1" />
        <rect x="25" y="25" width="50" height="50" rx="4" stroke="var(--accent)" strokeWidth="1" />
      </svg>
      {/* Cross shape */}
      <svg
        style={{
          position: "absolute",
          bottom: "25%",
          right: "12%",
          width: "clamp(40px, 5vw, 80px)",
          height: "clamp(40px, 5vw, 80px)",
          opacity: 0.06,
          animation: "rotate-slow 60s linear infinite reverse",
        }}
        viewBox="0 0 60 60"
        fill="none"
      >
        <line x1="30" y1="5" x2="30" y2="55" stroke="var(--accent)" strokeWidth="1.5" />
        <line x1="5" y1="30" x2="55" y2="30" stroke="var(--accent)" strokeWidth="1.5" />
      </svg>
    </div>
  );
}

export default function Hero() {
  const [url, setUrl] = useState("");
  const [submitted, setSubmitted] = useState(false);
  const heroRef = useRef<HTMLElement>(null);

  useEffect(() => {
    const el = heroRef.current;
    if (!el) return;

    const reveals = el.querySelectorAll(".reveal");
    reveals.forEach((r, i) => {
      setTimeout(() => r.classList.add("active"), 200 + i * 150);
    });
  }, []);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!url.trim()) return;
    setSubmitted(true);
    // In production, this would POST to the webhook
    setTimeout(() => setSubmitted(false), 4000);
  };

  return (
    <section
      ref={heroRef}
      id="hero"
      style={{
        position: "relative",
        minHeight: "100vh",
        display: "flex",
        flexDirection: "column",
        justifyContent: "center",
        alignItems: "center",
        overflow: "hidden",
        paddingTop: "clamp(6rem, 12vh, 10rem)",
        paddingBottom: "clamp(4rem, 8vh, 8rem)",
      }}
    >
      <AnimatedGrid />
      <FloatingShapes />

      <div
        className="container"
        style={{
          position: "relative",
          zIndex: 2,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          textAlign: "center",
          gap: "clamp(1.5rem, 3vh, 2.5rem)",
        }}
      >
        {/* Eyebrow */}
        <div className="reveal" style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
          <div
            style={{
              width: 8,
              height: 8,
              borderRadius: "50%",
              background: "var(--accent)",
              animation: "glow-pulse 2s ease-in-out infinite",
            }}
          />
          <span className="text-label">Award-Winning AI Design Studio</span>
        </div>

        {/* Main Headline */}
        <h1 className="text-display-xl reveal delay-1" style={{ maxWidth: "14ch" }}>
          Websites that{" "}
          <span style={{ color: "var(--accent)" }}>
            convert
          </span>
        </h1>

        {/* Sub-headline */}
        <p
          className="text-body-lg reveal delay-2"
          style={{
            maxWidth: "580px",
            color: "var(--gray-300)",
          }}
        >
          We build custom sites that make small businesses look like industry leaders.
          No templates. No WordPress. Just results.
        </p>

        {/* URL Input CTA */}
        <form
          onSubmit={handleSubmit}
          className="reveal delay-3"
          style={{ width: "100%", maxWidth: "620px", marginTop: "0.5rem" }}
        >
          <div className="url-input-wrapper">
            <svg
              width="20"
              height="20"
              viewBox="0 0 20 20"
              fill="none"
              style={{ marginLeft: "clamp(1rem, 1.5vw, 1.5rem)", flexShrink: 0, opacity: 0.4 }}
            >
              <circle cx="10" cy="10" r="8" stroke="currentColor" strokeWidth="1.5" />
              <path d="M10 2C10 2 6 6 6 10C6 14 10 18 10 18" stroke="currentColor" strokeWidth="1.5" />
              <path d="M10 2C10 2 14 6 14 10C14 14 10 18 10 18" stroke="currentColor" strokeWidth="1.5" />
              <line x1="2.5" y1="8" x2="17.5" y2="8" stroke="currentColor" strokeWidth="1.5" />
              <line x1="2.5" y1="12" x2="17.5" y2="12" stroke="currentColor" strokeWidth="1.5" />
            </svg>
            <input
              type="text"
              placeholder="Enter your website URL..."
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              aria-label="Your website URL"
            />
            <button type="submit">
              {submitted ? "We'll be in touch!" : "Free Audit"}
            </button>
          </div>
          <p
            style={{
              marginTop: "0.75rem",
              fontSize: "clamp(0.75rem, 0.9vw, 0.85rem)",
              color: "var(--gray-500)",
              fontFamily: '"Space Grotesk", sans-serif',
            }}
          >
            {submitted
              ? "Expect a personalized audit in your inbox within the hour."
              : "Drop your URL \u2014 we\u2019ll send you a free audit within 1 hour."}
          </p>
        </form>

        {/* Trust signals */}
        <div
          className="reveal delay-4"
          style={{
            display: "flex",
            alignItems: "center",
            gap: "clamp(1.5rem, 3vw, 2.5rem)",
            marginTop: "clamp(1rem, 2vh, 1.5rem)",
            flexWrap: "wrap",
            justifyContent: "center",
          }}
        >
          {[
            { value: "48hr", label: "Avg Delivery" },
            { value: "97+", label: "Lighthouse Score" },
            { value: "$500", label: "To Launch" },
          ].map((stat) => (
            <div key={stat.label} style={{ textAlign: "center" }}>
              <div
                style={{
                  fontFamily: '"Syne", sans-serif',
                  fontWeight: 800,
                  fontSize: "clamp(1.3rem, 2vw, 1.6rem)",
                  color: "var(--white)",
                  letterSpacing: "-0.02em",
                }}
              >
                {stat.value}
              </div>
              <div
                style={{
                  fontFamily: '"Space Grotesk", sans-serif',
                  fontSize: "clamp(0.7rem, 0.85vw, 0.8rem)",
                  color: "var(--gray-500)",
                  fontWeight: 500,
                  marginTop: "0.15rem",
                }}
              >
                {stat.label}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Scroll indicator */}
      <div
        className="reveal delay-5"
        style={{
          position: "absolute",
          bottom: "clamp(1.5rem, 3vh, 2.5rem)",
          left: "50%",
          transform: "translateX(-50%)",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          gap: "0.5rem",
          zIndex: 2,
        }}
      >
        <span
          style={{
            fontSize: "0.7rem",
            fontWeight: 500,
            color: "var(--gray-500)",
            letterSpacing: "0.15em",
            textTransform: "uppercase",
          }}
        >
          Scroll
        </span>
        <svg width="16" height="24" viewBox="0 0 16 24" fill="none">
          <rect x="1" y="1" width="14" height="22" rx="7" stroke="var(--gray-600)" strokeWidth="1.5" />
          <circle cx="8" cy="8" r="2" fill="var(--accent)">
            <animate
              attributeName="cy"
              values="8;16;8"
              dur="2s"
              repeatCount="indefinite"
              calcMode="spline"
              keySplines="0.45 0 0.55 1;0.45 0 0.55 1"
            />
            <animate
              attributeName="opacity"
              values="1;0.3;1"
              dur="2s"
              repeatCount="indefinite"
            />
          </circle>
        </svg>
      </div>
    </section>
  );
}
