# Scroll-Controlled Video Section Reference

Reference for building scroll-controlled video playback sections — the Apple-style
technique where video progress is tied to scroll position, not time.

## When to Use

- **Hero backgrounds**: cinematic video that plays as user scrolls past the hero
- **Section transitions**: video morph between two visual states (A → B)
- **Product reveals**: 360-degree product rotation controlled by scroll
- **Storytelling**: narrative video that unfolds as user reads/scrolls

## Aspect Ratio & Fit Rules

- ALL videos are generated at **16:9** aspect ratio (enforced by the Veo API `aspectRatio` parameter)
- ALL keyframe images are generated at **16:9** (enforced by Nano Banana's `aspectRatio` parameter)
- In CSS, ALL hero videos, poster images, and keyframe images MUST use **`object-fit: cover`** — this crops to fill the viewport at any screen size. NEVER use `contain` (causes letterboxing) or `fill` (causes stretching).
- The `<video>` and fallback `<img>` elements should be `absolute inset-0 w-full h-full object-cover`

## Video Encoding for Scroll Scrubbing

Scroll-controlled video requires dense keyframe spacing. Without it, browsers cannot seek to
arbitrary frames and show black/frozen frames during scrubbing. Veo-generated videos should
be re-encoded for scroll before embedding.

**Note**: If you're generating video via Veo API, the output MP4 already uses H.264 but may
not have dense keyframes. For the smoothest scroll experience, re-encode with `-g 2`:

```bash
# Optimize for scroll scrubbing (run on server/build step)
ffmpeg -i veo-output.mp4 \
  -vcodec libx264 -pix_fmt yuv420p \
  -profile:v baseline -level 3 \
  -an -vf "scale=-1:1080" \
  -preset veryslow -g 2 \
  -movflags faststart \
  output-scroll.mp4
```

Key flags: `-g 2` = keyframe every 2 frames (critical for smooth seeking),
`-movflags faststart` = enables progressive download, `-an` = strip audio (always muted).

## Video Generation Pipeline

### For Hero Videos
```
1. Call generate_video(prompt, project_name)
   → Returns /assets/hero-video-{id}.mp4
2. Use ScrollVideo component with pin + scrub
```

### For Transition Videos (A → B morph)
```
1. Call generate_transition_video(
     prompt="Smooth morph from aerial cityscape to intimate workspace",
     project_name=name,
     section="hero-to-about",
     keyframe_a_prompt="Aerial view of downtown skyline at golden hour, warm light, no text",
     keyframe_b_prompt="Close-up of modern workspace with laptop and coffee, warm tones, no text",
   )
   → Returns:
     keyframe_a: /assets/keyframe-hero-to-about-a-{id}.png
     keyframe_b: /assets/keyframe-hero-to-about-b-{id}.png  
     transition_video: /assets/transition-hero-to-about-{id}.mp4
2. Use TransitionSection component
```

### For Batch Asset Generation
```
1. Call generate_scene_assets(project_name, sections_json)
   → Generates all images, videos, and transitions in one call
   → Returns all asset paths
```

## Browser Scrubbing Tips

- **`requestVideoFrameCallback`** (Chrome 83+, Safari 15.4+) — fires when a new frame is
  presented. Use it instead of `requestAnimationFrame` for smoother frame updates:
  ```tsx
  video.requestVideoFrameCallback(function onFrame() {
    // Frame is actually displayed now — safe to update textures/canvas
    video.requestVideoFrameCallback(onFrame)
  })
  ```
- **Safari/iOS warmup**: Safari won't decode the first frame until video has been played once.
  After `loadedmetadata`, do `video.play(); video.pause(); video.currentTime = 0;`
- **Blob preloading**: For ultra-reliable seeking, fetch the entire video as a blob and set
  `video.src = URL.createObjectURL(blob)` — eliminates network seek latency

## Component: ScrollVideo

The core scroll-controlled video component. Pins the section and maps scroll
progress to `video.currentTime`.

```tsx
'use client'

import { useEffect, useRef, useState } from 'react'
import gsap from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'

gsap.registerPlugin(ScrollTrigger)

interface ScrollVideoProps {
  src: string              // Video source URL
  poster?: string          // Poster image (shown while loading)
  scrollLength?: number    // How many viewport heights to scroll through (default: 3)
  children?: React.ReactNode // Overlay content (text, CTAs)
}

export default function ScrollVideo({ 
  src, poster, scrollLength = 3, children 
}: ScrollVideoProps) {
  const sectionRef = useRef<HTMLDivElement>(null)
  const videoRef = useRef<HTMLVideoElement>(null)
  const [loaded, setLoaded] = useState(false)

  useEffect(() => {
    const video = videoRef.current
    const section = sectionRef.current
    if (!video || !section) return

    let st: ScrollTrigger | null = null

    const initScrollTrigger = () => {
      setLoaded(true)
      st = ScrollTrigger.create({
        trigger: section,
        start: 'top top',
        end: `+=${window.innerHeight * scrollLength}`,
        pin: true,
        scrub: 0.5, // Smooth scrubbing
        onUpdate: (self) => {
          if (video.duration && isFinite(video.duration)) {
            const targetTime = video.duration * self.progress
            // Only seek if difference is meaningful (avoid micro-seeks)
            if (Math.abs(video.currentTime - targetTime) > 0.05) {
              video.currentTime = targetTime
            }
          }
        },
      })
    }

    if (video.readyState >= 1) {
      initScrollTrigger()
    } else {
      video.addEventListener('loadedmetadata', initScrollTrigger, { once: true })
    }

    return () => {
      st?.kill()
      video.removeEventListener('loadedmetadata', initScrollTrigger)
    }
  }, [scrollLength])

  return (
    <div ref={sectionRef} className="relative h-screen w-full overflow-hidden">
      {/* Poster shown until video is ready */}
      {poster && !loaded && (
        <img
          src={poster}
          alt=""
          className="absolute inset-0 w-full h-full object-cover"
        />
      )}
      
      <video
        ref={videoRef}
        muted
        playsInline
        preload="auto"
        poster={poster}
        className="absolute inset-0 w-full h-full object-cover"
        style={{ opacity: loaded ? 1 : 0, transition: 'opacity 0.3s' }}
      >
        <source src={src} type="video/mp4" />
      </video>

      {/* Overlay content */}
      {children && (
        <div className="absolute inset-0 z-10 flex items-center justify-center">
          {children}
        </div>
      )}
    </div>
  )
}
```

## Component: TransitionSection

A section that morphs between two states using a Veo-generated transition video.
Shows keyframe A initially, plays the transition on scroll, ends on keyframe B.

```tsx
'use client'

import { useEffect, useRef, useState } from 'react'
import gsap from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'

gsap.registerPlugin(ScrollTrigger)

interface TransitionSectionProps {
  keyframeA: string      // Starting image
  keyframeB: string      // Ending image
  transitionVideo?: string // Veo-generated transition (optional — falls back to crossfade)
  scrollLength?: number
  overlayStart?: React.ReactNode  // Content shown at start
  overlayEnd?: React.ReactNode    // Content shown at end
}

export default function TransitionSection({
  keyframeA, keyframeB, transitionVideo,
  scrollLength = 2.5, overlayStart, overlayEnd,
}: TransitionSectionProps) {
  const sectionRef = useRef<HTMLDivElement>(null)
  const videoRef = useRef<HTMLVideoElement>(null)
  const startOverlayRef = useRef<HTMLDivElement>(null)
  const endOverlayRef = useRef<HTMLDivElement>(null)
  const [progress, setProgress] = useState(0)
  const hasVideo = !!transitionVideo

  useEffect(() => {
    const section = sectionRef.current
    const video = videoRef.current
    if (!section) return

    const st = ScrollTrigger.create({
      trigger: section,
      start: 'top top',
      end: `+=${window.innerHeight * scrollLength}`,
      pin: true,
      scrub: 0.5,
      onUpdate: (self) => {
        setProgress(self.progress)
        
        // Scrub video if available
        if (video && video.duration && isFinite(video.duration)) {
          video.currentTime = video.duration * self.progress
        }

        // Fade overlays
        if (startOverlayRef.current) {
          // Start overlay visible at 0%, fades out by 30%
          const startOpacity = Math.max(0, 1 - self.progress * 3.3)
          startOverlayRef.current.style.opacity = String(startOpacity)
        }
        if (endOverlayRef.current) {
          // End overlay fades in starting at 60%
          const endOpacity = Math.max(0, (self.progress - 0.6) * 2.5)
          endOverlayRef.current.style.opacity = String(endOpacity)
        }
      },
    })

    return () => st.kill()
  }, [scrollLength, hasVideo])

  return (
    <div ref={sectionRef} className="relative h-screen w-full overflow-hidden">
      {hasVideo ? (
        <>
          {/* Video transition */}
          <video
            ref={videoRef}
            muted playsInline preload="auto"
            poster={keyframeA}
            className="absolute inset-0 w-full h-full object-cover"
          >
            <source src={transitionVideo} type="video/mp4" />
          </video>
        </>
      ) : (
        <>
          {/* CSS crossfade fallback when no video available */}
          <img
            src={keyframeA}
            alt=""
            className="absolute inset-0 w-full h-full object-cover transition-opacity duration-300"
            style={{ opacity: 1 - progress }}
          />
          <img
            src={keyframeB}
            alt=""
            className="absolute inset-0 w-full h-full object-cover transition-opacity duration-300"
            style={{ opacity: progress }}
          />
        </>
      )}

      {/* Gradient overlay for text readability */}
      <div className="absolute inset-0 bg-gradient-to-b from-black/30 via-transparent to-black/30" />

      {/* Start overlay (visible at beginning of scroll) */}
      {overlayStart && (
        <div ref={startOverlayRef} className="absolute inset-0 z-10 flex items-center justify-center">
          {overlayStart}
        </div>
      )}

      {/* End overlay (visible at end of scroll) */}
      {overlayEnd && (
        <div ref={endOverlayRef} className="absolute inset-0 z-10 flex items-center justify-center" style={{ opacity: 0 }}>
          {overlayEnd}
        </div>
      )}
    </div>
  )
}
```

## Component: CanvasFrameScrubber (Apple-Style)

The highest-fidelity scroll video approach. Pre-loads an image sequence and draws frames
to a `<canvas>` element. Used by Apple for AirPods, MacBook, iPhone product pages.

**When to use**: When video scrubbing is jittery (not all browsers handle video.currentTime
seeking smoothly). Extract video frames as JPEGs and scrub through them on canvas.

**Trade-off**: ~7MB for 148 frames, but buttery smooth on all browsers.

```tsx
'use client'

import { useEffect, useRef, useCallback } from 'react'
import gsap from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'
gsap.registerPlugin(ScrollTrigger)

interface CanvasFrameScrubberProps {
  frameCount: number
  getFrameUrl: (index: number) => string // 1-based: (i) => `/assets/frames/frame_${String(i).padStart(4, '0')}.jpg`
  scrollLength?: number
}

export default function CanvasFrameScrubber({
  frameCount, getFrameUrl, scrollLength = 3,
}: CanvasFrameScrubberProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const sectionRef = useRef<HTMLDivElement>(null)
  const framesRef = useRef<HTMLImageElement[]>([])
  const currentFrame = useRef(0)

  const drawFrame = useCallback((index: number) => {
    const canvas = canvasRef.current
    const ctx = canvas?.getContext('2d')
    const img = framesRef.current[index]
    if (!canvas || !ctx || !img) return
    canvas.width = img.naturalWidth
    canvas.height = img.naturalHeight
    ctx.drawImage(img, 0, 0)
    currentFrame.current = index
  }, [])

  useEffect(() => {
    // Preload all frames
    const images: HTMLImageElement[] = []
    let loaded = 0

    for (let i = 1; i <= frameCount; i++) {
      const img = new Image()
      img.src = getFrameUrl(i)
      img.onload = () => {
        loaded++
        if (loaded === 1) drawFrame(0) // Draw first frame immediately
      }
      images.push(img)
    }
    framesRef.current = images

    // Scroll trigger
    const st = ScrollTrigger.create({
      trigger: sectionRef.current,
      start: 'top top',
      end: `+=${window.innerHeight * scrollLength}`,
      pin: true,
      scrub: 0.2,
      onUpdate: (self) => {
        const frameIndex = Math.min(
          Math.floor(self.progress * frameCount),
          frameCount - 1
        )
        if (frameIndex !== currentFrame.current) drawFrame(frameIndex)
      },
    })

    return () => st.kill()
  }, [frameCount, getFrameUrl, scrollLength, drawFrame])

  return (
    <div ref={sectionRef} className="relative h-screen w-full overflow-hidden">
      <canvas ref={canvasRef} className="absolute inset-0 w-full h-full object-cover" />
    </div>
  )
}
```

Use this only for premium product showcases where smooth scrubbing is critical. For most
client sites, the simpler `ScrollVideo` component with video.currentTime is sufficient.

## Mobile Fallback Pattern

On mobile, scroll-controlled video is unreliable (iOS restricts video.currentTime
seeking, performance is poor). Always provide a static fallback:

```tsx
'use client'

import { useState, useEffect } from 'react'
import dynamic from 'next/dynamic'

const ScrollVideo = dynamic(() => import('./ScrollVideo'), { ssr: false })

interface ResponsiveVideoSectionProps {
  videoSrc: string
  posterSrc: string
  mobileFallbackSrc: string // Static image for mobile
  scrollLength?: number
  children?: React.ReactNode
}

export default function ResponsiveVideoSection(props: ResponsiveVideoSectionProps) {
  const [isMobile, setIsMobile] = useState(true) // Default to mobile (SSR safe)

  useEffect(() => {
    setIsMobile(window.innerWidth < 768 || 'ontouchstart' in window)
  }, [])

  if (isMobile) {
    return (
      <div className="relative h-screen w-full overflow-hidden">
        <img
          src={props.mobileFallbackSrc}
          alt=""
          className="absolute inset-0 w-full h-full object-cover"
        />
        {props.children && (
          <div className="absolute inset-0 z-10 flex items-center justify-center">
            {props.children}
          </div>
        )}
      </div>
    )
  }

  return (
    <ScrollVideo
      src={props.videoSrc}
      poster={props.posterSrc}
      scrollLength={props.scrollLength}
    >
      {props.children}
    </ScrollVideo>
  )
}
```

## Video Prompt Guidelines

When writing prompts for `generate_video()` or `generate_transition_video()`:

### DO
- Describe camera movement explicitly: "slow dolly forward", "orbital pan left to right"
- Specify lighting: "warm golden hour light from camera left", "cool blue ambient"
- Include texture/material details: "polished marble surface", "rough concrete wall"
- Reference the brand colors: "dominant warm cream (#F5E6D3) with touches of burgundy"
- Keep it abstract/atmospheric — no text, logos, or faces
- Specify duration: "6 second smooth loop" or "8 second linear progression"

### DO NOT
- Include text, words, letters, or logos in any prompt
- Request rapid camera movements (bad for scroll scrubbing)
- Use complex multi-scene narratives (keep it one continuous shot)
- Request people's faces (AI generation artifacts)
- Use prompts longer than 200 words (diminishing returns)

### Example Prompts by Industry

**Restaurant**: "Slow overhead dolly shot of a rustic wooden table with warm ambient lighting. Steam rises gently from a freshly prepared dish. Soft bokeh background of a cozy restaurant interior. Warm color palette: cream, amber, deep brown. 6 seconds, no text."

**Law Firm**: "Slow orbital pan around a modern glass office building at twilight. Cool blue and warm interior lighting creates contrast. Reflections of city lights in the glass facade. Professional, authoritative atmosphere. Navy and silver tones. 8 seconds, no text."

**Salon**: "Slow macro dolly through abstract flowing liquid in soft pink and lavender tones. Iridescent surface catches light creating rainbow reflections. Dreamy, luxurious atmosphere. Smooth and continuous camera movement. 6 seconds, no text."

**Tech Startup**: "Slow forward dolly through a dark space filled with floating luminous geometric shapes. Cyan and electric blue light traces form data-like patterns. Particles scatter on approach. Futuristic, innovative atmosphere. 8 seconds, no text."
