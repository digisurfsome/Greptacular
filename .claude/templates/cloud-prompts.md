# Reusable Cloud Prompts

A collection of prompts you can copy and paste into any AI tool (ChatGPT, Claude, Gemini, etc.).

**To add a new prompt:** Copy the structure of any prompt below — duplicate everything between the `---` dividers, update the number/title, and paste in your new prompt content.

---

## Prompt 1: Style Guide Generator

### How To Use

1. Find a screenshot of an app, website, or dashboard whose visual style you love
2. Copy the prompt below
3. Paste it into ChatGPT, Claude, or Gemini along with your image
4. Copy the output and paste it into **Section 3** of the main Idea Code template

### The Prompt

> Copy everything in the block below.

**Role:** You are an expert Design System Architect and Senior Frontend Engineer. You specialize in "Atomic Design" principles and creating abstract, reusable component libraries.

**Objective:** I will provide an image. Your task is to ignore the specific content, text, and business context of the image. Instead, extract the underlying Visual Design Language (the "Visual DNA"). I need a generic, reusable style guide that I can apply to any type of application, not just the one shown in the image.

**Strict Constraints (Read Carefully):**
1. Do not mention specific text found in the image (e.g., do not say "The 'Revenue' title uses 16px"; say "Section Headers use 16px").
2. Do not mention specific business logic (e.g., do not say "The 'Sales Card' has a shadow"; say "The 'Primary Data Container' has a shadow").
3. Generalize all findings into reusable tokens and classes.

**Output Requirements:** Please generate a Technical Design System Report in Markdown covering:

#### 1. Abstract Color Tokens (Global Variables)
Extract the palette but name them by function, not content:
- **Brand/Primary:** (The main interaction color)
- **Surface/Backgrounds:** (Main background, Secondary background/sidebar, Card background)
- **Text Hierarchy:** (Primary, Secondary/Muted, Tertiary)
- **Borders/Dividers:** (Line colors)
- **Status Colors:** (If present: Success, Error, Warning)

#### 2. Global Typography System
- Identify the font family (or closest Google Font)
- Define the abstract hierarchy:
  - **Display/Hero:** (Largest text styles)
  - **Headings:** (H1, H2, H3 equivalents)
  - **Body:** (Regular and Bold variants)
  - **Microcopy:** (Labels, captions, small text)
- Detail: Include specific weights (400, 500, 600, 700) and approximate line-heights

#### 3. Universal Component Patterns (Molecules)
- **Surfaces/Cards:** Analyze the container style. What is the border radius? Is there a border stroke? Is there a box shadow? (Provide CSS values)
- **Interactables (Buttons/Links):** Analyze the primary and secondary button styles (padding, radius, color, hover effects)
- **Form Inputs:** Analyze the style of text fields (background color, border color, corner radius)
- **Iconography:** Describe the visual style of icons used (e.g., "Thin stroke, 1.5px, rounded corners" or "Solid filled, sharp edges")

#### 4. Layout & Spacing Physics
- **Spacing Scale:** Determine the base unit of the design (e.g., 4px, 8px, or 10px)
- **Density:** Is the design "Cozy" (lots of whitespace/padding) or "Compact" (data-dense)?
- **Radius Consistency:** What is the rule for rounded corners? (e.g., "4px for small elements, 12px for containers")

#### 5. Tailwind CSS Theme Extension
Based on the abstract analysis, write a tailwind.config.js theme object. Do not include content-specific names.

```javascript
// tailwind.config.js
module.exports = {
  theme: {
    extend: {
      colors: {
        brand: {
          light: '#...',
          DEFAULT: '#...',
          dark: '#...',
        },
        surface: {
          canvas: '#...',   // main app background
          base: '#...',     // cards, sidebar
          muted: '#...',    // input fields, hover states
        },
        text: {
          primary: '#...',   // headers, key values
          secondary: '#...', // body text, labels
          tertiary: '#...',  // placeholders, inactive
        },
        border: {
          subtle: '#...',
        },
      },
      fontFamily: {
        sans: ['...', 'ui-sans-serif', 'system-ui', 'sans-serif'],
      },
      borderRadius: {
        'card': '...',
        'input': '...',
        'btn': '...',
      },
      boxShadow: {
        'card': '...',
      },
    }
  }
}
```

### Example Output

Here's what good output looks like (you'll get something similar):

```
## Style Guide Analysis

### 1. Color Tokens

**Brand/Primary:**
- brand-light: #E7FBC3
- brand-DEFAULT: #DFFF5E (electric lime)
- brand-dark: #B8D940

**Surfaces:**
- surface-canvas: #F9FAFB (main background)
- surface-base: #FFFFFF (cards, nav)
- surface-muted: #F3F4F6 (inputs, hover)

**Text:**
- text-primary: #111827 (near black)
- text-secondary: #6B7280 (slate)
- text-tertiary: #9CA3AF (muted)

**Borders:**
- border-subtle: #E5E7EB

### 2. Typography

**Font Family:** Inter (Google Fonts)

| Level | Size | Weight | Usage |
|-------|------|--------|-------|
| Display | 30px | 700 | Large metrics |
| H1 | 24px | 600 | Page titles |
| H2 | 18px | 600 | Section headers |
| Body | 14px | 400/500 | Regular text |
| Micro | 12px | 400 | Labels, captions |

### 3. Component Patterns

**Cards:**
- Background: White
- Border: 1px solid #E5E7EB
- Radius: 12px
- Shadow: 0 1px 3px rgba(0,0,0,0.05)
- Padding: 20-24px

**Primary Buttons:**
- Background: Brand gradient or solid
- Text: Dark for contrast
- Radius: 8px
- Padding: 12px 24px

**Inputs:**
- Background: #F3F4F6
- Border: None
- Radius: 8px

**Icons:**
- Style: Line/stroke, 1.5px
- Caps: Rounded

### 4. Spacing

- Base unit: 8px
- Density: Cozy (generous whitespace)
- Card gaps: 16-24px
- Section gaps: 32px

### 5. Tailwind Config

[Tailwind config code here]
```

