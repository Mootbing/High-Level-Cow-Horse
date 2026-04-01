# Immersive Website Generation Reference

This is the master prompt for building award-winning, immersive client websites.
Every site built by Clarmi should feel like an Awwwards finalist — cinematic scroll experiences,
3D elements, scroll-controlled video, and micro-interactions that make visitors say "wow".

## The Clarmi Formula

**Every Clarmi site follows this structure — no exceptions:**

1. **Hero** = Scroll-controlled video (Nano Banana keyframes → Veo 3.1 first+last frame). Plays frame-by-frame as user scrolls.
2. **Rest of site** = Three.js persistent 3D scene + ReactBits animated components + GSAP smooth scroll animations in every section.

**The only decision is the AESTHETIC, not the architecture:**

| Brand Personality | Hero Keyframes | Three.js Scene Style | ReactBits Focus |
|-------------------|---------------|---------------------|-----------------|
| **Premium/Luxury** | Glass surfaces, architectural | Glass geometric, ChromaticAberration | Spotlight cards, magnetic buttons |
| **Warm/Inviting** | Organic textures, golden hour | Warm floating particles, soft bloom | Blur text reveals, aurora backgrounds |
| **Bold/Creative** | High contrast, dramatic angles | Abstract geometry, heavy bloom | Text scramble, tilt cards |
| **Tech/Modern** | Data streams, neon wireframes | Wireframe networks, neon bloom | Counter animations, grid reveals |

**Scroll depth**: Standard (5-6 sections) → Hero + TextReveal + Features + CTA + Footer. Cinematic (7-8) → Add ScrollTransition + Parallax + HorizontalScroll.

## The Scroll Story

Every Clarmi site tells a story through scroll. The user isn't just reading a webpage —
they're experiencing a narrative arc:

1. **Hook** (Hero) — Immediate visual impact. The visitor decides in 3 seconds if they'll stay.
2. **Context** (Text Reveal / Transition) — "Here's what this business is about." Breathing room.
3. **Proof** (Features / Gallery) — "Here's what they offer and why it's great." Show, don't tell.
4. **Trust** (Stats / Testimonials) — "Others trust them too." Social proof.
5. **Action** (CTA) — "Your turn." Clear, easy, compelling.

Every section serves one of these story beats. If a section doesn't serve the narrative, cut it.

## Tech Stack

- **Next.js 15** App Router, TypeScript
- **Tailwind CSS** for layout/utility styling
- **GSAP + ScrollTrigger** for scroll-driven animations (pin, scrub, stagger, timeline)
- **Lenis** for buttery smooth scrolling
- **React Three Fiber (@react-three/fiber)** for 3D scenes
- **@react-three/drei** for helpers (ScrollControls, useScroll, Float, MeshTransmissionMaterial, Environment)
- **@react-three/postprocessing** for cinematic post-processing (Bloom, ChromaticAberration, Vignette, Noise)
- **Three.js** directly when R3F abstractions aren't enough
- **Framer Motion** for layout animations and page transitions

## Architecture Pattern

```
app/
  layout.tsx          ← Google Fonts, metadata, SmoothScroller wrapper
  page.tsx            ← Section composition: ScrollVideo hero → Scene3D + content sections
  globals.css         ← Tailwind imports + custom properties + scroll utilities
components/
  SmoothScroller.tsx  ← Lenis initialization + GSAP ticker sync
  Hero.tsx            ← Scroll-controlled video hero (keyframe A→B via Veo 3.1)
  Scene3D.tsx         ← Persistent Three.js canvas behind content sections (dynamic import, SSR: false)
  ScrollVideo.tsx     ← Scroll-controlled video player (pin + scrub video.currentTime)
  TransitionSection.tsx ← Pinned section with video/CSS-crossfade transition between states
  TextReveal.tsx      ← Word-by-word scroll reveal (check ReactBits first)
  ParallaxSection.tsx ← Multi-layer parallax depth section
  Features.tsx        ← Staggered card entrance (ReactBits tilt/spotlight cards)
  CTA.tsx             ← ReactBits magnetic button + aurora/gradient background
  Footer.tsx          ← Footer with stagger-in animation
  [ReactBits]/        ← Components copied from ReactBits (text anims, backgrounds, buttons)
```

## Section Playbook

Every site is composed of 5-8 sections. Pick from this playbook based on the business type and content available.

### 1. Hero Section (REQUIRED — always first — ALWAYS scroll video)

Every Clarmi hero uses scroll-controlled video generated from two Nano Banana keyframes via Veo 3.1 first+last frame mode. The video plays frame-by-frame as the user scrolls — not autoplay.

