"use client";

import { useEffect, useRef, useState } from "react";

export default function CTA() {
  const sectionRef = useRef<HTMLElement>(null);
  const [url, setUrl] = useState("");
  const [email, setEmail] = useState("");
  const [submitted, setSubmitted] = useState(false);

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
      { threshold: 0.2 }
    );

    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!url.trim()) return;
    setSubmitted(true);
    setTimeout(() => setSubmitted(false), 5000);
  };

  return (
    <section
      ref={sectionRef}
      id="cta"
      className="section"
      style={{
        position: "relative",
        overflow: "hidden",
      }}
    >
      {/* Background glow */}
      <div
        style={{
          position: "absolute",
          top: "50%",
          left: "50%",
          transform: "translate(-50%, -50%)",
          width: "clamp(400px, 60vw, 900px)",
          height: "clamp(400px, 60vw, 900px)",
          borderRadius: "50%",
          background: "radial-gradient(circle, rgba(200,255,0,0.06) 0%, transparent 60%)",
          pointerEvents: "none",
        }}
      />

      {/* Decorative rings */}
      <svg
        style={{
          position: "absolute",
          top: "50%",
          left: "50%",
          transform: "translate(-50%, -50%)",
          width: "clamp(500px, 80vw, 1200px)",
          height: "clamp(500px, 80vw, 1200px)",
          opacity: 0.04,
          pointerEvents: "none",
        }}
        viewBox="0 0 800 800"
        fill="none"
      >
        <circle cx="400" cy="400" r="350" stroke="var(--accent)" strokeWidth="1" />
        <circle cx="400" cy="400" r="250" stroke="var(--accent)" strokeWidth="1" />
        <circle cx="400" cy="400" r="150" stroke="var(--accent)" strokeWidth="1" />
      </svg>

      <div
        className="container"
        style={{
          position: "relative",
          zIndex: 2,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          textAlign: "center",
        }}
      >
        <span className="text-label reveal">Ready?</span>

        <h2
          className="text-display-xl reveal delay-1"
          style={{ marginTop: "clamp(0.8rem, 1.5vh, 1.2rem)", maxWidth: "14ch" }}
        >
          Let&apos;s build
          <br />
          <span style={{ color: "var(--accent)" }}>yours</span>
        </h2>

        <p
          className="text-body-lg reveal delay-2"
          style={{ maxWidth: "520px", marginTop: "clamp(1rem, 2vh, 1.5rem)" }}
        >
          Drop your URL below. We&apos;ll audit your current site and send you a
          personalized proposal \u2014 free, no strings attached.
        </p>

        {/* Form */}
        <form
          onSubmit={handleSubmit}
          className="reveal delay-3"
          style={{
            width: "100%",
            maxWidth: "560px",
            marginTop: "clamp(1.5rem, 3vh, 2.5rem)",
            display: "flex",
            flexDirection: "column",
            gap: "clamp(0.75rem, 1.5vh, 1rem)",
          }}
        >
          {/* URL input */}
          <div className="url-input-wrapper">
            <svg
              width="18"
              height="18"
              viewBox="0 0 18 18"
              fill="none"
              style={{ marginLeft: "clamp(1rem, 1.5vw, 1.5rem)", flexShrink: 0, opacity: 0.4 }}
            >
              <circle cx="9" cy="9" r="7" stroke="currentColor" strokeWidth="1.5" />
              <path d="M9 2C9 2 5.5 5.5 5.5 9C5.5 12.5 9 16 9 16" stroke="currentColor" strokeWidth="1.5" />
              <path d="M9 2C9 2 12.5 5.5 12.5 9C12.5 12.5 9 16 9 16" stroke="currentColor" strokeWidth="1.5" />
              <line x1="2.5" y1="7" x2="15.5" y2="7" stroke="currentColor" strokeWidth="1.5" />
              <line x1="2.5" y1="11" x2="15.5" y2="11" stroke="currentColor" strokeWidth="1.5" />
            </svg>
            <input
              type="text"
              placeholder="yourwebsite.com"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              required
              aria-label="Your website URL"
            />
            <button type="submit" disabled={submitted}>
              {submitted ? "Sent!" : "Get Free Audit"}
            </button>
          </div>

          {/* Email input */}
          <div
            style={{
              display: "flex",
              borderRadius: "100px",
              background: "var(--gray-800)",
              border: "1px solid var(--gray-700)",
              overflow: "hidden",
              transition: "border-color 0.3s ease",
            }}
          >
            <svg
              width="18"
              height="18"
              viewBox="0 0 18 18"
              fill="none"
              style={{ marginLeft: "clamp(1rem, 1.5vw, 1.5rem)", alignSelf: "center", flexShrink: 0, opacity: 0.4 }}
            >
              <rect x="2" y="4" width="14" height="10" rx="2" stroke="currentColor" strokeWidth="1.5" />
              <path d="M2 6L9 11L16 6" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
            <input
              type="email"
              placeholder="your@email.com (optional)"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              aria-label="Your email address"
              style={{
                flex: 1,
                padding: "clamp(0.85rem, 1.2vw, 1rem) clamp(0.8rem, 1.5vw, 1.2rem)",
                background: "transparent",
                border: "none",
                outline: "none",
                color: "var(--white)",
                fontFamily: '"Space Grotesk", sans-serif',
                fontSize: "clamp(0.85rem, 1vw, 0.95rem)",
              }}
            />
          </div>

          <p
            style={{
              fontSize: "clamp(0.75rem, 0.85vw, 0.8rem)",
              color: submitted ? "var(--accent)" : "var(--gray-500)",
              fontFamily: '"Space Grotesk", sans-serif',
              transition: "color 0.3s ease",
            }}
          >
            {submitted
              ? "We\u2019re on it. Expect your personalized audit within 1 hour."
              : "Free audit. Personalized proposal. No obligation. Response within 1 hour."}
          </p>
        </form>
      </div>
    </section>
  );
}
