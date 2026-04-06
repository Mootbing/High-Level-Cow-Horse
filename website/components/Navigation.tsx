"use client";

import { useState, useEffect } from "react";

const NAV_LINKS = [
  { label: "Process", href: "#process" },
  { label: "Work", href: "#work" },
  { label: "Pricing", href: "#pricing" },
  { label: "Contact", href: "mailto:jason@clarmi.studio" },
];

export default function Navigation() {
  const [scrolled, setScrolled] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 50);
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  useEffect(() => {
    document.body.style.overflow = mobileOpen ? "hidden" : "";
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
          paddingTop: scrolled ? "calc(0.7rem + env(safe-area-inset-top, 0px))" : "calc(1rem + env(safe-area-inset-top, 0px))",
          paddingBottom: scrolled ? "0.7rem" : "1rem",
          background: scrolled ? "rgba(250,250,248,0.9)" : "transparent",
          backdropFilter: scrolled ? "blur(16px) saturate(180%)" : "none",
          borderBottom: scrolled ? "1px solid var(--border)" : "1px solid transparent",
          transition: "all 0.4s cubic-bezier(0.16, 1, 0.3, 1)",
        }}
      >
        <div className="container" style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <a
            href="#"
            style={{
              fontFamily: '"Instrument Serif", Georgia, serif',
              fontSize: "clamp(1.3rem, 1.8vw, 1.6rem)",
              letterSpacing: "-0.02em",
              color: "var(--text)",
            }}
          >
            Clarmi Studio
          </a>

          <div className="hide-mobile" style={{ display: "flex", alignItems: "center", gap: "clamp(2rem, 3.5vw, 3rem)" }}>
            {NAV_LINKS.map((link) => (
              <a
                key={link.href}
                href={link.href}
                style={{
                  fontSize: "0.88rem",
                  fontWeight: 400,
                  color: "var(--text-muted)",
                  transition: "color 0.3s ease",
                }}
                onMouseEnter={(e) => (e.currentTarget.style.color = "var(--text)")}
                onMouseLeave={(e) => (e.currentTarget.style.color = "var(--text-muted)")}
              >
                {link.label}
              </a>
            ))}
            <a href="#cta" className="btn-primary" style={{ padding: "0.6rem 1.4rem", fontSize: "0.85rem" }}>
              Free Audit
            </a>
          </div>

          <button
            className="hide-desktop"
            onClick={() => setMobileOpen(!mobileOpen)}
            aria-label="Toggle menu"
            style={{
              width: 36, height: 36,
              display: "flex", flexDirection: "column",
              alignItems: "center", justifyContent: "center",
              gap: mobileOpen ? 0 : 5,
              position: "relative", zIndex: 101,
            }}
          >
            <span style={{ width: 20, height: 1.5, background: "var(--text)", borderRadius: 1, transition: "all 0.3s ease", transform: mobileOpen ? "rotate(45deg)" : "none", position: mobileOpen ? "absolute" : "relative" }} />
            <span style={{ width: 20, height: 1.5, background: "var(--text)", borderRadius: 1, transition: "all 0.3s ease", opacity: mobileOpen ? 0 : 1 }} />
            <span style={{ width: 20, height: 1.5, background: "var(--text)", borderRadius: 1, transition: "all 0.3s ease", transform: mobileOpen ? "rotate(-45deg)" : "none", position: mobileOpen ? "absolute" : "relative" }} />
          </button>
        </div>
      </nav>

      <div className={`mobile-nav ${mobileOpen ? "open" : ""}`}>
        {NAV_LINKS.map((link) => (
          <a key={link.href} href={link.href} onClick={() => setMobileOpen(false)}>{link.label}</a>
        ))}
        <a href="#cta" className="btn-primary" style={{ marginTop: "1rem" }} onClick={() => setMobileOpen(false)}>Free Audit</a>
      </div>
    </>
  );
}
