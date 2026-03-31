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
  awards?: { title: string; org: string }[];
  darkPreview?: boolean;
}

export const PROJECTS: Project[] = [
  {
    slug: "jason-xu",
    name: "Jason Xu — Portfolio",
    industry: "Portfolio",
    caption: "award-winning at seventeen",
    color: "#60A5FA",
    gradient: "linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 40%, #16213e 70%, #0f3460 100%)",
    improvement: "3x Awwwards winner",
    brief:
      "Jason Xu is a fullstack developer and Figma designer — at 17. His work rivals studios twice his age, but his old portfolio didn't reflect that. He needed something that would turn heads and win industry recognition.",
    challenge:
      "Jason's projects were exceptional but his online presence was forgettable. A basic portfolio couldn't convey the depth of his design and engineering skills. He needed an immersive experience that matched his ambition — something award-worthy.",
    solution:
      "We built a cinematic, scroll-driven portfolio with fluid page transitions, custom animations, and a distinctive dark aesthetic. Every micro-interaction was crafted to reflect Jason's attention to detail — from smooth reveals to carefully choreographed scroll sequences. The result is a portfolio that feels like a product, not a template.",
    results: [
      "Won Awwwards Site of the Day",
      "Won CSS Design Awards Website of the Day",
      "Won Awwwards Developer Award",
      "Featured on FWA Site of the Day",
    ],
    tech: ["Next.js", "React", "GSAP", "Vercel"],
    rotation: -2.5,
    url: "https://17.jasonxu.me",
    darkPreview: true,
    awards: [
      { title: "Site of the Day", org: "Awwwards" },
      { title: "Developer Award", org: "Awwwards" },
      { title: "Website of the Day", org: "CSS Design Awards" },
      { title: "Site of the Day", org: "FWA" },
    ],
  },
  {
    slug: "payo",
    name: "Payo",
    industry: "Fintech",
    caption: "payments for the agent era",
    color: "#22D3EE",
    gradient: "linear-gradient(135deg, #0a0a0a 0%, #0c1220 40%, #0e1a2b 70%, #091b2a 100%)",
    improvement: "$25M raised post-launch",
    brief:
      "Payo — \"PayPal for Agents\" — was building payment infrastructure for AI agents, a category that didn't exist yet. They needed a developer-first landing page that could explain a complex product simply and support a Sequoia-led seed round.",
    challenge:
      "The product was groundbreaking: an SDK that lets AI agents make real payments autonomously. But explaining agent-to-agent payment rails to developers and investors required clarity that didn't exist in the market. They had no public presence and a fundraise on the line.",
    solution:
      "We designed a dark-mode, developer-first landing page with a clear 4-step integration flow, interactive code snippets, and an ecosystem visualization showcasing 20+ supported platforms — from OpenAI to Stripe. Every section balanced developer comprehension with investor confidence. Zero-dependency, sub-second loads.",
    results: [
      "Launched 2 weeks before $25M Sequoia-led seed round closed",
      "Developer signups exceeded target by 340% in first month",
      "99 Lighthouse performance score on launch day",
      "Featured on Hacker News front page",
    ],
    tech: ["Next.js", "TypeScript", "Tailwind CSS", "Vercel"],
    rotation: 1.8,
    url: "https://payo.dev",
    darkPreview: true,
  },
];
