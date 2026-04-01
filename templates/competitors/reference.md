# Competitor Analysis Deck — Generation Reference

Based on the same viewport-locked slide system as the pitch deck. Read this before generating a competitor analysis.

## Format

- **Single self-contained HTML file** — all CSS/JS inline, zero dependencies
- **Viewport-locked slides** — every `.slide` is exactly 100vh, no scrolling within slides
- **Scroll-snap navigation** — arrow keys, space, scroll, swipe all work
- Output to: `public/competitors/index.html` (Vercel serves it at `/competitors/`)

## Mandatory Rules

1. Include the FULL contents of `templates/pitch/viewport-base.css` inline in `<style>`
2. ALL font sizes and spacing must use `clamp()` — never fixed px/rem
3. Every `.slide` must have `height: 100vh; height: 100dvh; overflow: hidden`
4. Use fonts from Google Fonts — never system fonts
5. Never negate CSS functions directly — use `calc(-1 * clamp(...))` instead
6. Use a clean analytical font pair: **Space Grotesk** for headings, **DM Sans** for body — NOT decorative display fonts
7. Color-code quality signals: green (`#22c55e`) for good, amber (`#f59e0b`) for medium, red (`#ef4444`) for poor

## Content Density Per Slide

| Slide Type          | Max Content                                                        |
|---------------------|--------------------------------------------------------------------|
| Title slide         | 1 heading + 1 subtitle + tagline                                  |
| Market overview     | 1 heading + 4 stat badges + 1 paragraph                           |
| Competitor spotlight| Name/rating row + 2-col layout (metrics left, assessment right)    |
| Comparison grid     | 1 heading + responsive table (6 rows x 6 cols max)                |
| Gap analysis        | 1 heading + 3-4 opportunity statements                            |
| Recommendations     | 1 heading + 3-4 action items                                      |

Content exceeds limits? **Split into multiple slides. Never cram.**

---

## Slide Structure (8–10 slides)

### Slide 1: Title

- "Competitive Landscape" as main heading
- "Prepared for [COMPANY NAME]" subtitle
- "Market Intelligence by Clarmi Design Studio" small text
- Total competitors analyzed stat in accent color

### Slide 2: Market Overview

- 4 stat badges in a horizontal row:
  - **"X Competitors"** — total analyzed
  - **"Avg ★ X.X"** — average Google rating
  - **"Avg Site Score X.X/10"** — average website quality
  - **"Price Range $–$$$"** — range across competitors
- Brief paragraph: "We analyzed the top [N] competitors within [radius] miles of [Company]. Here's how the local market stacks up."
- Keep it high-level — details come in the spotlight slides

**Stat badge CSS**:
```css
.stat-badge {
    background: #111827;
    border: 1px solid #1f2937;
    border-radius: clamp(6px, 1vw, 12px);
    padding: clamp(0.5rem, 1.5vw, 1.25rem);
    text-align: center;
}
.stat-badge .stat-value {
    font-size: var(--h2-size);
    font-weight: 700;
    color: var(--accent);
}
.stat-badge .stat-label {
    font-size: var(--small-size);
    color: #9ca3af;
    margin-top: clamp(0.15rem, 0.5vw, 0.4rem);
}
```

### Slides 3–7: Competitor Spotlights (one per competitor, ranked by relevance)

Each spotlight slide has a two-column layout:

**Header row** (spans full width):
- Competitor name (large `--h2-size` heading) — **link to their website** if they have one (`<a href="[url]" target="_blank" rel="noopener">` styled with accent underline on hover, not default blue). If no website, show name as plain text with a `(no website)` label in muted color.
- Distance badge: `"0.3 mi away"` in a small pill/tag
- Price level: styled `$` symbols
- Small "Visit site &rarr;" link next to the website score bar (only if website exists)

**Left column — Metrics**:
- **Google rating**: CSS stars (★★★★☆) + numeric `(4.2)` + review count `"85 reviews"`
- **Website score**: horizontal bar (width = score × 10%) with numeric label `"6.2 / 10"`
- **Breakdown mini-bars** for each dimension: Visual, UX, Content, Technical, Mobile — smaller bars stacked vertically with labels

**Right column — Assessment**:
- **Strengths** (green text, checkmark prefix, max 3)
- **Weaknesses** (red/amber text, cross prefix, max 3)

If a competitor has no website, show "No website" with a score of 0 and a single weakness: "No online presence — invisible to search." Display the name as plain text (not a link) with `(no website)` in muted color next to it.

**Competitor link CSS**:
```css
.competitor-link {
    color: #fff;
    text-decoration: none;
    border-bottom: 2px solid transparent;
    transition: border-color 0.2s;
}
.competitor-link:hover {
    border-bottom-color: var(--accent);
}
.visit-site {
    font-size: var(--small-size);
    color: var(--accent);
    text-decoration: none;
    opacity: 0.7;
    transition: opacity 0.2s;
}
.visit-site:hover { opacity: 1; }
```

