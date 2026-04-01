# Responsive Design Patterns for Immersive Sites

Immersive effects must degrade gracefully. The desktop experience is cinematic;
the mobile experience should still feel premium but prioritize usability and performance.

## Breakpoint Strategy

```css
/* Mobile first — then progressively enhance */
/* Base: 0-767px (mobile) */
/* md: 768-1023px (tablet) */
/* lg: 1024-1439px (laptop) */
/* xl: 1440px+ (desktop) */
```

## Device-Tier Feature Matrix

| Feature | Mobile (< 768px) | Tablet (768-1023px) | Desktop (1024px+) |
|---------|:-:|:-:|:-:|
| Three.js 3D scene | Static image | Simplified scene | Full scene + post-processing |
| Scroll video | Poster image | Video (auto-plays, not scrubbed) | Scroll-scrubbed video |
| Parallax layers | Disabled | 2 layers, 50% intensity | 4-5 layers, full intensity |
| Custom cursor | Disabled | Disabled | Enabled |
| Horizontal scroll | Vertical stack | Vertical stack | Horizontal scroll |
| Pinned sections | Unpinned | Pinned (shorter duration) | Pinned (full duration) |
| Particle effects | Disabled | 25% count | Full count |
| Shader backgrounds | CSS gradient | CSS gradient | WebGL shader |
| Post-processing | None | 1 effect | 2 effects max |
| Card hover tilt | Disabled | Disabled | 3D tilt active |
| Text scramble | Instant reveal | Instant reveal | Full animation |
| Stagger animations | Simpler (y only) | Full stagger | Full stagger |

## Implementation Patterns

### Mobile Detection Hook
```tsx
'use client'
import { useState, useEffect } from 'react'

interface DeviceTier {
  isMobile: boolean   // < 768px or touch
  isTablet: boolean   // 768-1023px
  isDesktop: boolean  // 1024px+
  isTouch: boolean    // touch device
  tier: 'mobile' | 'tablet' | 'desktop'
}

export function useDeviceTier(): DeviceTier {
  const [device, setDevice] = useState<DeviceTier>({
    isMobile: true, isTablet: false, isDesktop: false,
    isTouch: true, tier: 'mobile',
  })

  useEffect(() => {
    const update = () => {
      const w = window.innerWidth
      const touch = 'ontouchstart' in window || navigator.maxTouchPoints > 0
      const mobile = w < 768 || (touch && w < 1024)
      const tablet = !mobile && w < 1024
      const desktop = w >= 1024

      setDevice({
        isMobile: mobile, isTablet: tablet, isDesktop: desktop,
        isTouch: touch,
        tier: mobile ? 'mobile' : tablet ? 'tablet' : 'desktop',
      })
    }

    update()
    window.addEventListener('resize', update)
    return () => window.removeEventListener('resize', update)
  }, [])

  return device
}
```

### Responsive Hero
```tsx
export default function Hero({ videoSrc, posterSrc, mobileFallback }: HeroProps) {
  const { tier, isTouch } = useDeviceTier()

  return (
    <section className="relative min-h-screen">
      {tier === 'desktop' && !isTouch ? (
        // Full 3D scene or scroll video
        <ScrollVideo src={videoSrc} poster={posterSrc} scrollLength={3} />
      ) : tier === 'tablet' ? (
        // Autoplay video (not scroll-controlled)
        <video autoPlay muted loop playsInline poster={posterSrc}
          className="absolute inset-0 w-full h-full object-cover">
          <source src={videoSrc} type="video/mp4" />
        </video>
      ) : (
        // Static image on mobile
        <img src={mobileFallback} alt=""
          className="absolute inset-0 w-full h-full object-cover" />
      )}
      {/* Content overlays work at all sizes */}
    </section>
  )
}
```

### Responsive Parallax
```tsx
export default function ParallaxSection({ children, images }: ParallaxProps) {
  const { tier } = useDeviceTier()

  useEffect(() => {
    if (tier === 'mobile') return // No parallax on mobile

    const intensity = tier === 'tablet' ? 0.5 : 1.0

    layers.forEach(({ el, speed }) => {
      gsap.to(el, {
        y: () => -(ScrollTrigger.maxScroll(window) * speed * 0.2 * intensity),
        ease: 'none',
        scrollTrigger: { start: 0, end: 'max', scrub: 0.3 },
      })
    })

    return () => ScrollTrigger.getAll().forEach(t => t.kill())
  }, [tier])

  return (
    <section className="relative">
      {/* On mobile: simple vertical stack. Desktop: parallax layers */}
      {tier === 'mobile' ? (
        <div className="space-y-8 px-6">{children}</div>
      ) : (
        <div className="relative" style={{ height: '150vh' }}>
          {/* Parallax layers */}
        </div>
      )}
    </section>
  )
}
```

