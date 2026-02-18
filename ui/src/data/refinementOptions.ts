/**
 * Refinement option definitions for the design refinement tab.
 * Each group contains options that can be adjusted to fine-tune the design.
 */

import type { DesignRefinement } from '../lib/types'

export interface RefinementOption {
  value: string
  label: string
  description: string
}

export interface RefinementGroup {
  key: keyof DesignRefinement
  label: string
  icon: string  // lucide icon name
  description: string
  options: RefinementOption[]
}

export const REFINEMENT_GROUPS: RefinementGroup[] = [
  {
    key: 'shadowIntensity',
    label: 'Shadows & Depth',
    icon: 'Layers',
    description: 'How much depth and shadow effect your cards and elements have',
    options: [
      { value: 'none', label: 'Flat', description: 'No shadows at all — completely flat design' },
      { value: 'subtle', label: 'Subtle', description: 'Barely visible shadows for a hint of depth' },
      { value: 'medium', label: 'Medium', description: 'Standard shadow depth — balanced and modern' },
      { value: 'deep', label: 'Deep', description: 'Pronounced shadows that make elements pop' },
      { value: 'dramatic', label: 'Dramatic', description: 'Heavy shadows for a bold, layered look' },
    ],
  },
  {
    key: 'borderRadius',
    label: 'Corner Rounding',
    icon: 'Square',
    description: 'How rounded or sharp the corners of buttons, cards, and inputs are',
    options: [
      { value: 'sharp', label: 'Sharp', description: 'No rounding — crisp 90-degree corners' },
      { value: 'slight', label: 'Slight', description: 'Just a touch of rounding (4px)' },
      { value: 'medium', label: 'Medium', description: 'Standard rounding — friendly and modern (8px)' },
      { value: 'round', label: 'Round', description: 'Very rounded corners (16px)' },
      { value: 'pill', label: 'Pill', description: 'Fully rounded — pill-shaped buttons and inputs' },
    ],
  },
  {
    key: 'borderStyle',
    label: 'Border Style',
    icon: 'Frame',
    description: 'How visible and prominent the borders are on cards and inputs',
    options: [
      { value: 'none', label: 'None', description: 'No borders — elements float freely' },
      { value: 'subtle', label: 'Subtle', description: 'Light, barely-there borders' },
      { value: 'defined', label: 'Defined', description: 'Clear borders that frame each element' },
      { value: 'bold', label: 'Bold', description: 'Thick, prominent borders (neobrutalist feel)' },
    ],
  },
  {
    key: 'animationSpeed',
    label: 'Animation Speed',
    icon: 'Timer',
    description: 'How fast transitions and animations happen when you interact',
    options: [
      { value: 'instant', label: 'Instant', description: 'No animations — everything changes immediately' },
      { value: 'fast', label: 'Fast', description: 'Quick, snappy transitions (150ms)' },
      { value: 'normal', label: 'Normal', description: 'Smooth, standard speed (300ms)' },
      { value: 'slow', label: 'Slow', description: 'Slower, more deliberate transitions (500ms)' },
    ],
  },
  {
    key: 'animationType',
    label: 'Animation Type',
    icon: 'Sparkles',
    description: 'What kind of motion effect happens when elements appear or change',
    options: [
      { value: 'none', label: 'None', description: 'No animation effects at all' },
      { value: 'fade', label: 'Fade', description: 'Elements smoothly fade in and out' },
      { value: 'slide', label: 'Slide', description: 'Elements slide in from a direction' },
      { value: 'scale', label: 'Scale', description: 'Elements grow/shrink when appearing' },
      { value: 'bounce', label: 'Bounce', description: 'Playful bouncing effect on appearance' },
    ],
  },
  {
    key: 'hoverEffect',
    label: 'Hover Effects',
    icon: 'MousePointer',
    description: 'What happens visually when you hover over buttons and interactive elements',
    options: [
      { value: 'none', label: 'None', description: 'No hover feedback' },
      { value: 'brighten', label: 'Brighten', description: 'Element gets slightly brighter' },
      { value: 'darken', label: 'Darken', description: 'Element gets slightly darker' },
      { value: 'lift', label: 'Lift', description: 'Element rises up with a shadow (most common)' },
      { value: 'grow', label: 'Grow', description: 'Element gets slightly larger' },
    ],
  },
  {
    key: 'darkMode',
    label: 'Dark Mode',
    icon: 'Moon',
    description: 'Whether your app supports dark mode and how it behaves',
    options: [
      { value: 'light', label: 'Light Only', description: 'Always light background — no dark mode' },
      { value: 'dark', label: 'Dark Only', description: 'Always dark background — no light mode' },
      { value: 'system', label: 'Follow System', description: 'Automatically matches the user\'s OS setting' },
      { value: 'toggle', label: 'User Toggle', description: 'User can switch between light and dark with a button' },
    ],
  },
  {
    key: 'typographyScale',
    label: 'Text Size',
    icon: 'Type',
    description: 'The overall size scale of text throughout the app',
    options: [
      { value: 'compact', label: 'Compact', description: 'Smaller text — fits more content on screen' },
      { value: 'normal', label: 'Normal', description: 'Standard readable text size' },
      { value: 'spacious', label: 'Large', description: 'Bigger text — easier to read, especially for older users' },
    ],
  },
  {
    key: 'headingWeight',
    label: 'Heading Weight',
    icon: 'Heading',
    description: 'How thick and bold your headings and titles appear',
    options: [
      { value: 'light', label: 'Light', description: 'Thin, elegant headings' },
      { value: 'normal', label: 'Normal', description: 'Standard weight headings' },
      { value: 'bold', label: 'Bold', description: 'Strong, prominent headings' },
      { value: 'extra-bold', label: 'Extra Bold', description: 'Very heavy, impactful headings' },
    ],
  },
  {
    key: 'layoutDensity',
    label: 'Layout Density',
    icon: 'LayoutGrid',
    description: 'How much space there is between elements on the page',
    options: [
      { value: 'compact', label: 'Compact', description: 'Less whitespace — dense, information-rich layout' },
      { value: 'comfortable', label: 'Comfortable', description: 'Balanced spacing — easy to scan' },
      { value: 'spacious', label: 'Spacious', description: 'Lots of breathing room — open and airy feel' },
    ],
  },
  {
    key: 'focusRing',
    label: 'Focus Indicators',
    icon: 'Target',
    description: 'The visual ring that appears when you tab to an element (accessibility)',
    options: [
      { value: 'none', label: 'None', description: 'No focus ring (not recommended for accessibility)' },
      { value: 'subtle', label: 'Subtle', description: 'Light focus ring that doesn\'t distract' },
      { value: 'bold', label: 'Bold', description: 'Clear, obvious focus ring for keyboard users' },
      { value: 'glow', label: 'Glow', description: 'Glowing focus effect that\'s impossible to miss' },
    ],
  },
]
