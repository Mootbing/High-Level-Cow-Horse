"use client";

import { useEffect, useRef, useState } from "react";

const STEPS = [
  {
    number: "01",
    title: "Send Us Your URL",
    detail: "4 min audit",
    desc: "Drop your link and we run a full audit — design, performance, SEO, mobile. A detailed report lands in your inbox in minutes.",
  },
  {
    number: "02",
    title: "We Research Everything",
    detail: "Competitor analysis",
    desc: "We crawl your competitors, extract your brand identity, colors, fonts, and content. We learn your business so the new site feels like yours.",
  },
  {
    number: "03",
    title: "Audit + Website, Free",
    detail: "No commitment",
    desc: "You get a full audit and a live preview of your redesigned site — completely free. No payment until you say \"deploy it.\"",
  },
  {
    number: "04",
    title: "Deploy Instantly",
    detail: "$500 to go live",
    desc: "Say the word and we push it live to your domain. SSL, hosting, analytics — all included. You're live in minutes, not weeks.",
  },
];

/* ── SVG illustrations (line art, drawn on scroll) ── */

function UrlSvg({ progress }: { progress: number }) {
  const d = 1 - progress;
  return (
    <svg viewBox="0 0 200 140" fill="none" style={{ width: "100%", height: "100%" }}>
      {/* Browser chrome */}
      <rect x="20" y="16" width="160" height="108" rx="8" stroke="var(--accent)" strokeWidth="1.5"
        strokeDasharray="536" strokeDashoffset={536 * d} style={{ transition: "stroke-dashoffset 0.1s linear" }} />
      <line x1="20" y1="40" x2="180" y2="40" stroke="var(--accent)" strokeWidth="1.5"
        strokeDasharray="160" strokeDashoffset={160 * d} style={{ transition: "stroke-dashoffset 0.1s linear" }} />
      {/* Dots */}
      <circle cx="34" cy="28" r="3" stroke="var(--accent)" strokeWidth="1.2"
        strokeDasharray="19" strokeDashoffset={19 * d} style={{ transition: "stroke-dashoffset 0.1s linear" }} />
      <circle cx="46" cy="28" r="3" stroke="var(--accent)" strokeWidth="1.2"
        strokeDasharray="19" strokeDashoffset={19 * d} style={{ transition: "stroke-dashoffset 0.1s linear" }} />
      <circle cx="58" cy="28" r="3" stroke="var(--accent)" strokeWidth="1.2"
        strokeDasharray="19" strokeDashoffset={19 * d} style={{ transition: "stroke-dashoffset 0.1s linear" }} />
      {/* URL bar */}
      <rect x="72" y="23" width="96" height="10" rx="5" stroke="var(--accent)" strokeWidth="1.2"
        strokeDasharray="200" strokeDashoffset={200 * d} style={{ transition: "stroke-dashoffset 0.1s linear" }} />
      {/* Globe icon in URL bar */}
      <circle cx="100" cy="70" r="16" stroke="var(--accent)" strokeWidth="1.2"
        strokeDasharray="101" strokeDashoffset={101 * d} style={{ transition: "stroke-dashoffset 0.1s linear" }} />
      <ellipse cx="100" cy="70" rx="8" ry="16" stroke="var(--accent)" strokeWidth="1"
        strokeDasharray="80" strokeDashoffset={80 * d} style={{ transition: "stroke-dashoffset 0.1s linear" }} />
      <line x1="84" y1="70" x2="116" y2="70" stroke="var(--accent)" strokeWidth="1"
        strokeDasharray="32" strokeDashoffset={32 * d} style={{ transition: "stroke-dashoffset 0.1s linear" }} />
      {/* Arrow pointing into browser */}
      <path d="M100 104 L100 92" stroke="var(--accent)" strokeWidth="1.5" strokeLinecap="round"
        strokeDasharray="12" strokeDashoffset={12 * d} style={{ transition: "stroke-dashoffset 0.1s linear" }} />
      <path d="M94 98 L100 104 L106 98" stroke="var(--accent)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"
        strokeDasharray="18" strokeDashoffset={18 * d} style={{ transition: "stroke-dashoffset 0.1s linear" }} />
    </svg>
  );
}

