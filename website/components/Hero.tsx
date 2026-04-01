"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import dynamic from "next/dynamic";

const PrismScene = dynamic(() => import("@/components/PrismScene"), {
  ssr: false,
  loading: () => null,
});

const ROTATING_WORDS = ["convert", "attract", "inspire", "perform", "deliver"];

function RotatingWord() {
  const [wordIndex, setWordIndex] = useState(0);
  const [charStates, setCharStates] = useState<("hidden" | "blurring" | "visible")[]>([]);
  const [phase, setPhase] = useState<"entering" | "holding" | "exiting">("entering");

  const currentWord = ROTATING_WORDS[wordIndex];

  const animateIn = useCallback((word: string) => {
    setPhase("entering");
    const states: ("hidden" | "blurring" | "visible")[] = new Array(word.length).fill("hidden");
    setCharStates([...states]);

    word.split("").forEach((_, i) => {
      setTimeout(() => {
        setCharStates((prev) => {
          const next = [...prev];
          next[i] = "blurring";
          return next;
        });
      }, i * 60);

      setTimeout(() => {
        setCharStates((prev) => {
          const next = [...prev];
          next[i] = "visible";
          return next;
        });
      }, i * 60 + 120);
    });

    // After all chars visible, hold, then exit
    setTimeout(() => setPhase("holding"), word.length * 60 + 200);
  }, []);

  const animateOut = useCallback((word: string, onDone: () => void) => {
    setPhase("exiting");
    word.split("").forEach((_, i) => {
      setTimeout(() => {
        setCharStates((prev) => {
          const next = [...prev];
          next[i] = "blurring";
          return next;
        });
      }, i * 40);

      setTimeout(() => {
        setCharStates((prev) => {
          const next = [...prev];
          next[i] = "hidden";
          return next;
        });
      }, i * 40 + 100);
    });

    setTimeout(onDone, word.length * 40 + 150);
  }, []);

  useEffect(() => {
    animateIn(ROTATING_WORDS[0]);
  }, [animateIn]);

  useEffect(() => {
    if (phase !== "holding") return;
    const timer = setTimeout(() => {
      animateOut(ROTATING_WORDS[wordIndex], () => {
        const next = (wordIndex + 1) % ROTATING_WORDS.length;
        setWordIndex(next);
        animateIn(ROTATING_WORDS[next]);
      });
    }, 2200);
    return () => clearTimeout(timer);
  }, [phase, wordIndex, animateIn, animateOut]);

  return (
    <span style={{ display: "inline-block", position: "relative" }}>
      {currentWord.split("").map((char, i) => {
        const state = charStates[i] || "hidden";
        return (
          <span
            key={`${wordIndex}-${i}`}
            style={{
              display: "inline-block",
              transition: "all 0.25s cubic-bezier(0.16, 1, 0.3, 1)",
              opacity: state === "hidden" ? 0 : state === "blurring" ? 0.4 : 1,
              filter: state === "hidden"
                ? "blur(12px)"
                : state === "blurring"
                  ? "blur(4px)"
                  : "blur(0px)",
              transform:
                state === "hidden"
                  ? "translateY(0.15em)"
                  : state === "blurring"
                    ? "translateY(0.05em)"
                    : "translateY(0)",
            }}
          >
            {char}
          </span>
        );
      })}
    </span>
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
      setTimeout(() => r.classList.add("active"), 150 + i * 100);
    });
  }, []);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!url.trim()) return;
    setSubmitted(true);
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
        alignItems: "center",
        overflow: "visible",
      }}
    >
      {/* Three.js Prism — right 50% on desktop, full width on mobile */}
      <div
        className="hero-canvas"
        style={{
          position: "absolute",
          top: 0,
          right: 0,
          height: "100%",
          zIndex: 1,
          pointerEvents: "none",
        }}
      >
        <PrismScene />
      </div>

      {/* Text content with frosted glass backdrop on mobile */}
      <div
        className="container hero-content"
        style={{
          position: "relative",
          zIndex: 2,
          paddingTop: "clamp(7rem, 15vh, 12rem)",
          paddingBottom: "clamp(5rem, 10vh, 8rem)",
        }}
      >
        <div style={{ maxWidth: "700px" }}>

        {/* Headline with rotating word */}
        <h1 className="text-display-hero reveal delay-1">
          Websites that
          <br />
          <em className="font-serif" style={{ fontStyle: "italic", color: "var(--accent)" }}>
              <RotatingWord />
          </em>
        </h1>

        {/* Sub */}
        <p
          className="text-body-lg reveal delay-2"
          style={{ maxWidth: "480px", marginTop: "clamp(1.2rem, 2.5vh, 2rem)" }}
        >
          We&apos;ll audit your site and build you a new one — free. Don&apos;t pay until you&apos;re happy.
        </p>

        {/* URL Input CTA */}
        <form
          onSubmit={handleSubmit}
          className="reveal delay-3"
          style={{ marginTop: "clamp(1.5rem, 3vh, 2.5rem)" }}
        >
          <div className="url-input-wrapper">
            <svg
              width="18" height="18" viewBox="0 0 18 18" fill="none"
              style={{ marginLeft: "clamp(0.9rem, 1.2vw, 1.3rem)", flexShrink: 0, opacity: 0.3 }}
            >
              <circle cx="9" cy="9" r="7" stroke="currentColor" strokeWidth="1.5" />
              <path d="M9 2C9 2 5.5 5.5 5.5 9C5.5 12.5 9 16 9 16" stroke="currentColor" strokeWidth="1.5" />
              <path d="M9 2C9 2 12.5 5.5 12.5 9C12.5 12.5 9 16 9 16" stroke="currentColor" strokeWidth="1.5" />
              <line x1="2.5" y1="7" x2="15.5" y2="7" stroke="currentColor" strokeWidth="1.5" />
              <line x1="2.5" y1="11" x2="15.5" y2="11" stroke="currentColor" strokeWidth="1.5" />
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
              marginTop: "0.6rem",
              fontSize: "clamp(0.75rem, 0.85vw, 0.82rem)",
              color: submitted ? "var(--accent)" : "var(--text-light)",
            }}
          >
            {submitted
              ? "Expect your personalized audit within 1 hour."
              : "Personalized audits delivered within 1 hour."}
          </p>
        </form>

        {/* Trust signals */}
        <div
          className="reveal delay-4"
          style={{
            display: "flex",
            alignItems: "center",
            gap: "clamp(2rem, 4vw, 3rem)",
            marginTop: "clamp(2rem, 4vh, 3rem)",
            flexWrap: "wrap",
          }}
        >
          {[
            { value: "48hr", label: "Delivery" },
            { value: "97+", label: "Lighthouse" },
            { value: "$500", label: "To Launch" },
          ].map((stat) => (
            <div key={stat.label}>
              <div style={{ fontFamily: '"Instrument Serif", Georgia, serif', fontSize: "clamp(1.4rem, 2vw, 1.7rem)", color: "var(--text)", letterSpacing: "-0.02em" }}>
                {stat.value}
              </div>
              <div style={{ fontSize: "clamp(0.7rem, 0.8vw, 0.78rem)", color: "var(--text-light)", marginTop: "0.1rem" }}>
                {stat.label}
              </div>
            </div>
          ))}
        </div>
        </div>
      </div>
    </section>
  );
}
