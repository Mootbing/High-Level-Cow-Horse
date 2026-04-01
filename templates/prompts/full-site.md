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
app/page.tsx            ← Section composition: ScrollVideo hero → Scene3D + content
app/globals.css         ← Tailwind + brand CSS properties
components/
  SmoothScroller.tsx    ← Lenis + GSAP sync
  Hero.tsx              ← Scroll-controlled video hero (keyframe A→B via Veo 3.1)
  Scene3D.tsx           ← Persistent Three.js canvas behind content sections (dynamic import, ssr: false)
  ScrollVideo.tsx       ← Scroll-controlled video (pin + scrub video.currentTime)
  TransitionSection.tsx ← Veo transition between sections
  TextReveal.tsx        ← ReactBits text animation + word-by-word scroll reveal
  Features.tsx          ← ReactBits tilt/spotlight cards with 3D tilt hover
  CTA.tsx               ← ReactBits magnetic button + aurora/gradient background
  Footer.tsx            ← Stagger-in footer
  [ReactBits]/          ← Components copied from ReactBits library
```

## Section Composition (pick 5-8)

1. **Hero** (REQUIRED) — ALWAYS scroll-controlled video:
   - Nano Banana generates keyframe A (opening state) + keyframe B (ending state)
   - Veo 3.1 generates transition video using first+last frame mode
   - Video plays frame-by-frame as user scrolls (pinned, scrub through)
   - Poster = keyframe A. Mobile fallback = keyframe A as static image.

2. **Scroll Transition** — pinned video morph (Veo-generated A→B) between hero and content

3. **Text Reveal** — large statement, word-by-word opacity + blur reveal on scroll

4. **Parallax Section** — multi-speed depth layers (3-5 layers, 0.15x to 1.1x scroll speed)

5. **Feature Cards** — ReactBits tilt/spotlight cards, staggered entrance, Three.js ambient shapes behind

6. **Horizontal Scroll** — pinned vertical→horizontal scroll, ReactBits reveal animations per card

7. **Stats** — ReactBits counter component, Three.js particle burst on number reveal

8. **CTA** — ReactBits magnetic button + aurora/spotlight background, Three.js accent elements

9. **Footer** — ReactBits fade-in, subtle Three.js ambient

## Animation Rules
- GPU-only: transform, opacity, filter, clip-path
- Entrances: power3.out, 0.8-1.2s
- Scrub: linear ('none'), scrub value 0.3-1
- Stagger: 0.08-0.15s between elements
- Pin sections: 2-3x viewport height max
- Mobile: disable 3D, reduce parallax 50%, static video fallbacks

## Three.js Persistent Scene (REQUIRED — behind all content sections)
- Dynamic import: `dynamic(() => import('./Scene3D'), { ssr: false })`
- Single Canvas per page — positioned behind content sections (not the hero)
- 3D elements respond to scroll position (rotate, morph, scale as user scrolls)
- Max 2 post-processing effects
- Mobile: show static fallback image
- Scene style matched to industry (see templates/prompts/three-js-scene.md)
- Fades in as hero video scrolls out

## Scroll Video Hero (REQUIRED — always the hero)
- Pin section, scrub video.currentTime
- poster= keyframe A for instant visual
- preload="auto" muted playsInline
- Video generated from keyframe A + B via Veo 3.1 first+last frame
- Mobile: keyframe A as static image fallback

## ReactBits Components (REQUIRED — use in every section)
- Search ReactBits BEFORE writing custom effects
- Text sections: text reveal/blur/split components
- CTA: magnetic button, spotlight button
- Cards: tilt card, spotlight card
- Backgrounds: aurora, spotlight, gradient
- Copy source from get_component into components/ directory

## Content & Image Rules
- Every heading, name, description from brand data — never invented
- **Prefer real photos** from the prospect's existing site over AI-generated images
- Use extracted image URLs for galleries, features, parallax, about sections — wherever they contextually fit
- Only use Nano Banana for hero keyframes, transition keyframes, and abstract atmosphere where no real photo works
- Don't force a real photo into a section where it doesn't make sense (food photo ≠ CTA background)
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
