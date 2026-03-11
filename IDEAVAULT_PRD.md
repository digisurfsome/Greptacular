# Project: IdeaVault — App Idea Organizer

# Agent OS Context

---

## STANDARDS LAYER

### Coding Conventions
- **Language**: TypeScript (strict mode)
- **Style Guide**: ESLint recommended + Prettier
- **Key Patterns**:
  - Functional components with React hooks only (no class components)
  - Custom hooks for all localStorage operations (useLocalStorage, useIdeas)
  - All state mutations go through a central ideas context/hook
  - UUID generation via `crypto.randomUUID()`

### Architecture Standards
- **Architecture Type**: Single-page application, client-only (no backend)
- **Folder Structure**:
  ```
  src/
  ├── components/        # React components
  │   ├── layout/        # Header, Sidebar, PageWrapper
  │   ├── ideas/         # IdeaCard, IdeaForm, IdeaList
  │   ├── scoring/       # ScoreSlider, TierBadge, ScoreDisplay
  │   ├── dashboard/     # StatCard, DashboardSummary
  │   ├── groups/        # GroupView, GroupSection
  │   └── common/        # Modal, ConfirmDialog, SearchBar, Badge
  ├── hooks/             # Custom React hooks
  ├── types/             # TypeScript interfaces and enums
  ├── utils/             # Pure utility functions (scoring, filtering, export)
  └── styles/            # Tailwind config and globals
  ```
- **Component Organization**: One component per file, co-located types where small

### Quality Standards
- **Testing**: Manual verification against failure conditions per phase
- **Documentation**: Inline comments only where logic is non-obvious
- **Security**: No external API calls, all data stays in localStorage
- **Performance**: Instant UI updates, no loading states needed (local data only)

### Technology Stack
- **Frontend**: React 19 + TypeScript + Tailwind CSS + Vite
- **State**: localStorage with custom hooks (no Redux, no backend)
- **Build**: Vite with default React-TS template
- **Icons**: Lucide React (lightweight icon set)

### Design Standards
- **Theme**: Dark mode only
- **Cards**: Clean with subtle borders (`border-gray-700/800`), rounded corners
- **Badges**: Colored pills for categories and status
- **Typography**: System font stack, clear hierarchy
- **Layout**: Responsive grid — 1 col mobile, 2 col tablet, 3-4 col desktop
- **Interactions**: Modals for create/edit, confirm dialogs for destructive actions

---

## PRODUCT LAYER

### Vision
A fast, local-first app for capturing, scoring, and organizing app ideas — so you never lose a good idea and can objectively compare them when deciding what to build next.

### Target Users
Solo developers, indie hackers, and makers who constantly generate app ideas and need a structured way to evaluate and prioritize them.

### Core Use Cases
1. **Capture** — Quickly save an app idea with a title and one-liner before you forget it
2. **Evaluate** — Score ideas on market potential, feasibility, uniqueness, and excitement to get an objective ranking
3. **Organize** — Tag, group, filter, and search ideas to find patterns and make build decisions
4. **Export** — Back up all ideas as JSON and import them on another device

### Roadmap
- **Phase 1**: Core CRUD — create, read, update, delete ideas with localStorage persistence
- **Phase 2**: Scoring system — 4-axis scoring, composite score, tier badges, sort/filter
- **Phase 3**: Smart organization — tags, groups, search, dashboard summary, export/import

---

## SPECS LAYER

--- PHASE 1 ---
Build the foundation of IdeaVault, an app idea organizer.
Tech: React 19 + TypeScript + Tailwind CSS + Vite. All data stored in localStorage (no backend).
Data model for each idea:
- id (uuid)
- title (string)
- oneLiner (string, 1-sentence pitch)
- description (string, longer notes)
- category (enum: SaaS, Tool, Marketplace, AI/Automation, Content, Other)
- status (enum: Raw Idea, Exploring, Ready to Build, In Progress, Shipped, Parked)
- createdAt, updatedAt (timestamps)
Build these views:
1. Idea List — card grid showing all ideas with title, one-liner, category badge, status badge. Sort by newest first.
2. Add/Edit Idea — modal form with all fields. Title and oneLiner required, rest optional.
3. Delete — confirm dialog, removes from localStorage.
Design: Dark theme, clean cards with subtle borders, category badges are colored pills. Keep it minimal and fast. Mobile responsive.
FAILURE CONDITIONS — not done if:
- Ideas don't persist after page refresh
- Can't create, edit, and delete ideas
- Cards don't show category and status badges
- Form doesn't validate required fields

--- PHASE 2 ---
Add the scoring and judging system to IdeaVault.
Each idea gets 4 scores (1-10 scale, set by user via slider or number input):
- marketPotential — "How big is the audience?"
- feasibility — "How hard is this to build?"
- uniqueness — "Does anything like this exist?"
- excitement — "How fired up am I about this?"
Auto-calculated fields:
- compositeScore = weighted average: (market * 0.3) + (feasibility * 0.25) + (uniqueness * 0.2) + (excitement * 0.25)
- tier = "S" (9-10), "A" (7-8.9), "B" (5-6.9), "C" (below 5), "Unscored" (no scores yet)
Update the UI:
1. Idea cards now show the composite score as a large number and the tier as a colored letter badge (S=gold, A=green, B=blue, C=gray)
2. Add scoring section to the edit modal — 4 sliders with labels and the live composite score
3. Add sort options to the list: by score (high to low), by date, by name, by tier
4. Add filter by: category, status, tier
FAILURE CONDITIONS — not done if:
- Scores don't save to localStorage
- Composite score doesn't update live as sliders move
- Can't sort and filter the idea list
- Tier badges don't show on cards

--- PHASE 3 ---
Add smart grouping, search, and a dashboard summary to IdeaVault.
Feature 1 — Tags and Groups:
- Add a "tags" field to ideas (array of strings, free-text input with autocomplete from existing tags)
- Add a "group" field (optional string — e.g., "Marketing Tools", "AI Agents", "Content Apps")
- Add a Groups view: shows groups as collapsible sections, with idea cards inside. Ungrouped ideas go in an "Ungrouped" section.
- Users can drag ideas between groups OR assign group from the edit modal.
Feature 2 — Search:
- Add a search bar at the top of the idea list
- Searches across title, oneLiner, description, tags, and group name
- Instant filter as you type
Feature 3 — Dashboard Summary (top of page):
- Total ideas count
- Breakdown by tier (how many S, A, B, C, Unscored)
- Breakdown by status (how many Raw, Exploring, Ready to Build, etc.)
- Top 5 highest-scored ideas as a quick list with links
- Display as a row of stat cards above the idea grid
Feature 4 — Export:
- "Export All" button that downloads all ideas as a JSON file
- "Import" button that loads a JSON file and merges with existing ideas (skip duplicates by id)
FAILURE CONDITIONS — not done if:
- Search doesn't filter across all text fields
- Tags don't autocomplete from existing tags
- Groups view doesn't show ideas organized by group
- Export/Import doesn't round-trip cleanly (export then import = same data)
- Dashboard stats don't match actual idea counts