### Responsive Pinned Sections
```tsx
useEffect(() => {
  if (tier === 'mobile') return // No pin on mobile

  const scrollLength = tier === 'tablet' ? 2 : 3 // Shorter pin on tablet

  ScrollTrigger.create({
    trigger: sectionRef.current,
    start: 'top top',
    end: `+=${window.innerHeight * scrollLength}`,
    pin: true,
    scrub: 0.5,
    onUpdate: (self) => { /* ... */ },
  })

  return () => ScrollTrigger.getAll().forEach(t => t.kill())
}, [tier])
```

### Responsive Horizontal Scroll → Vertical Stack
```tsx
export default function ServicesSection({ services }: Props) {
  const { tier } = useDeviceTier()

  if (tier === 'mobile' || tier === 'tablet') {
    return (
      <section className="py-20 px-6">
        <div className="space-y-12">
          {services.map((s) => <ServiceCard key={s.id} {...s} />)}
        </div>
      </section>
    )
  }

  // Desktop: horizontal scroll
  return (
    <section ref={sectionRef} className="relative h-screen overflow-hidden">
      <div ref={containerRef} className="flex h-full items-center gap-8 px-16" 
           style={{ width: `${services.length * 400 + 200}px` }}>
        {services.map((s) => <ServiceCard key={s.id} {...s} />)}
      </div>
    </section>
  )
}
```

## Typography Scaling

```css
/* Fluid typography using clamp() — works at ALL viewport sizes */
:root {
  --text-hero: clamp(2.5rem, 8vw, 6rem);     /* Hero headline */
  --text-h1: clamp(2rem, 5vw, 4rem);          /* Section headings */
  --text-h2: clamp(1.5rem, 3.5vw, 2.5rem);    /* Sub-headings */
  --text-h3: clamp(1.25rem, 2.5vw, 1.75rem);  /* Card headings */
  --text-body: clamp(0.875rem, 1.5vw, 1.125rem); /* Body text */
  --text-small: clamp(0.75rem, 1vw, 0.875rem);   /* Captions */

  --space-section: clamp(4rem, 12vh, 10rem);   /* Between sections */
  --space-content: clamp(1.5rem, 4vw, 4rem);   /* Content padding */
}
```

## Touch Interaction Adjustments

```tsx
// Hover effects should not rely on :hover alone on touch
// Use this pattern for cards with hover effects:
<div
  className="group cursor-pointer transition-all duration-300
    hover:scale-[1.02] hover:shadow-xl active:scale-[0.98]
    md:hover:scale-[1.03]"
>
  {/* active:scale for touch feedback, hover:scale for mouse */}
</div>
```

## Image Optimization by Viewport

```tsx
// Use Next.js Image with responsive sizes
import Image from 'next/image'

<Image
  src={imageSrc}
  alt={imageAlt}
  fill
  sizes="(max-width: 768px) 100vw, (max-width: 1024px) 50vw, 33vw"
  priority={isAboveFold}
  quality={75}
  className="object-cover"
/>
```

For prospect images (external URLs), use regular `<img>` with loading="lazy":
```tsx
<img
  src={prospectImageUrl}
  alt={description}
  loading={isAboveFold ? 'eager' : 'lazy'}
  decoding="async"
  className="w-full h-full object-cover"
/>
```

## Testing Checklist

Before deploying, test at these viewports:
- [ ] 375px (iPhone SE) — all content readable, no horizontal overflow
- [ ] 390px (iPhone 14) — hero image looks good, CTA accessible
- [ ] 768px (iPad) — tablet layout active, video auto-plays
- [ ] 1024px (iPad landscape/laptop) — desktop features enable
- [ ] 1440px (desktop) — full immersive experience active
- [ ] 1920px (large desktop) — nothing stretches or breaks

Test with:
- [ ] Chrome DevTools device emulation
- [ ] Throttle CPU to 4x to catch animation perf issues
- [ ] `prefers-reduced-motion: reduce` simulation in DevTools
