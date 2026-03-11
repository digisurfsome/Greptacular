# Build Planner — Feature Backlog

Everything that's NOT yet in the Build Planner, organized by priority.

---

## What's Currently Built (v1)

- [x] Project basics (name, description)
- [x] Boilerplate picker (Web/Mobile/Web+Mobile/Scratch)
- [x] Tech summary display per boilerplate
- [x] GitHub repo creation (checkbox + name + token + create)
- [x] Rule blocks with AI-powered combination
- [x] Feature list with S/M/L sizing
- [x] Dependencies (text area)
- [x] Build settings (model, turns, phase transitions, error handling, git commits, phase count)
- [x] Phase assignments (text area)
- [x] Prompt generation (PRD, Phase-Split, Build Scripts)
- [x] "Run with AI" on each prompt output
- [x] Copy to clipboard on outputs

---

## HIGH PRIORITY — Should Build Next

### 1. Dependency Graph Visualization
- Interactive graph after PRD generation showing feature relationships
- Drag to reorder, add edges visually
- Auto-detect parallel work opportunities
- Phase boundary visualization
- Feed graph data back into phase-split prompt
- **Status: PRD written — ready for AutoForge**

### 2. Style Set / Design System Picker
- Pick a design style (neobrutalism, glassmorphism, minimal, etc.)
- Color palette selection or generation
- Font pairing suggestions
- Inject style rules into the build prompts automatically
- Connect to the existing Style Profiles system already in AutoForge

### 3. Save & Load Plans
- Save build plans to localStorage or server
- Load previous plans to continue editing
- Export/import as JSON
- Plan history with timestamps

### 4. One-Click "Start Build" Button
- Take the completed plan and create an actual AutoForge project
- Pre-populate the app spec, features, and dependencies
- Skip the New Project wizard entirely
- Go straight from Build Planner → running agent

### 5. Template Library / Preset Plans
- Pre-made build plans for common app types (SaaS, e-commerce, blog, dashboard)
- Community-shared templates
- "Start from template" option that pre-fills everything

---

## MEDIUM PRIORITY — Quality of Life

### 6. AI Feature Generator
- Describe your app in one sentence
- AI generates a full feature list with sizes, categories, and dependencies
- User reviews and edits before accepting
- "Suggest more features" button

### 7. Feature Dependencies (Visual)
- Replace the text area with a proper dependency picker
- Dropdown per feature to select "depends on" features
- Visual lines showing dependency chains
- Cycle detection warning

### 8. Cost & Time Estimator
- Estimate tokens/cost based on features, sizes, and model
- Estimate number of sessions needed
- Show per-phase breakdown
- Compare Sonnet vs Opus cost

### 9. Multi-Model Strategy
- Assign different models per phase (Haiku for setup, Sonnet for features, Opus for complex)
- Smart defaults based on feature complexity
- Cost optimization mode

### 10. Phase Auto-Assignment
- AI-powered phase assignment based on dependencies and sizes
- Topological sort with parallel grouping
- Drag-and-drop phase reordering
- Balance phase workloads automatically

### 11. Build Rules Library
- Save reusable rule blocks (e.g., "TypeScript strict", "Tailwind only", "No class components")
- Categorized rule templates
- Import rules from CLAUDE.md files
- Share rules across projects

### 12. Live Preview of Generated Prompts
- Side-by-side view: settings on left, live prompt preview on right
- See prompt update in real-time as you change settings
- Syntax highlighting for the prompt text
- Token count display

### 13. Boilerplate Preview
- Show README / screenshot of each boilerplate before selecting
- List of pre-built features with checkboxes (so user knows what's included)
- "View on GitHub" link
- Tech stack diagram

---

## LOWER PRIORITY — Future Ideas

### 14. Collaborative Planning
- Share build plan via link
- Multiple people editing simultaneously
- Comments on features/phases
- Approval workflow before starting build

### 15. Build History & Analytics
- Track all builds started from the planner
- Success/failure rates per template
- Average build time per app type
- Feature completion heatmap

### 16. Git Integration (Beyond Repo Creation)
- Branch strategy planner (main, dev, feature branches)
- PR template generation
- CI/CD pipeline config generation (GitHub Actions, Netlify, Vercel)
- Auto-create .gitignore based on tech stack

### 17. Environment Setup Generator
- Generate .env.example with all needed variables
- Docker/docker-compose generation
- Package.json scaffolding
- Database schema planning

### 18. API Design Tool
- Visual API endpoint designer
- Generate OpenAPI/Swagger spec from features
- Auto-detect needed endpoints from feature descriptions
- REST vs GraphQL decision helper

### 19. Database Schema Planner
- Visual table/collection designer
- Relationship mapping
- Migration script generation
- Seed data templates

### 20. Testing Strategy Planner
- Define testing approach per feature (unit, integration, e2e)
- Generate test file structure
- Testing framework selection
- Coverage targets per phase

### 21. Deployment Planner
- Choose hosting (Netlify, Vercel, AWS, GCP, etc.)
- Domain setup checklist
- SSL/DNS configuration guide
- Environment-specific settings (dev/staging/prod)

### 22. Prompt Chain Builder (Advanced)
- Visual flow builder for multi-step AI prompts
- Connect prompts in a pipeline
- Conditional branching based on AI output
- Test prompts with sample data before full build

### 23. Mobile-Specific Planning
- Platform selection (iOS only, Android only, both)
- App store submission checklist
- Push notification planning
- Deep linking strategy

### 24. Internationalization Planner
- Language selection
- i18n strategy (key-based, auto-translate)
- RTL support planning
- Content management for translations

### 25. Accessibility Planner
- WCAG compliance level target
- Screen reader testing plan
- Keyboard navigation requirements
- Color contrast verification

---

## User's Original Ideas (from conversations)

- Boilerplate picker in the dropdown ✅ (done)
- GitHub repo creation ✅ (done)
- Dependency graph in the planner (PRD written)
- Phase ordering from dependency analysis
- Parallel section detection for faster builds
- Style Set integration with the planner
- One-page tool feel (everything on one screen)

---

## Notes

- The Build Planner lives at `/#/build-planner` (`ui/src/pages/BuildPlannerPage.tsx`)
- It's a standalone page, separate from the New Project wizard
- All prompt generation is client-side (no server needed except for "Run with AI")
- The `/api/build-planner/generate` endpoint handles AI generation
