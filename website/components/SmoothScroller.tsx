"use client";

import { useEffect, useRef } from "react";
import { usePathname } from "next/navigation";
import Lenis from "lenis";

export default function SmoothScroller({
  children,
}: {
  children: React.ReactNode;
}) {
  const lenisRef = useRef<Lenis | null>(null);
  const pathname = usePathname();

  useEffect(() => {
    if (!lenisRef.current) return;
    const hash = window.location.hash;
    if (hash) {
      // Smooth scroll to hash target after DOM settles
      requestAnimationFrame(() => {
        const target = document.querySelector(hash);
        if (target) {
          lenisRef.current?.scrollTo(target as HTMLElement, { duration: 1.2 });
        } else {
          lenisRef.current?.scrollTo(0, { immediate: true });
        }
      });
    } else {
      lenisRef.current.scrollTo(0, { immediate: true });
    }
  }, [pathname]);

  useEffect(() => {
    const lenis = new Lenis({
      duration: 1.2,
      easing: (t: number) => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
      touchMultiplier: 2,
    });

    lenisRef.current = lenis;

    function raf(time: number) {
      lenis.raf(time);
      requestAnimationFrame(raf);
    }
    requestAnimationFrame(raf);

    return () => {
      lenis.destroy();
    };
  }, []);

  return <>{children}</>;
}
