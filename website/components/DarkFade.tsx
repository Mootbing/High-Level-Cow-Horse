"use client";

import { useEffect, useRef, useState } from "react";

export default function DarkFade({ children }: { children: React.ReactNode }) {
  const ref = useRef<HTMLDivElement>(null);
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;

    const handleScroll = () => {
      const rect = el.getBoundingClientRect();
      const fadeZone = window.innerHeight * 0.8;
      // Fade starts when section enters viewport, completes over fadeZone
      const raw = (window.innerHeight - rect.top) / fadeZone;
      setProgress(Math.max(0, Math.min(1, raw)));
    };

    window.addEventListener("scroll", handleScroll, { passive: true });
    handleScroll();
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  // Interpolate from #FAFAF8 (250,250,248) to #0a0a0a (10,10,10)
  const r = Math.round(250 - progress * 240);
  const g = Math.round(250 - progress * 240);
  const b = Math.round(248 - progress * 238);
  const bg = `rgb(${r},${g},${b})`;

  // Text color interpolation
  const textR = Math.round(10 + progress * 245);
  const textG = Math.round(10 + progress * 245);
  const textB = Math.round(10 + progress * 245);

  return (
    <div
      ref={ref}
      style={{
        background: bg,
        // Override CSS custom properties for children
        ["--text" as string]: `rgb(${textR},${textG},${textB})`,
        ["--text-muted" as string]: progress > 0.5
          ? `rgba(255,255,255,${0.4 + (progress - 0.5) * 0.4})`
          : `rgb(${107 + progress * 200},${107 + progress * 200},${107 + progress * 200})`,
        ["--text-light" as string]: progress > 0.5
          ? `rgba(255,255,255,${0.25 + (progress - 0.5) * 0.3})`
          : `rgb(${154 + progress * 150},${154 + progress * 150},${154 + progress * 150})`,
        ["--border" as string]: progress > 0.5
          ? `rgba(255,255,255,${0.08 + (progress - 0.5) * 0.08})`
          : `rgba(232,232,228,${1 - progress * 0.8})`,
        ["--bg-card" as string]: progress > 0.5
          ? `rgba(255,255,255,0.05)`
          : `rgba(255,255,255,${1 - progress * 0.9})`,
        transition: "background 0.05s linear",
      }}
    >
      {children}
    </div>
  );
}
