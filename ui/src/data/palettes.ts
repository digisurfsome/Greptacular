/**
 * Color Palette Presets
 *
 * 24 curated UI color palettes organized by category.
 * Each palette has 6 functional color slots:
 *   brand      – primary action color (buttons, links, CTAs)
 *   background – page/app background
 *   surface    – cards, modals, panels
 *   text       – primary readable text
 *   accent     – highlights, badges, secondary actions
 *   muted      – borders, dividers, subtle backgrounds
 *
 * Free tier: palettes 1-10.  Premium tier: palettes 11-24.
 */

export interface PaletteData {
  id: string
  name: string
  category: string
  brand: string
  background: string
  surface: string
  text: string
  accent: string
  muted: string
  tier: 'free' | 'premium'
  vibe: string
}

export const PALETTES: PaletteData[] = [
  // ── Professional / Corporate ──────────────────────────────────────────────
  {
    id: 'midnight-office',
    name: 'Midnight Office',
    category: 'Professional',
    brand: '#2563EB',
    background: '#F8FAFC',
    surface: '#FFFFFF',
    text: '#0F172A',
    accent: '#F59E0B',
    muted: '#E2E8F0',
    tier: 'free',
    vibe: 'Corporate trust, clean authority',
  },
  {
    id: 'charcoal-cream',
    name: 'Charcoal & Cream',
    category: 'Professional',
    brand: '#374151',
    background: '#FFFBEB',
    surface: '#FFFFFF',
    text: '#1F2937',
    accent: '#DC2626',
    muted: '#D1D5DB',
    tier: 'free',
    vibe: 'Sophisticated, editorial',
  },
  {
    id: 'deep-teal',
    name: 'Deep Teal',
    category: 'Professional',
    brand: '#0D9488',
    background: '#F0FDFA',
    surface: '#FFFFFF',
    text: '#134E4A',
    accent: '#F97316',
    muted: '#CCFBF1',
    tier: 'free',
    vibe: 'Calm professionalism, healthcare/finance',
  },

  // ── Warm & Friendly ───────────────────────────────────────────────────────
  {
    id: 'sunset-glow',
    name: 'Sunset Glow',
    category: 'Warm',
    brand: '#EA580C',
    background: '#FFFBEB',
    surface: '#FFFFFF',
    text: '#431407',
    accent: '#7C3AED',
    muted: '#FED7AA',
    tier: 'free',
    vibe: 'Warm, inviting, food/lifestyle',
  },
  {
    id: 'rose-garden',
    name: 'Rose Garden',
    category: 'Warm',
    brand: '#E11D48',
    background: '#FFF1F2',
    surface: '#FFFFFF',
    text: '#1C1917',
    accent: '#0EA5E9',
    muted: '#FECDD3',
    tier: 'free',
    vibe: 'Friendly, approachable, community',
  },
  {
    id: 'terracotta',
    name: 'Terracotta',
    category: 'Warm',
    brand: '#C2410C',
    background: '#FEF3C7',
    surface: '#FFFBEB',
    text: '#292524',
    accent: '#4F46E5',
    muted: '#D6D3D1',
    tier: 'free',
    vibe: 'Earthy, artisan, handmade',
  },

  // ── Cool & Modern ─────────────────────────────────────────────────────────
  {
    id: 'arctic-blue',
    name: 'Arctic Blue',
    category: 'Cool',
    brand: '#0284C7',
    background: '#F0F9FF',
    surface: '#FFFFFF',
    text: '#0C4A6E',
    accent: '#E11D48',
    muted: '#BAE6FD',
    tier: 'free',
    vibe: 'Clean tech, SaaS',
  },
  {
    id: 'indigo-night',
    name: 'Indigo Night',
    category: 'Cool',
    brand: '#6366F1',
    background: '#EEF2FF',
    surface: '#FFFFFF',
    text: '#1E1B4B',
    accent: '#10B981',
    muted: '#C7D2FE',
    tier: 'free',
    vibe: 'Modern, creative tools',
  },
  {
    id: 'mint-fresh',
    name: 'Mint Fresh',
    category: 'Cool',
    brand: '#059669',
    background: '#ECFDF5',
    surface: '#FFFFFF',
    text: '#064E3B',
    accent: '#8B5CF6',
    muted: '#A7F3D0',
    tier: 'free',
    vibe: 'Fresh, health/wellness',
  },

  // ── Bold & Energetic ──────────────────────────────────────────────────────
  {
    id: 'electric-coral',
    name: 'Electric Coral',
    category: 'Bold',
    brand: '#F43F5E',
    background: '#FFFFFF',
    surface: '#FFF1F2',
    text: '#18181B',
    accent: '#06B6D4',
    muted: '#F4F4F5',
    tier: 'free',
    vibe: 'Bold, startups, social apps',
  },
  {
    id: 'neon-slate',
    name: 'Neon Slate',
    category: 'Bold',
    brand: '#8B5CF6',
    background: '#020617',
    surface: '#0F172A',
    text: '#E2E8F0',
    accent: '#22D3EE',
    muted: '#334155',
    tier: 'premium',
    vibe: 'Dark mode, developer tools, gaming',
  },
  {
    id: 'sunburst',
    name: 'Sunburst',
    category: 'Bold',
    brand: '#D97706',
    background: '#FFFFF0',
    surface: '#FFFFFF',
    text: '#1C1917',
    accent: '#2563EB',
    muted: '#FDE68A',
    tier: 'premium',
    vibe: 'Energetic, marketplaces, education',
  },

  // ── Nature-Inspired ───────────────────────────────────────────────────────
  {
    id: 'forest-floor',
    name: 'Forest Floor',
    category: 'Nature',
    brand: '#15803D',
    background: '#F5F5F4',
    surface: '#FFFFFF',
    text: '#1C1917',
    accent: '#B45309',
    muted: '#D6D3D1',
    tier: 'premium',
    vibe: 'Organic, outdoors, sustainability',
  },
  {
    id: 'ocean-dusk',
    name: 'Ocean Dusk',
    category: 'Nature',
    brand: '#1D4ED8',
    background: '#0F172A',
    surface: '#1E293B',
    text: '#CBD5E1',
    accent: '#F59E0B',
    muted: '#334155',
    tier: 'premium',
    vibe: 'Deep, immersive, storytelling (dark)',
  },
  {
    id: 'sand-stone',
    name: 'Sand & Stone',
    category: 'Nature',
    brand: '#92400E',
    background: '#FAF5F0',
    surface: '#FFFFFF',
    text: '#292524',
    accent: '#0891B2',
    muted: '#E7E5E4',
    tier: 'premium',
    vibe: 'Warm minimal, boutique, calm',
  },

  // ── Monochrome & Minimal ──────────────────────────────────────────────────
  {
    id: 'pure-ink',
    name: 'Pure Ink',
    category: 'Monochrome',
    brand: '#374151',
    background: '#FAFAFA',
    surface: '#FFFFFF',
    text: '#111827',
    accent: '#6366F1',
    muted: '#D1D5DB',
    tier: 'premium',
    vibe: 'Near-monochrome with a touch of indigo, typography-first',
  },
  {
    id: 'slate-mode',
    name: 'Slate Mode',
    category: 'Monochrome',
    brand: '#475569',
    background: '#F1F5F9',
    surface: '#FFFFFF',
    text: '#0F172A',
    accent: '#0EA5E9',
    muted: '#CBD5E1',
    tier: 'premium',
    vibe: 'Neutral, no-nonsense, data-heavy apps',
  },

  // ── Luxury & Premium ──────────────────────────────────────────────────────
  {
    id: 'champagne',
    name: 'Champagne',
    category: 'Luxury',
    brand: '#A16207',
    background: '#FFFBEB',
    surface: '#FEF3C7',
    text: '#422006',
    accent: '#1D4ED8',
    muted: '#FDE68A',
    tier: 'premium',
    vibe: 'Luxury, gold tones, premium feel',
  },
  {
    id: 'plum-velvet',
    name: 'Plum Velvet',
    category: 'Luxury',
    brand: '#7E22CE',
    background: '#FAF5FF',
    surface: '#FFFFFF',
    text: '#3B0764',
    accent: '#E11D48',
    muted: '#E9D5FF',
    tier: 'premium',
    vibe: 'Rich, creative agencies, fashion',
  },
  {
    id: 'obsidian-gold',
    name: 'Obsidian Gold',
    category: 'Luxury',
    brand: '#EAB308',
    background: '#09090B',
    surface: '#18181B',
    text: '#FAFAF9',
    accent: '#A855F7',
    muted: '#27272A',
    tier: 'premium',
    vibe: 'Premium dark, fintech, luxury (dark)',
  },

  // ── Playful & Creative ────────────────────────────────────────────────────
  {
    id: 'candy-pop',
    name: 'Candy Pop',
    category: 'Playful',
    brand: '#EC4899',
    background: '#FDF2F8',
    surface: '#FFFFFF',
    text: '#1E1B4B',
    accent: '#8B5CF6',
    muted: '#FBCFE8',
    tier: 'premium',
    vibe: 'Fun, youthful, social, Gen Z',
  },
  {
    id: 'retro-arcade',
    name: 'Retro Arcade',
    category: 'Playful',
    brand: '#A855F7',
    background: '#0F0526',
    surface: '#1A0940',
    text: '#E0E7FF',
    accent: '#34D399',
    muted: '#312E81',
    tier: 'premium',
    vibe: 'Synthwave, gaming, retro-futurism (dark)',
  },
  {
    id: 'citrus-splash',
    name: 'Citrus Splash',
    category: 'Playful',
    brand: '#65A30D',
    background: '#FEFCE8',
    surface: '#FFFFFF',
    text: '#1A2E05',
    accent: '#E11D48',
    muted: '#D9F99D',
    tier: 'premium',
    vibe: 'Fresh, energetic, food tech, fitness',
  },

  // ── Muted & Sophisticated ─────────────────────────────────────────────────
  {
    id: 'sage-whisper',
    name: 'Sage Whisper',
    category: 'Muted',
    brand: '#4D7C0F',
    background: '#F5F5F4',
    surface: '#FAFAF9',
    text: '#292524',
    accent: '#0E7490',
    muted: '#D6D3D1',
    tier: 'premium',
    vibe: 'Organic, wellness, journals, calm apps',
  },
]

/** Unique category names in display order */
export const PALETTE_CATEGORIES = [
  'Professional',
  'Warm',
  'Cool',
  'Bold',
  'Nature',
  'Monochrome',
  'Luxury',
  'Playful',
  'Muted',
] as const

/** Look up a palette by ID */
export function getPaletteById(id: string): PaletteData | undefined {
  return PALETTES.find(p => p.id === id)
}

/** Get all palettes in a given category */
export function getPalettesByCategory(category: string): PaletteData[] {
  return PALETTES.filter(p => p.category === category)
}

/** Get only free-tier palettes */
export function getFreePalettes(): PaletteData[] {
  return PALETTES.filter(p => p.tier === 'free')
}
