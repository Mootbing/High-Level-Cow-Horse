'use client'

import { useEffect, useRef } from 'react'
import gsap from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'
import Image from 'next/image'

gsap.registerPlugin(ScrollTrigger)

interface ParallaxSectionProps {
  images: string[]
  title: string
}

export function ParallaxSection({ images, title }: ParallaxSectionProps) {
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const ctx = gsap.context(() => {
      const items = containerRef.current?.querySelectorAll('.parallax-item')
      items?.forEach((item, i) => {
        gsap.fromTo(
          item,
          { y: 100 + i * 30, opacity: 0 },
          {
            y: -50 * (i + 1),
            opacity: 1,
            scrollTrigger: {
              trigger: item,
              start: 'top bottom',
              end: 'bottom top',
              scrub: 1,
            },
          }
        )
      })
    }, containerRef)

    return () => ctx.revert()
  }, [])

  return (
    <section ref={containerRef} className="relative min-h-screen py-32">
      <h2 className="mb-20 text-center font-heading text-5xl font-bold">
        {title}
      </h2>
      <div className="mx-auto grid max-w-6xl grid-cols-1 gap-8 px-8 md:grid-cols-3">
        {images.map((src, i) => (
          <div key={i} className="parallax-item overflow-hidden rounded-2xl">
            <Image
              src={src}
              alt={`Showcase ${i + 1}`}
              width={600}
              height={400}
              className="h-full w-full object-cover"
            />
          </div>
        ))}
      </div>
    </section>
  )
}
