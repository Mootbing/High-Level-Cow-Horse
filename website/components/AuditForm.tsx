"use client";

import { useState } from "react";

export default function AuditForm({ className }: { className?: string }) {
  const [url, setUrl] = useState("");
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!url.trim()) return;
    setSubmitted(true);
    setTimeout(() => setSubmitted(false), 4000);
  };

  return (
    <form onSubmit={handleSubmit} className={className}>
      <div className="url-input-wrapper">
        <svg
          width="18" height="18" viewBox="0 0 18 18" fill="none"
          style={{ marginLeft: "clamp(0.9rem, 1.2vw, 1.3rem)", flexShrink: 0, opacity: 0.3 }}
        >
          <circle cx="9" cy="9" r="7" stroke="currentColor" strokeWidth="1.5" />
          <path d="M9 2C9 2 5.5 5.5 5.5 9C5.5 12.5 9 16 9 16" stroke="currentColor" strokeWidth="1.5" />
          <path d="M9 2C9 2 12.5 5.5 12.5 9C12.5 12.5 9 16 9 16" stroke="currentColor" strokeWidth="1.5" />
          <line x1="2.5" y1="7" x2="15.5" y2="7" stroke="currentColor" strokeWidth="1.5" />
          <line x1="2.5" y1="11" x2="15.5" y2="11" stroke="currentColor" strokeWidth="1.5" />
        </svg>
        <input
          type="text"
          placeholder="Enter your website URL..."
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          aria-label="Your website URL"
        />
        <button type="submit">
          {submitted ? "We'll be in touch!" : "Upgrade!"}
        </button>
      </div>
      <p
        style={{
          marginTop: "0.6rem",
          fontSize: "clamp(0.75rem, 0.85vw, 0.82rem)",
          color: submitted ? "var(--accent)" : "var(--text-light)",
        }}
      >
        {submitted
          ? "Expect your personalized audit within 1 hour."
          : "Personalized audits delivered within 1 hour."}
      </p>
    </form>
  );
}
