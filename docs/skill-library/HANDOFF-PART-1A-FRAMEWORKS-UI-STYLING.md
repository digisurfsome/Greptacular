# Skill Generation Handoff — Part 1A: Frameworks, UI, Styling, Components (Skills 1-13)

> **For fresh agents:** This is a self-contained guide. Run `npx ctx7 skills generate`, paste the prompt for each skill, and save the output to the listed path.
>
> **Setup (one-time):** Run `npx ctx7 setup` first. Free tier, no credit card.
>
> **Quality rule:** Every skill must cover CURRENT version patterns. Exclude deprecated APIs. When the wizard asks clarifying questions, use the tips provided.

---

## FRAMEWORKS

### 1. next-js-app-router
- **Save to:** `skills/frameworks/next-js-app-router.md`
- **Library:** Next.js 16+ | **Boilerplate:** web, dual

**Paste this prompt into ctx7:**
> Next.js 16 App Router comprehensive patterns including: server components vs client components decision tree, route handlers (GET/POST/PUT/DELETE), middleware for auth and redirects, server actions for form mutations, streaming with Suspense, static and dynamic rendering, caching strategies (fetch cache, full route cache, router cache), metadata API for SEO, parallel routes, intercepting routes, and error boundaries. App Router ONLY — do NOT include Pages Router patterns.

**When the wizard asks:**
- Routing model? → "App Router only, not Pages Router"
- React version? → "React 19 with server components"
- Deployment? → "Vercel-optimized but platform-agnostic"

**Must include these patterns:**
- `'use client'` vs default server component decision rules
- Route handlers in `app/api/` (GET, POST, PUT, DELETE exports)
- Server Actions with `'use server'` for form mutations
- Caching: `revalidatePath()`, `revalidateTag()`, fetch cache options
- Middleware for auth redirects and path rewriting

---

### 2. nuxt-4
- **Save to:** `skills/frameworks/nuxt-4.md`
- **Library:** Nuxt 4 | **Boilerplate:** universal

**Paste this prompt into ctx7:**
> Nuxt 4 full-stack patterns including: auto-imports system for components and composables, file-based routing with dynamic params, server routes in server/api/ and server/routes/, useFetch and useAsyncData for data fetching with deduplication, route middleware (defineNuxtRouteMiddleware) and global middleware, Nitro server engine configuration, composables for shared logic, state management with useState, SEO with useHead and useSeoMeta, and Nuxt module ecosystem. Nuxt 4 ONLY — not Nuxt 3 or Nuxt 2 patterns.

**When the wizard asks:**
- Vue version? → "Vue 3 Composition API with script setup"
- Rendering mode? → "Universal (SSR) by default"
- Package manager? → "pnpm preferred"

**Must include these patterns:**
- Auto-imports (no manual import for components, composables, utils)
- `useFetch` vs `useAsyncData` vs `$fetch` — when to use each
- Server routes in `server/api/` directory
- `defineNuxtRouteMiddleware` for route protection
- Nitro server configuration and presets

---

### 3. sveltekit
- **Save to:** `skills/frameworks/sveltekit.md`
- **Library:** SvelteKit 2+ | **Boilerplate:** universal

**Paste this prompt into ctx7:**
> SvelteKit comprehensive patterns including: load functions (+page.server.ts and +page.ts), form actions for mutations, hooks (handle, handleFetch, handleError in hooks.server.ts), file-based routing with +page/+layout/+error conventions, server-side rendering and prerendering, adapter configuration for different deployment targets, environment variables with $env, and error handling with error() and redirect(). Current SvelteKit with Svelte 5 runes integration.

**When the wizard asks:**
- Svelte version? → "Svelte 5 with runes"
- Rendering? → "SSR by default with selective prerendering"
- Adapter? → "adapter-auto for flexibility"

**Must include these patterns:**
- `+page.server.ts` load functions for server data
- Form actions with `+page.server.ts` actions export
- `hooks.server.ts` handle function for middleware
- `$env/static/private` and `$env/dynamic/public` usage
- Error/redirect helpers from `@sveltejs/kit`

---

### 4. remix
- **Save to:** `skills/frameworks/remix.md`
- **Library:** Remix 2+ | **Boilerplate:** universal

**Paste this prompt into ctx7:**
> Remix patterns including: loader functions for GET data fetching, action functions for POST/PUT/DELETE mutations, nested routes with Outlet for layout composition, error boundaries with ErrorBoundary export, form handling with Form component and useActionData, deferred data loading with defer() and Await component, meta function for SEO, route module API (links, headers, handle), and resource routes for non-HTML responses. Current Remix with Vite and React Router v7 integration.

**When the wizard asks:**
- Bundler? → "Vite"
- React version? → "React 19"
- Deployment? → "Platform-agnostic"

