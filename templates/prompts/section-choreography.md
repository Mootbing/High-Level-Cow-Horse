# Section Flow & Choreography Guide

How to compose sections into a cohesive scroll experience. Good immersive sites
have rhythm — fast/slow, active/passive, dense/spacious — like music.

## The Rhythm Principle

A page that's ALL cinematic feels exhausting. A page that's ALL static feels boring.
Alternate between **active** (scroll-driven, interactive) and **passive** (static, readable) sections.

```
ACTIVE  → Hero (3D/video, scroll-pinned)
PASSIVE → Text reveal (simple, breathing room)
ACTIVE  → Scroll transition (video morph, pinned)
PASSIVE → Feature cards (stagger entrance, then static)
ACTIVE  → Parallax gallery or horizontal scroll
PASSIVE → Stats/testimonials (simple animations)
ACTIVE  → CTA (magnetic button, gradient/particles)
PASSIVE → Footer (stagger-in, then static)
```

**Rule of thumb**: Never stack 3 active sections in a row. The user needs rest.

## Section Pacing

| Section Type | Scroll Length | Feel |
|-------------|-------------|------|
| Hero (pinned) | 2-3x viewport | "Entering a world" — slow, cinematic |
| Text Reveal (scrubbed) | 1.5-2x viewport | "Discovering a message" — contemplative |
| Scroll Transition (pinned) | 2-2.5x viewport | "Morphing between ideas" — magical |
| Feature Cards (triggered) | 1x viewport | "Here's what we offer" — informational, quick |
| Parallax Section (scrubbed) | 1.5x viewport | "Depth and richness" — immersive but not locked |
| Horizontal Scroll (pinned) | Width of content | "Exploring a gallery" — discovery |
| Stats/Counters (triggered) | 0.5x viewport | "Quick proof" — punchy and fast |
| CTA (triggered) | 0.75x viewport | "Take action" — clear and immediate |
| Footer (triggered) | 0.5x viewport | "Wrapping up" — informational |

## Composition Templates

### Template A: "The Showcase" (most common — restaurants, salons, retail)
```
1. Scroll Video Hero (3x pin) — brand video plays through
2. Text Reveal — mission statement or tagline
3. Feature Cards — services/menu highlights (stagger entrance)
4. Parallax Gallery — photos of work/products at different depths
5. Stats — "500+ happy customers", "4.9 Google rating"
6. CTA — "Book Now" / "Visit Us" with magnetic button
7. Footer
```
Total scroll: ~12x viewport heights. Duration: ~45-60 seconds of engaged scrolling.

### Template B: "The Experience" (tech, agencies, luxury)
```
1. 3D Scene Hero (2x pin) — glass/wireframe object, scroll dissolves it
2. Scroll Transition — Veo morph from abstract to concrete
3. Text Reveal — bold value proposition, word by word
4. Horizontal Scroll — services/portfolio as horizontal cards
5. Feature Grid — key differentiators (stagger + 3D tilt)
6. CTA — gradient shader background + magnetic button
7. Footer
```
Total scroll: ~14x viewport heights. Duration: ~60-90 seconds.

### Template C: "The Story" (real estate, hospitality, education)
```
1. Scroll Video Hero (3x pin) — aerial/establishing shot
2. Text Reveal — "Where [quality] meets [quality]"
3. Parallax Gallery — property/campus photos at different speeds
4. Scroll Transition — morph from exterior to interior
5. Feature Cards — amenities/programs (stagger entrance)
6. Stats — key numbers (animated counters)
7. CTA — "Schedule a Visit" / "Apply Now"
8. Footer
```
Total scroll: ~15x viewport heights. Duration: ~75-90 seconds.

### Template D: "Quick & Bold" (when minimal content is available)
```
1. Kinetic Typography Hero — giant animated headline
2. Feature Cards — 3 key points (stagger entrance)
3. CTA — simple, clean, effective
4. Footer
```
Total scroll: ~5x viewport heights. Duration: ~20 seconds.

## Transition Rules Between Sections

### Hero → First Content Section
- Hero should **dissolve** (fade + scale down) as user scrolls past
- First content section should fade in with subtle translateY
- Never hard-cut — always overlap the transition

### Between Passive Sections
- Use IntersectionObserver-triggered fade-in (not scroll-scrubbed)
- 0.8-1s entrance animation per section
- Each section should have its own clear visual identity (background color shift, spacing)

### Between Active (Pinned) Sections
- **Mandatory breathing room**: insert a non-pinned section between two pinned ones
- Without this, users feel "trapped" — they scroll and scroll but nothing moves

### Into CTA Section
- CTA should feel like arrival, not interruption
- Use a background color shift (darker → lighter or vice versa) to signal "this is different"
- The CTA button should be the most interactive element on the page (magnetic, hover glow)

## Visual Weight Distribution

```
Section 1 (Hero):        █████████████████████ (heavy — 3D/video, maximum visual impact)
Section 2 (Text):        ████ (light — breathing room, typography-only)
Section 3 (Transition):  ████████████ (medium-heavy — video morph, but brief)
Section 4 (Features):    ████████ (medium — cards with animation, informational)
Section 5 (Gallery):     ████████████████ (heavy — parallax images, rich visual)
Section 6 (Stats):       ██ (very light — just numbers, fast)
Section 7 (CTA):         ██████ (medium — button interaction, gradient bg)
Section 8 (Footer):      █ (minimal — just info)
```

The "weight" curve should be: HIGH → low → MEDIUM → medium → HIGH → low → MEDIUM → minimal

## Color Flow

Sections should have subtle background color shifts to create visual chapters:

```css
/* Example: warm restaurant */
.hero { background: transparent; } /* Video fills this */
.text-reveal { background: #1a0f0a; } /* Dark warm brown */
.features { background: #f5ebe0; } /* Light cream */
.gallery { background: #1a0f0a; } /* Back to dark */
.stats { background: #f5ebe0; } /* Light again */
.cta { background: linear-gradient(135deg, #722f37, #1a0f0a); } /* Brand gradient */
.footer { background: #0a0505; } /* Darkest */
```

Alternate between light and dark creates visual rhythm. The CTA section should be the most
visually distinct — it's the climax of the page.

## Animation Timing Orchestration

When multiple elements animate in a section, they must feel choreographed, not random:

### Entrance Sequence for a Content Section
```
0ms    — Section background color transition starts
100ms  — Heading begins fade-in + translateY
200ms  — Subheading begins (stagger)
350ms  — First card/item begins
450ms  — Second card (stagger: 100ms)
550ms  — Third card
700ms  — Supporting text/details
900ms  — CTA button (always last — the payoff)
```

### Scrub Sequence for a Pinned Section
```
0-20%   — First element fades in
20-40%  — First element holds + second fades in
40-50%  — Brief pause (both visible)
50-60%  — First fades out
60-80%  — Third element fades in
80-100% — Section transitions to next
```

Never animate everything at once. Stagger creates hierarchy and guides the eye.
