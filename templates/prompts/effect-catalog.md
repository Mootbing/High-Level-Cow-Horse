# Animation & Effect Catalog

Copy-paste patterns for scroll animations, micro-interactions, and visual effects.
Pick effects that match the brand personality — don't use all of them on every site.

## Effect Selection by Brand Personality

| Brand Vibe | Recommended Effects | Avoid |
|-----------|--------------------|----|
| **Premium/Luxury** | Glass 3D, smooth parallax, magnetic buttons, text reveal, subtle chromatic | Bouncy animations, confetti, horizontal scroll |
| **Warm/Inviting** | Fade-ins, warm bloom, gentle parallax, counter animations | Heavy 3D, neon, aggressive scrub |
| **Bold/Creative** | Horizontal scroll, text scramble, custom cursor, clip-path reveals | Subtle/minimal effects (too boring) |
| **Clean/Professional** | Stagger entrances, simple parallax, fade-in cards | Custom cursor, heavy post-processing |
| **Playful/Fun** | Elastic easing, confetti, magnetic buttons, bouncy cards | Glass 3D, vignette, monochrome |
| **Tech/Modern** | Data network 3D, neon bloom, grid animations, counter | Warm organic, elastic easing |

## GSAP ScrollTrigger Patterns

### 1. Pin + Scrub (Cinematic Scroll Sequence)
```tsx
// Pin a section and animate contents on scroll
useEffect(() => {
  const tl = gsap.timeline({
    scrollTrigger: {
      trigger: sectionRef.current,
      start: 'top top',
      end: '+=300%', // 3x viewport height of scroll
      pin: true,
      scrub: 0.5,
    },
  })

  // Sequence of animations that play as user scrolls
  tl.to(headingRef.current, { opacity: 1, y: 0, duration: 0.3 })
    .to(paragraphRef.current, { opacity: 1, y: 0, duration: 0.3 }, '+=0.1')
    .to(imageRef.current, { scale: 1, opacity: 1, duration: 0.4 }, '+=0.1')
    .to(headingRef.current, { opacity: 0, y: -50, duration: 0.3 }, '+=0.3')
    .to(nextContentRef.current, { opacity: 1, y: 0, duration: 0.3 })

  return () => { tl.kill(); ScrollTrigger.getAll().forEach(t => t.kill()) }
}, [])
```

### 2. Horizontal Scroll Section
```tsx
useEffect(() => {
  const container = scrollContainerRef.current
  const section = sectionRef.current
  if (!container || !section) return

  const totalScroll = container.scrollWidth - window.innerWidth

  gsap.to(container, {
    x: -totalScroll,
    ease: 'none',
    scrollTrigger: {
      trigger: section,
      start: 'top top',
      end: () => `+=${totalScroll}`,
      pin: true,
      scrub: 1,
      invalidateOnRefresh: true,
    },
  })

  return () => ScrollTrigger.getAll().forEach(t => t.kill())
}, [])
```

### 3. Text Word-by-Word Reveal
```tsx
function TextReveal({ text, className }: { text: string; className?: string }) {
  const containerRef = useRef<HTMLParagraphElement>(null)

  useEffect(() => {
    const el = containerRef.current
    if (!el) return

    // Split text into word spans
    const words = text.split(' ')
    el.innerHTML = words
      .map(word => `<span class="reveal-word" style="display:inline-block;opacity:0.1;filter:blur(4px);transition:none">${word}&nbsp;</span>`)
      .join('')

    const wordEls = el.querySelectorAll('.reveal-word')
    wordEls.forEach((word) => {
      gsap.to(word, {
        opacity: 1,
        filter: 'blur(0px)',
        ease: 'none',
        scrollTrigger: {
          trigger: word,
          start: 'top 85%',
          end: 'top 50%',
          scrub: true,
        },
      })
    })

    return () => ScrollTrigger.getAll().forEach(t => t.kill())
  }, [text])

  return <p ref={containerRef} className={className} />
}
```

### 4. Staggered Card Entrance
```tsx
useEffect(() => {
  const cards = gsap.utils.toArray<HTMLElement>('.feature-card')
  
  gsap.from(cards, {
    y: 60,
    opacity: 0,
    scale: 0.95,
    duration: 0.8,
    stagger: 0.12,
    ease: 'power3.out',
    scrollTrigger: {
      trigger: gridRef.current,
      start: 'top 75%',
    },
  })

  return () => ScrollTrigger.getAll().forEach(t => t.kill())
}, [])
```

