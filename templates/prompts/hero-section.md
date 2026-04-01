# Hero Section Generation Reference

The hero is the first thing visitors see — it must be cinematic, immersive, and instant.
Choose one of three approaches based on the prospect's industry and brand personality.

## Hero Types

### Option A: 3D Scene Hero

Best for: tech, professional services, luxury, creative agencies, beauty/spa

A full-viewport React Three Fiber canvas renders behind the headline. The 3D object
responds to mouse movement and dissolves/transforms on scroll.

```tsx
// Hero.tsx
'use client'
import { useEffect, useRef, useState } from 'react'
import dynamic from 'next/dynamic'
import gsap from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'

gsap.registerPlugin(ScrollTrigger)

const Scene3D = dynamic(() => import('@/components/Scene3D'), {
  ssr: false,
  loading: () => null,
})

export default function Hero() {
  const heroRef = useRef<HTMLElement>(null)
  const contentRef = useRef<HTMLDivElement>(null)
  const canvasWrapRef = useRef<HTMLDivElement>(null)
  const [isMobile, setIsMobile] = useState(true) // SSR-safe default

  useEffect(() => {
    setIsMobile(window.innerWidth < 768 || 'ontouchstart' in window)
  }, [])

  // Scroll: fade out hero content + scale down 3D scene
  useEffect(() => {
    if (!heroRef.current || !contentRef.current || !canvasWrapRef.current) return

    const tl = gsap.timeline({
      scrollTrigger: {
        trigger: heroRef.current,
        start: 'top top',
        end: 'bottom top',
        scrub: 0.3,
      },
    })

    tl.to(contentRef.current, { y: -100, opacity: 0 }, 0)
    tl.to(canvasWrapRef.current, { scale: 0.9, opacity: 0 }, 0)

    return () => ScrollTrigger.getAll().forEach(t => t.kill())
  }, [])

  // Staggered entrance animation for text elements
  useEffect(() => {
    const reveals = heroRef.current?.querySelectorAll('.hero-reveal')
    if (!reveals) return
    gsap.from(reveals, {
      y: 60, opacity: 0, duration: 1, stagger: 0.15, ease: 'power3.out', delay: 0.3,
    })
  }, [])

  return (
    <section ref={heroRef} className="relative min-h-screen flex items-center overflow-hidden">
      {/* 3D Canvas (desktop only) */}
      <div ref={canvasWrapRef} className="absolute inset-0 z-0">
        {!isMobile ? (
          <Scene3D />
        ) : (
          <img src="/assets/hero-fallback.png" alt="" className="w-full h-full object-cover" />
        )}
      </div>

      {/* Content overlay */}
      <div ref={contentRef} className="relative z-10 max-w-3xl px-6 md:px-16">
        <h1 className="hero-reveal text-5xl md:text-7xl font-bold leading-tight">
          {/* Brand headline here */}
        </h1>
        <p className="hero-reveal mt-6 text-lg md:text-xl text-muted max-w-lg">
          {/* Brand subtitle here */}
        </p>
        <div className="hero-reveal mt-8">
          {/* CTA button */}
        </div>
      </div>
    </section>
  )
}
```

### Option B: Scroll Video Hero

Best for: restaurants, real estate, experiential brands, hospitality, retail

A full-screen Veo-generated video plays frame-by-frame as the user scrolls.
The section is pinned for 3x viewport height, giving a cinematic reveal effect.

```tsx
// Hero.tsx
'use client'
import { useEffect, useRef, useState } from 'react'
import gsap from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'

gsap.registerPlugin(ScrollTrigger)

interface VideoHeroProps {
  videoSrc: string
  posterSrc: string
  fallbackSrc: string // Mobile fallback image
}

export default function Hero({ videoSrc, posterSrc, fallbackSrc }: VideoHeroProps) {
  const sectionRef = useRef<HTMLDivElement>(null)
  const videoRef = useRef<HTMLVideoElement>(null)
  const contentRef = useRef<HTMLDivElement>(null)
  const [isMobile, setIsMobile] = useState(true)

  useEffect(() => {
    setIsMobile(window.innerWidth < 768 || 'ontouchstart' in window)
  }, [])

  // Scroll-controlled video + content fade sequence
  useEffect(() => {
    if (isMobile) return
    const video = videoRef.current
    const section = sectionRef.current
    if (!video || !section) return

    const init = () => {
      const tl = gsap.timeline({
        scrollTrigger: {
          trigger: section,
          start: 'top top',
          end: '+=300%',
          pin: true,
          scrub: 0.5,
        },
      })

      // Video scrubs through first 70% of scroll
      ScrollTrigger.create({
        trigger: section,
        start: 'top top',
        end: '+=300%',
        scrub: 0.5,
        onUpdate: (self) => {
          if (video.duration) {
            video.currentTime = video.duration * Math.min(self.progress / 0.7, 1)
          }
        },
      })

      // Content fades in during last 40% of scroll
      tl.fromTo(contentRef.current,
        { opacity: 0, y: 60 },
        { opacity: 1, y: 0, duration: 0.3 },
        0.6 // starts at 60% progress
      )
    }

    if (video.readyState >= 1) init()
    else video.addEventListener('loadedmetadata', init, { once: true })

    return () => ScrollTrigger.getAll().forEach(t => t.kill())
  }, [isMobile])

  return (
    <div ref={sectionRef} className="relative h-screen w-full overflow-hidden">
      {isMobile ? (
        <img src={fallbackSrc} alt="" className="absolute inset-0 w-full h-full object-cover" />
      ) : (
        <video
          ref={videoRef}
          muted playsInline preload="auto" poster={posterSrc}
          className="absolute inset-0 w-full h-full object-cover"
        >
          <source src={videoSrc} type="video/mp4" />
        </video>
      )}

      {/* Dark gradient overlay */}
      <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-black/20" />

      {/* Content (fades in on scroll for desktop, visible immediately on mobile) */}
      <div
        ref={contentRef}
        className="absolute inset-0 z-10 flex items-end pb-20 px-6 md:px-16"
        style={isMobile ? {} : { opacity: 0 }}
      >
        <div className="max-w-2xl">
          <h1 className="text-4xl md:text-6xl font-bold text-white leading-tight">
            {/* Brand headline */}
          </h1>
          <p className="mt-4 text-lg text-white/80">
            {/* Brand subtitle */}
          </p>
        </div>
      </div>
    </div>
  )
}
```