#### Rating Stars CSS
```css
.stars {
    color: #f59e0b;
    font-size: var(--body-size);
    letter-spacing: 2px;
}
.stars .empty {
    color: #374151;
}
```
Render as: `<span class="stars">★★★★<span class="empty">☆</span></span>`

To show fractional ratings (e.g. 4.3), round to nearest half-star. Use `★` for full, `½` or a half-width span for half, `☆` for empty.

#### Score Bar CSS
```css
.score-bar {
    background: #1f2937;
    border-radius: 4px;
    height: clamp(6px, 1vh, 10px);
    width: 100%;
    overflow: hidden;
    position: relative;
}
.score-bar-fill {
    height: 100%;
    border-radius: 4px;
    width: 0;
    transition: width 0.8s cubic-bezier(0.16, 1, 0.3, 1);
}
.slide.visible .score-bar-fill {
    width: var(--score-width);
}
.score-bar-fill.good { background: #22c55e; }
.score-bar-fill.medium { background: #f59e0b; }
.score-bar-fill.poor { background: #ef4444; }
```
Set `--score-width` inline: `style="--score-width: 62%"` for a 6.2/10 score.
Color thresholds: **good** ≥ 7, **medium** 5–6, **poor** ≤ 4.

#### Mini Breakdown Bars
Same as score bars but smaller:
```css
.mini-bar {
    display: flex;
    align-items: center;
    gap: clamp(0.3rem, 0.8vw, 0.6rem);
    margin-bottom: clamp(0.15rem, 0.4vh, 0.3rem);
}
.mini-bar-label {
    font-size: var(--small-size);
    color: #9ca3af;
    width: clamp(3rem, 8vw, 5rem);
    text-align: right;
    flex-shrink: 0;
}
.mini-bar .score-bar {
    height: clamp(4px, 0.6vh, 6px);
    flex: 1;
}
.mini-bar-value {
    font-size: var(--small-size);
    color: #d1d5db;
    width: clamp(1.5rem, 3vw, 2rem);
    flex-shrink: 0;
}
```

#### Price Level CSS
```css
.price-level span {
    color: #374151;
    font-weight: 600;
    font-size: var(--body-size);
}
.price-level span.active {
    color: #22c55e;
}
```
Render active `$` symbols up to the level. PRICE_LEVEL_INEXPENSIVE = 1 dollar, MODERATE = 2, EXPENSIVE = 3, VERY_EXPENSIVE = 4:
```html
<span class="price-level">
    <span class="active">$</span><span class="active">$</span><span>$</span><span>$</span>
</span>
```

#### Strength / Weakness CSS
```css
.assessment-list {
    list-style: none;
    padding: 0;
    margin: 0;
    display: flex;
    flex-direction: column;
    gap: clamp(0.3rem, 0.8vh, 0.6rem);
}
.assessment-list li {
    font-size: var(--body-size);
    line-height: 1.4;
}
.strength { color: #22c55e; }
.strength::before { content: "✓ "; font-weight: 700; }
.weakness { color: #ef4444; }
.weakness::before { content: "✗ "; font-weight: 700; }
```

### Slide 8: Head-to-Head Comparison

Responsive grid comparing all 5 competitors + the prospect across key metrics.

**Desktop (≥ 601px)**: HTML `<table>` with fixed columns.

| Metric     | [Prospect] | Comp 1 | Comp 2 | Comp 3 | Comp 4 | Comp 5 |
|------------|------------|--------|--------|--------|--------|--------|
| Rating     | ★ 4.5      | ★ 4.2  | ★ 3.8  | ...    | ...    | ...    |
| Reviews    | 120        | 85     | 210    | ...    | ...    | ...    |
| Price      | $$         | $$$    | $$     | ...    | ...    | ...    |
| Site Score | —          | 6.2    | 4.5    | ...    | ...    | ...    |
| Mobile     | —          | ✓      | ✗      | ...    | ...    | ...    |
| CTA        | —          | ✓      | ✗      | ...    | ...    | ...    |

- **Prospect column** highlighted with accent color border or background
- Use `✓` (green) and `✗` (red) for boolean fields
- Highest rating/score in each row should be **bold**

**Mobile (< 600px)**: Switch to stacked comparison cards.

```css
.comparison-table {
    width: 100%;
    border-collapse: separate;
    border-spacing: 0;
    font-size: var(--small-size);
}
.comparison-table th,
.comparison-table td {
    padding: clamp(0.2rem, 0.5vw, 0.5rem);
    text-align: center;
    border-bottom: 1px solid #1f2937;
}
.comparison-table th {
    color: #9ca3af;
    font-weight: 400;
    font-size: var(--small-size);
}
.comparison-table .prospect-col {
    background: rgba(var(--accent-rgb), 0.08);
    border-left: 2px solid var(--accent);
    border-right: 2px solid var(--accent);
}
@media (max-width: 600px) {
    .comparison-table { display: none; }
    .comparison-cards { display: flex; flex-direction: column; gap: var(--element-gap); }
}
@media (min-width: 601px) {
    .comparison-cards { display: none; }
}
```

