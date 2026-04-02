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
  url?: string;
  screenshot?: string;
  screenshots?: string[];
  originalScreenshot?: string;
  demoVideo?: string;
  awards?: { title: string; org: string }[];
  darkPreview?: boolean;
}

export const PROJECTS: Project[] = [
  {
    slug: "original-china-garden",
    name: "Original China Garden",
    industry: "Restaurant",
    caption: "55 years of Houston tradition",
    color: "#C41E3A",
    gradient: "linear-gradient(135deg, #0a0a0a 0%, #1a0e0e 40%, #2a1212 70%, #0a0a0a 100%)",
    improvement: "4.5★ TripAdvisor, est. 1969",
    brief:
      "Original China Garden is a Houston institution — a family-owned Chinese restaurant that started as an import store in 1968 and has been serving downtown Houston for over 55 years. Their reputation was built on tableside sizzling rice soup and Texas-Chinese fusion, but their website didn't reflect five decades of legacy.",
    challenge:
      "A restaurant with 55 years of history and a prime downtown location near the George R. Brown Convention Center had an outdated web presence. Convention visitors, hotel guests, and loyal regulars couldn't find menus, hours, or the story behind Houston's longest-running Chinese restaurant.",
    solution:
      "We built an elegant, dark-themed site with warm cream typography that honors the restaurant's heritage. Playfair Display headlines evoke tradition, while the layout spotlights their signature dishes — Sizzling Fried Rice Soup, Jalapeño Shrimp — with rich imagery. Prominent location info and hours serve the downtown foot traffic they depend on.",
    results: [
      "Full menu with signature dishes highlighted",
      "Heritage storytelling — 55-year history front and center",
      "Downtown location and hours prominently featured",
      "Shipped and deployed in under 24 hours",
    ],
    tech: ["Next.js", "TypeScript", "Vercel", "Tailwind CSS"],
    rotation: 2.2,
    url: "https://original-china-garden-c84a02.vercel.app/",
    screenshot: "/assets/china-garden/0.png",
    originalScreenshot: "/assets/china-garden/original.png",
    screenshots: [
      "/assets/china-garden/0.png",
      "/assets/china-garden/1.png",
      "/assets/china-garden/2.png",
      "/assets/china-garden/3.png",
    ],
    demoVideo: "/assets/demos/china-garden/demo.mp4",
    darkPreview: true,
  },
  {
    slug: "ros-niyom",
    name: "Ros Niyom Thai",
    industry: "Restaurant",
    caption: "from street food to spotlight",
    color: "#D4A853",
    gradient: "linear-gradient(135deg, #1a1207 0%, #2a1f0e 40%, #3d2b10 70%, #1a1207 100%)",
    improvement: "4.9 stars, 1,000+ reviews",
    brief:
      "Ros Niyom Thai serves authentic Northern Thai street food in Long Island City, Queens. They had earned a loyal following — 4.9 stars and 1,000+ reviews — but their online presence didn't match the quality of their food.",
    challenge:
      "Ros Niyom had a website, and it wasn't bad — but it wasn't built for mobile. With 70% of their traffic coming from phones, the experience fell apart on smaller screens. Menus were hard to navigate, hours were buried, and ordering required jumping to third-party apps. For a spot with 4.9 stars and a cult following, the mobile experience didn't match the food.",
    solution:
      "We built a dark, gold-accented landing page that feels as rich as their Khao Soi. A visual menu with prices and descriptions, prominent hours and location info, one-tap ordering and call buttons, and social proof pulled from their real reviews. Cormorant Garamond headlines give it an elevated feel without losing the street food soul.",
    results: [
      "Full interactive menu with 50+ items live on day one",
      "One-tap call, directions, and delivery ordering",
      "Mobile-first design — 70% of their traffic is phone",
      "Shipped and deployed in under 24 hours",
    ],
    tech: ["Next.js", "TypeScript", "Vercel", "Tailwind CSS"],
    rotation: -2.5,
    url: "https://ros-niyom-thai-4993e7.vercel.app",
    screenshot: "/assets/ros-niyom/site.png",
    originalScreenshot: "/assets/ros-niyom/original.png",
    demoVideo: "/assets/demos/ros-niyom/demo.mp4",
    screenshots: [
      "/assets/ros-niyom/0.png",
      "/assets/ros-niyom/1.png",
      "/assets/ros-niyom/2.png",
      "/assets/ros-niyom/3.png",
      "/assets/ros-niyom/4.png",
      "/assets/ros-niyom/5.png",
    ],
    darkPreview: true,
  },
  {
    slug: "payo",
    name: "Payo",
    industry: "Fintech",
    caption: "payments for the agent era",
    color: "#22D3EE",
    gradient: "linear-gradient(135deg, #0a0a0a 0%, #0c1220 40%, #0e1a2b 70%, #091b2a 100%)",
    improvement: "99 Lighthouse score",
    brief:
      "Payo — \"PayPal for Agents\" — is building payment infrastructure for AI agents, a category that didn't exist yet. They needed a developer-first landing page that could explain a complex product simply and build trust with developers.",
    challenge:
      "The product was groundbreaking: an SDK that lets AI agents make real payments autonomously. But explaining agent-to-agent payment rails to developers required clarity that didn't exist in the market. They had no public presence and needed to ship fast.",
    solution:
      "We designed a dark-mode, developer-first landing page with a clear 4-step integration flow, interactive code snippets, and an ecosystem visualization showcasing 20+ supported platforms — from OpenAI to Stripe. Every section balanced developer comprehension with investor confidence. Zero-dependency, sub-second loads.",
    results: [
      "Shipped in under 48 hours from first call",
      "99 Lighthouse performance score on launch day",
      "Zero-dependency, sub-second page loads",
      "Developer-first design praised across the ecosystem",
    ],
    tech: ["Next.js", "TypeScript", "Tailwind CSS", "Vercel"],
    rotation: 1.8,
    url: "https://payo.dev",
    screenshot: "/assets/payo/site.png",
    darkPreview: true,
  },
  {
    slug: "jason-xu",
    name: "Jason Xu — Founder Portfolio",
    industry: "Portfolio",
    caption: "the founder's story",
    color: "#60A5FA",
    gradient: "linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 40%, #16213e 70%, #0f3460 100%)",
    improvement: "3x Awwwards winner",
    brief:
      "Jason Xu is the founder of Clarmi Design Studio — a fullstack engineer and designer who started winning international design awards at 17. This portfolio captures the craft and vision behind the studio itself.",
    challenge:
      "As the founder of a design studio, Jason's personal brand is the studio's brand. His previous portfolio didn't reflect the caliber of work Clarmi delivers. He needed an immersive, award-worthy experience that would establish credibility for both himself and the studio.",
    solution:
      "We built a cinematic, scroll-driven portfolio with fluid page transitions, custom animations, and a distinctive dark aesthetic. Every micro-interaction was crafted to reflect the attention to detail that defines Clarmi's work — from smooth reveals to carefully choreographed scroll sequences. The result is a portfolio that feels like a product, not a template.",
    results: [
      "Won Awwwards Site of the Day",
      "Won CSS Design Awards Website of the Day",
      "Won Awwwards Developer Award",
      "Featured on FWA Site of the Day",
    ],
    tech: ["Next.js", "React", "GSAP", "Vercel"],
    rotation: -1.2,
    url: "https://17.jasonxu.me",
    screenshot: "/assets/jason-xu/site.png",
    darkPreview: true,
    awards: [
      { title: "Site of the Day", org: "Awwwards" },
      { title: "Developer Award", org: "Awwwards" },
      { title: "Website of the Day", org: "CSS Design Awards" },
      { title: "Site of the Day", org: "FWA" },
    ],
  },
];
