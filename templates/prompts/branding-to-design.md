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
  "hero_treatment": "3d_scene | scroll_video | kinetic_typography",
  "scene_style": "glass_geometric | warm_organic | iridescent_fluid | wireframe_data | golden_architecture | product_studio | molecular_soft | abstract_bold",
  "scene_materials": "Description of Three.js materials to use",
  "scene_lighting": "Description of lighting setup",
  "post_processing": ["Bloom", "ChromaticAberration", "Vignette", "Noise"],
  "video_prompts": {
    "hero": "Detailed Veo prompt for hero video — industry-appropriate, brand colors, no text",
    "transition": "Prompt for A→B transition video — what morph to create"
  },
  "sections": ["hero-3d", "scroll-transition", "text-reveal", "parallax-gallery", "features", "stats", "cta"],
  "animation_personality": "premium | warm | bold | clean | playful | tech",
  "micro_interactions": ["magnetic_buttons", "3d_card_tilt", "text_scramble", "counter", "cursor_follower"],
  "mobile_fallback": "Description of static image to use on mobile instead of 3D/video",
  "style": "One-line description of overall aesthetic"
}
```

## Industry-to-Style Mapping

| Industry | hero_treatment | scene_style | animation_personality | Background |
|----------|---------------|-------------|----------------------|------------|
| Restaurant/Food | scroll_video | warm_organic | warm | Light (cream/warm white) |
| Law/Finance | 3d_scene | glass_geometric | premium | Dark (navy/charcoal) |
| Salon/Beauty | 3d_scene | iridescent_fluid | premium | Light (soft pink/lavender) |
| Tech/SaaS | 3d_scene | wireframe_data | tech | Dark (near black) |
| Real Estate | scroll_video | golden_architecture | premium | Light (warm white) |
| Retail/E-commerce | scroll_video | product_studio | clean | Light (white) |
| Healthcare | 3d_scene | molecular_soft | clean | Light (clean white) |
| Creative/Agency | 3d_scene | abstract_bold | bold | Dark (black) |
| Construction | scroll_video | golden_architecture | bold | Light (concrete gray) |
| Education | kinetic_typography | — | warm | Light (soft blue/green) |
