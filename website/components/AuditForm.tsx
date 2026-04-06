"use client";

import { useState } from "react";

const AUDIT_API_URL = process.env.NEXT_PUBLIC_AUDIT_API_URL || "";

type Step = "url" | "email" | "submitting" | "done" | "error";

export default function AuditForm({ className }: { className?: string }) {
  const [url, setUrl] = useState("");
  const [email, setEmail] = useState("");
  const [step, setStep] = useState<Step>("url");
  const [errorMsg, setErrorMsg] = useState("");

  const handleUrlSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!url.trim()) return;
    setStep("email");
  };

  const handleAuditSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.trim()) return;
    setStep("submitting");
    setErrorMsg("");

    try {
      const res = await fetch(`${AUDIT_API_URL}/api/v1/audit`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: url.trim(), email: email.trim() }),
      });

      if (res.status === 429) {
        setErrorMsg("Too many requests. Please try again later.");
        setStep("error");
        return;
      }

      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        setErrorMsg(data.detail || "Something went wrong. Please try again.");
        setStep("error");
        return;
      }

      setStep("done");
    } catch {
      setErrorMsg("Network error. Please check your connection.");
      setStep("error");
    }
  };

  const handleBack = () => {
    setStep("url");
    setEmail("");
    setErrorMsg("");
  };

  const handleReset = () => {
    setUrl("");
    setEmail("");
    setStep("url");
    setErrorMsg("");
  };

  // Step 1: URL input
  if (step === "url") {
    return (
      <form onSubmit={handleUrlSubmit} className={className}>
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
          <button type="submit">Free Audit</button>
        </div>
        <p
          style={{
            marginTop: "0.6rem",
            fontSize: "clamp(0.75rem, 0.85vw, 0.82rem)",
            color: "var(--text-light)",
          }}
        >
          Personalized audits delivered within 1 hour. Website drafted by next business day.
        </p>
      </form>
    );
  }

  // Step 2: Email input
  if (step === "email") {
    return (
      <form onSubmit={handleAuditSubmit} className={className}>
        <div className="url-input-wrapper">
          <svg
            width="18" height="18" viewBox="0 0 18 18" fill="none"
            style={{ marginLeft: "clamp(0.9rem, 1.2vw, 1.3rem)", flexShrink: 0, opacity: 0.3 }}
          >
            <rect x="2" y="4" width="14" height="10" rx="2" stroke="currentColor" strokeWidth="1.5" />
            <path d="M2 6l7 4.5L16 6" stroke="currentColor" strokeWidth="1.5" />
          </svg>
          <input
            type="email"
            placeholder="Where should we send your audit?"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            aria-label="Your email address"
            required
            autoFocus
          />
          <button type="submit">Send My Audit</button>
        </div>
        <p
          style={{
            marginTop: "0.6rem",
            fontSize: "clamp(0.75rem, 0.85vw, 0.82rem)",
            color: "var(--text-light)",
          }}
        >
          <button
            type="button"
            onClick={handleBack}
            style={{
              background: "none",
              border: "none",
              color: "var(--accent)",
              cursor: "pointer",
              fontSize: "inherit",
              padding: 0,
              textDecoration: "underline",
            }}
          >
            &larr; Change URL
          </button>
          {" "}&middot; Auditing <strong>{url}</strong>
        </p>
      </form>
    );
  }

  // Submitting state
  if (step === "submitting") {
    return (
      <div className={className} style={{ opacity: 1, transform: "none" }}>
        <div
          className="url-input-wrapper"
          style={{ justifyContent: "center", padding: "clamp(0.9rem, 1.3vw, 1.1rem)" }}
        >
          <span style={{ fontSize: "clamp(0.88rem, 1vw, 0.95rem)", color: "var(--text-muted)" }}>
            Analyzing your website...
          </span>
        </div>
      </div>
    );
  }

  // Done state — show success message + URL bar for another audit
  if (step === "done") {
    return (
      <div className={className} style={{ opacity: 1, transform: "none" }}>
        <p
          style={{
            marginBottom: "0.6rem",
            fontSize: "clamp(0.82rem, 0.95vw, 0.9rem)",
            color: "var(--text)",
          }}
        >
          <span style={{ color: "var(--accent)" }}>&#10003;</span> Audit sent to <strong>{email}</strong> — check your inbox shortly.
        </p>
        <form onSubmit={(e) => { e.preventDefault(); if (!url.trim()) return; setEmail(""); setStep("email"); }}>
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
              placeholder="Audit another website..."
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              aria-label="Your website URL"
            />
            <button type="submit">Free Audit</button>
          </div>
        </form>
      </div>
    );
  }

  // Error state — show error + URL bar to retry
  return (
    <div className={className} style={{ opacity: 1, transform: "none" }}>
      <p
        style={{
          marginBottom: "0.6rem",
          fontSize: "clamp(0.82rem, 0.95vw, 0.9rem)",
          color: "#ef4444",
        }}
      >
        {errorMsg}
      </p>
      <form onSubmit={(e) => { e.preventDefault(); if (!url.trim()) return; setEmail(""); setErrorMsg(""); setStep("email"); }}>
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
          <button type="submit">Free Audit</button>
        </div>
      </form>
    </div>
  );
}
