# Style Catalog — 12 Predefined Styles

> Complete token sets for all 12 styles. The skill curates 3 from these 12 based on app type + audience fit.

## Curation Algorithm

To select 3 styles from the catalog:

1. **Score each style** against three criteria (0-100 each):
   - `audience_fit`: Does the style match the target user's age, profession, and expectations?
   - `vibe_match`: Does the style's vibe align with the product's core value proposition?
   - `app_type_fit`: Is this style commonly used for this app type?
2. **Composite score** = (audience_fit × 0.4) + (vibe_match × 0.35) + (app_type_fit × 0.25)
3. **Pick top 3** by composite score. If a tie, prefer more universally appealing styles.
4. **"Choose for me"** default = highest composite score.

### App Type Affinity Matrix

| Style | dashboard | chat | wizard | marketplace | tool | landing | settings |
|-------|-----------|------|--------|-------------|------|---------|----------|
| flat-design | 95 | 80 | 90 | 85 | 80 | 85 | 90 |
| minimalism | 85 | 85 | 85 | 80 | 75 | 95 | 85 |
| neumorphism | 80 | 60 | 75 | 55 | 70 | 60 | 85 |
| glassmorphism | 75 | 80 | 70 | 75 | 65 | 90 | 70 |
| skeuomorphism | 50 | 45 | 60 | 55 | 65 | 40 | 70 |
| neubrutalism | 55 | 65 | 50 | 70 | 55 | 85 | 45 |
| bauhaus | 60 | 55 | 55 | 60 | 70 | 80 | 50 |
| claymorphism | 55 | 70 | 75 | 65 | 45 | 75 | 60 |
| retro-futurism | 45 | 50 | 40 | 50 | 60 | 70 | 35 |
| cyberpunk | 50 | 55 | 35 | 45 | 70 | 65 | 40 |
| dark-mode | 90 | 85 | 65 | 70 | 95 | 75 | 80 |
| warmer-shades | 70 | 75 | 80 | 75 | 50 | 80 | 80 |

### Audience Affinity Guide

| Audience Trait | Best Styles | Avoid |
|---------------|-------------|-------|
| Enterprise / Corporate | flat-design, minimalism, dark-mode | neubrutalism, cyberpunk, claymorphism |
| Gen Z / Young Adults | neubrutalism, glassmorphism, cyberpunk | skeuomorphism, neumorphism |
| Creative Professionals | bauhaus, minimalism, dark-mode | skeuomorphism, flat-design |
| General Consumer | flat-design, claymorphism, warmer-shades | cyberpunk, bauhaus |
| Developers / Technical | dark-mode, flat-design, minimalism | claymorphism, skeuomorphism |
| Older Demographics (50+) | skeuomorphism, warmer-shades, flat-design | cyberpunk, neubrutalism |
| Health / Wellness | claymorphism, minimalism, warmer-shades | cyberpunk, neubrutalism |
| Gaming / Entertainment | cyberpunk, retro-futurism, neubrutalism | minimalism, flat-design |
| Finance / Banking | neumorphism, dark-mode, minimalism | claymorphism, retro-futurism |
| Education | flat-design, claymorphism, warmer-shades | cyberpunk, bauhaus |

---

## Style Definitions

### 1. flat-design

**Vibe:** Clean, clear, universal — the "just works" default
**Best for:** Clarity, scalability, universal appeal

