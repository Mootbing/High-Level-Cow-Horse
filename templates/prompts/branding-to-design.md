# Convert Prospect Branding to Design Spec

Given the following prospect branding data:

## Prospect: {{prospect_data}}

Generate a design specification that:
1. Elevates their existing brand identity to an immersive, award-winning level
2. Maintains brand color consistency but adds premium cinematic feel
3. Suggests complementary fonts if current ones are basic
4. Selects appropriate 3D scene style and video treatment for their industry
5. Defines a complete design system:

Output as JSON:
```json
{
  "colors": {
    "primary": "#hex — from brand_colors[0]",
    "secondary": "#hex — from brand_colors[1] or complementary",
    "accent": "#hex — from brand_colors[2] or contrast color",
    "background": "#hex — light or dark based on industry",
    "text": "#hex — high contrast against background",
    "muted": "#hex — subtle text color"
  },
  "fonts": {
    "heading": "Google Font Name — from prospect fonts or industry-matched",
    "body": "Google Font Name — from prospect fonts or industry-matched"
  },
  "hero_video": {
    "keyframe_a_prompt": "Opening visual state — what visitors see on page load. [Brand colors]. No text.",
    "keyframe_b_prompt": "Ending visual state — what visitors see after scrolling through hero. [Brand colors]. No text.",
    "transition_prompt": "Smooth cinematic morph between opening and ending states. No text."
  },
  "persistent_3d_scene": {
    "style": "glass_geometric | warm_organic | iridescent_fluid | wireframe_data | golden_architecture | product_studio | molecular_soft | abstract_bold",
    "materials": "Description of Three.js materials to use",
    "lighting": "Description of lighting setup",
    "post_processing": ["Bloom", "ChromaticAberration", "Vignette", "Noise"],
    "scroll_behavior": "How 3D elements react to scroll (rotate, morph, scale, color shift)"
  },
  "transition_prompts": {
    "hero_to_content": "Prompt for A→B transition video between hero end and first content section"
  },
  "sections": ["hero-scroll-video", "scroll-transition", "text-reveal", "parallax-gallery", "features", "stats", "cta"],
  "animation_personality": "premium | warm | bold | clean | playful | tech",
  "reactbits_components": ["aurora_background", "magnetic_button", "blur_text", "tilt_card", "spotlight_card", "counter"],
  "micro_interactions": ["magnetic_buttons", "3d_card_tilt", "text_scramble", "counter", "cursor_follower"],
  "mobile_fallback": "Description of static image to use on mobile instead of 3D/video (keyframe A from hero)",
  "style": "One-line description of overall aesthetic"
}
```

## Industry-to-Style Mapping

Hero is ALWAYS scroll video (keyframe A→B via Veo 3.1). The `persistent_3d_scene` style determines the Three.js 3D elements that run behind content sections.

| Industry | Hero Keyframe Style | Persistent 3D Scene | animation_personality | Background |
|----------|-------------------|--------------------|-----------------------|------------|
| Restaurant/Food | Warm organic textures, steam, golden hour | warm_organic (floating particles) | warm | Light (cream/warm white) |
| Law/Finance | Architectural glass, twilight cityscape | glass_geometric | premium | Dark (navy/charcoal) |
| Salon/Beauty | Iridescent fluids, soft macro textures | iridescent_fluid | premium | Light (soft pink/lavender) |
| Tech/SaaS | Data streams, neon wireframes | wireframe_data | tech | Dark (near black) |
| Real Estate | Aerial golden hour, architecture | golden_architecture | premium | Light (warm white) |
| Retail/E-commerce | Product showcase, studio lighting | product_studio | clean | Light (white) |
| Healthcare | Clean modern spaces, molecular | molecular_soft | clean | Light (clean white) |
| Creative/Agency | Bold abstract, dramatic angles | abstract_bold | bold | Dark (black) |
| Construction | Site aerials, materials close-up | golden_architecture | bold | Light (concrete gray) |
| Education | Campus atmosphere, warm interiors | warm_organic | warm | Light (soft blue/green) |
