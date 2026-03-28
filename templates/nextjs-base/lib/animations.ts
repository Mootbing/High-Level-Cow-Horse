import gsap from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'

gsap.registerPlugin(ScrollTrigger)

export function fadeInOnScroll(element: HTMLElement, options?: gsap.TweenVars) {
  return gsap.from(element, {
    y: 60,
    opacity: 0,
    duration: 1,
    ease: 'power3.out',
    scrollTrigger: {
      trigger: element,
      start: 'top 85%',
      toggleActions: 'play none none reverse',
    },
    ...options,
  })
}

export function parallax(element: HTMLElement, speed: number = 0.5) {
  return gsap.to(element, {
    y: () => -ScrollTrigger.maxScroll(window) * speed,
    ease: 'none',
    scrollTrigger: {
      start: 0,
      end: 'max',
      scrub: true,
    },
  })
}

export function staggerReveal(elements: HTMLElement[], stagger: number = 0.1) {
  return gsap.from(elements, {
    y: 40,
    opacity: 0,
    stagger,
    duration: 0.8,
    ease: 'power2.out',
    scrollTrigger: {
      trigger: elements[0],
      start: 'top 80%',
      toggleActions: 'play none none reverse',
    },
  })
}
