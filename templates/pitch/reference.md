# Pitch Slide Generation Reference

Based on [frontend-slides](https://github.com/zarazhangrui/frontend-slides). Read this before generating a pitch.

## Format

- **Single self-contained HTML file** — all CSS/JS inline, zero dependencies
- **Viewport-locked slides** — every `.slide` is exactly 100vh, no scrolling within slides
- **Scroll-snap navigation** — arrow keys, space, scroll, swipe all work
- Output to: `public/pitch/index.html` (Vercel serves it at `/pitch/`)

## Mandatory Rules

1. Include the FULL contents of `templates/pitch/viewport-base.css` inline in `<style>`
2. ALL font sizes and spacing must use `clamp()` — never fixed px/rem
3. Every `.slide` must have `height: 100vh; height: 100dvh; overflow: hidden`
4. Use fonts from Google Fonts — never system fonts
5. Never negate CSS functions directly — use `calc(-1 * clamp(...))` instead

## Content Density Per Slide

| Slide Type    | Max Content                                            |
|---------------|--------------------------------------------------------|
| Title slide   | 1 heading + 1 subtitle + optional tagline              |
| Content slide | 1 heading + 4-6 bullet points OR 1 heading + 2 paragraphs |
| Feature grid  | 1 heading + 6 cards max (2x3 or 3x2)                  |
| Quote slide   | 1 quote (max 3 lines) + attribution                   |

Content exceeds limits? **Split into multiple slides. Never cram.**

## Pitch Slide Structure (5 slides)

### Slide 1: Title
- "Prepared for [COMPANY]" subtitle
- Bold headline referencing their industry
- "A proposal from Clarmi Design Studio"

### Slide 2: The Current Reality
- Use prospect's `site_problems` from `lookup_prospect(url)`
- 3-4 punchy bullets max (split if more)
- Impact statement at bottom

### Slide 3: What We're Proposing
- Text-only — NO images or mockups
- 2 short paragraphs describing the replacement site
- Closing quote: "This is the version of [company] people should see before they walk in."

### Slide 4: Key Improvements
- 3-column grid: Brand Upgrade / Customer Experience / Operational Wins
- 3 bullets each max
- Checkmark accent for each item

### Slide 5: Pricing
- Comparison pricing stack, vertically centered, each row is a label + price:
  1. "AGENCIES" — "$10,000 + $200/mo" — struck through with `text-decoration: line-through`, dimmed opacity
  2. "LOCAL DESIGNERS" — "$5,000 + $150/mo" — struck through with `text-decoration: line-through`, dimmed opacity
  3. "CLARMI" — "$500 + $50/mo" — NOT struck through, full opacity, accent color highlight, largest size
- Animate rows in sequence (stagger reveal): first two appear and get struck, then Clarmi appears bold
- 4 included items below the stack
- Optional add-ons below divider
- "One clean upgrade that pays for itself in new customers."

### Slide 6 (optional): Live Demo
- Only include if `deployed_url` exists
- Link button to the live site
- If not deployed yet, skip this slide entirely

## Design Direction

- **Text-only** — no images, mockups, or screenshots. Typography carries the page.
- Dark theme: `#0a0a0a` background, white text, one accent from prospect's brand palette
- Bold oversized headings, heavy whitespace
- Simple animations only: fade-in + subtle translateY on scroll entry
- Use `.reveal` class + IntersectionObserver pattern from frontend-slides

## Animation Pattern

```css
.reveal {
    opacity: 0;
    transform: translateY(30px);
    transition: opacity 0.6s cubic-bezier(0.16, 1, 0.3, 1),
                transform 0.6s cubic-bezier(0.16, 1, 0.3, 1);
}
.slide.visible .reveal {
    opacity: 1;
    transform: translateY(0);
}
/* Stagger children */
.reveal:nth-child(1) { transition-delay: 0.1s; }
.reveal:nth-child(2) { transition-delay: 0.2s; }
.reveal:nth-child(3) { transition-delay: 0.3s; }
.reveal:nth-child(4) { transition-delay: 0.4s; }
```

## JS Requirements

Include a `SlidePresentation` class with:
- IntersectionObserver adding `.visible` class on scroll
- Keyboard nav (arrows, space, page up/down)
- Touch/swipe support
- Progress bar
- Nav dots

## DO NOT

- Use generic fonts (Inter, Roboto, Arial, system fonts)
- Use ultra-wide/stretched bold display fonts for headings (e.g. Unbounded, Rubik Mono One) — pick elegant, well-proportioned typefaces
- Use images, illustrations, or mockups
- Use placeholder content — every line must reference actual prospect data
- Scroll within slides
- Use fixed px/rem sizes
