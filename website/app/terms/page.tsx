import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Terms of Service — Clarmi Design Studio",
};

export default function Terms() {
  return (
    <main style={{ background: "var(--bg)", minHeight: "100vh" }}>
      <div className="container" style={{ maxWidth: 720, paddingTop: "clamp(6rem, 12vh, 10rem)", paddingBottom: "clamp(4rem, 8vh, 6rem)" }}>
        <a href="/" style={{ display: "inline-flex", alignItems: "center", gap: "0.4rem", fontSize: "clamp(0.82rem, 0.92vw, 0.88rem)", color: "var(--text-muted)", marginBottom: "clamp(2rem, 4vh, 3rem)", transition: "color 0.3s" }}>
          &larr; Back to home
        </a>

        <h1 className="text-display-md" style={{ marginBottom: "clamp(0.6rem, 1vh, 0.8rem)" }}>Terms of Service</h1>
        <p className="text-body" style={{ marginBottom: "clamp(2rem, 4vh, 3rem)" }}>Last updated: March 31, 2026</p>

        {[
          {
            title: "Services",
            body: "Clarmi Design Studio provides custom website design, development, and maintenance services. Our standard offering includes a custom-designed Next.js website delivered within 48 hours, with unlimited pre-launch revisions and ongoing monthly maintenance.",
          },
          {
            title: "Pricing & Payment",
            body: "Our standard pricing is $500 one-time for website design and development, plus $50/month for hosting, maintenance, and ongoing revisions. You don't pay until you're satisfied with the design. Monthly fees are billed on the first of each month. All prices are in USD.",
          },
          {
            title: "Revisions",
            body: "Pre-launch revisions are unlimited — we keep iterating until you're happy. After launch, your monthly plan includes ongoing revisions and updates. We aim to complete revision requests within 24–48 hours.",
          },
          {
            title: "Ownership & Intellectual Property",
            body: "Once payment is received in full, you own the website design and all custom assets created for your project. The underlying code is built on open-source technologies (Next.js, React) and remains subject to their respective licenses. We retain the right to showcase your project in our portfolio unless you request otherwise.",
          },
          {
            title: "Hosting & Maintenance",
            body: "Your monthly fee covers hosting on Vercel, SSL certificates, uptime monitoring, performance optimization, and security updates. If you cancel your monthly plan, we will provide your source code and assist with a transition to your own hosting.",
          },
          {
            title: "Cancellation",
            body: "You may cancel your monthly maintenance plan at any time. There are no long-term contracts or cancellation fees. Upon cancellation, you retain full ownership of your website code and assets.",
          },
          {
            title: "Refunds",
            body: "Since you don't pay until you approve the design, refunds are generally not applicable. If for any reason you're unsatisfied after payment, contact us within 14 days and we'll work with you to make it right.",
          },
          {
            title: "Content Responsibility",
            body: "You are responsible for providing accurate business information, images, and content for your website. We are not liable for any inaccuracies in content you provide. We will never fabricate testimonials, reviews, or credentials.",
          },
          {
            title: "Limitation of Liability",
            body: "Clarmi Design Studio is not liable for any indirect, incidental, or consequential damages arising from the use of our services or your website. Our total liability is limited to the amount you have paid us in the preceding 12 months.",
          },
          {
            title: "Changes to Terms",
            body: "We may update these terms from time to time. Active clients will be notified of significant changes via email. Continued use of our services constitutes acceptance of updated terms.",
          },
          {
            title: "Contact",
            body: "Questions about these terms? Reach out at hello@clarmi.com.",
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
