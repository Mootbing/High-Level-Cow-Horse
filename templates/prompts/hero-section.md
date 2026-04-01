# Hero Section Generation Reference

The hero is the first thing visitors see — it must be cinematic, immersive, and instant.
Every Clarmi hero uses **scroll-controlled video** generated from two Nano Banana keyframes via Veo 3.1 first+last frame mode.

## Hero Video Pipeline

1. **Nano Banana** generates **keyframe A** (opening visual state — what visitors see on page load)
2. **Nano Banana** generates **keyframe B** (ending visual state — what visitors see after scrolling through)
3. **Veo 3.1** generates a smooth transition video between A and B using first+last frame mode
4. The video is embedded as scroll-controlled `<video>` — `video.currentTime` mapped to scroll progress

## Scroll Video Hero (ALWAYS — every site)

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

### Fallback: Kinetic Typography Hero

ONLY use when ALL video AND image generation has failed (quota exhausted, API down).
This is a last resort — not a design choice.

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

## Fallback Chain

| Situation | What to do |
|-----------|-----------|
| Video generation succeeds | Scroll-controlled video hero (default) |
| Video fails, keyframes succeed | CSS crossfade between keyframe A + B on scroll |
| All generation fails | Kinetic typography hero (last resort) |

## Rules for the Scroll Video Hero

1. **Must fill full viewport** — `h-screen`
2. **Content must be readable** — use gradient overlays on video
3. **Staggered entrance animation** — headline first, then subtitle, then CTA (0.1-0.15s stagger)
4. **Scroll interaction** — video plays frame-by-frame on scroll, content fades in during last 40%
5. **Mobile fallback** — keyframe A as static image (iOS restricts video.currentTime)
6. **LCP optimization** — poster (keyframe A) must load within 2.5s (preload in `<head>`)
7. **No layout shift** — use fixed dimensions or aspect-ratio to prevent CLS
8. **Three.js scene fades in** — as the hero video scrolls out, the persistent Three.js scene fades in behind content sections