**Must include these patterns:**
- `loader` function returning `json()` responses
- `action` function handling form submissions
- `<Form>` component with method="post"
- `defer()` + `<Await>` for streaming data
- Nested `<Outlet>` for layout composition

---

### 5. astro
- **Save to:** `skills/frameworks/astro.md`
- **Library:** Astro 5+ | **Boilerplate:** universal

**Paste this prompt into ctx7:**
> Astro patterns including: content collections with defineCollection and type-safe schemas, islands architecture for partial hydration (client:load, client:visible, client:idle directives), view transitions API for SPA-like navigation, SSG and SSR rendering modes, integration system for React/Vue/Svelte components, frontmatter scripting in .astro files, Astro.glob for dynamic imports, image optimization with astro:assets, and endpoint routes for API responses.

**When the wizard asks:**
- Rendering? → "SSG default with SSR opt-in per route"
- UI framework? → "Multi-framework (React, Vue, Svelte via integrations)"
- Content? → "Content collections with Zod schemas"

**Must include these patterns:**
- `defineCollection` with Zod schema validation
- `client:load` / `client:visible` / `client:idle` hydration directives
- View Transitions with `<ViewTransitions />` component
- Frontmatter (`---`) scripting for server logic
- `getCollection()` and `getEntry()` for querying content

---

## UI LIBRARIES

### 6. react-19
- **Save to:** `skills/ui/react-19.md`
- **Library:** React 19 | **Boilerplate:** web, dual

**Paste this prompt into ctx7:**
> React 19 patterns including: server components (default) vs client components ('use client'), the use() hook for reading promises and context, Actions for async form handling, useOptimistic for optimistic UI updates, useFormStatus for pending states, transitions with useTransition and startTransition, Suspense boundaries for loading states, ref as prop (no forwardRef needed), and document metadata with title/meta tags in components. React 19 ONLY — do NOT include React 18 patterns like forwardRef or old Context.Provider syntax.

**When the wizard asks:**
- Version? → "React 19 only, not React 18"
- Framework? → "Framework-agnostic (works with Next.js, Remix, Vite)"
- State management? → "Built-in hooks, not external libraries"

**Must include these patterns:**
- Server vs client component decision tree
- `use()` hook replacing useContext and for promise resolution
- `useOptimistic` for instant UI feedback
- `useFormStatus` for form pending states
- `<Suspense>` boundaries with fallback UI

---

### 7. vue-3
- **Save to:** `skills/ui/vue-3.md`
- **Library:** Vue 3 | **Boilerplate:** universal

**Paste this prompt into ctx7:**
> Vue 3 Composition API patterns including: script setup syntax with defineProps and defineEmits, reactive state with ref() and reactive(), computed properties with computed(), watchers with watch() and watchEffect(), dependency injection with provide/inject, component lifecycle with onMounted/onUnmounted, template refs, slots and scoped slots, Pinia store creation with defineStore, and TypeScript integration with PropType and generic components.

**When the wizard asks:**
- API style? → "Composition API with script setup only, not Options API"
- State management? → "Pinia"
- TypeScript? → "Yes, full TypeScript support"

**Must include these patterns:**
- `<script setup>` with `defineProps<{}>()` and `defineEmits<{}>()`
- `ref()` vs `reactive()` — when to use each
- `computed()` for derived state
- `watch()` with getter function vs `watchEffect()`
- Pinia `defineStore` with setup syntax

---

### 8. svelte-5
- **Save to:** `skills/ui/svelte-5.md`
- **Library:** Svelte 5 | **Boilerplate:** universal

**Paste this prompt into ctx7:**
> Svelte 5 runes system including: $state for reactive declarations, $derived for computed values, $effect for side effects, $props for component props with defaults, $bindable for two-way binding props, snippets for reusable template blocks replacing slots, event handling with onclick (not on:click), and component composition patterns. Svelte 5 runes ONLY — do NOT include Svelte 4 syntax (let declarations, export let, $: reactive, on: directive).

**When the wizard asks:**
- Version? → "Svelte 5 only, not Svelte 4"
- Reactivity? → "Runes only ($state, $derived, $effect)"
- Events? → "New syntax (onclick) not old (on:click)"

**Must include these patterns:**
- `let count = $state(0)` for reactive state
- `let doubled = $derived(count * 2)` for computed
- `$effect(() => { ... })` for side effects
- `let { name = 'default' } = $props()` for component props
- Snippets replacing `<slot>` for template composition

---

## STYLING

### 9. tailwind-css-v4
- **Save to:** `skills/styling/tailwind-css-v4.md`
- **Library:** Tailwind CSS v4 | **Boilerplate:** web, dual

**Paste this prompt into ctx7:**
> Tailwind CSS v4 patterns including: CSS-first configuration with @theme directive replacing tailwind.config.js, PostCSS setup with @tailwindcss/postcss plugin, new utility classes and syntax changes from v3, container queries with @container, CSS custom properties for theming, dark mode with media or class strategy, @layer for custom utilities, and migration patterns from v3 config files to v4 CSS-first approach. Tailwind v4 ONLY — do NOT include v3 JavaScript config patterns.