function ResearchSvg({ progress }: { progress: number }) {
  const d = 1 - progress;
  return (
    <svg viewBox="0 0 200 140" fill="none" style={{ width: "100%", height: "100%" }}>
      {/* Magnifying glass */}
      <circle cx="80" cy="60" r="28" stroke="var(--accent)" strokeWidth="1.5"
        strokeDasharray="176" strokeDashoffset={176 * d} style={{ transition: "stroke-dashoffset 0.1s linear" }} />
      <line x1="100" y1="80" x2="120" y2="100" stroke="var(--accent)" strokeWidth="2" strokeLinecap="round"
        strokeDasharray="28" strokeDashoffset={28 * d} style={{ transition: "stroke-dashoffset 0.1s linear" }} />
      {/* Content lines inside lens */}
      <line x1="64" y1="50" x2="96" y2="50" stroke="var(--accent)" strokeWidth="1.2" strokeLinecap="round"
        strokeDasharray="32" strokeDashoffset={32 * d} style={{ transition: "stroke-dashoffset 0.1s linear" }} />
      <line x1="64" y1="58" x2="88" y2="58" stroke="var(--accent)" strokeWidth="1.2" strokeLinecap="round"
        strokeDasharray="24" strokeDashoffset={24 * d} style={{ transition: "stroke-dashoffset 0.1s linear" }} />
      <line x1="64" y1="66" x2="92" y2="66" stroke="var(--accent)" strokeWidth="1.2" strokeLinecap="round"
        strokeDasharray="28" strokeDashoffset={28 * d} style={{ transition: "stroke-dashoffset 0.1s linear" }} />
      {/* Color palette swatches */}
      <rect x="136" y="30" width="14" height="14" rx="3" stroke="var(--accent)" strokeWidth="1.2"
        strokeDasharray="48" strokeDashoffset={48 * d} style={{ transition: "stroke-dashoffset 0.1s linear" }} />
      <rect x="154" y="30" width="14" height="14" rx="3" stroke="var(--accent)" strokeWidth="1.2"
        strokeDasharray="48" strokeDashoffset={48 * d} style={{ transition: "stroke-dashoffset 0.1s linear" }} />
      <rect x="136" y="48" width="14" height="14" rx="3" stroke="var(--accent)" strokeWidth="1.2"
        strokeDasharray="48" strokeDashoffset={48 * d} style={{ transition: "stroke-dashoffset 0.1s linear" }} />
      <rect x="154" y="48" width="14" height="14" rx="3" stroke="var(--accent)" strokeWidth="1.2"
        strokeDasharray="48" strokeDashoffset={48 * d} style={{ transition: "stroke-dashoffset 0.1s linear" }} />
      {/* Font sample "Aa" */}
      <text x="145" y="88" fontFamily="Instrument Serif, serif" fontSize="18" fill="none" stroke="var(--accent)" strokeWidth="0.8"
        strokeDasharray="80" strokeDashoffset={80 * d} style={{ transition: "stroke-dashoffset 0.1s linear" }}>Aa</text>
      {/* Connecting dots */}
      <circle cx="130" cy="76" r="2" stroke="var(--accent)" strokeWidth="1"
        strokeDasharray="13" strokeDashoffset={13 * d} style={{ transition: "stroke-dashoffset 0.1s linear" }} />
    </svg>
  );
}

