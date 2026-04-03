# Component Placement Conventions

> Standard UI component placement patterns per app type. Used by Sub-6b to place components on pages.

## Universal Placement Rules

These apply to ALL app types:

1. **Navigation** goes at the top (horizontal) or left side (vertical sidebar). Never bottom, never right.
2. **Primary action buttons** (CTA) go top-right of the content area or bottom-right of forms.
3. **Search** goes at the top, either in the nav bar or immediately below it.
4. **User menu / avatar** goes top-right corner, always.
5. **Notifications** go top-right, near the user menu (bell icon pattern).
6. **Breadcrumbs** go immediately below the top nav, above the content area.
7. **Modals** center on screen with backdrop overlay.
8. **Toast notifications** appear top-right or bottom-right, stacked.
9. **Loading states** replace the content area; never show a blank page.
10. **Empty states** show in the content area with illustration + CTA to create first item.

## Per-App-Type Conventions

### Dashboard

| Component Type | Placement | Notes |
|---------------|-----------|-------|
| Summary cards (KPIs) | Main content, top row | 3-5 cards in a row, full-width |
| Data tables | Main content, below cards | Full-width or 2/3 width |
| Charts/graphs | Main content, mixed with tables | Card containers, responsive grid |
| Activity feed | Sidebar (right) or bottom of main | Scrollable, time-ordered |
| Quick actions | Top bar or sidebar | Common operations (create, export) |
| Filters / date range | Top of content area, below breadcrumbs | Persistent across page sections |
| Navigation items | Left sidebar | Grouped by category with icons |

### Chat

| Component Type | Placement | Notes |
|---------------|-----------|-------|
| Conversation list | Left panel (fixed width ~300px) | Scrollable, search at top |
| Message thread | Center panel (flex) | Scrollable, newest at bottom |
| Message input | Bottom of center panel | Fixed position, expands on focus |
| User/channel info | Right panel (collapsible) | Member list, shared files, pinned items |
| Typing indicator | Above input bar | Inline with message thread |
| File attachments | Inline in messages + drag-drop zone | Preview thumbnails |
| Emoji/reaction picker | Popover from input bar or message hover | Floating panel |

### Wizard / Form

| Component Type | Placement | Notes |
|---------------|-----------|-------|
| Step indicator | Top of content area | Horizontal steps with numbers/labels |
| Form fields | Center content (max-width ~600px) | Single column, generous spacing |
| Field validation | Inline below each field | Red text + icon on error |
| Next/Back buttons | Bottom of form area, right-aligned | Primary (next) + secondary (back) |
| Summary/review step | Final step, read-only view of all inputs | Editable via "edit" links per section |
| Progress bar | Top, as part of step indicator | Percentage or step count |
| Help text / tooltips | Inline below labels or hover info icons | Context-sensitive |

### Marketplace

| Component Type | Placement | Notes |
|---------------|-----------|-------|
| Search bar | Top, prominent, full-width or centered | Auto-suggest, recent searches |
| Category filters | Left sidebar (desktop) / top accordion (mobile) | Collapsible sections per filter type |
| Product grid | Main content (right of filters) | 3-4 columns, responsive to 1-2 on mobile |
| Product card | Within grid | Image, title, price, rating, CTA |
| Sort controls | Top of product grid, right-aligned | Dropdown: relevance, price, rating, newest |
| Pagination | Bottom of product grid | Page numbers or infinite scroll |
| Cart icon | Top nav, right side | Badge with item count |
| Product detail | Full page (replaces grid) | Image gallery left, info right |

### Tool

| Component Type | Placement | Notes |
|---------------|-----------|-------|
| Toolbar | Top of workspace | Icon buttons, grouped by function |
| Tool palette | Left sidebar (narrow, icon-only) | Vertical icon strip |
| Canvas/workspace | Center (takes maximum space) | Scrollable/zoomable |
| Properties panel | Right sidebar (collapsible) | Context-sensitive to selected element |
| Layers panel | Right sidebar (below properties) | Drag-reorderable list |
| Zoom controls | Bottom-right of canvas | Zoom in/out/fit buttons |
| Status bar | Bottom of screen, full-width | File info, cursor position, zoom level |
| Command palette | Center modal (on keyboard shortcut) | Searchable command list |

### Landing Page

| Component Type | Placement | Notes |
|---------------|-----------|-------|
| Nav bar | Top, sticky on scroll | Logo left, links center/right, CTA right |
| Hero section | Full-width, first section | Headline, subheadline, CTA, optional image/video |
| Feature grid | Below hero | 3-4 columns, icon + title + description |
| Social proof / testimonials | Below features | Carousel or grid of testimonial cards |
| Pricing table | Own section | 2-4 tier columns, highlight recommended |
| FAQ | Below pricing | Accordion pattern |
| CTA banner | Above footer | Full-width, contrasting background |
| Footer | Bottom | Logo, link columns, social icons, legal |

### Settings

| Component Type | Placement | Notes |
|---------------|-----------|-------|
| Tab/section nav | Left sidebar (vertical) or top (horizontal) | Category labels: Profile, Security, Notifications, etc. |
| Form sections | Main content area | Grouped by category, separated by dividers |
| Toggle switches | Inline in form sections | Right-aligned within rows |
| Save/Cancel buttons | Bottom of each section or sticky footer | Primary (save) + secondary (cancel) |
| Danger zone | Bottom of settings, red-bordered | Account deletion, data export |
| Avatar upload | Top of profile section | Click-to-upload with preview |
| Connected accounts | Own section | List with connect/disconnect buttons |

## Page Grouping Rules

When grouping mechanisms into pages:

| Mechanism Pattern | Page Pattern | Notes |
|------------------|-------------|-------|
| Auth (login, register, forgot password) | 1-3 pages: Login, Register, Forgot Password | Can be combined into one page with tabs |
| CRUD for an entity | 2 pages: Entity List + Entity Detail | Detail page handles create/edit via modal or inline |
| User profile | 1 page: Profile (within settings or standalone) | Combines view + edit modes |
| Search + Browse | 1 page with filters | Search is a component, not a separate page |
| Notifications | 0 pages (dropdown) or 1 page (full history) | Depends on notification volume |
| Admin panel | Multiple pages mirroring main app | Often a separate route prefix (/admin/*) |
| Onboarding | 1 wizard page (multi-step) | Shown once after registration |
| Error pages | 2 pages: 404, 500 | Static, minimal |

## Route Conventions

| Route Pattern | Usage |
|--------------|-------|
| `/` | Dashboard or landing (authenticated vs not) |
| `/login`, `/register`, `/forgot-password` | Auth pages |
| `/{entity}` | Entity list (e.g., `/tasks`, `/products`) |
| `/{entity}/:id` | Entity detail (e.g., `/tasks/123`) |
| `/{entity}/new` | Create new entity |
| `/settings` | Settings root |
| `/settings/{section}` | Settings sub-section |
| `/admin` | Admin panel root |
| `/admin/{entity}` | Admin entity management |