### Slide 9: Gap Analysis

**Heading**: "Where You Can Win"

3–4 opportunity cards based on common competitor weaknesses:
- Each card: bold title + 1-sentence description referencing actual data
- e.g. **"Mobile Gap"** — "3 of 5 competitors score below 5/10 on mobile. A mobile-first build puts you ahead of 60% of the market."
- e.g. **"Social Proof"** — "Only 1 competitor showcases testimonials. Featuring real reviews builds instant trust."
- e.g. **"Speed Wins"** — "4 competitors run WordPress with 5s+ load times. A modern stack loads in under 1 second."

**Rules**:
- Every opportunity MUST reference actual competitor data — name specific numbers or competitor names
- No generic advice — every statement traces back to what the analysis found
- Max 4 opportunities, each under 2 sentences
- Use the `common_competitor_weaknesses` data from `generate_competitor_report`

```css
.opportunity-card {
    background: #111827;
    border-left: 3px solid var(--accent);
    padding: clamp(0.5rem, 1.5vw, 1rem) clamp(0.75rem, 2vw, 1.5rem);
    border-radius: 0 clamp(4px, 0.5vw, 8px) clamp(4px, 0.5vw, 8px) 0;
}
.opportunity-card h3 {
    font-size: var(--h3-size);
    margin-bottom: clamp(0.2rem, 0.5vw, 0.4rem);
}
.opportunity-card p {
    font-size: var(--body-size);
    color: #d1d5db;
    line-height: 1.5;
}
```

### Slide 10: Recommendations

**Heading**: "Your Competitive Edge"

3–4 concrete, actionable recommendations for the website build:
- Format: **bold action title** + 1-line explanation
- e.g. **"Launch with online ordering"** — "Only 1 competitor offers it, and their UX scored 3/10. A clean ordering flow is an instant differentiator."
- e.g. **"Hero with video background"** — "Zero competitors use video. Cinematic first impression sets you apart."
- e.g. **"Prominent Google reviews"** — "You have 4.7 stars with 200+ reviews — your competitors average 3.9. Make this the first thing visitors see."

These recommendations should directly inform Step 3 (Build) of the website pipeline.

**Rules**:
- Each recommendation must cite competitor data as evidence
- Action-oriented — "Launch X", "Add Y", "Feature Z" — not "Consider" or "Think about"
- These are commitments for the build, not suggestions

---

## Design Direction

- **Dark theme**: `#0a0a0a` background, `#ffffff` text — same as pitch
- **One accent color** from the prospect's brand palette — used for prospect highlights, borders, stat values
- **Analytical aesthetic**: more data-dense than the pitch, but still clean and scannable
- **Color coding**: green (`#22c55e`) strengths/good scores, amber (`#f59e0b`) medium/warnings, red (`#ef4444`) poor/weaknesses — these are universal, NOT the accent color
- **Competitor data**: muted gray (`#9ca3af` text, `#111827` backgrounds) to contrast with accent-highlighted prospect data
- **Data visualization**: ALL CSS-only — no SVG, no canvas, no chart libraries
- Bold oversized headings, generous whitespace between data sections
- Score bars and stars are the primary visual language

## CSS Custom Properties

Define at the top of `<style>` (after viewport-base.css):
```css
:root {
    --accent: [prospect brand color];
    --accent-rgb: [r, g, b version for rgba()];
    --good: #22c55e;
    --medium: #f59e0b;
    --poor: #ef4444;
    --muted: #9ca3af;
    --card-bg: #111827;
    --border: #1f2937;
}
```

## Animation Pattern

Same as pitch — `.reveal` with IntersectionObserver:

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
.reveal:nth-child(1) { transition-delay: 0.1s; }
.reveal:nth-child(2) { transition-delay: 0.2s; }
.reveal:nth-child(3) { transition-delay: 0.3s; }
.reveal:nth-child(4) { transition-delay: 0.4s; }
.reveal:nth-child(5) { transition-delay: 0.5s; }
```

Score bars animate their width on slide entry (fill starts at 0, transitions to `--score-width` when `.slide.visible`).

## JS Requirements

Same `SlidePresentation` class as the pitch deck:
- IntersectionObserver adding `.visible` class on scroll
- Keyboard nav (arrows, space, page up/down)
- Touch/swipe support
- Progress bar
- Nav dots

## DO NOT

- Add a closing/footer slide — the last slide is Recommendations, nothing after
- Use generic fonts (Inter, Roboto, Arial, system fonts)
- Use ultra-wide/stretched bold display fonts (Unbounded, Rubik Mono One, etc.)
- Use images, illustrations, mockups, or screenshots
- Use placeholder content — every data point must come from actual competitor analysis data
- Scroll within slides
- Use fixed px/rem sizes — everything uses `clamp()`
- Invent competitor data — only use what the tools returned
- Show more than 5 competitors in the spotlights
- Include the prospect's own business in the competitor list
- Use SVG, canvas, or external chart libraries — CSS-only data visualization
