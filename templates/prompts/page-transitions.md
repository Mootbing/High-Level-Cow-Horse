# Page Transition Patterns

For multi-page sites (e.g., sites with separate About, Services, Contact pages),
use View Transitions API for native-feeling page transitions.

## View Transitions API (Next.js App Router)

The View Transitions API provides native browser-level page transitions.
Supported in Chrome 111+, Safari 18+. Gracefully falls back to instant navigation.

### Setup in Next.js

```tsx
// app/layout.tsx — enable view transitions
export const metadata = {
  // ... other metadata
}

// The ViewTransition component wraps page content
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <Navigation />
        <main style={{ viewTransitionName: 'main-content' }}>
          {children}
        </main>
      </body>
    </html>
  )
}
```

```css
/* globals.css — transition styles */

/* Default crossfade transition */
::view-transition-old(main-content) {
  animation: fadeOut 0.3s ease-in both;
}
::view-transition-new(main-content) {
  animation: fadeIn 0.3s ease-out both;
}

@keyframes fadeOut {
  to { opacity: 0; transform: translateY(-10px); }
}
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
}

/* Slide transition for specific elements */
::view-transition-old(hero-image) {
  animation: slideOut 0.4s ease-in both;
}
::view-transition-new(hero-image) {
  animation: slideIn 0.4s ease-out both;
}

@keyframes slideOut {
  to { transform: translateX(-100%); opacity: 0; }
}
@keyframes slideIn {
  from { transform: translateX(100%); opacity: 0; }
}
```

### Named Transitions for Shared Elements

```tsx
// Card on listing page
<div style={{ viewTransitionName: `project-${id}` }}>
  <img src={thumbnail} alt={title} />
  <h3>{title}</h3>
</div>

// Same element on detail page — browser morphs between them
<div style={{ viewTransitionName: `project-${id}` }}>
  <img src={fullImage} alt={title} />
  <h1>{title}</h1>
</div>
```

## Framer Motion Page Transitions (Fallback)

For browsers without View Transitions API support, or for more complex animations.

```tsx
// components/PageTransition.tsx
'use client'

import { motion, AnimatePresence } from 'framer-motion'
import { usePathname } from 'next/navigation'

const variants = {
  hidden: { opacity: 0, y: 20 },
  enter: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -20 },
}

export default function PageTransition({ children }: { children: React.ReactNode }) {
  const pathname = usePathname()

  return (
    <AnimatePresence mode="wait">
      <motion.div
        key={pathname}
        variants={variants}
        initial="hidden"
        animate="enter"
        exit="exit"
        transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
      >
        {children}
      </motion.div>
    </AnimatePresence>
  )
}
```

## Clip-Path Page Transition (Premium)

A full-screen circle/rectangle wipe between pages.

```tsx
'use client'

import { motion } from 'framer-motion'
import { usePathname } from 'next/navigation'

export default function ClipPathTransition({ children }: { children: React.ReactNode }) {
  const pathname = usePathname()

  return (
    <div className="relative">
      {/* Transition overlay */}
      <motion.div
        key={`overlay-${pathname}`}
        className="fixed inset-0 z-50 bg-black pointer-events-none"
        initial={{ clipPath: 'circle(150% at 50% 50%)' }}
        animate={{ clipPath: 'circle(0% at 50% 50%)' }}
        transition={{ duration: 0.8, ease: [0.76, 0, 0.24, 1], delay: 0.2 }}
      />
      
      {/* Page content */}
      <motion.div
        key={pathname}
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.5, delay: 0.3 }}
      >
        {children}
      </motion.div>
    </div>
  )
}
```

## When to Use Page Transitions

Most Clarmi client sites are **single-page** — all sections on one page with scroll navigation.
Page transitions are only needed when there are **separate routes**:

| Site Type | Transition Approach |
|-----------|-------------------|
| Single-page landing (most common) | No page transitions needed — scroll animations handle it |
| Multi-page with case studies | View Transitions API with shared element morph |
| Multi-page with separate services | Framer Motion fade/slide |
| Portfolio with project detail pages | Clip-path wipe transition |

## Rules

- **Single-page sites don't need page transitions** — focus scroll animation budget there
- View Transitions API is preferred (native, performant, progressive enhancement)
- Framer Motion transitions add bundle size — only use if needed
- Transition duration: 0.3-0.5s (longer feels sluggish)
- Always ensure content is accessible during transitions (no trapping focus)