**How the hero video is created:**
1. Nano Banana generates **keyframe A** (opening visual state — what visitors see on page load)
2. Nano Banana generates **keyframe B** (ending visual state — what they see after scrolling through)
3. Veo 3.1 generates a smooth transition video between A and B using first+last frame mode
4. The video is embedded as scroll-controlled `<video>` — `video.currentTime` mapped to scroll progress

**Hero structure:**
- Full-viewport video that plays on scroll (not autoplay)
- `video.currentTime` mapped to scroll progress via GSAP ScrollTrigger scrub
- Pinned for 2-3x viewport height so the video plays through as user scrolls
- Text overlays appear/disappear at specific scroll progress points
- Poster image = keyframe A (instant visual before video loads)
- Mobile fallback = keyframe A as static image (iOS restricts video.currentTime)

```tsx
// ScrollVideo pattern — pin section, scrub video.currentTime
'use client'
import { useEffect, useRef } from 'react'
import gsap from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'
gsap.registerPlugin(ScrollTrigger)

export default function ScrollVideo({ src, poster }: { src: string; poster?: string }) {
  const videoRef = useRef<HTMLVideoElement>(null)
  const sectionRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const video = videoRef.current
    const section = sectionRef.current
    if (!video || !section) return

    // Wait for video metadata to load
    const onLoaded = () => {
      ScrollTrigger.create({
        trigger: section,
        start: 'top top',
        end: `+=${window.innerHeight * 3}`,
        pin: true,
        scrub: 0.5,
        onUpdate: (self) => {
          if (video.duration) {
            video.currentTime = video.duration * self.progress
          }
        },
      })
    }

    video.addEventListener('loadedmetadata', onLoaded)
    return () => {
      video.removeEventListener('loadedmetadata', onLoaded)
      ScrollTrigger.getAll().forEach(t => t.kill())
    }
  }, [])

  return (
    <div ref={sectionRef} className="relative h-screen w-full overflow-hidden">
      <video
        ref={videoRef}
        src={src}
        poster={poster}
        muted playsInline preload="auto"
        className="absolute inset-0 w-full h-full object-cover"
      />
    </div>
  )
}
```

**Fallback (when video generation fails):** The tool returns keyframe A + B images. Use CSS crossfade on scroll instead — still scroll-controlled, just images crossfading instead of video frames:

```tsx
// CSS crossfade fallback when no video available
<div ref={sectionRef} className="relative h-screen w-full overflow-hidden">
  <img src={keyframeA} className="absolute inset-0 w-full h-full object-cover" style={{ opacity: 1 - progress }} />
  <img src={keyframeB} className="absolute inset-0 w-full h-full object-cover" style={{ opacity: progress }} />
</div>
```

### 2. Scroll Transition Section (between hero and content)

A pinned section where a Veo-generated transition video plays on scroll, visually morphing from the hero aesthetic to the content aesthetic.

- Uses `generate_transition_video()` to create the A→B video
- Section is pinned for 2x viewport height
- Video scrubs from frame 0 to final frame as user scrolls through
- At 0% progress: shows keyframe A (matches hero)
- At 100% progress: shows keyframe B (matches next section)
- Overlaid text fades in at ~60% progress introducing the next section

### 3. Text Reveal Section

Large statement text that reveals word-by-word as the user scrolls.

```tsx
// Split text into words, animate each on scroll
const words = text.split(' ')
words.forEach((word, i) => {
  gsap.fromTo(wordEl, 
    { opacity: 0.1, filter: 'blur(4px)' },
    {
      opacity: 1, filter: 'blur(0px)',
      scrollTrigger: {
        trigger: wordEl,
        start: 'top 85%',
        end: 'top 50%',
        scrub: true,
      }
    }
  )
})
```

Best for: mission statements, value propositions, brand stories.

### 4. Parallax Depth Section

Multi-layer parallax with 3-5 depth layers moving at different scroll speeds.

- Background layer: moves slowest (0.2x scroll speed)
- Midground: images/decorative elements at 0.5x
- Foreground: content cards at 1x (normal)
- Optional: floating 3D elements at 1.3x (move faster than scroll)

```tsx
// Multi-layer parallax via GSAP ScrollTrigger
layers.forEach(({ element, speed }) => {
  gsap.to(element, {
    y: () => -ScrollTrigger.maxScroll(window) * speed,
    ease: 'none',
    scrollTrigger: { start: 0, end: 'max', scrub: 0.3 },
  })
})
```

