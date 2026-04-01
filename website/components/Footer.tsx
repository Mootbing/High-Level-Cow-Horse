"use client";

const LINKS = {
  Company: [
    { label: "From The Founder", href: "#founder" },
    { label: "Process", href: "#process" },
    { label: "Pricing", href: "#pricing" },
    { label: "Contact", href: "mailto:jason@clarmi.studio" },
  ],
  Resources: [
    { label: "Free Audit", href: "#cta" },
    { label: "Case Studies", href: "#work" },
  ],
};

export default function Footer() {
  return (
    <footer style={{ borderTop: "1px solid var(--border)", paddingTop: "clamp(3rem, 6vh, 5rem)", paddingBottom: "clamp(1.5rem, 3vh, 2rem)", background: "var(--bg)" }}>
      <div className="container">
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(min(100%, 160px), 1fr))", gap: "clamp(2rem, 4vw, 4rem)", marginBottom: "clamp(3rem, 6vh, 4rem)" }}>
          {/* Brand */}
          <div>
            <a href="#" style={{ fontFamily: '"Instrument Serif", Georgia, serif', fontSize: "clamp(1.2rem, 1.6vw, 1.4rem)", color: "var(--text)", display: "block", marginBottom: "clamp(0.8rem, 1.5vh, 1rem)" }}>
              Clarmi
            </a>
            <p style={{ fontSize: "clamp(0.82rem, 0.92vw, 0.88rem)", color: "var(--text-muted)", lineHeight: 1.6, maxWidth: "260px" }}>
              Award-winning design studio building custom websites for small businesses.
            </p>
          </div>

          {Object.entries(LINKS).map(([title, links]) => (
            <div key={title}>
              <h4 style={{ fontSize: "clamp(0.75rem, 0.85vw, 0.82rem)", fontWeight: 500, color: "var(--text)", letterSpacing: "0.05em", textTransform: "uppercase", marginBottom: "clamp(0.8rem, 1.5vh, 1rem)" }}>{title}</h4>
              <ul style={{ listStyle: "none", display: "flex", flexDirection: "column", gap: "0.45rem" }}>
                {links.map((l) => (
                  <li key={l.label}>
                    <a href={l.href} style={{ fontSize: "clamp(0.82rem, 0.92vw, 0.88rem)", color: "var(--text-muted)", transition: "color 0.3s" }}
                      onMouseEnter={(e) => (e.currentTarget.style.color = "var(--text)")}
                      onMouseLeave={(e) => (e.currentTarget.style.color = "var(--text-muted)")}
                    >{l.label}</a>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <div style={{ borderTop: "1px solid var(--border)", paddingTop: "clamp(0.8rem, 1.5vh, 1rem)", display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "0.5rem" }}>
          <p style={{ fontSize: "clamp(0.72rem, 0.82vw, 0.78rem)", color: "var(--text-light)" }}>
            &copy; {new Date().getFullYear()} Clarmi Design Studio
          </p>
          <div style={{ display: "flex", gap: "clamp(1rem, 2vw, 1.5rem)" }}>
            {[{ label: "Privacy", href: "/privacy" }, { label: "Terms", href: "/terms" }].map((t) => (
              <a key={t.label} href={t.href} style={{ fontSize: "clamp(0.72rem, 0.82vw, 0.78rem)", color: "var(--text-light)", transition: "color 0.3s" }}
                onMouseEnter={(e) => (e.currentTarget.style.color = "var(--text)")}
                onMouseLeave={(e) => (e.currentTarget.style.color = "var(--text-light)")}
              >{t.label}</a>
            ))}
          </div>
        </div>
      </div>
    </footer>
  );
}
