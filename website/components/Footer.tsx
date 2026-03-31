"use client";

const FOOTER_LINKS = {
  Services: [
    { label: "Web Design", href: "#services" },
    { label: "Web Development", href: "#services" },
    { label: "SEO Optimization", href: "#services" },
    { label: "Maintenance", href: "#services" },
  ],
  Company: [
    { label: "About", href: "#" },
    { label: "Process", href: "#process" },
    { label: "Pricing", href: "#pricing" },
    { label: "Contact", href: "#cta" },
  ],
  Resources: [
    { label: "Free Audit", href: "#cta" },
    { label: "Case Studies", href: "#work" },
    { label: "Blog", href: "#" },
    { label: "FAQ", href: "#" },
  ],
};

export default function Footer() {
  return (
    <footer
      style={{
        borderTop: "1px solid var(--gray-800)",
        paddingTop: "clamp(3rem, 6vh, 5rem)",
        paddingBottom: "clamp(1.5rem, 3vh, 2.5rem)",
      }}
    >
      <div className="container">
        {/* Top section */}
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(min(100%, 180px), 1fr))",
            gap: "clamp(2rem, 4vw, 4rem)",
            marginBottom: "clamp(3rem, 6vh, 5rem)",
          }}
        >
          {/* Brand column */}
          <div style={{ gridColumn: "span 1" }}>
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
                marginBottom: "clamp(1rem, 2vh, 1.5rem)",
              }}
            >
              <svg width="24" height="24" viewBox="0 0 28 28" fill="none">
                <rect x="2" y="2" width="24" height="24" rx="6" stroke="var(--accent)" strokeWidth="2.5" fill="none" />
                <rect x="8" y="8" width="12" height="12" rx="3" fill="var(--accent)" />
              </svg>
              CLARMI
            </a>
            <p
              style={{
                fontFamily: '"Space Grotesk", sans-serif',
                fontSize: "clamp(0.85rem, 1vw, 0.95rem)",
                color: "var(--gray-400)",
                lineHeight: 1.6,
                maxWidth: "280px",
              }}
            >
              AI-powered design studio building custom websites for small
              businesses. Fast, affordable, no templates.
            </p>

            {/* Social links */}
            <div
              style={{
                display: "flex",
                gap: "0.75rem",
                marginTop: "clamp(1rem, 2vh, 1.5rem)",
              }}
            >
              {[
                {
                  label: "Twitter",
                  icon: (
                    <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
                      <path
                        d="M2 2L7.5 9.5L2 16H3.5L8.25 10.5L12 16H16.5L10.5 8L15.5 2H14L9.75 7L6.5 2H2ZM4 3.5H5.75L14.5 14.5H12.75L4 3.5Z"
                        fill="currentColor"
                      />
                    </svg>
                  ),
                },
                {
                  label: "LinkedIn",
                  icon: (
                    <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
                      <rect x="2" y="6" width="3" height="10" rx="0.5" fill="currentColor" />
                      <circle cx="3.5" cy="3.5" r="1.8" fill="currentColor" />
                      <path
                        d="M7 16V9.5C7 8 8 6.5 10 6.5C12 6.5 13 8 13 9.5V16H16V9C16 6 14 4.5 11.5 4.5C9.5 4.5 8 5.5 7 6.5V6H7V16Z"
                        fill="currentColor"
                      />
                    </svg>
                  ),
                },
                {
                  label: "Instagram",
                  icon: (
                    <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
                      <rect x="2" y="2" width="14" height="14" rx="4" stroke="currentColor" strokeWidth="1.5" />
                      <circle cx="9" cy="9" r="3.5" stroke="currentColor" strokeWidth="1.5" />
                      <circle cx="13" cy="5" r="1" fill="currentColor" />
                    </svg>
                  ),
                },
              ].map((social) => (
                <a
                  key={social.label}
                  href="#"
                  aria-label={social.label}
                  style={{
                    width: 36,
                    height: 36,
                    borderRadius: "50%",
                    border: "1px solid var(--gray-700)",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    color: "var(--gray-400)",
                    transition: "all 0.3s ease",
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.borderColor = "var(--accent)";
                    e.currentTarget.style.color = "var(--accent)";
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.borderColor = "var(--gray-700)";
                    e.currentTarget.style.color = "var(--gray-400)";
                  }}
                >
                  {social.icon}
                </a>
              ))}
            </div>
          </div>

          {/* Link columns */}
          {Object.entries(FOOTER_LINKS).map(([title, links]) => (
            <div key={title}>
              <h4
                style={{
                  fontFamily: '"Space Grotesk", sans-serif',
                  fontWeight: 600,
                  fontSize: "clamp(0.8rem, 0.95vw, 0.9rem)",
                  color: "var(--white)",
                  letterSpacing: "0.05em",
                  textTransform: "uppercase",
                  marginBottom: "clamp(1rem, 2vh, 1.5rem)",
                }}
              >
                {title}
              </h4>
              <ul
                style={{
                  listStyle: "none",
                  display: "flex",
                  flexDirection: "column",
                  gap: "0.6rem",
                }}
              >
                {links.map((link) => (
                  <li key={link.label}>
                    <a
                      href={link.href}
                      style={{
                        fontFamily: '"Space Grotesk", sans-serif',
                        fontSize: "clamp(0.85rem, 1vw, 0.9rem)",
                        color: "var(--gray-400)",
                        transition: "color 0.3s ease",
                      }}
                      onMouseEnter={(e) => (e.currentTarget.style.color = "var(--white)")}
                      onMouseLeave={(e) => (e.currentTarget.style.color = "var(--gray-400)")}
                    >
                      {link.label}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        {/* Bottom bar */}
        <div
          style={{
            borderTop: "1px solid var(--gray-800)",
            paddingTop: "clamp(1rem, 2vh, 1.5rem)",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            flexWrap: "wrap",
            gap: "0.75rem",
          }}
        >
          <p
            style={{
              fontFamily: '"Space Grotesk", sans-serif',
              fontSize: "clamp(0.75rem, 0.85vw, 0.8rem)",
              color: "var(--gray-500)",
            }}
          >
            &copy; {new Date().getFullYear()} Clarmi Design Studio. All rights reserved.
          </p>
          <div
            style={{
              display: "flex",
              gap: "clamp(1rem, 2vw, 2rem)",
            }}
          >
            <a
              href="#"
              style={{
                fontFamily: '"Space Grotesk", sans-serif',
                fontSize: "clamp(0.75rem, 0.85vw, 0.8rem)",
                color: "var(--gray-500)",
                transition: "color 0.3s ease",
              }}
              onMouseEnter={(e) => (e.currentTarget.style.color = "var(--white)")}
              onMouseLeave={(e) => (e.currentTarget.style.color = "var(--gray-500)")}
            >
              Privacy
            </a>
            <a
              href="#"
              style={{
                fontFamily: '"Space Grotesk", sans-serif',
                fontSize: "clamp(0.75rem, 0.85vw, 0.8rem)",
                color: "var(--gray-500)",
                transition: "color 0.3s ease",
              }}
              onMouseEnter={(e) => (e.currentTarget.style.color = "var(--white)")}
              onMouseLeave={(e) => (e.currentTarget.style.color = "var(--gray-500)")}
            >
              Terms
            </a>
          </div>
        </div>
      </div>
    </footer>
  );
}
