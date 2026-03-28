'use client'

import { useEffect, useRef } from 'react'
import gsap from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'

gsap.registerPlugin(ScrollTrigger)

interface Card {
  title: string
  description: string
}

interface ScrollCardsProps {
  cards: Card[]
}

export function ScrollCards({ cards }: ScrollCardsProps) {
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const ctx = gsap.context(() => {
      const items = containerRef.current?.querySelectorAll('.scroll-card')
      items?.forEach((card, i) => {
        gsap.from(card, {
          x: i % 2 === 0 ? -100 : 100,
          opacity: 0,
          duration: 1,
          ease: 'power3.out',
          scrollTrigger: {
            trigger: card,
            start: 'top 80%',
            end: 'top 50%',
            toggleActions: 'play none none reverse',
          },
        })
      })
    }, containerRef)

    return () => ctx.revert()
  }, [])

  return (
    <section ref={containerRef} className="min-h-screen py-32">
      <div className="mx-auto max-w-4xl space-y-16 px-8">
        {cards.map((card, i) => (
          <div
            key={i}
            className="scroll-card rounded-3xl border border-white/10 bg-white/5 p-12 backdrop-blur-sm"
          >
            <h3 className="font-heading text-3xl font-bold">{card.title}</h3>
            <p className="mt-4 text-lg text-white/60">{card.description}</p>
          </div>
        ))}
      </div>
    </section>
  )
}
