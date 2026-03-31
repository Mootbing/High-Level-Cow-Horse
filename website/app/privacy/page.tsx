import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Privacy Policy — Clarmi Design Studio",
};

export default function Privacy() {
  return (
    <main style={{ background: "var(--bg)", minHeight: "100vh" }}>
      <div className="container" style={{ maxWidth: 720, paddingTop: "clamp(6rem, 12vh, 10rem)", paddingBottom: "clamp(4rem, 8vh, 6rem)" }}>
        <a href="/" style={{ display: "inline-flex", alignItems: "center", gap: "0.4rem", fontSize: "clamp(0.82rem, 0.92vw, 0.88rem)", color: "var(--text-muted)", marginBottom: "clamp(2rem, 4vh, 3rem)", transition: "color 0.3s" }}>
          &larr; Back to home
        </a>

        <h1 className="text-display-md" style={{ marginBottom: "clamp(0.6rem, 1vh, 0.8rem)" }}>Privacy Policy</h1>
        <p className="text-body" style={{ marginBottom: "clamp(2rem, 4vh, 3rem)" }}>Last updated: March 31, 2026</p>

        {[
          {
            title: "Information We Collect",
            body: "When you submit your website URL through our audit form, we collect the URL you provide and any contact information you share (such as your email address). We also collect standard analytics data including page views, browser type, and device information through privacy-respecting analytics tools.",
          },
          {
            title: "How We Use Your Information",
            body: "We use your information to perform website audits, create personalized proposals, build and deliver your website, communicate with you about your project, and improve our services. We never sell your personal information to third parties.",
          },
          {
            title: "Website Audits",
            body: "When you submit a URL for a free audit, we crawl the publicly available pages of that website to assess design, performance, and SEO. We do not access any private, password-protected, or admin areas of your site.",
          },
          {
            title: "Data Storage",
            body: "Your project data (designs, code, and assets) is stored securely on GitHub and deployed via Vercel. We retain your data for the duration of our working relationship and for a reasonable period afterward unless you request deletion.",
          },
          {
            title: "Cookies",
            body: "Our website uses minimal, essential cookies for functionality. We do not use tracking cookies or third-party advertising cookies.",
          },
          {
            title: "Third-Party Services",
            body: "We use the following third-party services to deliver our work: Vercel (hosting), GitHub (code storage), and Google Fonts (typography). Each has their own privacy policies governing how they handle data.",
          },
          {
            title: "Your Rights",
            body: "You have the right to access, correct, or delete your personal information at any time. You can also request a copy of all data we hold about you. To exercise any of these rights, email us at hello@clarmi.com.",
          },
          {
            title: "Changes to This Policy",
            body: "We may update this policy from time to time. We will notify active clients of any significant changes via email.",
          },
          {
            title: "Contact",
            body: "If you have questions about this privacy policy, please reach out at hello@clarmi.com.",
          },
        ].map((section) => (
          <div key={section.title} style={{ marginBottom: "clamp(1.5rem, 3vh, 2rem)" }}>
            <h2 style={{
              fontFamily: '"Instrument Serif", Georgia, serif',
              fontSize: "clamp(1.2rem, 1.6vw, 1.4rem)",
              color: "var(--text)",
              marginBottom: "0.5rem",
            }}>
              {section.title}
            </h2>
            <p className="text-body">{section.body}</p>
          </div>
        ))}
      </div>
    </main>
  );
}
