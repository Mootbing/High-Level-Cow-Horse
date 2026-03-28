# Scroll Animation Patterns

## Available Patterns:

### 1. Scrub Animation
Ties animation progress to scroll position.
```js
gsap.to(element, {
  scrollTrigger: { trigger, start: 'top top', end: 'bottom top', scrub: true },
  y: -100, opacity: 0.3, scale: 1.1
})
```

### 2. Toggle Animation
Plays animation when entering viewport, reverses when leaving.
```js
gsap.from(element, {
  scrollTrigger: { trigger, start: 'top 80%', toggleActions: 'play none none reverse' },
  y: 60, opacity: 0, duration: 1, ease: 'power3.out'
})
```

### 3. Staggered Entrance
Multiple elements animate in sequence.
```js
gsap.from(elements, {
  y: 40, opacity: 0, stagger: 0.1, duration: 0.8,
  scrollTrigger: { trigger: container, start: 'top 80%' }
})
```

### 4. Parallax Layers
Elements move at different speeds relative to scroll.
```js
gsap.to(layer, {
  y: () => -ScrollTrigger.maxScroll(window) * speed,
  scrollTrigger: { start: 0, end: 'max', scrub: true }
})
```

### 5. Text Word-by-Word Reveal
Each word fades in as user scrolls.
```js
words.forEach(word => {
  gsap.from(word, {
    opacity: 0.1,
    scrollTrigger: { trigger: word, start: 'top 80%', end: 'top 40%', scrub: true }
  })
})
```
