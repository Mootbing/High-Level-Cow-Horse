"use client";

import { useState, useEffect } from "react";

const NAV_LINKS = [
  { label: "Services", href: "#services" },
  { label: "Process", href: "#process" },
  { label: "Work", href: "#work" },
  { label: "Pricing", href: "#pricing" },
];

export default function Navigation() {
  const [scrolled, setScrolled] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 60);
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  useEffect(() => {
    if (mobileOpen) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
    }
  }, [mobileOpen]);

  return (
    <>
      <nav
        style={{
          position: "fixed",
          top: 0,
          left: 0,
          right: 0,
          zIndex: 100,
          padding: scrolled ? "0.8rem 0" : "1.2rem 0",
          background: scrolled
            ? "rgba(5, 5, 5, 0.85)"
            : "transparent",
          backdropFilter: scrolled ? "blur(20px)" : "none",
          borderBottom: scrolled
            ? "1px solid rgba(255,255,255,0.05)"
            : "1px solid transparent",
          transition: "all 0.4s cubic-bezier(0.16, 1, 0.3, 1)",
        }}
      >
        <div className="container" style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          {/* Logo */}
          <a
            href="#"
            style={{
              fontFamily: '"Syne", sans-serif',
              fontWeight: 800,
              fontSize: "clamp(1.2rem, 1.8vw, 1.5rem)",
              letterSpacing: "-0.02em",
              display: "flex",
              alignItems: "center",
              gap: "0.5rem",
            }}
          >
            <svg width="28" height="28" viewBox="0 0 28 28" fill="none">
              <rect
                x="2"
                y="2"
                width="24"
                height="24"
                rx="6"
                stroke="var(--accent)"
                strokeWidth="2.5"
                fill="none"
              />
              <rect
                x="8"
                y="8"
                width="12"
                height="12"
                rx="3"
                fill="var(--accent)"
              />
            </svg>
            CLARMI
          </a>

          {/* Desktop Links */}
          <div
            className="hide-mobile"
            style={{ display: "flex", alignItems: "center", gap: "clamp(1.5rem, 3vw, 2.5rem)" }}
          >
            {NAV_LINKS.map((link) => (
              <a
                key={link.href}
                href={link.href}
                style={{
                  fontFamily: '"Space Grotesk", sans-serif',
                  fontSize: "0.9rem",
                  fontWeight: 500,
                  color: "var(--gray-300)",
                  transition: "color 0.3s ease",
                  letterSpacing: "0.01em",
                }}
                onMouseEnter={(e) => (e.currentTarget.style.color = "var(--white)")}
                onMouseLeave={(e) => (e.currentTarget.style.color = "var(--gray-300)")}
              >
                {link.label}
              </a>
            ))}
            <a href="#cta" className="btn-primary" style={{ padding: "0.7rem 1.5rem", fontSize: "0.85rem" }}>
              Free Audit
            </a>
          </div>

          {/* Mobile Hamburger */}
          <button
            className="hide-desktop"
            onClick={() => setMobileOpen(!mobileOpen)}
            aria-label="Toggle menu"
            style={{
              width: 40,
              height: 40,
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              justifyContent: "center",
              gap: mobileOpen ? 0 : 6,
              position: "relative",
              zIndex: 101,
            }}
          >
            <span
              style={{
                width: 24,
                height: 2,
                background: "var(--white)",
                borderRadius: 1,
                transition: "all 0.3s ease",
                transform: mobileOpen ? "rotate(45deg) translateY(0)" : "none",
                position: mobileOpen ? "absolute" : "relative",
              }}
            />
            <span
              style={{
                width: 24,
                height: 2,
                background: "var(--white)",
                borderRadius: 1,
                transition: "all 0.3s ease",
                opacity: mobileOpen ? 0 : 1,
              }}
            />
            <span
              style={{
                width: 24,
                height: 2,
                background: "var(--white)",
                borderRadius: 1,
                transition: "all 0.3s ease",
                transform: mobileOpen ? "rotate(-45deg) translateY(0)" : "none",
                position: mobileOpen ? "absolute" : "relative",
              }}
            />
          </button>
        </div>
      </nav>

      {/* Mobile Nav Overlay */}
      <div className={`mobile-nav ${mobileOpen ? "open" : ""}`}>
        {NAV_LINKS.map((link) => (
          <a
            key={link.href}
            href={link.href}
            onClick={() => setMobileOpen(false)}
          >
            {link.label}
          </a>
        ))}
        <a
          href="#cta"
          className="btn-primary"
          style={{ marginTop: "1rem", fontSize: "1.1rem", padding: "1rem 2.5rem" }}
          onClick={() => setMobileOpen(false)}
        >
          Free Audit
        </a>
      </div>
    </>
  );
}