**When the wizard asks:**
- Version? → "v4 only, not v3"
- Config approach? → "CSS-first with @theme, not tailwind.config.js"
- Framework? → "Works with any framework, PostCSS-based"

**Must include these patterns:**
- `@theme { }` block replacing `tailwind.config.js` entirely
- `@tailwindcss/postcss` plugin in PostCSS config
- `@theme { --color-*: }` for custom color tokens
- Container queries with `@container` and `@min-width`
- Migration: how v3 `extend` maps to v4 `@theme`

---

### 10. css-modules
- **Save to:** `skills/styling/css-modules.md`
- **Library:** CSS Modules | **Boilerplate:** universal

**Paste this prompt into ctx7:**
> CSS Modules patterns including: scoped class names with .module.css files, composes keyword for style composition, :global() selector for global overrides, TypeScript typed CSS modules with declaration files or plugins, Next.js CSS Modules integration, dynamic class application with classnames/clsx, and CSS Modules with PostCSS for nesting and custom properties.

**When the wizard asks:**
- Framework? → "Next.js primary, but framework-agnostic patterns"
- TypeScript? → "Yes, with typed modules"
- Preprocessor? → "PostCSS, not Sass"

**Must include these patterns:**
- `import styles from './Component.module.css'` usage
- `composes: className from './other.module.css'`
- `:global(.className)` for escaping scope
- TypeScript declarations for `.module.css` files
- `clsx(styles.base, condition && styles.active)` dynamic classes

---

## COMPONENT LIBRARIES

### 11. shadcn-ui
- **Save to:** `skills/components/shadcn-ui.md`
- **Library:** shadcn/ui | **Boilerplate:** web, dual

**Paste this prompt into ctx7:**
> shadcn/ui patterns including: npx shadcn-ui init setup and configuration, CLI for adding individual components (npx shadcn-ui add button), CSS variable theming with globals.css, customizing components after installation, class-variance-authority (CVA) for variant patterns, extending components with additional variants, dark mode with next-themes, form components with react-hook-form integration, and the components.json configuration file.

**When the wizard asks:**
- Framework? → "Next.js with React 19"
- Styling? → "Tailwind CSS v4"
- Package manager? → "pnpm"

**Must include these patterns:**
- `npx shadcn-ui init` setup flow and `components.json`
- `npx shadcn-ui add [component]` for individual installs
- CSS variables in `globals.css` for theme customization
- `cva()` for creating variant components
- Extending installed components (they're YOUR code, not a library)

---

### 12. radix-ui
- **Save to:** `skills/components/radix-ui.md`
- **Library:** Radix UI | **Boilerplate:** web, dual

**Paste this prompt into ctx7:**
> Radix UI primitives patterns including: Dialog (modal, sheet, alert dialog), DropdownMenu with items and sub-menus, Accordion with single and multiple modes, Toast for notifications, NavigationMenu for nav bars, ScrollArea for custom scrollbars, Tabs with content panels, Popover for tooltips and popovers, compound component composition pattern (Root/Trigger/Content), accessibility features (WAI-ARIA, keyboard navigation, focus management), and styling with Tailwind CSS.

**When the wizard asks:**
- Styling approach? → "Unstyled primitives, styled with Tailwind CSS"
- Framework? → "React"
- Accessibility? → "Full WAI-ARIA compliance is critical"

**Must include these patterns:**
- `<Dialog.Root>/<Dialog.Trigger>/<Dialog.Content>` compound pattern
- `<DropdownMenu.Root>` with items, separators, sub-menus
- Controlled vs uncontrolled usage (open/onOpenChange)
- Keyboard navigation (Arrow keys, Escape, Enter)
- `asChild` prop for merging with custom components

---

### 13. headless-ui
- **Save to:** `skills/components/headless-ui.md`
- **Library:** Headless UI | **Boilerplate:** universal

**Paste this prompt into ctx7:**
> Headless UI patterns for React and Vue including: Listbox for custom selects, Combobox for searchable selects, Dialog for modals, Menu for dropdown menus, Disclosure for collapsible sections, Tabs for tabbed interfaces, Transition for enter/leave animations, and RadioGroup for custom radio buttons. Include compound component patterns, controlled state, keyboard navigation, and screen reader accessibility.

**When the wizard asks:**
- Framework? → "React primary, Vue secondary"
- Styling? → "Unstyled, bring your own Tailwind classes"
- Animations? → "Transition component for enter/leave"

**Must include these patterns:**
- `<Listbox>` with `<Listbox.Option>` for custom selects
- `<Combobox>` with filtering and custom display
- `<Dialog>` with overlay and panel composition
- `<Transition>` with enter/enterFrom/enterTo/leave classes
- Render prop pattern for custom styling control
