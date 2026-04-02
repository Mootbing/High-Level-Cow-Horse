"use client";

const ITEMS = [
  "Restaurants",
  "Salons",
  "Law Firms",
  "Gyms",
  "Dentists",
  "Contractors",
  "Real Estate",
  "Retail",
  "Clinics",
  "Studios",
  "Agencies",
  "Consultants",
];

export default function Marquee() {
  return (
    <div
      style={{
        borderTop: "1px solid var(--border)",
        padding: "clamp(0.9rem, 1.5vh, 1.2rem) 0",
        overflow: "hidden",
        position: "relative",
        background: "var(--bg)",
      }}
    >
      <div
        style={{
          position: "absolute", left: 0, top: 0, bottom: 0,
          width: "clamp(40px, 8vw, 100px)",
          background: "linear-gradient(90deg, var(--bg), transparent)",
          zIndex: 2, pointerEvents: "none",
        }}
      />
      <div
        style={{
          position: "absolute", right: 0, top: 0, bottom: 0,
          width: "clamp(40px, 8vw, 100px)",
          background: "linear-gradient(270deg, var(--bg), transparent)",
          zIndex: 2, pointerEvents: "none",
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
            }}
          >
            <span
              style={{
                fontFamily: '"Instrument Serif", Georgia, serif',
                fontSize: "clamp(0.95rem, 1.2vw, 1.1rem)",
                color: "var(--text-light)",
              }}
            >
              {item}
            </span>
            <span
              style={{
                width: 4, height: 4, borderRadius: "50%",
                background: "var(--border-hover)",
                flexShrink: 0,
              }}
            />
          </div>
        ))}
      </div>
    </div>
  );
}