```json
{
  "colors": {
    "primary": "#3B82F6",
    "secondary": "#8B5CF6",
    "accent": "#F59E0B",
    "surface": "#FFFFFF",
    "surface_alt": "#F8FAFC",
    "text": "#1E293B",
    "text_secondary": "#64748B",
    "border": "#E2E8F0",
    "success": "#22C55E",
    "warning": "#F59E0B",
    "error": "#EF4444",
    "info": "#3B82F6"
  },
  "typography": {
    "heading_font": "Inter, system-ui, sans-serif",
    "body_font": "Inter, system-ui, sans-serif",
    "mono_font": "JetBrains Mono, Fira Code, monospace",
    "sizes": {
      "xs": "0.75rem", "sm": "0.875rem", "base": "1rem", "lg": "1.125rem",
      "xl": "1.25rem", "2xl": "1.5rem", "3xl": "1.875rem", "4xl": "2.25rem"
    },
    "weights": { "normal": 400, "medium": 500, "semibold": 600, "bold": 700 },
    "line_heights": { "tight": 1.25, "normal": 1.5, "relaxed": 1.75 }
  },
  "spacing": {
    "1": "0.25rem", "2": "0.5rem", "3": "0.75rem", "4": "1rem",
    "5": "1.25rem", "6": "1.5rem", "8": "2rem", "10": "2.5rem",
    "12": "3rem", "16": "4rem", "20": "5rem", "24": "6rem"
  },
  "border_radius": { "sm": "0.25rem", "md": "0.375rem", "lg": "0.5rem", "xl": "0.75rem", "full": "9999px" },
  "shadows": {
    "sm": "0 1px 2px rgba(0,0,0,0.05)",
    "md": "0 4px 6px rgba(0,0,0,0.07)",
    "lg": "0 10px 15px rgba(0,0,0,0.1)",
    "xl": "0 20px 25px rgba(0,0,0,0.1)"
  }
}
```

**Tailwind overrides:**
```json
{
  "extend": {
    "colors": { "primary": "#3B82F6", "secondary": "#8B5CF6", "accent": "#F59E0B" },
    "fontFamily": { "heading": ["Inter", "system-ui", "sans-serif"], "body": ["Inter", "system-ui", "sans-serif"] }
  }
}
```

---

### 2. minimalism

**Vibe:** Premium, elegant, Apple-inspired — less is more
**Best for:** Premium feel, Apple-style elegance

```json
{
  "colors": {
    "primary": "#000000",
    "secondary": "#6B7280",
    "accent": "#2563EB",
    "surface": "#FFFFFF",
    "surface_alt": "#FAFAFA",
    "text": "#111827",
    "text_secondary": "#9CA3AF",
    "border": "#F3F4F6",
    "success": "#10B981",
    "warning": "#F59E0B",
    "error": "#EF4444",
    "info": "#2563EB"
  },
  "typography": {
    "heading_font": "SF Pro Display, -apple-system, system-ui, sans-serif",
    "body_font": "SF Pro Text, -apple-system, system-ui, sans-serif",
    "mono_font": "SF Mono, Menlo, monospace",
    "sizes": {
      "xs": "0.75rem", "sm": "0.875rem", "base": "1rem", "lg": "1.125rem",
      "xl": "1.25rem", "2xl": "1.5rem", "3xl": "2rem", "4xl": "2.5rem"
    },
    "weights": { "normal": 400, "medium": 500, "semibold": 600, "bold": 700 },
    "line_heights": { "tight": 1.2, "normal": 1.5, "relaxed": 1.75 }
  },
  "spacing": {
    "1": "0.25rem", "2": "0.5rem", "3": "0.75rem", "4": "1rem",
    "5": "1.25rem", "6": "1.5rem", "8": "2rem", "10": "2.5rem",
    "12": "3rem", "16": "4rem", "20": "5rem", "24": "6rem"
  },
  "border_radius": { "sm": "0.25rem", "md": "0.5rem", "lg": "0.75rem", "xl": "1rem", "full": "9999px" },
  "shadows": {
    "sm": "0 1px 3px rgba(0,0,0,0.04)",
    "md": "0 4px 6px rgba(0,0,0,0.04)",
    "lg": "0 10px 20px rgba(0,0,0,0.06)",
    "xl": "0 25px 50px rgba(0,0,0,0.08)"
  }
}
```

---

### 3. neumorphism

**Vibe:** Soft, tactile, embossed — like pressing real buttons
**Best for:** Finance apps, dashboards, toggles

