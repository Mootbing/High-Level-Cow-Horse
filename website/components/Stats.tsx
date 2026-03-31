"use client";

import { useEffect, useRef, useState } from "react";

function Counter({ end, suffix = "", prefix = "", active }: { end: number; suffix?: string; prefix?: string; active: boolean }) {
  const [count, setCount] = useState(0);
  const ran = useRef(false);

  useEffect(() => {
    if (!active || ran.current) return;
    ran.current = true;
    const start = performance.now();
    const dur = 2000;
    const step = (now: number) => {
      const p = Math.min((now - start) / dur, 1);
      const eased = 1 - Math.pow(1 - p, 3);
      setCount(Math.round(eased * end));
      if (p < 1) requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
  }, [active, end]);

  return (
    <span style={{ fontFamily: '"Instrument Serif", Georgia, serif', fontSize: "clamp(3rem, 6vw, 5rem)", lineHeight: 1, color: "var(--text)", letterSpacing: "-0.03em" }}>
      {prefix}{count}{suffix}
    </span>
  );
}

const STATS = [
  { end: 48, suffix: "hr", prefix: "", label: "Average delivery time" },
  { end: 97, suffix: "+", prefix: "", label: "Lighthouse performance score" },
  { end: 500, suffix: "", prefix: "$", label: "One-time build cost" },
  { end: 0, suffix: "", prefix: "", label: "Templates used. Ever." },
];

export default function Stats() {
  const ref = useRef<HTMLElement>(null);
  const [active, setActive] = useState(false);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            setActive(true);
            el.querySelectorAll(".reveal").forEach((r, i) => {
              setTimeout(() => r.classList.add("active"), i * 80);
            });
            observer.disconnect();
          }
        });
      },
      { threshold: 0.3 }
    );
    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  return (
    <section
      ref={ref}
      className="section"
      style={{
        background: "var(--bg-alt)",
        borderTop: "1px solid var(--border)",
        borderBottom: "1px solid var(--border)",
      }}
    >
      <div className="container">
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(min(100%, 180px), 1fr))", gap: "clamp(2rem, 4vw, 4rem)", textAlign: "center" }}>
          {STATS.map((s, i) => (
            <div key={s.label} className={`reveal delay-${i + 1}`} style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: "0.5rem" }}>
              <Counter end={s.end} suffix={s.suffix} prefix={s.prefix} active={active} />
              <p style={{ fontSize: "clamp(0.82rem, 0.95vw, 0.9rem)", color: "var(--text-muted)", maxWidth: "180px" }}>{s.label}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
