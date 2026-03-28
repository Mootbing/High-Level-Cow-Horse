'use client'

import { useEffect, useRef } from 'react'
import gsap from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'

gsap.registerPlugin(ScrollTrigger)

interface TextRevealProps {
  text: string
}

export function TextReveal({ text }: TextRevealProps) {
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const ctx = gsap.context(() => {
      const words = containerRef.current?.querySelectorAll('.word')
      words?.forEach((word, i) => {
        gsap.from(word, {
          opacity: 0.1,
          scrollTrigger: {
            trigger: word,
            start: 'top 80%',
            end: 'top 40%',
            scrub: true,
          },
        })
      })
    }, containerRef)

    return () => ctx.revert()
  }, [])

  return (
    <section ref={containerRef} className="flex min-h-[50vh] items-center justify-center px-8">
      <p className="max-w-4xl text-center font-heading text-4xl font-bold leading-relaxed md:text-6xl">
        {text.split(' ').map((word, i) => (
          <span key={i} className="word inline-block mr-[0.25em]">
            {word}
          </span>
        ))}
      </p>
    </section>
  )
}