```json
{
  "colors": {
    "primary": "#6366F1",
    "secondary": "#8B5CF6",
    "accent": "#EC4899",
    "surface": "#E0E5EC",
    "surface_alt": "#D1D9E6",
    "text": "#2D3748",
    "text_secondary": "#718096",
    "border": "#C9D1DC",
    "success": "#48BB78",
    "warning": "#ECC94B",
    "error": "#FC8181",
    "info": "#63B3ED"
  },
  "typography": {
    "heading_font": "Poppins, sans-serif",
    "body_font": "Poppins, sans-serif",
    "mono_font": "Fira Code, monospace",
    "sizes": {
      "xs": "0.75rem", "sm": "0.875rem", "base": "1rem", "lg": "1.125rem",
      "xl": "1.25rem", "2xl": "1.5rem", "3xl": "1.875rem", "4xl": "2.25rem"
    },
    "weights": { "normal": 400, "medium": 500, "semibold": 600, "bold": 700 },
    "line_heights": { "tight": 1.25, "normal": 1.5, "relaxed": 1.75 }
  },
  "spacing": {
    "1": "0.25rem", "2": "0.5rem", "3": "0.75rem", "4": "1rem",
    "5": "1.25rem", "6": "1.5rem", "8": "2rem", "10": "2.5rem",
    "12": "3rem", "16": "4rem", "20": "5rem", "24": "6rem"
  },
  "border_radius": { "sm": "0.5rem", "md": "0.75rem", "lg": "1rem", "xl": "1.5rem", "full": "9999px" },
  "shadows": {
    "sm": "3px 3px 6px #b8b9be, -3px -3px 6px #ffffff",
    "md": "5px 5px 10px #b8b9be, -5px -5px 10px #ffffff",
    "lg": "8px 8px 16px #b8b9be, -8px -8px 16px #ffffff",
    "xl": "12px 12px 24px #b8b9be, -12px -12px 24px #ffffff"
  }
}
```

---

### 4. glassmorphism

**Vibe:** Frosted glass, depth, modern — translucent layers
**Best for:** Modern SaaS, trendy products

```json
{
  "colors": {
    "primary": "#7C3AED",
    "secondary": "#2DD4BF",
    "accent": "#F472B6",
    "surface": "rgba(255, 255, 255, 0.25)",
    "surface_alt": "rgba(255, 255, 255, 0.15)",
    "text": "#1E293B",
    "text_secondary": "#64748B",
    "border": "rgba(255, 255, 255, 0.3)",
    "success": "#34D399",
    "warning": "#FBBF24",
    "error": "#F87171",
    "info": "#60A5FA"
  },
  "typography": {
    "heading_font": "Plus Jakarta Sans, sans-serif",
    "body_font": "Plus Jakarta Sans, sans-serif",
    "mono_font": "JetBrains Mono, monospace",
    "sizes": {
      "xs": "0.75rem", "sm": "0.875rem", "base": "1rem", "lg": "1.125rem",
      "xl": "1.25rem", "2xl": "1.5rem", "3xl": "1.875rem", "4xl": "2.25rem"
    },
    "weights": { "normal": 400, "medium": 500, "semibold": 600, "bold": 700 },
    "line_heights": { "tight": 1.25, "normal": 1.5, "relaxed": 1.75 }
  },
  "spacing": {
    "1": "0.25rem", "2": "0.5rem", "3": "0.75rem", "4": "1rem",
    "5": "1.25rem", "6": "1.5rem", "8": "2rem", "10": "2.5rem",
    "12": "3rem", "16": "4rem", "20": "5rem", "24": "6rem"
  },
  "border_radius": { "sm": "0.5rem", "md": "0.75rem", "lg": "1rem", "xl": "1.5rem", "full": "9999px" },
  "shadows": {
    "sm": "0 2px 8px rgba(0,0,0,0.1)",
    "md": "0 8px 32px rgba(0,0,0,0.12)",
    "lg": "0 16px 48px rgba(0,0,0,0.15)",
    "xl": "0 24px 64px rgba(0,0,0,0.18)"
  }
}
```

**Note:** Glassmorphism requires `backdrop-filter: blur(16px)` on surface elements.

---

### 5. skeuomorphism

**Vibe:** Familiar, physical, textured — like real-world objects
**Best for:** Familiarity, older demographics

