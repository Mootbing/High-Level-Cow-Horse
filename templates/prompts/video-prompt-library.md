# Video & Image Prompt Library

Pre-written, tested prompts for Veo (video) and Nano Banana (image) generation.
Customize with the prospect's brand colors and specific details.

## Prompt Structure

Every prompt follows this pattern:
```
[Camera movement] [through/over/around] [subject/scene].
[Lighting description]. [Atmosphere/mood].
[Brand color references]. [Duration]. No text, no words, no logos.
```

## Hero Video Prompts (Veo — 6-8 seconds)

### Restaurant / Bakery / Cafe
```
Slow overhead dolly shot descending toward a rustic wooden table set with artisanal 
dishes. Warm amber candlelight creates soft bokeh in the background. Steam rises 
gently from a freshly prepared plate. Rich textures of wood grain, ceramic, and 
fresh herbs. Color palette: warm cream (#F5E6D3) and deep brown (#3D2914) tones 
with touches of herb green. 8 seconds. No text, no words, no logos.
```

**Variation — coffee shop**:
```
Slow forward dolly through a minimalist coffee bar at golden hour. Warm light 
streams through large windows, catching particles of steam from a fresh pour-over. 
Exposed brick and natural wood surfaces. Soft bokeh of hanging pendant lights in 
background. Warm tones: cream, amber, espresso brown. 6 seconds. No text.
```

### Law Firm / Financial Services
```
Slow orbital pan around a modern glass-and-steel office building at twilight. Cool 
blue interior lighting contrasts with warm amber sunset reflections on the facade. 
Camera reveals the building's geometric precision and authority. Professional, 
confident atmosphere. Navy (#1B2A4A) and silver (#C0C7D0) color palette. 
8 seconds. No text, no words, no logos.
```

### Salon / Beauty / Spa
```
Slow macro dolly through abstract flowing liquid in soft pastel tones. Iridescent 
surface catches shifting light creating rainbow oil-slick reflections. Organic, 
fluid movement suggests luxury and transformation. Soft pink (#F4C2C2), lavender 
(#E6D5F2), and pearl white tones. Dreamy bokeh throughout. 6 seconds. No text.
```

### Tech Startup / SaaS
```
Slow forward tracking shot through a dark void filled with luminous floating 
geometric shapes. Cyan (#00E5FF) and electric blue (#2979FF) light traces form 
data-like flowing patterns between nodes. Particles scatter outward as camera 
approaches. Clean, futuristic, innovative atmosphere. Dark background with neon 
accents. 8 seconds. No text, no words, no logos.
```

### Real Estate / Property
```
Slow cinematic drone shot ascending over a luxury property at golden hour. Warm 
sunlight catches architectural details — clean lines, large windows, manicured 
landscaping. Camera rises to reveal the surrounding neighborhood with soft depth 
of field. Warm golden (#D4A574) and cream white tones. Aspirational, inviting 
atmosphere. 8 seconds. No text.
```

### Retail / E-Commerce
```
Slow dolly forward through a beautifully styled product display. Soft studio 
lighting with clean white surfaces and subtle shadows. Products arranged with 
intentional negative space. Camera glides smoothly at product height. Clean, 
modern, desirable aesthetic. Bright, well-lit with subtle warm tones. 
6 seconds. No text, no words, no logos.
```

### Healthcare / Medical
```
Slow forward tracking through a bright, modern medical facility. Clean white 
surfaces with soft natural light streaming through large windows. Subtle touches 
of calming blue and green. Everything is orderly, clean, and reassuring. Soft 
focus on background details. Professional yet welcoming atmosphere. 
6 seconds. No text.
```

### Construction / Architecture
```
Slow cinematic pan across a modern building under construction, transitioning to 
the completed structure. Golden hour light catches steel beams and glass surfaces. 
Dust particles catch sunlight. Strong geometric lines and angular shadows. 
Industrial materials: concrete, steel, glass. Powerful, precise, authoritative 
atmosphere. 8 seconds. No text, no words, no logos.
```

## Transition Video Prompts (Veo — 4-6 seconds)

### Hero → About (Generic)
```
Smooth cinematic transition from an expansive aerial view gradually descending and 
morphing into an intimate close-up of a workspace. Camera movement is continuous 
and fluid. Lighting shifts from cool exterior to warm interior. Natural, organic 
transition feel. 6 seconds. No text.
```

### Exterior → Interior (Real Estate)
```
Continuous camera push through the front door of a luxury home. Start with the 
exterior facade in warm sunlight, pass through the doorway, and reveal a bright 
open-plan interior with natural light. Smooth, unbroken camera movement. Golden 
hour transitions to diffused interior light. 5 seconds. No text.
```

### Abstract → Concrete (Tech)
```
Luminous geometric shapes in dark space gradually converge and organize into a 
structured grid pattern. Chaotic particles align into ordered data streams. Blue 
and cyan tones throughout. The abstract becomes structured — representing 
technology bringing order. 6 seconds. No text.
```

### Day → Night (Restaurant/Hospitality)
```
Warm golden hour light on a restaurant exterior gradually transitions to evening. 
Windows begin to glow warm amber as interior lights turn on. The atmosphere shifts 
from bright and inviting to intimate and cozy. Smooth timelapse compression. 
6 seconds. No text.
```

## Keyframe Image Prompts (Nano Banana)

### Section Backgrounds (Abstract/Atmospheric)
```
Abstract organic texture in [BRAND_COLOR_1] and [BRAND_COLOR_2]. Soft gradients 
with subtle noise texture. Slightly out of focus with gentle bokeh effect. 
No objects, no text, no logos. Pure atmospheric texture for website background.
```

### Hero Fallback (Static)
```
[Industry-appropriate scene] at golden hour. Professional photography style with 
shallow depth of field. Rich color palette: [BRAND_COLORS]. Cinematic composition 
with strong leading lines. No people's faces visible. No text, no logos.
```

### CTA Section Background
```
Warm, inviting abstract gradient transitioning from [BRAND_COLOR_1] to 
[BRAND_COLOR_2]. Soft light source from upper left creates depth. Gentle 
lens flare or light leak effect. Optimistic, forward-looking mood. 
No text, no logos.
```

## Prompt Modification Rules

1. **Always replace placeholders** with actual prospect data:
   - `[BRAND_COLOR_1]` → actual hex from `brand_colors[0]`
   - `[Industry-appropriate]` → specific to the business (e.g., "artisanal bakery" not "restaurant")

2. **Never use these verbatim** — adapt to the specific business:
   - A pizza restaurant needs different imagery than a fine dining restaurant
   - A family law firm needs different tone than a corporate law firm

3. **Reference specific brand elements** when available:
   - If the business has a signature product, describe it
   - If they have a distinctive interior style, reference it
   - Use their actual neighborhood/location for context

4. **Camera movement rules**:
   - Always slow and deliberate — no fast movements (bad for scroll scrubbing)
   - Forward dolly and orbital pan work best
   - Avoid zoom (feels artificial) — prefer physical camera movement
   - One continuous shot — no cuts or scene changes