### 5. Multi-Speed Parallax
```tsx
useEffect(() => {
  const layers = [
    { el: bgRef.current, speed: 0.15 },
    { el: midRef.current, speed: 0.4 },
    { el: fgRef.current, speed: 0.7 },
    { el: floatRef.current, speed: 1.1 }, // Faster than scroll
  ]

  layers.forEach(({ el, speed }) => {
    if (!el) return
    gsap.to(el, {
      y: () => -(ScrollTrigger.maxScroll(window) * speed * 0.2),
      ease: 'none',
      scrollTrigger: { start: 0, end: 'max', scrub: 0.3 },
    })
  })

  return () => ScrollTrigger.getAll().forEach(t => t.kill())
}, [])
```

### 6. SVG Path Draw on Scroll
```tsx
useEffect(() => {
  const path = pathRef.current
  if (!path) return

  const length = path.getTotalLength()
  gsap.set(path, { strokeDasharray: length, strokeDashoffset: length })
  
  gsap.to(path, {
    strokeDashoffset: 0,
    ease: 'none',
    scrollTrigger: {
      trigger: svgRef.current,
      start: 'top 60%',
      end: 'bottom 40%',
      scrub: true,
    },
  })

  return () => ScrollTrigger.getAll().forEach(t => t.kill())
}, [])
```

### 7. Image Reveal with Clip-Path
```tsx
// Directional wipe reveal
gsap.from(imageEl, {
  clipPath: 'inset(0 100% 0 0)', // Wipe from left
  // clipPath: 'inset(100% 0 0 0)', // Wipe from bottom
  // clipPath: 'inset(0 0 0 100%)', // Wipe from right
  // clipPath: 'circle(0% at 50% 50%)', // Circle expand from center
  duration: 1.2,
  ease: 'power3.inOut',
  scrollTrigger: { trigger: imageEl, start: 'top 75%' },
})
```

## Micro-Interactions

### Magnetic Button
```tsx
'use client'

import { useRef } from 'react'
import gsap from 'gsap'

export default function MagneticButton({ children, className, ...props }: React.ButtonHTMLAttributes<HTMLButtonElement>) {
  const buttonRef = useRef<HTMLButtonElement>(null)

  const onMouseMove = (e: React.MouseEvent) => {
    const btn = buttonRef.current
    if (!btn) return
    const rect = btn.getBoundingClientRect()
    const x = e.clientX - rect.left - rect.width / 2
    const y = e.clientY - rect.top - rect.height / 2
    gsap.to(btn, { x: x * 0.3, y: y * 0.3, duration: 0.3, ease: 'power2.out' })
  }

  const onMouseLeave = () => {
    gsap.to(buttonRef.current, { x: 0, y: 0, duration: 0.6, ease: 'elastic.out(1, 0.3)' })
  }

  return (
    <button
      ref={buttonRef}
      onMouseMove={onMouseMove}
      onMouseLeave={onMouseLeave}
      className={className}
      {...props}
    >
      {children}
    </button>
  )
}
```

### 3D Card Tilt on Hover
```tsx
const onMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
  const card = e.currentTarget
  const rect = card.getBoundingClientRect()
  const x = (e.clientX - rect.left) / rect.width - 0.5
  const y = (e.clientY - rect.top) / rect.height - 0.5
  
  gsap.to(card, {
    rotateY: x * 15,
    rotateX: -y * 15,
    transformPerspective: 800,
    duration: 0.3,
    ease: 'power2.out',
  })
}

const onMouseLeave = (e: React.MouseEvent<HTMLDivElement>) => {
  gsap.to(e.currentTarget, {
    rotateY: 0, rotateX: 0,
    duration: 0.5, ease: 'power2.out',
  })
}
```

### Text Scramble/Decode
```tsx
function useTextScramble(finalText: string, trigger: boolean) {
  const [display, setDisplay] = useState('')
  const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*'

  useEffect(() => {
    if (!trigger) return
    let iteration = 0
    const interval = setInterval(() => {
      setDisplay(
        finalText.split('').map((char, i) => {
          if (char === ' ') return ' '
          if (i < iteration) return char
          return chars[Math.floor(Math.random() * chars.length)]
        }).join('')
      )
      if (iteration >= finalText.length) clearInterval(interval)
      iteration += 1 / 3
    }, 30)
    return () => clearInterval(interval)
  }, [trigger, finalText])

  return display
}
```

### Smooth Number Counter
```tsx
function AnimatedCounter({ target, duration = 2 }: { target: number; duration?: number }) {
  const ref = useRef<HTMLSpanElement>(null)

  useEffect(() => {
    const el = ref.current
    if (!el) return

    gsap.from(el, {
      textContent: 0,
      duration,
      ease: 'power1.out',
      snap: { textContent: 1 },
      scrollTrigger: {
        trigger: el,
        start: 'top 80%',
      },
      onUpdate: function () {
        el.textContent = Math.ceil(Number(el.textContent)).toLocaleString()
      },
    })

    return () => ScrollTrigger.getAll().forEach(t => t.kill())
  }, [target, duration])

  return <span ref={ref}>{target.toLocaleString()}</span>
}
```

