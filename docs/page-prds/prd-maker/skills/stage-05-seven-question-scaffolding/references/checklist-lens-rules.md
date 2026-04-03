# Martin's Checklist Rules as Scaffolding Lens

These are the Martin's Structural Checklist rules most relevant to Stage 5 scaffolding decisions. These rules SHAPE how you answer the 7 questions — they are the building code the architect follows WHILE designing.

## How to Use This Document

When scaffolding a mechanism's steps, consult these rules to inform your answers:
- **When defining WALLs:** Rules ensure walls are clean (single responsibility, no state leakage)
- **When setting phase boundaries:** Rules enforce isolation between phases
- **When writing verification:** Rules define what "correct" looks like structurally

Record every rule ID that influenced a scaffolding decision in `build_rules_applied`.

## Key Rules by Scaffolding Decision

### Step Granularity (Single Responsibility)

| Rule ID | Category | Rule | Scaffolding Impact |
|---------|----------|------|-------------------|
| FileStructure.1 | File Structure | One component per file | Each UI step maps to one component file |
| FileStructure.2 | File Structure | Feature folders for grouping | Steps in the same mechanism phase share a feature folder |
| FileStructure.3 | File Structure | Centralized type definitions | Data types are WALLs — defined once, referenced everywhere |

### Data Access (Service Layer Enforcement)

| Rule ID | Category | Rule | Scaffolding Impact |
|---------|----------|------|-------------------|
| FileStructure.8 | File Structure | Services folder for data access | Any step that touches DB → WALL with service layer access pattern |
| DataService.1 | Data Service Layer | All CRUD via service functions | Direct DB imports in components = violation. Service layer = WALL. |
| DataService.2 | Data Service Layer | Typed return values | Service functions return typed data → verification is type-checkable |
| DataService.3 | Data Service Layer | Error handling in service layer | Errors caught in service, not in components → clean phase boundaries |

### State Management (Phase Isolation)

| Rule ID | Category | Rule | Scaffolding Impact |
|---------|----------|------|-------------------|
| Stack.5 | Stack | Built-in state management | State flows through framework primitives → WALL (deterministic) |
| Stack.6 | Stack | No external state libraries | State complexity stays bounded → fewer DOORs needed |
| Config.1 | Configuration | Single config source | Config is a WALL — one place, one format, no variation |

### Authentication (Heavy WALL Zone)

| Rule ID | Category | Rule | Scaffolding Impact |
|---------|----------|------|-------------------|
| Auth.1 | Authentication | Auth provider pattern | Auth steps are WALLs — provider handles, code enforces |
| Auth.2 | Authentication | Auth context wraps app | Auth state check = WALL precondition for protected routes |
| Auth.3 | Authentication | Redirect on auth failure | Auth failure routing = WALL (code decides, not AI) |
| RouteGuard.1 | Route Guards | Protected route component | Route protection = WALL entry condition for every protected phase |

### Validation (Boundary Enforcement)

| Rule ID | Category | Rule | Scaffolding Impact |
|---------|----------|------|-------------------|
| DataAPI.1 | Data/API Patterns | Input validation before writes | Every data-write step must have a validation WALL before it |
| DataAPI.2 | Data/API Patterns | Sanitize user input | Input handling = WALL (deterministic sanitization) |
| ErrorHandling.1 | Error Handling | Consistent error format | Error display = DOOR (text varies) with WALL format constraint |
| ErrorHandling.2 | Error Handling | User-facing error messages | Never expose raw errors → DOOR with constraint |

### UI Patterns (Component Classification)

| Rule ID | Category | Rule | Scaffolding Impact |
|---------|----------|------|-------------------|
| UX.1 | UX Standards | Loading states for async | Loading indicator = WALL (always present during async) |
| UX.2 | UX Standards | Empty states with guidance | Empty state = DOOR (text varies, must guide user) |
| UX.3 | UX Standards | Confirmation for destructive | Confirm dialog = WALL (must appear before delete/destroy) |
| UX.6 | UX Standards | Form validation feedback | Inline validation = WALL (immediate, specific feedback) |

### Separation of Concerns

| Rule ID | Category | Rule | Scaffolding Impact |
|---------|----------|------|-------------------|
| FileStructure.4 | File Structure | Custom hooks per feature | Logic steps separate from UI steps → clean phase splits |
| FileStructure.5 | File Structure | Required directory structure | File placement = WALL (deterministic by convention) |
| DataStructure.1 | Data Structure | Typed interfaces | Schema definition = WALL (code enforces shape) |

## Rule Citation Format

When recording rules in `build_rules_applied`, use the format: `"Category.RuleNumber"` — for example:
- `"FileStructure.8"` — Services folder for data access
- `"DataService.1"` — All CRUD via service functions
- `"Auth.1"` — Auth provider pattern
- `"UX.3"` — Confirmation for destructive actions
- `"ErrorHandling.1"` — Consistent error format

## Most Common Rules Per Mechanism Type

| Mechanism Type | Commonly Applied Rules |
|---------------|----------------------|
| Authentication | Auth.1, Auth.2, Auth.3, RouteGuard.1, DataAPI.1 |
| Data CRUD | DataService.1, DataService.2, FileStructure.8, DataAPI.1, DataAPI.2 |
| UI Forms | UX.6, ErrorHandling.1, ErrorHandling.2, DataStructure.1 |
| Navigation | RouteGuard.1, Auth.2, FileStructure.5 |
| Dashboard/Display | UX.1, UX.2, FileStructure.4, DataService.1 |
| User Settings | UX.3, DataService.1, DataAPI.1, ErrorHandling.2 |
| Search/Filter | DataService.1, UX.1, FileStructure.4 |
| File Upload | DataAPI.2, UX.1, ErrorHandling.1, DataService.1 |
