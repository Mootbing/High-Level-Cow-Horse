# Section Flow & Choreography Guide

How to compose sections into a cohesive scroll experience. Good immersive sites
have rhythm — fast/slow, active/passive, dense/spacious — like music.

## The Rhythm Principle

A page that's ALL cinematic feels exhausting. A page that's ALL static feels boring.
Alternate between **active** (scroll-driven, interactive) and **passive** (static, readable) sections.

The Three.js persistent scene runs behind ALL content sections, providing ambient visual depth.
ReactBits components add polish to every section. The hero is ALWAYS scroll-controlled video.

```
ACTIVE  → Hero (scroll video, pinned — keyframe A→B via Veo 3.1)
PASSIVE → Text reveal (ReactBits text animation, Three.js floats behind)
ACTIVE  → Scroll transition (video morph, pinned)
PASSIVE → Feature cards (ReactBits tilt cards, Three.js ambient behind)
ACTIVE  → Parallax gallery or horizontal scroll
PASSIVE → Stats/testimonials (ReactBits counters, Three.js particle accents)
ACTIVE  → CTA (ReactBits magnetic button + aurora bg, Three.js accent elements)
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
1. Scroll Video Hero (3x pin) — keyframe A→B video plays frame-by-frame on scroll
2. Text Reveal — mission statement or tagline (ReactBits blur text, Three.js particles behind)
3. Feature Cards — services/menu highlights (ReactBits tilt cards, Three.js warm organic shapes)
4. Parallax Gallery — photos of work/products at different depths (Three.js floating elements)
5. Stats — "500+ happy customers", "4.9 Google rating" (ReactBits counters)
6. CTA — "Book Now" / "Visit Us" (ReactBits magnetic button + aurora background)
7. Footer
```
Total scroll: ~12x viewport heights. Duration: ~45-60 seconds of engaged scrolling.

### Template B: "The Experience" (tech, agencies, luxury)
```
1. Scroll Video Hero (3x pin) — keyframe A→B video, abstract opening to concrete reveal
2. Scroll Transition — Veo morph from hero end state to content aesthetic
3. Text Reveal — bold value proposition (ReactBits split text, Three.js wireframe network behind)
4. Horizontal Scroll — services/portfolio as horizontal cards (ReactBits spotlight cards)
5. Feature Grid — key differentiators (ReactBits tilt cards, Three.js geometric accents)
6. CTA — ReactBits magnetic button + aurora bg, Three.js glass elements
7. Footer
```
Total scroll: ~14x viewport heights. Duration: ~60-90 seconds.

### Template C: "The Story" (real estate, hospitality, education)
```
1. Scroll Video Hero (3x pin) — keyframe A: wide exterior → keyframe B: intimate interior
2. Text Reveal — "Where [quality] meets [quality]" (ReactBits blur text)
3. Parallax Gallery — property/campus photos (Three.js golden architecture forms behind)
4. Scroll Transition — morph from exterior to interior
5. Feature Cards — amenities/programs (ReactBits spotlight cards)
6. Stats — key numbers (ReactBits animated counters, Three.js particle burst)
7. CTA — "Schedule a Visit" / "Apply Now" (ReactBits magnetic button)
8. Footer
```
Total scroll: ~15x viewport heights. Duration: ~75-90 seconds.

### Template D: "Quick & Bold" (minimal content available)
```
1. Scroll Video Hero (2x pin) — keyframe A→B, shorter scroll duration
2. Feature Cards — 3 key points (ReactBits tilt cards, Three.js ambient shapes)
3. CTA — ReactBits magnetic button + gradient background
4. Footer
```
Total scroll: ~7x viewport heights. Duration: ~25 seconds.

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

Three.js persistent scene runs behind ALL sections below the hero, adding ambient depth throughout.

```
Section 1 (Hero):        █████████████████████ (heavy — scroll video, maximum visual impact)
Section 2 (Text):        █████ (light — ReactBits text anim + Three.js floats behind)
Section 3 (Transition):  ████████████ (medium-heavy — video morph, but brief)
Section 4 (Features):    █████████ (medium — ReactBits cards + Three.js ambient shapes)
Section 5 (Gallery):     ████████████████ (heavy — parallax images + Three.js depth layers)
Section 6 (Stats):       ███ (light — ReactBits counters + Three.js particle accents)
Section 7 (CTA):         ███████ (medium — ReactBits magnetic btn + aurora + Three.js)
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
