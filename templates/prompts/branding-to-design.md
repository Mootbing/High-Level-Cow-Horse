# Convert Prospect Branding to Design Spec

Given the following prospect branding data:

## Prospect: {{prospect_data}}

Generate a design specification that:
1. Elevates their existing brand identity
2. Maintains brand color consistency but adds premium feel
3. Suggests complementary fonts if current ones are basic
4. Defines a complete design system:
   - Primary, secondary, accent, and neutral colors
   - Heading and body font families
   - Type scale (h1 through body text sizes)
   - Spacing scale (4px base)
   - Border radius tokens
   - Shadow tokens
   - Animation timing defaults

Output as JSON:
```json
{
  "colors": {
    "primary": "#hex",
    "secondary": "#hex",
    "accent": "#hex",
    "background": "#hex",
    "text": "#hex",
    "muted": "#hex"
  },
  "fonts": {
    "heading": "Font Name",
    "body": "Font Name"
  },
  "layout": "single-page-scroll",
  "sections": ["hero-video", "text-reveal", "parallax-gallery", "features", "cta"],
  "style": "description of overall aesthetic"
}
```
