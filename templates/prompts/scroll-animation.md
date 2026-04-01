# Scroll Animation Patterns

Complete reference for scroll-driven animations. All patterns use GSAP + ScrollTrigger + Lenis.
For advanced effects (3D, video), see `three-js-scene.md` and `scroll-video-section.md`.

## Setup (required in every project)

```tsx
// SmoothScroller.tsx — must wrap all page content
'use client'
import { useEffect } from 'react'
import Lenis from '@studio-freight/lenis'
import gsap from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'
gsap.registerPlugin(ScrollTrigger)

export default function SmoothScroller({ children }: { children: React.ReactNode }) {
  useEffect(() => {
    const lenis = new Lenis({ duration: 1.2, easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)) })
    lenis.on('scroll', ScrollTrigger.update)
    gsap.ticker.add((time) => lenis.raf(time * 1000))
    gsap.ticker.lagSmoothing(0)
    return () => { lenis.destroy(); gsap.ticker.remove(lenis.raf) }
  }, [])
  return <>{children}</>
}
```

## CSS-Native Scroll Animations (Progressive Enhancement)

Modern browsers support CSS `animation-timeline: scroll()` which runs on the compositor
thread — zero JS overhead. Use for simple fade/slide effects, with GSAP for complex sequences.

```css
/* Fade-in on scroll (CSS-only — Chrome/Edge 115+, Safari 18+) */
.scroll-fade {
  animation: scrollFadeIn linear both;
  animation-timeline: view();
  animation-range: entry 0% entry 100%;
}
@keyframes scrollFadeIn {
  from { opacity: 0; transform: translateY(40px); }
  to { opacity: 1; transform: translateY(0); }
}
```

Use CSS scroll animations for simple entrance effects. Use GSAP for anything requiring:
pin, scrub, timeline sequencing, stagger, or complex choreography.

## GSAP Pattern Catalog

### 1. Scrub Animation (tied to scroll position)
```tsx
gsap.to(element, {
  scrollTrigger: { trigger, start: 'top top', end: 'bottom top', scrub: 0.3 },
  y: -100, opacity: 0.3, scale: 1.05
})
```

### 2. Toggle Animation (play on enter, reverse on leave)
```tsx
gsap.from(element, {
  scrollTrigger: { trigger, start: 'top 80%', toggleActions: 'play none none reverse' },
  y: 60, opacity: 0, duration: 1, ease: 'power3.out'
})
```

### 3. Staggered Entrance (cards, grid items, list items)
```tsx
gsap.from(elements, {
  y: 40, opacity: 0, scale: 0.95, stagger: 0.12, duration: 0.8,
  ease: 'power3.out',
  scrollTrigger: { trigger: container, start: 'top 75%' }
})
```

### 4. Multi-Speed Parallax (depth layers)
```tsx
[
  { el: bgLayer, speed: 0.15 },    // Slow background
  { el: midLayer, speed: 0.4 },    // Medium
  { el: fgLayer, speed: 0.7 },     // Foreground
  { el: floatLayer, speed: 1.1 },  // Faster than scroll
].forEach(({ el, speed }) => {
  gsap.to(el, {
    y: () => -(ScrollTrigger.maxScroll(window) * speed * 0.2),
    ease: 'none',
    scrollTrigger: { start: 0, end: 'max', scrub: 0.3 },
  })
})
```

### 5. Word-by-Word Text Reveal
```tsx
words.forEach((wordEl) => {
  gsap.fromTo(wordEl,
    { opacity: 0.1, filter: 'blur(4px)' },
    {
      opacity: 1, filter: 'blur(0px)', ease: 'none',
      scrollTrigger: { trigger: wordEl, start: 'top 85%', end: 'top 50%', scrub: true }
    }
  )
})
```