### 5. Feature Cards with Stagger

Cards that enter the viewport with staggered animation.

- Cards scale from 0.9 → 1, opacity 0 → 1, y 60 → 0
- Stagger: 0.1s between each card
- On hover: card lifts (translateY -8px), subtle shadow expansion
- Optional: 3D tilt effect on hover using CSS perspective + rotateX/Y

### 6. Horizontal Scroll Section

A pinned section that scrolls content horizontally while the user scrolls vertically.

```tsx
// GSAP horizontal scroll
gsap.to(scrollContainer, {
  x: () => -(scrollContainer.scrollWidth - window.innerWidth),
  ease: 'none',
  scrollTrigger: {
    trigger: section,
    start: 'top top',
    end: () => `+=${scrollContainer.scrollWidth - window.innerWidth}`,
    pin: true,
    scrub: 1,
  },
})
```

Best for: portfolios, service showcases, timelines.

### 7. Persistent Three.js Scene (REQUIRED — runs behind content sections)

A single React Three Fiber canvas that renders behind ALL content sections (not the hero — the hero uses scroll video). The 3D scene provides ambient visual depth throughout the page.

- **ALWAYS** `dynamic(() => import('./Scene3D'), { ssr: false })` — NEVER server-render
- Single Canvas positioned `fixed` or `absolute` behind content sections
- 3D elements respond to scroll position: objects rotate, scale, morph, change material as user scrolls through different sections
- Pick scene style from the industry table in `templates/prompts/three-js-scene.md`
- Scene fades in as the hero video scrolls out (opacity transition)
- Mobile: show static fallback image on `< 768px`

**How to integrate with sections:**
- Canvas sits behind content with `z-index: 0`
- Content sections have semi-transparent or transparent backgrounds so 3D shows through
- Use GSAP ScrollTrigger to animate 3D properties (rotation, scale, color) as user scrolls past each section
- Particles/floating shapes provide ambient motion even when content is static

### 8. CTA Section

- Background: ReactBits aurora/spotlight/gradient component + Three.js accent elements showing through
- Magnetic button: use ReactBits magnetic button component (search "magnetic")
- On click: particle burst animation (confetti or sparkles)

## Animation Rules

### GPU-Only Properties
ONLY animate these properties — everything else triggers layout/paint:
- `transform` (translate, scale, rotate, skew)
- `opacity`
- `filter` (blur, brightness — use sparingly, can be expensive)
- `clip-path` (for reveal effects)

### Easing
- Entrances: `power3.out` or `cubic-bezier(0.16, 1, 0.3, 1)` — fast start, gentle land
- Exits: `power2.in` — gentle start, quick exit
- Scrub animations: `'none'` (linear) — scroll position IS the easing
- Elastic/bounce: `elastic.out(1, 0.3)` — ONLY for playful brands (restaurants, entertainment)

