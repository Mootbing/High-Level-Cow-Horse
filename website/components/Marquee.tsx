"use client";

const ITEMS = [
  "RESTAURANTS",
  "SALONS",
  "LAW FIRMS",
  "GYMS",
  "DENTISTS",
  "CONTRACTORS",
  "REAL ESTATE",
  "RETAIL",
  "CLINICS",
  "STUDIOS",
  "AGENCIES",
  "CONSULTANTS",
];

export default function Marquee() {
  return (
    <div
      style={{
        borderTop: "1px solid var(--gray-800)",
        borderBottom: "1px solid var(--gray-800)",
        padding: "clamp(1rem, 2vh, 1.5rem) 0",
        overflow: "hidden",
        position: "relative",
      }}
    >
      {/* Fade edges */}
      <div
        style={{
          position: "absolute",
          left: 0,
          top: 0,
          bottom: 0,
          width: "clamp(40px, 8vw, 120px)",
          background: "linear-gradient(90deg, var(--black), transparent)",
          zIndex: 2,
          pointerEvents: "none",
        }}
      />
      <div
        style={{
          position: "absolute",
          right: 0,
          top: 0,
          bottom: 0,
          width: "clamp(40px, 8vw, 120px)",
          background: "linear-gradient(270deg, var(--black), transparent)",
          zIndex: 2,
          pointerEvents: "none",
        }}
      />

      <div className="marquee-track">
        {[...ITEMS, ...ITEMS].map((item, i) => (
          <div
            key={i}
            style={{
              display: "flex",
              alignItems: "center",
              gap: "clamp(1.5rem, 3vw, 2.5rem)",
              paddingRight: "clamp(1.5rem, 3vw, 2.5rem)",
              whiteSpace: "nowrap",
            }}
          >
            <span
              style={{
                fontFamily: '"Syne", sans-serif',
                fontWeight: 700,
                fontSize: "clamp(0.8rem, 1.2vw, 1rem)",
                letterSpacing: "0.12em",
                color: "var(--gray-500)",
                transition: "color 0.3s ease",
              }}
            >
              {item}
            </span>
            <svg
              width="6"
              height="6"
              viewBox="0 0 6 6"
              fill="var(--accent)"
              style={{ opacity: 0.5, flexShrink: 0 }}
            >
              <circle cx="3" cy="3" r="3" />
            </svg>
          </div>
        ))}
      </div>
    </div>
  );
}