function AuditSvg({ progress }: { progress: number }) {
  const d = 1 - progress;
  return (
    <svg viewBox="0 0 200 140" fill="none" style={{ width: "100%", height: "100%" }}>
      {/* Document / audit report */}
      <rect x="24" y="16" width="68" height="108" rx="6" stroke="var(--accent)" strokeWidth="1.5"
        strokeDasharray="344" strokeDashoffset={344 * d} style={{ transition: "stroke-dashoffset 0.1s linear" }} />
      <line x1="38" y1="36" x2="78" y2="36" stroke="var(--accent)" strokeWidth="1.2" strokeLinecap="round"
        strokeDasharray="40" strokeDashoffset={40 * d} style={{ transition: "stroke-dashoffset 0.1s linear" }} />
      <line x1="38" y1="46" x2="72" y2="46" stroke="var(--accent)" strokeWidth="1.2" strokeLinecap="round"
        strokeDasharray="34" strokeDashoffset={34 * d} style={{ transition: "stroke-dashoffset 0.1s linear" }} />
      <line x1="38" y1="56" x2="76" y2="56" stroke="var(--accent)" strokeWidth="1.2" strokeLinecap="round"
        strokeDasharray="38" strokeDashoffset={38 * d} style={{ transition: "stroke-dashoffset 0.1s linear" }} />
      {/* Checkmarks */}
      <path d="M38 72 L44 78 L56 66" stroke="var(--accent)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"
        strokeDasharray="26" strokeDashoffset={26 * d} style={{ transition: "stroke-dashoffset 0.1s linear" }} />
      <path d="M38 88 L44 94 L56 82" stroke="var(--accent)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"
        strokeDasharray="26" strokeDashoffset={26 * d} style={{ transition: "stroke-dashoffset 0.1s linear" }} />
      <path d="M38 104 L44 110 L56 98" stroke="var(--accent)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"
        strokeDasharray="26" strokeDashoffset={26 * d} style={{ transition: "stroke-dashoffset 0.1s linear" }} />
      {/* + sign */}
      <line x1="108" y1="66" x2="108" y2="78" stroke="var(--accent)" strokeWidth="1.5" strokeLinecap="round"
        strokeDasharray="12" strokeDashoffset={12 * d} style={{ transition: "stroke-dashoffset 0.1s linear" }} />
      <line x1="102" y1="72" x2="114" y2="72" stroke="var(--accent)" strokeWidth="1.5" strokeLinecap="round"
        strokeDasharray="12" strokeDashoffset={12 * d} style={{ transition: "stroke-dashoffset 0.1s linear" }} />
      {/* Website preview */}
      <rect x="124" y="24" width="56" height="96" rx="6" stroke="var(--accent)" strokeWidth="1.5"
        strokeDasharray="296" strokeDashoffset={296 * d} style={{ transition: "stroke-dashoffset 0.1s linear" }} />
      {/* Screen content */}
      <rect x="132" y="36" width="40" height="20" rx="3" stroke="var(--accent)" strokeWidth="1"
        strokeDasharray="112" strokeDashoffset={112 * d} style={{ transition: "stroke-dashoffset 0.1s linear" }} />
      <line x1="132" y1="66" x2="172" y2="66" stroke="var(--accent)" strokeWidth="1" strokeLinecap="round"
        strokeDasharray="40" strokeDashoffset={40 * d} style={{ transition: "stroke-dashoffset 0.1s linear" }} />
      <line x1="132" y1="74" x2="164" y2="74" stroke="var(--accent)" strokeWidth="1" strokeLinecap="round"
        strokeDasharray="32" strokeDashoffset={32 * d} style={{ transition: "stroke-dashoffset 0.1s linear" }} />
      <line x1="132" y1="82" x2="168" y2="82" stroke="var(--accent)" strokeWidth="1" strokeLinecap="round"
        strokeDasharray="36" strokeDashoffset={36 * d} style={{ transition: "stroke-dashoffset 0.1s linear" }} />
      {/* FREE badge */}
      <rect x="138" y="96" width="28" height="14" rx="7" stroke="var(--accent)" strokeWidth="1.2"
        strokeDasharray="76" strokeDashoffset={76 * d} style={{ transition: "stroke-dashoffset 0.1s linear" }} />
    </svg>
  );
}