```json
{
  "colors": {
    "primary": "#2E7D32",
    "secondary": "#5D4037",
    "accent": "#FF8F00",
    "surface": "#F5F0EB",
    "surface_alt": "#EDE7E0",
    "text": "#3E2723",
    "text_secondary": "#6D4C41",
    "border": "#BCAAA4",
    "success": "#2E7D32",
    "warning": "#FF8F00",
    "error": "#C62828",
    "info": "#1565C0"
  },
  "typography": {
    "heading_font": "Georgia, Times New Roman, serif",
    "body_font": "Verdana, Geneva, sans-serif",
    "mono_font": "Courier New, monospace",
    "sizes": {
      "xs": "0.75rem", "sm": "0.875rem", "base": "1rem", "lg": "1.125rem",
      "xl": "1.25rem", "2xl": "1.5rem", "3xl": "1.875rem", "4xl": "2.25rem"
    },
    "weights": { "normal": 400, "medium": 500, "semibold": 600, "bold": 700 },
    "line_heights": { "tight": 1.3, "normal": 1.6, "relaxed": 1.8 }
  },
  "spacing": {
    "1": "0.25rem", "2": "0.5rem", "3": "0.75rem", "4": "1rem",
    "5": "1.25rem", "6": "1.5rem", "8": "2rem", "10": "2.5rem",
    "12": "3rem", "16": "4rem", "20": "5rem", "24": "6rem"
  },
  "border_radius": { "sm": "0.25rem", "md": "0.375rem", "lg": "0.5rem", "xl": "0.625rem", "full": "9999px" },
  "shadows": {
    "sm": "0 1px 2px rgba(0,0,0,0.15), inset 0 1px 0 rgba(255,255,255,0.3)",
    "md": "0 3px 6px rgba(0,0,0,0.2), inset 0 1px 0 rgba(255,255,255,0.25)",
    "lg": "0 6px 12px rgba(0,0,0,0.25), inset 0 1px 0 rgba(255,255,255,0.2)",
    "xl": "0 10px 20px rgba(0,0,0,0.3), inset 0 1px 0 rgba(255,255,255,0.15)"
  }
}
```

---

### 6. neubrutalism

**Vibe:** Bold, raw, unapologetic — thick borders, loud colors
**Best for:** Young/edgy, Gen Z products

```json
{
  "colors": {
    "primary": "#FF6B6B",
    "secondary": "#4ECDC4",
    "accent": "#FFE66D",
    "surface": "#FFFFFF",
    "surface_alt": "#FFF8E1",
    "text": "#000000",
    "text_secondary": "#333333",
    "border": "#000000",
    "success": "#4ECDC4",
    "warning": "#FFE66D",
    "error": "#FF6B6B",
    "info": "#45B7D1"
  },
  "typography": {
    "heading_font": "Space Grotesk, sans-serif",
    "body_font": "Space Grotesk, sans-serif",
    "mono_font": "Space Mono, monospace",
    "sizes": {
      "xs": "0.75rem", "sm": "0.875rem", "base": "1rem", "lg": "1.25rem",
      "xl": "1.5rem", "2xl": "2rem", "3xl": "2.5rem", "4xl": "3rem"
    },
    "weights": { "normal": 400, "medium": 500, "semibold": 700, "bold": 800 },
    "line_heights": { "tight": 1.1, "normal": 1.4, "relaxed": 1.6 }
  },
  "spacing": {
    "1": "0.25rem", "2": "0.5rem", "3": "0.75rem", "4": "1rem",
    "5": "1.25rem", "6": "1.5rem", "8": "2rem", "10": "2.5rem",
    "12": "3rem", "16": "4rem", "20": "5rem", "24": "6rem"
  },
  "border_radius": { "sm": "0", "md": "0.25rem", "lg": "0.5rem", "xl": "0.75rem", "full": "9999px" },
  "shadows": {
    "sm": "2px 2px 0 #000000",
    "md": "4px 4px 0 #000000",
    "lg": "6px 6px 0 #000000",
    "xl": "8px 8px 0 #000000"
  }
}
```

**Note:** Neubrutalism uses thick solid borders (2-3px black) instead of subtle borders.

---

### 7. bauhaus

**Vibe:** Geometric, primary colors, form-follows-function
**Best for:** Design-forward, artistic

