"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import AuditForm from "@/components/AuditForm";
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
  const heroRef = useRef<HTMLElement>(null);

  useEffect(() => {
    const el = heroRef.current;
    if (!el) return;
    const reveals = el.querySelectorAll(".reveal");
    reveals.forEach((r, i) => {
      setTimeout(() => r.classList.add("active"), 150 + i * 100);
    });
  }, []);

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
          style={{ maxWidth: "480px", marginTop: "clamp(1.2rem, 2.5vh, 2rem)", marginBottom: "clamp(1.5rem, 3vh, 2.5rem)" }}
        >
          We&apos;ll audit your site and build you a new one — free. Don&apos;t pay until you&apos;re happy.
        </p>

        {/* URL Input CTA */}
        <AuditForm className="reveal delay-3" />

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
            { value: "<48hr", label: "Delivery" },
            { value: "<0.5s", label: "Page Load" },
            { value: "$250", label: "To Launch" },
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
