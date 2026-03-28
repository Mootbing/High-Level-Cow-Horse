# Full Site Generation Prompt

Generate a complete Next.js landing page with the following specifications:

## Project: {{project_name}}
## Brief: {{brief}}
## Design Spec: {{design_spec}}

## Requirements:
- Next.js 15 App Router with TypeScript
- Tailwind CSS for styling
- GSAP + ScrollTrigger for scroll animations
- Lenis for smooth scrolling
- Responsive: mobile-first, breakpoints at 768px, 1024px, 1440px
- Lighthouse performance score target: 95+
- All images lazy-loaded with proper dimensions
- Semantic HTML with ARIA attributes
- Dark theme with accent colors from design spec

## Sections (in order):
1. Hero with video background (GSAP scrub on scroll)
2. Text reveal section (words reveal on scroll)
3. Parallax image gallery (3 columns, different scroll speeds)
4. Feature cards (staggered entrance animation)
5. CTA section (fade-in with scale)
6. Footer

## Animation Guidelines:
- Use GPU-accelerated properties only (transform, opacity)
- Scroll animations should feel smooth, not jittery
- Entrance animations: power3.out easing
- Parallax: subtle, max 20% speed difference between layers
- Mobile: reduce animation complexity for performance