```json
{
  "colors": {
    "primary": "#D32F2F",
    "secondary": "#1976D2",
    "accent": "#FBC02D",
    "surface": "#FAFAFA",
    "surface_alt": "#F5F5F5",
    "text": "#212121",
    "text_secondary": "#757575",
    "border": "#BDBDBD",
    "success": "#388E3C",
    "warning": "#FBC02D",
    "error": "#D32F2F",
    "info": "#1976D2"
  },
  "typography": {
    "heading_font": "Oswald, sans-serif",
    "body_font": "Roboto, sans-serif",
    "mono_font": "Roboto Mono, monospace",
    "sizes": {
      "xs": "0.75rem", "sm": "0.875rem", "base": "1rem", "lg": "1.125rem",
      "xl": "1.25rem", "2xl": "1.75rem", "3xl": "2.25rem", "4xl": "3rem"
    },
    "weights": { "normal": 400, "medium": 500, "semibold": 600, "bold": 700 },
    "line_heights": { "tight": 1.2, "normal": 1.5, "relaxed": 1.7 }
  },
  "spacing": {
    "1": "0.25rem", "2": "0.5rem", "3": "0.75rem", "4": "1rem",
    "5": "1.25rem", "6": "1.5rem", "8": "2rem", "10": "2.5rem",
    "12": "3rem", "16": "4rem", "20": "5rem", "24": "6rem"
  },
  "border_radius": { "sm": "0", "md": "0", "lg": "0", "xl": "0", "full": "50%" },
  "shadows": {
    "sm": "0 2px 4px rgba(0,0,0,0.1)",
    "md": "0 4px 8px rgba(0,0,0,0.12)",
    "lg": "0 8px 16px rgba(0,0,0,0.15)",
    "xl": "0 16px 32px rgba(0,0,0,0.18)"
  }
}
```

**Note:** Bauhaus uses sharp corners (border-radius: 0) except for deliberate circles (full: 50%).

---

### 8. claymorphism

**Vibe:** Soft, puffy, friendly — like clay or dough
**Best for:** Friendly, approachable products

```json
{
  "colors": {
    "primary": "#7C5CFC",
    "secondary": "#FF8A65",
    "accent": "#4DD0E1",
    "surface": "#F0EEFF",
    "surface_alt": "#E8E4FF",
    "text": "#2D2B55",
    "text_secondary": "#6E6B9A",
    "border": "#D4D0F0",
    "success": "#66BB6A",
    "warning": "#FFB74D",
    "error": "#EF5350",
    "info": "#42A5F5"
  },
  "typography": {
    "heading_font": "Nunito, sans-serif",
    "body_font": "Nunito, sans-serif",
    "mono_font": "Source Code Pro, monospace",
    "sizes": {
      "xs": "0.75rem", "sm": "0.875rem", "base": "1rem", "lg": "1.125rem",
      "xl": "1.25rem", "2xl": "1.5rem", "3xl": "1.875rem", "4xl": "2.25rem"
    },
    "weights": { "normal": 400, "medium": 600, "semibold": 700, "bold": 800 },
    "line_heights": { "tight": 1.3, "normal": 1.6, "relaxed": 1.8 }
  },
  "spacing": {
    "1": "0.25rem", "2": "0.5rem", "3": "0.75rem", "4": "1rem",
    "5": "1.25rem", "6": "1.5rem", "8": "2rem", "10": "2.5rem",
    "12": "3rem", "16": "4rem", "20": "5rem", "24": "6rem"
  },
  "border_radius": { "sm": "0.75rem", "md": "1rem", "lg": "1.5rem", "xl": "2rem", "full": "9999px" },
  "shadows": {
    "sm": "0 4px 8px rgba(124,92,252,0.15), inset 0 -2px 4px rgba(0,0,0,0.05)",
    "md": "0 8px 16px rgba(124,92,252,0.18), inset 0 -3px 6px rgba(0,0,0,0.06)",
    "lg": "0 12px 24px rgba(124,92,252,0.2), inset 0 -4px 8px rgba(0,0,0,0.07)",
    "xl": "0 16px 32px rgba(124,92,252,0.22), inset 0 -5px 10px rgba(0,0,0,0.08)"
  }
}
```

---

### 9. retro-futurism