function DeploySvg({ progress }: { progress: number }) {
  const d = 1 - progress;
  return (
    <svg viewBox="0 0 200 140" fill="none" style={{ width: "100%", height: "100%" }}>
      {/* Rocket body */}
      <path d="M100 20 C100 20 82 50 82 80 C82 95 90 108 100 108 C110 108 118 95 118 80 C118 50 100 20 100 20Z" stroke="var(--accent)" strokeWidth="1.5"
        strokeDasharray="220" strokeDashoffset={220 * d} style={{ transition: "stroke-dashoffset 0.1s linear" }} />
      {/* Window */}
      <circle cx="100" cy="64" r="8" stroke="var(--accent)" strokeWidth="1.2"
        strokeDasharray="50" strokeDashoffset={50 * d} style={{ transition: "stroke-dashoffset 0.1s linear" }} />
      {/* Fins */}
      <path d="M82 84 C82 84 66 90 64 104 L82 98" stroke="var(--accent)" strokeWidth="1.2" strokeLinejoin="round"
        strokeDasharray="60" strokeDashoffset={60 * d} style={{ transition: "stroke-dashoffset 0.1s linear" }} />
      <path d="M118 84 C118 84 134 90 136 104 L118 98" stroke="var(--accent)" strokeWidth="1.2" strokeLinejoin="round"
        strokeDasharray="60" strokeDashoffset={60 * d} style={{ transition: "stroke-dashoffset 0.1s linear" }} />
      {/* Exhaust flames */}
      <path d="M92 108 L100 126 L108 108" stroke="var(--accent)" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round"
        strokeDasharray="40" strokeDashoffset={40 * d} style={{ transition: "stroke-dashoffset 0.1s linear" }} />
      <path d="M96 108 L100 118 L104 108" stroke="var(--accent)" strokeWidth="1" strokeLinecap="round" strokeLinejoin="round"
        strokeDasharray="24" strokeDashoffset={24 * d} style={{ transition: "stroke-dashoffset 0.1s linear" }} />
      {/* Speed lines */}
      <line x1="60" y1="44" x2="48" y2="44" stroke="var(--accent)" strokeWidth="1" strokeLinecap="round"
        strokeDasharray="12" strokeDashoffset={12 * d} style={{ transition: "stroke-dashoffset 0.1s linear" }} />
      <line x1="56" y1="54" x2="40" y2="54" stroke="var(--accent)" strokeWidth="1" strokeLinecap="round"
        strokeDasharray="16" strokeDashoffset={16 * d} style={{ transition: "stroke-dashoffset 0.1s linear" }} />
      <line x1="140" y1="44" x2="152" y2="44" stroke="var(--accent)" strokeWidth="1" strokeLinecap="round"
        strokeDasharray="12" strokeDashoffset={12 * d} style={{ transition: "stroke-dashoffset 0.1s linear" }} />
      <line x1="144" y1="54" x2="160" y2="54" stroke="var(--accent)" strokeWidth="1" strokeLinecap="round"
        strokeDasharray="16" strokeDashoffset={16 * d} style={{ transition: "stroke-dashoffset 0.1s linear" }} />
    </svg>
  );
}

const SVG_COMPONENTS = [UrlSvg, ResearchSvg, AuditSvg, DeploySvg];

