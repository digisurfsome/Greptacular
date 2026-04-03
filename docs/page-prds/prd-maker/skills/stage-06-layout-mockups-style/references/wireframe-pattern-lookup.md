# Wireframe Pattern Lookup Table

> Deterministic mapping from app type to wireframe pattern. This is NOT AI creativity — it's a lookup. The AI identifies the app type; the pattern follows from this table.

## Primary Patterns (92% Case)

| App Type | Wireframe Pattern | Navigation | Content Area | Key Elements |
|----------|------------------|------------|-------------|-------------|
| `dashboard` | Sidebar + Top Nav + Content Grid + Cards | Collapsible sidebar (left), breadcrumb top bar | Grid of cards/widgets, charts, tables | Summary cards, data tables, charts, activity feed, quick actions |
| `chat` | Conversation List + Message Thread + Input Bar | Left panel (conversation list), no top nav needed | Message thread (center), optional right panel (details) | Contact/channel list, message bubbles, input with attachments, typing indicator |
| `wizard` | Step Indicator + Single Form Area + Next/Back | Step progress bar (top), minimal nav | Single form section (center), navigation buttons (bottom) | Progress steps, form fields, validation, prev/next buttons, summary step |
| `marketplace` | Search Bar + Filter Sidebar + Product Grid | Top search bar, left filter panel | Product card grid (center), pagination | Search input, category filters, price range, sort, product cards, cart icon |
| `tool` | Toolbar + Workspace + Properties Panel | Toolbar (top), tool palette (left optional) | Canvas/workspace (center), properties panel (right) | Tool buttons, canvas area, property editors, layers panel, zoom controls |
| `landing` | Hero + Features + Testimonials + CTA | Sticky top nav with CTA button | Full-width sections, stacked vertically | Hero with headline + CTA, feature grid, testimonial cards, pricing table, footer |
| `settings` | Tab List + Form Sections | Vertical tab list (left) or horizontal tabs (top) | Form sections per tab | Tab navigation, labeled form groups, toggles, save/cancel buttons |

## Secondary Patterns (Variations)

### Dashboard Variations

| Variant | Description | When to Use |
|---------|-------------|-------------|
| Top Nav Only + Grid | No sidebar, horizontal nav with dropdowns | Simple dashboards with < 5 sections |
| Sidebar + Cards Only | No top nav, sidebar handles all navigation | Data-heavy dashboards, admin panels |
| Tabbed Dashboard | Tab bar at top, each tab is a dashboard view | Multi-role dashboards (e.g., admin vs user view) |

### Chat Variations

| Variant | Description | When to Use |
|---------|-------------|-------------|
| Full-width Thread | No conversation list visible, toggle to switch | Mobile-first chat, single-conversation focus |
| Chat + Sidebar Widgets | Conversation list + thread + right sidebar with tools | Support/helpdesk apps with customer context |
| Threaded Channels | Channel list + thread + nested replies | Team communication (Slack-like) |

### Wizard Variations

| Variant | Description | When to Use |
|---------|-------------|-------------|
| Sidebar Steps | Steps listed in left sidebar instead of top bar | Complex wizards with 8+ steps |
| Card-per-Step | Each step is a card, all visible, expand on click | Short wizards (3-4 steps) where overview matters |
| Modal Wizard | Wizard in a modal overlay | Secondary flows (e.g., onboarding after signup) |

### Marketplace Variations

| Variant | Description | When to Use |
|---------|-------------|-------------|
| Map + List | Split view: map (left/top) + list (right/bottom) | Location-based marketplaces (Airbnb-like) |
| Gallery Grid | No filter sidebar, full-width masonry grid | Visual-first marketplaces (art, photography) |
| Category Browse | Category cards → subcategory → product list | Deep catalog with hierarchical categories |

### Tool Variations

| Variant | Description | When to Use |
|---------|-------------|-------------|
| Split Pane | Two resizable panes (e.g., code editor + preview) | Editor/IDE tools, diff viewers |
| Canvas Only | Full-screen canvas, floating toolbars | Drawing/design tools, whiteboard apps |
| Command Palette | Minimal UI, keyboard-driven with command palette | Developer tools, power-user interfaces |

### Landing Variations

| Variant | Description | When to Use |
|---------|-------------|-------------|
| Single Page Scroll | All sections on one page, smooth scroll between | Simple products with one offering |
| Multi-page Marketing | Landing + separate pages for features, pricing, docs | Complex products needing deep content |
| App-Shell Landing | Landing that transitions into the app (no full reload) | SaaS products with free-tier access |

## Hybrid Pattern Resolution

When an app combines two types (e.g., dashboard + chat):

1. Identify the DOMINANT type — what does the user spend 70%+ of their time doing?
2. Use the dominant type's pattern as the PRIMARY arrangement
3. Embed the secondary type as a component WITHIN the primary layout:
   - Chat in a dashboard → Chat panel in sidebar or slide-out drawer
   - Dashboard in a tool → Stats widgets in the tool's properties panel
   - Marketplace with chat → Chat as a modal/drawer from product detail
4. Present BOTH the pure dominant pattern AND the hybrid as separate arrangement options

## Archetype-to-App-Type Mapping

| Archetype Keywords | App Type |
|-------------------|----------|
| productivity, admin, analytics, monitoring, CRM, ERP | `dashboard` |
| messaging, communication, support, helpdesk | `chat` |
| onboarding, form-builder, survey, checkout, registration | `wizard` |
| e-commerce, listings, search-browse, two-sided | `marketplace` |
| editor, builder, IDE, canvas, designer | `tool` |
| marketing, portfolio, product-page, SaaS-homepage | `landing` |
| preferences, configuration, profile, account | `settings` |

If the archetype contains keywords from multiple types, it's a hybrid — follow the hybrid resolution above.