### Cursor Follower (Desktop Only)
```tsx
'use client'

import { useEffect, useRef } from 'react'
import gsap from 'gsap'

export default function CustomCursor() {
  const dotRef = useRef<HTMLDivElement>(null)
  const ringRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    // Skip on touch devices
    if ('ontouchstart' in window) return

    const dot = dotRef.current
    const ring = ringRef.current
    if (!dot || !ring) return

    const moveCursor = (e: MouseEvent) => {
      gsap.to(dot, { x: e.clientX, y: e.clientY, duration: 0.1 })
      gsap.to(ring, { x: e.clientX, y: e.clientY, duration: 0.3 })
    }

    // Scale up on interactive elements
    const onEnterInteractive = () => {
      gsap.to(ring, { scale: 2, opacity: 0.3, duration: 0.3 })
    }
    const onLeaveInteractive = () => {
      gsap.to(ring, { scale: 1, opacity: 0.5, duration: 0.3 })
    }

    window.addEventListener('mousemove', moveCursor)
    document.querySelectorAll('a, button, [role="button"]').forEach(el => {
      el.addEventListener('mouseenter', onEnterInteractive)
      el.addEventListener('mouseleave', onLeaveInteractive)
    })

    return () => {
      window.removeEventListener('mousemove', moveCursor)
    }
  }, [])

  return (
    <>
      <div ref={dotRef} className="fixed top-0 left-0 pointer-events-none z-[9999] -translate-x-1/2 -translate-y-1/2 w-2 h-2 rounded-full bg-white mix-blend-difference" />
      <div ref={ringRef} className="fixed top-0 left-0 pointer-events-none z-[9999] -translate-x-1/2 -translate-y-1/2 w-8 h-8 rounded-full border border-white/50 mix-blend-difference" style={{ opacity: 0.5 }} />
    </>
  )
}
```

## Section Transition Effects

### Clip-Path Section Reveal
```css
/* Next section reveals through expanding circle */
.section-reveal {
  clip-path: circle(0% at 50% 50%);
}
.section-reveal.active {
  clip-path: circle(150% at 50% 50%);
  transition: clip-path 1.2s cubic-bezier(0.16, 1, 0.3, 1);
}
```

### Gradient Wipe Between Sections
```tsx
// Use GSAP to animate a gradient mask position
gsap.fromTo(sectionEl, 
  { '--mask-position': '100%' },
  {
    '--mask-position': '0%',
    scrollTrigger: { trigger: sectionEl, start: 'top 80%', end: 'top 20%', scrub: true },
  }
)
// CSS: mask-image: linear-gradient(to bottom, black var(--mask-position), transparent calc(var(--mask-position) + 10%))
```

## Lenis + GSAP Sync Setup

Always include this in the SmoothScroller component:

```tsx
'use client'

import { useEffect, useRef } from 'react'
import Lenis from '@studio-freight/lenis'
import gsap from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'

gsap.registerPlugin(ScrollTrigger)

export default function SmoothScroller({ children }: { children: React.ReactNode }) {
  const lenisRef = useRef<Lenis | null>(null)

  useEffect(() => {
    const lenis = new Lenis({
      duration: 1.2,
      easing: (t: number) => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
      touchMultiplier: 2,
    })
    lenisRef.current = lenis

    // Sync Lenis scroll position with GSAP ScrollTrigger
    lenis.on('scroll', ScrollTrigger.update)
    gsap.ticker.add((time) => lenis.raf(time * 1000))
    gsap.ticker.lagSmoothing(0)

    return () => {
      lenis.destroy()
      gsap.ticker.remove(lenis.raf)
    }
  }, [])

  return <>{children}</>
}
```

## Advanced Effects

### Split-Text Line-by-Line Reveal
```tsx
// Split text into lines and reveal each on scroll with clip-path
function LineReveal({ text, className }: { text: string; className?: string }) {
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const el = containerRef.current
    if (!el) return

    // Wrap each line in a span with overflow hidden
    const lines = el.querySelectorAll('.line')
    lines.forEach((line) => {
      gsap.from(line, {
        yPercent: 100,
        duration: 1,
        ease: 'power3.out',
        scrollTrigger: { trigger: line, start: 'top 90%' },
      })
    })

    return () => ScrollTrigger.getAll().forEach(t => t.kill())
  }, [])

  // Split text by newlines or by measuring line breaks
  return (
    <div ref={containerRef} className={className}>
      {text.split('\n').map((line, i) => (
        <div key={i} style={{ overflow: 'hidden' }}>
          <div className="line">{line}</div>
        </div>
      ))}
    </div>
  )
}
```

