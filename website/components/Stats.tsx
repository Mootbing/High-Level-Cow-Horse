"use client";

import { useEffect, useRef, useState } from "react";

interface CounterProps {
  end: number;
  suffix?: string;
  prefix?: string;
  duration?: number;
  active: boolean;
}

function Counter({ end, suffix = "", prefix = "", duration = 2000, active }: CounterProps) {
  const [count, setCount] = useState(0);
  const hasAnimated = useRef(false);

  useEffect(() => {
    if (!active || hasAnimated.current) return;
    hasAnimated.current = true;

    const startTime = performance.now();

    const animate = (currentTime: number) => {
      const elapsed = currentTime - startTime;
      const progress = Math.min(elapsed / duration, 1);

      // Ease out cubic
      const eased = 1 - Math.pow(1 - progress, 3);
      setCount(Math.round(eased * end));

      if (progress < 1) {
        requestAnimationFrame(animate);
      }
    };

    requestAnimationFrame(animate);
  }, [active, end, duration]);

  return (
    <span className="stat-number">
      {prefix}
      {count}
      {suffix}
    </span>
  );
}

const STATS = [
  { end: 48, suffix: "hr", label: "Average delivery time", prefix: "" },
  { end: 97, suffix: "+", label: "Lighthouse performance score", prefix: "" },
  { end: 500, suffix: "", label: "One-time build cost", prefix: "$" },
  { end: 0, suffix: "", label: "Templates used. Ever.", prefix: "" },
];

export default function Stats() {
  const sectionRef = useRef<HTMLElement>(null);
  const [active, setActive] = useState(false);

  useEffect(() => {
    const el = sectionRef.current;
    if (!el) return;

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            setActive(true);
            const reveals = el.querySelectorAll(".reveal");
            reveals.forEach((r, i) => {
              setTimeout(() => r.classList.add("active"), i * 100);
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
      ref={sectionRef}
      className="section"
      style={{
        background: "var(--gray-900)",
        borderTop: "1px solid var(--gray-800)",
        borderBottom: "1px solid var(--gray-800)",
      }}
    >
      <div className="container">
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(min(100%, 200px), 1fr))",
            gap: "clamp(2rem, 4vw, 4rem)",
            textAlign: "center",
          }}
        >
          {STATS.map((stat, i) => (
            <div
              key={stat.label}
              className={`reveal delay-${i + 1}`}
              style={{
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                gap: "clamp(0.5rem, 1vh, 0.8rem)",
              }}
            >
              <Counter
                end={stat.end}
                suffix={stat.suffix}
                prefix={stat.prefix}
                active={active}
              />
              <p
                style={{
                  fontFamily: '"Space Grotesk", sans-serif',
                  fontSize: "clamp(0.85rem, 1vw, 0.95rem)",
                  color: "var(--gray-400)",
                  fontWeight: 500,
                  maxWidth: "200px",
                }}
              >
                {stat.label}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
