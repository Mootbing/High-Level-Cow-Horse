# Full Site Generation Prompt

Generate an immersive, award-winning Next.js landing page.

## Project: {{project_name}}
## Brief: {{brief}}
## Design Spec: {{design_spec}}

## Tech Stack
- Next.js 15 App Router, TypeScript
- Tailwind CSS
- GSAP + ScrollTrigger for scroll animations (pin, scrub, stagger, timeline)
- Lenis for smooth scrolling
- React Three Fiber + @react-three/drei + postprocessing for 3D scenes
- Framer Motion for layout animations

## Architecture
```
app/layout.tsx          ← Google Fonts, metadata, SmoothScroller
app/page.tsx            ← Section composition
app/globals.css         ← Tailwind + brand CSS properties
components/
  SmoothScroller.tsx    ← Lenis + GSAP sync
  Hero.tsx              ← 3D scene OR scroll video hero
  Scene3D.tsx           ← R3F canvas (dynamic import, ssr: false)
  ScrollVideo.tsx       ← Scroll-controlled video (pin + scrub)
  TransitionSection.tsx ← Veo transition between sections
  TextReveal.tsx        ← Word-by-word scroll reveal
  Features.tsx          ← Staggered cards with 3D tilt hover
  CTA.tsx               ← Magnetic button + gradient background
  Footer.tsx            ← Stagger-in footer
```

## Section Composition (pick 5-8)

1. **Hero** (REQUIRED) — choose one:
   - 3D scene background with text overlay + staggered entrance animation
   - Scroll-controlled video (pinned, scrub through on scroll)
   - Kinetic typography (no images — pure animated type)

2. **Scroll Transition** — pinned video morph (Veo-generated A→B) between hero and content

3. **Text Reveal** — large statement, word-by-word opacity + blur reveal on scroll

4. **Parallax Section** — multi-speed depth layers (3-5 layers, 0.15x to 1.1x scroll speed)

5. **Feature Cards** — staggered entrance (y+60, opacity 0→1, scale 0.95→1), 3D tilt on hover

6. **Horizontal Scroll** — pinned vertical→horizontal scroll for portfolio/timeline

7. **Stats** — animated counters triggered on scroll entry

8. **CTA** — magnetic button, gradient/particle background

9. **Footer** — stagger-in animation

## Animation Rules
- GPU-only: transform, opacity, filter, clip-path
- Entrances: power3.out, 0.8-1.2s
- Scrub: linear ('none'), scrub value 0.3-1
- Stagger: 0.08-0.15s between elements
- Pin sections: 2-3x viewport height max
- Mobile: disable 3D, reduce parallax 50%, static video fallbacks

## 3D Scene (if used)
- Dynamic import: `dynamic(() => import('./Scene3D'), { ssr: false })`
- Single Canvas per page
- Max 2 post-processing effects
- Mobile: show static fallback image
- Scene style matched to industry (see templates/prompts/three-js-scene.md)

## Scroll Video (if used)
- Pin section, scrub video.currentTime
- poster= for instant visual
- preload="auto" muted playsInline
- Mobile: keyframe image fallback

## Content Rules
- Every heading, name, description from brand data — never invented
- Reuse prospect's image URLs, copy, navigation, contact info, pricing
- Colors from brand_colors, fonts from fonts array
- Industry-appropriate palette (NOT default dark+gold)

## Performance Targets
- Lighthouse: > 85 average
- LCP: < 2.5s
- Three.js bundle: < 200KB gzipped
- Video assets: < 5MB each

## References
- `templates/prompts/immersive-site.md` — master design system
- `templates/prompts/three-js-scene.md` — 3D scene recipes
- `templates/prompts/scroll-video-section.md` — video patterns
- `templates/prompts/effect-catalog.md` — micro-interactions
- `templates/prompts/scroll-animation.md` — GSAP patterns