**Vibe:** Neon + nostalgia, VHS tracking lines, 80s sci-fi
**Best for:** Gaming, entertainment

```json
{
  "colors": {
    "primary": "#FF00FF",
    "secondary": "#00FFFF",
    "accent": "#FFFF00",
    "surface": "#1A0033",
    "surface_alt": "#2A0052",
    "text": "#FFFFFF",
    "text_secondary": "#B794F6",
    "border": "#6B21A8",
    "success": "#00FF88",
    "warning": "#FFFF00",
    "error": "#FF0066",
    "info": "#00CCFF"
  },
  "typography": {
    "heading_font": "Orbitron, sans-serif",
    "body_font": "Rajdhani, sans-serif",
    "mono_font": "Share Tech Mono, monospace",
    "sizes": {
      "xs": "0.75rem", "sm": "0.875rem", "base": "1rem", "lg": "1.125rem",
      "xl": "1.25rem", "2xl": "1.5rem", "3xl": "2rem", "4xl": "2.5rem"
    },
    "weights": { "normal": 400, "medium": 500, "semibold": 600, "bold": 700 },
    "line_heights": { "tight": 1.2, "normal": 1.5, "relaxed": 1.7 }
  },
  "spacing": {
    "1": "0.25rem", "2": "0.5rem", "3": "0.75rem", "4": "1rem",
    "5": "1.25rem", "6": "1.5rem", "8": "2rem", "10": "2.5rem",
    "12": "3rem", "16": "4rem", "20": "5rem", "24": "6rem"
  },
  "border_radius": { "sm": "0", "md": "0.25rem", "lg": "0.5rem", "xl": "0.75rem", "full": "9999px" },
  "shadows": {
    "sm": "0 0 8px rgba(255,0,255,0.4)",
    "md": "0 0 16px rgba(255,0,255,0.5)",
    "lg": "0 0 32px rgba(255,0,255,0.5), 0 0 8px rgba(0,255,255,0.3)",
    "xl": "0 0 48px rgba(255,0,255,0.6), 0 0 16px rgba(0,255,255,0.4)"
  }
}
```

---

### 10. cyberpunk

**Vibe:** Dark, glitchy, neon-on-black, tech-dystopia
**Best for:** Edgy tech, gaming

```json
{
  "colors": {
    "primary": "#00F0FF",
    "secondary": "#FF003C",
    "accent": "#B6FF00",
    "surface": "#0D0D0D",
    "surface_alt": "#1A1A2E",
    "text": "#E0E0E0",
    "text_secondary": "#888888",
    "border": "#333355",
    "success": "#B6FF00",
    "warning": "#FFB800",
    "error": "#FF003C",
    "info": "#00F0FF"
  },
  "typography": {
    "heading_font": "Exo 2, sans-serif",
    "body_font": "IBM Plex Sans, sans-serif",
    "mono_font": "IBM Plex Mono, monospace",
    "sizes": {
      "xs": "0.75rem", "sm": "0.875rem", "base": "1rem", "lg": "1.125rem",
      "xl": "1.25rem", "2xl": "1.5rem", "3xl": "2rem", "4xl": "2.5rem"
    },
    "weights": { "normal": 400, "medium": 500, "semibold": 600, "bold": 700 },
    "line_heights": { "tight": 1.2, "normal": 1.5, "relaxed": 1.7 }
  },
  "spacing": {
    "1": "0.25rem", "2": "0.5rem", "3": "0.75rem", "4": "1rem",
    "5": "1.25rem", "6": "1.5rem", "8": "2rem", "10": "2.5rem",
    "12": "3rem", "16": "4rem", "20": "5rem", "24": "6rem"
  },
  "border_radius": { "sm": "0", "md": "0.125rem", "lg": "0.25rem", "xl": "0.5rem", "full": "9999px" },
  "shadows": {
    "sm": "0 0 6px rgba(0,240,255,0.3)",
    "md": "0 0 12px rgba(0,240,255,0.4)",
    "lg": "0 0 24px rgba(0,240,255,0.4), 0 0 6px rgba(255,0,60,0.2)",
    "xl": "0 0 48px rgba(0,240,255,0.5), 0 0 12px rgba(255,0,60,0.3)"
  }
}
```

