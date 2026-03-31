export interface Project {
  slug: string;
  name: string;
  industry: string;
  caption: string;
  color: string;
  gradient: string;
  improvement: string;
  brief: string;
  challenge: string;
  solution: string;
  results: string[];
  tech: string[];
  rotation: number;
}

export const PROJECTS: Project[] = [
  {
    slug: "bella-vista",
    name: "Bella Vista Ristorante",
    industry: "Restaurant",
    caption: "from slow to stunning",
    color: "#E8956A",
    gradient: "linear-gradient(135deg, #fef3c7 0%, #fde68a 50%, #fbbf24 100%)",
    improvement: "4.2s → 1.1s load time",
    brief:
      "Bella Vista had been running on a WordPress site with 23 plugins for six years. Load times averaged 4.2 seconds. Their menu was a PDF. Their online presence didn't match the quality of their food.",
    challenge:
      "The existing site was built on a bloated WordPress install with an outdated theme. The menu was an embedded PDF that didn't render on mobile. Contact info was buried three clicks deep. Google PageSpeed scored 34.",
    solution:
      "We rebuilt the entire site on Next.js with a scroll-driven layout showcasing their menu, ambiance photos, and story. The menu became a beautifully typeset interactive page. We added online reservation integration and optimized every image with next/image.",
    results: [
      "Load time dropped from 4.2s to 1.1s",
      "Lighthouse score went from 34 to 97",
      "Online reservations increased 180% in the first month",
      "Catering inquiries doubled through the new dedicated catering page",
    ],
    tech: ["Next.js", "GSAP", "Vercel", "Tailwind CSS"],
    rotation: -2.5,
  },
  {
    slug: "summit-legal",
    name: "Summit Legal Group",
    industry: "Law Firm",
    caption: "trust starts at the homepage",
    color: "#5B8DEF",
    gradient: "linear-gradient(135deg, #dbeafe 0%, #93c5fd 50%, #3b82f6 100%)",
    improvement: "312% more contact submissions",
    brief:
      "Summit Legal's Wix site looked like every other law firm template on the internet. Generic stock photos, buried contact forms, and zero social proof. Potential clients were bouncing before they ever reached out.",
    challenge:
      "The template design inspired no confidence. Practice areas were listed in a wall of text. Attorney bios were afterthoughts. The contact form was on a separate page nobody visited. Mobile experience was broken.",
    solution:
      "We designed a trust-first experience. Attorney photos and credentials above the fold. Case results with real numbers. Practice areas as visual cards with clear CTAs. The contact form appears contextually throughout the page, not hidden away.",
    results: [
      "Contact form submissions increased 312%",
      "Average session duration went from 45s to 3m 12s",
      "Bounce rate dropped from 78% to 34%",
      "Ranked for 12 new local keywords within 6 weeks",
    ],
    tech: ["Next.js", "TypeScript", "Vercel", "Lenis"],
    rotation: 1.8,
  },
  {
    slug: "pure-glow",
    name: "Pure Glow Aesthetics",
    industry: "Medical Spa",
    caption: "beauty meets conversion",
    color: "#C77DBA",
    gradient: "linear-gradient(135deg, #fce7f3 0%, #f9a8d4 50%, #ec4899 100%)",
    improvement: "Page 1 of Google in 3 weeks",
    brief:
      "Pure Glow had a Squarespace site that looked dated and didn't reflect the premium experience their clients receive in person. Online bookings were nearly nonexistent — most clients called in.",
    challenge:
      "The Squarespace template couldn't showcase before/after galleries properly. The booking flow required three page loads. Service descriptions were copy-pasted from a competitor. No local SEO optimization whatsoever.",
    solution:
      "We built a cinematic experience with a hero video, swipeable before/after galleries, and one-click booking integration. Every service page was written with real treatment details. We added schema markup and optimized for local search terms.",
    results: [
      "Ranked on page 1 of Google for 8 target keywords in 3 weeks",
      "Online bookings increased from near-zero to 60% of total bookings",
      "Average page load: 0.9 seconds",
      "Instagram-worthy design increased social shares 4x",
    ],
    tech: ["Next.js", "Three.js", "Vercel", "GSAP"],
    rotation: -1.2,
  },
];