### Image Distortion on Hover (CSS-only)
```tsx
// Premium hover effect — image warps subtly when mouse enters
<div className="group relative overflow-hidden">
  <img
    src={imageSrc}
    alt={imageAlt}
    className="w-full h-full object-cover transition-transform duration-700
      group-hover:scale-110"
    style={{
      filter: 'brightness(0.9)',
      transition: 'filter 0.7s ease, transform 0.7s cubic-bezier(0.16, 1, 0.3, 1)',
    }}
  />
  {/* Overlay that reveals on hover */}
  <div className="absolute inset-0 bg-black/0 group-hover:bg-black/20
    transition-colors duration-500" />
</div>
```

### Marquee / Infinite Scroll Text
```tsx
// Infinite horizontal text scroll — great for brand statements
function Marquee({ text, speed = 20 }: { text: string; speed?: number }) {
  return (
    <div className="overflow-hidden whitespace-nowrap">
      <div
        className="inline-block"
        style={{
          animation: `marquee ${speed}s linear infinite`,
        }}
      >
        {/* Repeat text 3x for seamless loop */}
        {[1, 2, 3].map((i) => (
          <span key={i} className="mx-8 text-8xl font-bold opacity-10">
            {text}
          </span>
        ))}
      </div>
    </div>
  )
}
// CSS: @keyframes marquee { from { transform: translateX(0) } to { transform: translateX(-33.33%) } }
```

### Smooth Color Morph Between Sections
```tsx
// Sections smoothly transition background colors as user scrolls
useEffect(() => {
  const sections = gsap.utils.toArray<HTMLElement>('.color-section')

  sections.forEach((section) => {
    const bgColor = section.dataset.bgColor || '#000000'
    const textColor = section.dataset.textColor || '#ffffff'

    ScrollTrigger.create({
      trigger: section,
      start: 'top 60%',
      end: 'top 40%',
      scrub: true,
      onUpdate: (self) => {
        // Smoothly transition body background
        document.body.style.backgroundColor = bgColor
        document.body.style.color = textColor
        document.body.style.transition = 'background-color 0.3s, color 0.3s'
      },
    })
  })

  return () => ScrollTrigger.getAll().forEach(t => t.kill())
}, [])
// Usage: <section className="color-section" data-bg-color="#f5ebe0" data-text-color="#1a0f0a">
```

### Loading Screen / Preloader
```tsx
// Show while 3D and video assets load, then animate out
'use client'
import { useState, useEffect } from 'react'
import gsap from 'gsap'

export default function Preloader({ onComplete }: { onComplete: () => void }) {
  const [progress, setProgress] = useState(0)
  const overlayRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    // Simulate load progress (in real usage, track actual asset loading)
    let current = 0
    const interval = setInterval(() => {
      current += Math.random() * 15
      if (current >= 100) {
        current = 100
        clearInterval(interval)

        // Animate out
        gsap.to(overlayRef.current, {
          clipPath: 'circle(0% at 50% 50%)',
          duration: 1,
          ease: 'power3.inOut',
          delay: 0.3,
          onComplete,
        })
      }
      setProgress(Math.min(current, 100))
    }, 100)

    return () => clearInterval(interval)
  }, [onComplete])

  return (
    <div
      ref={overlayRef}
      className="fixed inset-0 z-50 flex items-center justify-center bg-background"
      style={{ clipPath: 'circle(150% at 50% 50%)' }}
    >
      <div className="text-center">
        <div className="text-6xl font-bold">{Math.round(progress)}%</div>
        <div className="mt-4 w-48 h-0.5 bg-white/10 rounded-full overflow-hidden">
          <div
            className="h-full bg-white rounded-full transition-all duration-200"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>
    </div>
  )
}
```

Use the preloader only when the page has heavy 3D or video assets that take > 2s to load.
For simpler sites, skip it — nobody wants to wait for a loading screen.

## Performance Checklist

Before deploying, verify:
- [ ] All Three.js components use `dynamic(() => import(...), { ssr: false })`
- [ ] Mobile devices show static fallbacks (no Three.js, no scroll video)
- [ ] All `useEffect` cleanups call `ScrollTrigger.getAll().forEach(t => t.kill())`
- [ ] Videos have `poster` attribute for instant visual
- [ ] Videos use `preload="auto"` and `muted playsInline`
- [ ] No `overflow: hidden` on body (breaks Lenis)
- [ ] `will-change: transform` on scroll-animated elements
- [ ] Reduced motion media query respected