### Timing
- Entrance animations: 0.8-1.2s duration
- Stagger delay: 0.08-0.15s between elements
- Scrub smoothness: `scrub: 0.3` to `scrub: 1` (higher = smoother but laggier)
- Hold scroll-pinned sections for 2-3x viewport height (feel, don't rush)

### Mobile Rules
- Disable Three.js canvas on `(max-width: 768px)` — show static image fallback
- Reduce parallax intensity by 50% on mobile
- Disable custom cursor on touch devices
- Use `will-change: transform` on animated elements (remove after animation)
- Reduce particle counts by 75% on mobile
- Test with Chrome DevTools throttled to 4x CPU slowdown

## Three.js Persistent Scene by Industry

The Three.js scene runs behind ALL content sections (not the hero — the hero uses scroll video). Pick the scene style based on industry. The 3D elements provide ambient visual depth and respond to scroll position.

| Industry | Persistent Scene Style | Materials | Lighting | Post-Processing |
|----------|----------------------|-----------|----------|-----------------|
| Restaurant/Food | Floating warm particles, organic spheres | Standard, warm colors | Warm point lights, soft shadows | Bloom (warm), subtle grain |
| Law/Finance | Glass geometric forms, monolithic | MeshPhysicalMaterial (glass, transmission) | Cool directional, rim light | ChromaticAberration, Vignette |
| Salon/Beauty | Fluid shapes, iridescent | MeshTransmissionMaterial, iridescence | Soft pink/purple point lights | Bloom, soft ChromaticAberration |
| Tech/SaaS | Wireframe, data nodes, grids | MeshBasicMaterial (wireframe) | Neon point lights | Bloom (high), scanline grain |
| Real Estate | Architectural forms, golden light | MeshStandardMaterial | Golden hour directional | Bloom, warm color grade |
| Retail | Product-like forms, studio lighting | MeshPhysicalMaterial (clearcoat) | 3-point studio lighting | Subtle bloom, SSAO |
| Healthcare | Soft organic, molecular | MeshPhysicalMaterial (subsurface) | Clean white, soft fill | Minimal — clean and medical |
| Creative/Agency | Abstract, bold geometry | Mix of glass + matte | Dramatic colored lights | Heavy bloom, chromatic |

## Scroll-Controlled Video Pipeline

Every Clarmi site uses scroll-controlled video. The pipeline is always:
**Nano Banana (keyframe A) + Nano Banana (keyframe B) → Veo 3.1 first+last frame → scroll scrub**

1. **Hero video** (ALWAYS): keyframe A (page load state) + keyframe B (scroll end state) → Veo 3.1 transition → full-screen, pinned, scrub through on scroll
2. **Section transitions**: Pin between two sections, A→B morph scrub via same keyframe pipeline
3. **Fallback**: If video generation fails, crossfade between keyframe A and B images on scroll

### Video Encoding Requirements
- **Format**: MP4 with H.264 codec (widest browser support for seeking)
- **Resolution**: 1920x1080 (scale down for mobile with `<source>` + media query)
- **Duration**: 4-8 seconds (mapped to 2-3 viewport heights of scroll)
- **Keyframes**: Every 1 second (enables precise seeking without decode lag)

### Fallback Strategy
- **Desktop**: Full scroll-controlled video playback
- **Tablet**: Scroll-controlled video with reduced resolution
- **Mobile**: Static keyframe image with CSS crossfade transition on scroll
- **Slow connection**: Show poster image immediately, progressive load video

```tsx
// Responsive video with mobile fallback
const isMobile = typeof window !== 'undefined' && window.innerWidth < 768

{isMobile ? (
  <img src={keyframeA} className="absolute inset-0 w-full h-full object-cover" />
) : (
  <video ref={videoRef} muted playsInline preload="auto" poster={keyframeA}>
    <source src={videoSrc} type="video/mp4" />
  </video>
)}
```

## Micro-Interaction Catalog

### Magnetic Button
```tsx
const onMouseMove = (e: React.MouseEvent) => {
  const rect = buttonRef.current!.getBoundingClientRect()
  const x = e.clientX - rect.left - rect.width / 2
  const y = e.clientY - rect.top - rect.height / 2
  gsap.to(buttonRef.current, { x: x * 0.3, y: y * 0.3, duration: 0.3, ease: 'power2.out' })
}
const onMouseLeave = () => {
  gsap.to(buttonRef.current, { x: 0, y: 0, duration: 0.5, ease: 'elastic.out(1, 0.3)' })
}
```

### Text Scramble Effect
```tsx
// Reveal text with random character cycling before settling
const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%'
function scramble(el: HTMLElement, finalText: string) {
  let iteration = 0
  const interval = setInterval(() => {
    el.textContent = finalText.split('').map((char, i) => {
      if (i < iteration) return char
      return chars[Math.floor(Math.random() * chars.length)]
    }).join('')
    if (iteration >= finalText.length) clearInterval(interval)
    iteration += 1 / 3
  }, 30)
}
```

### Smooth Counter
```tsx
// Number counter that animates from 0 to target on scroll entry
gsap.from(counterEl, {
  textContent: 0,
  duration: 2,
  ease: 'power1.out',
  snap: { textContent: 1 },
  scrollTrigger: { trigger: counterEl, start: 'top 80%' },
})
```

### Image Reveal with Clip-Path
```tsx
// Image slides in with a clip-path wipe
gsap.from(imageEl, {
  clipPath: 'inset(0 100% 0 0)', // hidden from right
  duration: 1.2,
  ease: 'power3.inOut',
  scrollTrigger: { trigger: imageEl, start: 'top 75%' },
})
```

### Cursor Trail (desktop only)
```tsx
// Lightweight custom cursor with trailing dots
'use client'
import { useEffect, useRef } from 'react'
// Only render on non-touch devices
// Use mix-blend-mode: difference for the cursor dot
// Trail: 5-8 dots with decreasing opacity, each lerping toward cursor position
```

## Performance Budget

| Metric | Target | Critical Threshold |
|--------|--------|--------------------|
| LCP | < 2.5s | < 4.0s |
| FID | < 100ms | < 300ms |
| CLS | < 0.1 | < 0.25 |
| Three.js bundle | < 200KB gzipped | < 350KB |
| Total JS | < 500KB gzipped | < 800KB |
| Video assets | < 5MB per video | < 10MB |
| Lighthouse perf | > 85 | > 70 |

### Performance Techniques
1. **Dynamic import** all Three.js components: `dynamic(() => import('./Scene'), { ssr: false })`
2. **Suspense boundary** around 3D canvas with skeleton/placeholder
3. **Intersection Observer** to mount/unmount 3D scenes when off-screen
4. **requestAnimationFrame** budget: aim for < 16ms per frame
5. **Texture compression**: use WebP for textures, MP4 H.264 Baseline for video
6. **GPU detection**: if `renderer.capabilities.maxTextureSize < 4096`, reduce quality
7. **Dispose everything**: dispose geometries, materials, textures in cleanup return

## Accessibility & Reduced Motion

ALWAYS respect `prefers-reduced-motion`. Immersive doesn't mean inaccessible.

```css
/* globals.css — reduced motion override */
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.2s !important;
    scroll-behavior: auto !important;
  }
}
```

```tsx
// In any component with GSAP animations
useEffect(() => {
  const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches
  if (prefersReduced) return // Skip all scroll animations

  // ... GSAP animations here ...
}, [])
```

### Accessibility checklist
- All images have descriptive `alt` text (or `alt=""` for decorative)
- 3D canvas has `role="img"` and `aria-label` describing the visual
- Video has no audio (muted) — no caption needed for decorative video
- Focus is never trapped by scroll-pinned sections
- All interactive elements are keyboard-accessible
- Color contrast ratio >= 4.5:1 for all text
- Skip-to-content link at top of page

## Common Pitfalls & Fixes

| Symptom | Cause | Fix |
|---------|-------|-----|
| White flash before 3D loads | No Suspense fallback | Add loading placeholder matching bg color |
| Scroll feels "stuck" | Pin section too long | Reduce scroll length to 2-3x viewport |
| Jittery scroll on mobile | Lenis + ScrollTrigger conflict | Use `touchMultiplier: 2` in Lenis config |
| 3D scene black on some devices | Missing environment/lights | Always include `<Environment>` + ambient light |
| Video shows black while scrubbing | Sparse keyframes in video | Re-encode with `-g 2` (keyframe every 2 frames) |
| Lighthouse perf < 70 | Three.js loaded eagerly | Use Intersection Observer to lazy-mount canvas |
| Hydration mismatch error | Three.js running on server | MUST use `dynamic(() => import(...), { ssr: false })` |
| `overflow: hidden` breaks scroll | CSS overflow on body | Never set overflow hidden on html/body |
| Parallax elements jump | ScrollTrigger not synced | Must call `lenis.on('scroll', ScrollTrigger.update)` |

## Image Sourcing Priority

**Real photos from the prospect's site FIRST, AI-generated images LAST.**

During research, image URLs are extracted from the prospect's existing site. These are authentic photos of the actual business — food, products, team, space. Use them wherever they contextually fit:

| Image Type | Best Placement |
|-----------|---------------|
| Food/dish photos | Menu section, parallax gallery, feature cards |
| Team/staff photos | About section, testimonials |
| Interior/space photos | Parallax backgrounds, gallery |
| Product photos | Feature cards, horizontal scroll |
| Exterior/storefront | Parallax background, about section |

**Only use `generate_image` (Nano Banana) for:**
- Hero video keyframes (abstract opening + ending visual states)
- Transition keyframes (abstract A→B morph states)
- Abstract atmospheric backgrounds where no real photo fits

**Never force a real photo into a section where it doesn't contextually belong** — a food photo shouldn't be a CTA background, a team photo shouldn't be in a menu grid.

## DO NOT

- Use Three.js on mobile viewports (< 768px) — always provide image fallback
- Create more than one Three.js Canvas per page (reuse a single canvas)
- Autoplay video with sound — always muted
- Use `position: fixed` for parallax (use `transform: translate3d` instead)
- Animate `width`, `height`, `top`, `left`, `margin`, `padding` — GPU-only properties
- Create scroll-pinned sections longer than 4x viewport height (feels stuck)
- Use more than 2 post-processing effects simultaneously (perf killer)
- Skip the video poster/fallback image (shows black flash otherwise)
- Forget `will-change: transform` on scroll-animated elements
- Use `overflow: hidden` on the body (breaks smooth scroll)
- Skip the `prefers-reduced-motion` check — always respect user preference
- Use `cursor: none` globally — only hide default cursor if custom cursor component is active