### Option C: Kinetic Typography Hero

Best for: agencies, bold brands, when no video/3D assets are available

No images or 3D — pure typography in motion. Giant headline with character-by-character
animation. Parallax depth between heading and subtext.

```tsx
// Hero.tsx
'use client'
import { useEffect, useRef } from 'react'
import gsap from 'gsap'

export default function Hero() {
  const heroRef = useRef<HTMLElement>(null)
  const headingRef = useRef<HTMLHeadingElement>(null)

  useEffect(() => {
    const heading = headingRef.current
    if (!heading) return

    // Split heading into characters
    const text = heading.textContent || ''
    heading.innerHTML = text.split('').map((char) =>
      char === ' '
        ? '<span class="char" style="display:inline-block">&nbsp;</span>'
        : `<span class="char" style="display:inline-block">${char}</span>`
    ).join('')

    const chars = heading.querySelectorAll('.char')

    // Staggered character entrance with blur
    gsap.from(chars, {
      opacity: 0,
      y: 80,
      rotateX: -90,
      filter: 'blur(10px)',
      stagger: 0.03,
      duration: 1,
      ease: 'power3.out',
      delay: 0.5,
    })

    // Subtitle and CTA entrance
    gsap.from('.hero-sub', {
      opacity: 0, y: 40, duration: 1, ease: 'power3.out',
      delay: 0.8 + chars.length * 0.03,
    })
  }, [])

  return (
    <section ref={heroRef} className="relative min-h-screen flex items-center justify-center overflow-hidden">
      {/* Animated gradient background */}
      <div
        className="absolute inset-0"
        style={{
          background: 'linear-gradient(135deg, var(--color-primary), var(--color-secondary))',
          backgroundSize: '400% 400%',
          animation: 'gradientShift 15s ease infinite',
        }}
      />

      <div className="relative z-10 text-center px-6 max-w-5xl">
        <h1
          ref={headingRef}
          className="text-6xl md:text-9xl font-bold leading-none tracking-tight"
          style={{ perspective: '1000px' }}
        >
          {/* Brand headline */}
        </h1>
        <p className="hero-sub mt-8 text-xl md:text-2xl opacity-80 max-w-2xl mx-auto">
          {/* Brand subtitle */}
        </p>
        <div className="hero-sub mt-10">
          {/* CTA button */}
        </div>
      </div>
    </section>
  )
}
```

## Hero Selection Guide

| Signal | Best Hero Type |
|--------|---------------|
| Prospect has strong visual content (food, property, products) | **Scroll Video** |
| Prospect is professional/tech/luxury with abstract brand | **3D Scene** |
| Prospect is a creative agency or bold brand | **Kinetic Typography** |
| Video generation failed / no assets available | **Kinetic Typography** |
| Mobile-only audience (food truck, salon) | **Scroll Video** with strong fallback |

## Rules for All Hero Types

1. **Must fill full viewport** — `min-h-screen` or `h-screen`
2. **Content must be readable** — use gradient overlays or backdrop-blur on video/3D heroes
3. **Staggered entrance animation** — headline first, then subtitle, then CTA (0.1-0.15s stagger)
4. **Scroll interaction** — hero content must respond to scroll (fade, parallax, or dissolve)
5. **Mobile fallback** — always provide a static image path for mobile/low-power devices
6. **LCP optimization** — hero image/poster must load within 2.5s (preload in `<head>`)
7. **No layout shift** — use fixed dimensions or aspect-ratio to prevent CLS