---

### 11. dark-mode

**Vibe:** Refined dark, professional, easy on the eyes
**Best for:** Developer tools, media apps

```json
{
  "colors": {
    "primary": "#818CF8",
    "secondary": "#34D399",
    "accent": "#FBBF24",
    "surface": "#111827",
    "surface_alt": "#1F2937",
    "text": "#F9FAFB",
    "text_secondary": "#9CA3AF",
    "border": "#374151",
    "success": "#34D399",
    "warning": "#FBBF24",
    "error": "#F87171",
    "info": "#60A5FA"
  },
  "typography": {
    "heading_font": "Inter, system-ui, sans-serif",
    "body_font": "Inter, system-ui, sans-serif",
    "mono_font": "JetBrains Mono, Fira Code, monospace",
    "sizes": {
      "xs": "0.75rem", "sm": "0.875rem", "base": "1rem", "lg": "1.125rem",
      "xl": "1.25rem", "2xl": "1.5rem", "3xl": "1.875rem", "4xl": "2.25rem"
    },
    "weights": { "normal": 400, "medium": 500, "semibold": 600, "bold": 700 },
    "line_heights": { "tight": 1.25, "normal": 1.5, "relaxed": 1.75 }
  },
  "spacing": {
    "1": "0.25rem", "2": "0.5rem", "3": "0.75rem", "4": "1rem",
    "5": "1.25rem", "6": "1.5rem", "8": "2rem", "10": "2.5rem",
    "12": "3rem", "16": "4rem", "20": "5rem", "24": "6rem"
  },
  "border_radius": { "sm": "0.25rem", "md": "0.375rem", "lg": "0.5rem", "xl": "0.75rem", "full": "9999px" },
  "shadows": {
    "sm": "0 1px 2px rgba(0,0,0,0.3)",
    "md": "0 4px 6px rgba(0,0,0,0.4)",
    "lg": "0 10px 15px rgba(0,0,0,0.5)",
    "xl": "0 20px 25px rgba(0,0,0,0.6)"
  }
}
```

---

### 12. warmer-shades

**Vibe:** Warm, nostalgic, comfortable — earth tones and soft edges
**Best for:** Nostalgic, comfortable feel

```json
{
  "colors": {
    "primary": "#B45309",
    "secondary": "#92400E",
    "accent": "#D97706",
    "surface": "#FFFBEB",
    "surface_alt": "#FEF3C7",
    "text": "#451A03",
    "text_secondary": "#78350F",
    "border": "#D6C4A8",
    "success": "#65A30D",
    "warning": "#D97706",
    "error": "#DC2626",
    "info": "#0284C7"
  },
  "typography": {
    "heading_font": "Lora, Georgia, serif",
    "body_font": "Source Sans 3, sans-serif",
    "mono_font": "Source Code Pro, monospace",
    "sizes": {
      "xs": "0.75rem", "sm": "0.875rem", "base": "1rem", "lg": "1.125rem",
      "xl": "1.25rem", "2xl": "1.5rem", "3xl": "1.875rem", "4xl": "2.25rem"
    },
    "weights": { "normal": 400, "medium": 500, "semibold": 600, "bold": 700 },
    "line_heights": { "tight": 1.3, "normal": 1.6, "relaxed": 1.8 }
  },
  "spacing": {
    "1": "0.25rem", "2": "0.5rem", "3": "0.75rem", "4": "1rem",
    "5": "1.25rem", "6": "1.5rem", "8": "2rem", "10": "2.5rem",
    "12": "3rem", "16": "4rem", "20": "5rem", "24": "6rem"
  },
  "border_radius": { "sm": "0.375rem", "md": "0.5rem", "lg": "0.75rem", "xl": "1rem", "full": "9999px" },
  "shadows": {
    "sm": "0 1px 3px rgba(120,53,15,0.08)",
    "md": "0 4px 8px rgba(120,53,15,0.1)",
    "lg": "0 8px 16px rgba(120,53,15,0.12)",
    "xl": "0 16px 32px rgba(120,53,15,0.15)"
  }
}
```