### 6. Pin + Timeline Sequence (cinematic scroll section)
```tsx
const tl = gsap.timeline({
  scrollTrigger: {
    trigger: section, start: 'top top', end: '+=300%', pin: true, scrub: 0.5
  }
})
tl.to(heading, { opacity: 1, y: 0, duration: 0.3 })
  .to(paragraph, { opacity: 1, y: 0, duration: 0.3 }, '+=0.1')
  .to(image, { scale: 1, clipPath: 'inset(0 0% 0 0)', duration: 0.4 }, '+=0.1')
  .to(heading, { opacity: 0, y: -50, duration: 0.3 }, '+=0.3')
  .to(nextContent, { opacity: 1, y: 0, duration: 0.3 })
```

### 7. Horizontal Scroll Section
```tsx
const totalScroll = container.scrollWidth - window.innerWidth
gsap.to(container, {
  x: -totalScroll, ease: 'none',
  scrollTrigger: {
    trigger: section, start: 'top top',
    end: () => `+=${totalScroll}`,
    pin: true, scrub: 1, invalidateOnRefresh: true
  }
})
```

### 8. Scroll-Controlled Video Playback
```tsx
ScrollTrigger.create({
  trigger: section, start: 'top top', end: '+=300%',
  pin: true, scrub: 0.5,
  onUpdate: (self) => {
    if (video.duration) video.currentTime = video.duration * self.progress
  }
})
```

### 9. Image Reveal with Clip-Path
```tsx
gsap.from(imageEl, {
  clipPath: 'inset(0 100% 0 0)',   // Wipe from left
  duration: 1.2, ease: 'power3.inOut',
  scrollTrigger: { trigger: imageEl, start: 'top 75%' }
})
// Variants: 'inset(100% 0 0 0)' bottom, 'circle(0% at 50% 50%)' center expand
```

### 10. SVG Path Draw
```tsx
const length = path.getTotalLength()
gsap.set(path, { strokeDasharray: length, strokeDashoffset: length })
gsap.to(path, {
  strokeDashoffset: 0, ease: 'none',
  scrollTrigger: { trigger: svg, start: 'top 60%', end: 'bottom 40%', scrub: true }
})
```

### 11. Counter Animation
```tsx
gsap.from(counterEl, {
  textContent: 0, duration: 2, ease: 'power1.out',
  snap: { textContent: 1 },
  scrollTrigger: { trigger: counterEl, start: 'top 80%' }
})
```

### 12. 3D Scene + Scroll (React Three Fiber)
```tsx
// Camera path driven by scroll position
import { useScroll } from '@react-three/drei'
function ScrollCamera() {
  const scroll = useScroll()
  const path = useMemo(() => new THREE.CatmullRomCurve3([
    new THREE.Vector3(0, 0, 5), new THREE.Vector3(3, 1, 3),
    new THREE.Vector3(0, 2, 2), new THREE.Vector3(-2, 0, 4)
  ]), [])
  useFrame(({ camera }) => {
    camera.position.copy(path.getPointAt(scroll.offset))
    camera.lookAt(0, 0, 0)
  })
  return null
}
```

## Easing Reference

| Use Case | Easing | GSAP Value |
|----------|--------|------------|
| Element enters viewport | Fast start, soft land | `power3.out` |
| Element exits viewport | Gentle start, quick exit | `power2.in` |
| Scroll-scrubbed | Linear | `'none'` |
| Button spring-back | Elastic overshoot | `elastic.out(1, 0.3)` |
| Smooth transitions | S-curve | `power3.inOut` |
| Playful/bouncy | Bounce | `bounce.out` |

## Cleanup Pattern (ALWAYS include)

```tsx
useEffect(() => {
  // ... create animations ...
  return () => ScrollTrigger.getAll().forEach(t => t.kill())
}, [])
```

## Performance Rules

- Only animate: `transform`, `opacity`, `filter`, `clip-path`
- Scrub: 0.3-1 (lower = responsive, higher = smoother)
- Pin: max 4x viewport height
- Mobile: reduce parallax 50%, disable complex effects
- Always: `@media (prefers-reduced-motion: reduce)` support