export default function Process() {
  const sectionRef = useRef<HTMLDivElement>(null);
  const stickyRef = useRef<HTMLDivElement>(null);
  const [scrollProgress, setScrollProgress] = useState(0);

  useEffect(() => {
    const section = sectionRef.current;
    if (!section) return;

    const handleScroll = () => {
      const rect = section.getBoundingClientRect();
      const scrollableDistance = section.offsetHeight - window.innerHeight;
      if (scrollableDistance <= 0) return;
      const raw = -rect.top / scrollableDistance;
      setScrollProgress(Math.max(0, Math.min(1, raw)));
    };

    window.addEventListener("scroll", handleScroll, { passive: true });
    handleScroll();
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  const totalCards = STEPS.length;
  // First card visible at rest, scroll moves through remaining 3
  const cardWidthVw = 85;
  const totalTravel = (totalCards - 1) * cardWidthVw;

  return (
    <div
      ref={sectionRef}
      id="process"
      style={{ height: `${totalCards * 100}vh`, position: "relative" }}
    >
      <div
        ref={stickyRef}
        style={{
          position: "sticky",
          top: 0,
          height: "100vh",
          overflow: "hidden",
          display: "flex",
          flexDirection: "column",
        }}
      >

        {/* Header */}
        <div style={{
          padding: "clamp(6rem, 14vh, 10rem) clamp(1.5rem, 4vw, 4rem) clamp(1.5rem, 3vh, 2rem)",
          textAlign: "center",
          flexShrink: 0,
        }}>
          <h2 className="text-display-lg">
            From <em className="font-serif" style={{ fontStyle: "italic" }}>outdated</em>
            <br />To <em className="font-serif" style={{ fontStyle: "italic" }}>outstanding</em>
          </h2>
        </div>

        {/* Horizontal track */}
        <div style={{
          flex: 1,
          display: "flex",
          alignItems: "center",
          overflow: "hidden",
        }}>
          <div style={{
            display: "flex",
            gap: "clamp(1.5rem, 3vw, 2.5rem)",
            paddingLeft: "calc((100vw - min(700px, 85vw)) / 2)",
            paddingRight: "clamp(1.5rem, 4vw, 4rem)",
            transform: `translateX(-${scrollProgress * totalTravel}vw)`,
            willChange: "transform",
          }}>
            {STEPS.map((step, i) => {
              // Each card becomes active over its segment of the scroll
              // SVG should be fully drawn BY the time card is centered
              const cardCenter = i / (totalCards - 1);
              const seg = 1 / (totalCards - 1);
              // Animation runs in the half-segment BEFORE center
              const drawStart = cardCenter - seg;
              const drawEnd = cardCenter;
              const cardProgress = i === 0
                ? 1
                : Math.max(0, Math.min(1, (scrollProgress - drawStart) / (drawEnd - drawStart)));
              const isActive = i === 0 || scrollProgress >= drawStart;
              // Fade out as card moves past center toward left edge
              const fadeOut = scrollProgress > cardCenter
                ? Math.max(0, 1 - (scrollProgress - cardCenter) / (seg * 0.5))
                : 1;
              const opacity = isActive ? Math.max(0.08, fadeOut) : 0.15;
              const SvgComponent = SVG_COMPONENTS[i];

              return (
                <div
                  key={step.number}
                  style={{
                    flex: "0 0 auto",
                    width: `${cardWidthVw}vw`,
                    maxWidth: 700,
                    display: "flex",
                    alignItems: "center",
                    gap: "clamp(2rem, 5vw, 4rem)",
                    opacity,
                    transition: "opacity 0.4s ease",
                  }}
                >
                  {/* SVG illustration */}
                  <div style={{
                    flex: "0 0 auto",
                    width: "clamp(140px, 22vw, 220px)",
                    height: "clamp(100px, 16vw, 160px)",
                  }}>
                    <SvgComponent progress={isActive ? cardProgress : 0} />
                  </div>

                  {/* Text */}
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <span style={{
                      fontFamily: '"Instrument Serif", Georgia, serif',
                      fontSize: "clamp(2rem, 3.5vw, 3rem)",
                      lineHeight: 1,
                      color: "var(--accent)",
                      opacity: 0.2,
                    }}>
                      {step.number}
                    </span>

                    <h3 style={{
                      fontFamily: '"Instrument Serif", Georgia, serif',
                      fontSize: "clamp(1.4rem, 2.5vw, 2rem)",
                      color: "var(--text)",
                      lineHeight: 1.15,
                      marginTop: "clamp(0.4rem, 1vh, 0.6rem)",
                    }}>
                      {step.title}
                    </h3>

                    <p style={{
                      fontSize: "clamp(0.85rem, 1vw, 0.95rem)",
                      color: "var(--text-muted)",
                      lineHeight: 1.6,
                      marginTop: "clamp(0.5rem, 1vh, 0.8rem)",
                      maxWidth: 380,
                    }}>
                      {step.desc}
                    </p>

                    <span style={{
                      display: "inline-block",
                      marginTop: "clamp(0.6rem, 1.2vh, 0.8rem)",
                      padding: "0.3rem 0.75rem",
                      background: "var(--accent-soft)",
                      borderRadius: "var(--radius-full)",
                      fontSize: "clamp(0.72rem, 0.82vw, 0.78rem)",
                      fontWeight: 500,
                      color: "var(--accent)",
                    }}>
                      {step.detail}
                    </span>
                  </div>

                  {/* Arrow between cards */}
                  {i < STEPS.length - 1 && (
                    <svg
                      width="32" height="32" viewBox="0 0 32 32" fill="none"
                      style={{ flexShrink: 0, color: "var(--text-light)", opacity: 0.3 }}
                    >
                      <path d="M8 16H24M24 16L18 10M24 16L18 22" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                    </svg>
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* Bottom progress bar — 1px black, left to right */}
        <div style={{
          position: "absolute",
          bottom: 0,
          left: 0,
          width: "100%",
          height: 3,
          background: "var(--border)",
        }}>
          <div style={{
            height: "100%",
            width: `${scrollProgress * 100}%`,
            background: "var(--accent)",
          }} />
        </div>
      </div>
    </div>
  );
}