### After Generating

Copy the relevant parts (colors, typography, component styles) and paste them into **Section 3: Style Guide** of your main Idea Code prompt template.

---

## Prompt 2: App Idea Generator

### How To Use

1. Copy the prompt below
2. Paste it into ChatGPT, Claude, or Gemini
3. Describe your app idea (can be rough/vague — that's fine!)
4. Copy the structured output into **Sections 1 & 2** of the main Idea Code template

### The Prompt

> Copy everything in the block below.

**Role:** You are a product strategist and startup advisor who helps people turn vague app ideas into clear, buildable MVPs.

**Objective:** I'm going to describe an app idea. It might be rough, incomplete, or just a general concept. Your job is to help me clarify it and output a structured specification I can use to build it.

**Your Process:**
1. If my idea is unclear, ask me 2-3 quick clarifying questions first
2. Once you understand, output the structured format below
3. Keep it MVP-focused — only essential features, nothing fancy

**Output Format (Follow Exactly):**

```
## SECTION 1: APP IDENTITY

**App Name:** [Suggest a short, memorable name]

**One-Line Description:** [What it does in one sentence — be specific]

**Target User:** [Who is this for? Be specific about their situation]

**Core Problem It Solves:** [What pain point does this eliminate?]

---

## SECTION 2: FEATURES

**Core Features (3-5 max):**
1. [Feature 1 — specific and actionable]
2. [Feature 2]
3. [Feature 3]
4. [Feature 4 — if needed]
5. [Feature 5 — if needed]

**What Users Can Do:**
- [Main action 1 — e.g., "Create and save recipes"]
- [Main action 2 — e.g., "Organize recipes into collections"]
- [Main action 3 — e.g., "Search their saved recipes"]
```

**Rules:**
- Maximum 5 features — this is an MVP
- Each feature should be one clear thing, not multiple things bundled
- "What Users Can Do" should be plain English actions, not technical jargon
- Don't include features like "user authentication" or "responsive design" — those are assumed
- Focus on what makes this app unique and useful

### My App Idea

[Describe your idea here — can be as rough as "an app for tracking workouts" or as detailed as you want]

### Examples

**Example Input:**
"I want an app where I can paste a recipe URL and it saves just the recipe without all the blog nonsense"

**Example Output:**

#### SECTION 1: APP IDENTITY

**App Name:** CleanRecipe

**One-Line Description:** Paste any recipe URL and get just the ingredients and steps — no life stories, no ads, no popups.

**Target User:** Home cooks who are frustrated by recipe blogs that bury the actual recipe under paragraphs of unnecessary content.

**Core Problem It Solves:** Recipe websites are bloated with ads, stories, and popups. Users just want the ingredients and steps in a clean format they can actually use while cooking.

#### SECTION 2: FEATURES

**Core Features (3-5 max):**
1. Paste a URL and automatically extract the recipe (ingredients + steps only)
2. Save extracted recipes to a personal collection
3. Scale recipe servings up or down with auto-calculated ingredients
4. Search saved recipes by ingredient or name

**What Users Can Do:**
- Paste a recipe URL and instantly see the clean version
- Save recipes to their personal cookbook
- Adjust serving sizes and see updated measurements
- Find saved recipes by searching ingredients they have

---

**Example Input:**
"something for freelancers to track time and invoices"

**Example Output:**

#### SECTION 1: APP IDENTITY

**App Name:** FreelanceFlow

**One-Line Description:** Track time on client projects and generate professional invoices in one click.

**Target User:** Freelancers and solo consultants who bill hourly and need a simple way to track time and get paid.

**Core Problem It Solves:** Freelancers waste time switching between time tracking apps and invoice tools, often forgetting to log hours or creating invoices manually from scattered notes.

#### SECTION 2: FEATURES

**Core Features (3-5 max):**
1. One-click timer to track time on any project
2. Organize time entries by client and project
3. Generate invoices from tracked time with one click
4. Dashboard showing unbilled hours and pending payments

**What Users Can Do:**
- Start/stop a timer when working on client projects
- See all time logged for each client
- Create a professional invoice from their tracked hours
- View how much money is outstanding across all clients

### Tips For Describing Your Idea

**Good inputs:**
- "An app for meal planning that suggests recipes based on what's in my fridge"
- "I want to track my guitar practice and see streaks"
- "A tool for teachers to create and share worksheets"
- "Something that helps me remember to water my plants"

**Too vague (I'll ask clarifying questions):**
- "A productivity app"
- "Something with AI"
- "An app for businesses"

**Too complex (I'll help you simplify to MVP):**
- "A full social network with marketplace, messaging, stories, live streaming, and AI recommendations"

---

<!-- ADD MORE PROMPTS BELOW — Copy the pattern: ## Prompt N: Title, ### How To Use, ### The Prompt, then a --- divider -->
