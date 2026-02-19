/**
 * Font options for the design font selector.
 * These are popular Google Fonts + system defaults.
 */

export interface FontOption {
  id: string
  name: string
  family: string  // CSS font-family value
  category: 'sans-serif' | 'serif' | 'monospace' | 'display'
  googleFont?: string  // Google Fonts name for loading
}

export const FONT_OPTIONS: FontOption[] = [
  { id: 'inter', name: 'Inter', family: "'Inter', system-ui, sans-serif", category: 'sans-serif', googleFont: 'Inter' },
  { id: 'roboto', name: 'Roboto', family: "'Roboto', sans-serif", category: 'sans-serif', googleFont: 'Roboto' },
  { id: 'poppins', name: 'Poppins', family: "'Poppins', sans-serif", category: 'sans-serif', googleFont: 'Poppins' },
  { id: 'open-sans', name: 'Open Sans', family: "'Open Sans', sans-serif", category: 'sans-serif', googleFont: 'Open+Sans' },
  { id: 'montserrat', name: 'Montserrat', family: "'Montserrat', sans-serif", category: 'sans-serif', googleFont: 'Montserrat' },
  { id: 'dm-sans', name: 'DM Sans', family: "'DM Sans', sans-serif", category: 'sans-serif', googleFont: 'DM+Sans' },
  { id: 'space-grotesk', name: 'Space Grotesk', family: "'Space Grotesk', sans-serif", category: 'sans-serif', googleFont: 'Space+Grotesk' },
  { id: 'nunito', name: 'Nunito', family: "'Nunito', sans-serif", category: 'sans-serif', googleFont: 'Nunito' },
  { id: 'playfair', name: 'Playfair Display', family: "'Playfair Display', serif", category: 'serif', googleFont: 'Playfair+Display' },
  { id: 'merriweather', name: 'Merriweather', family: "'Merriweather', serif", category: 'serif', googleFont: 'Merriweather' },
  { id: 'lato', name: 'Lato', family: "'Lato', sans-serif", category: 'sans-serif', googleFont: 'Lato' },
  { id: 'source-code', name: 'Source Code Pro', family: "'Source Code Pro', monospace", category: 'monospace', googleFont: 'Source+Code+Pro' },
]
