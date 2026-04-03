# Protocol Tier Templates

## Pulse Check Template (Per-File)

Generate after EVERY file in the build_order. Checks must be SPECIFIC to the file.

### Pattern: Determine checks from file type and purpose

| File Type | Standard Checks | Additional Checks |
|-----------|----------------|-------------------|
| Library/utility (`.ts`, `.py`) | file exists, no syntax errors | exports expected functions by name |
| React component (`.tsx`, `.jsx`) | file exists, no syntax errors | exports named component, accepts expected props |
| Context/Provider (`.tsx`) | file exists, no syntax errors | exports Provider component, exports custom hook |
| Page component (`.tsx`, `.jsx`) | file exists, no syntax errors | exports default/named page component |
| Route config (`App.tsx`, `router.ts`) | file exists, no syntax errors | route paths defined, routes point to imports |
| API route (`/api/*.ts`) | file exists, no syntax errors | exports handler function, correct HTTP method |
| Schema/model (`.prisma`, `.sql`) | file exists, no syntax errors | defines expected tables/models |
| Config file (`.config.ts`) | file exists, no syntax errors | exports config object |
| Style file (`.css`, `.scss`) | file exists | defines expected classes/tokens |
| Test file (`.test.ts`) | file exists, no syntax errors | imports subject under test, has test cases |

### Deriving "Expected Functions/Components"

Read the mechanism blueprint (`stage_5.mechanism_blueprints`) for the mechanism this file serves. Each WALL step = a deterministic function. Each DOOR step = a constrained AI function. Each ROOM step = a creative component. The exports should map to these steps.

Example: Mechanism "auth_core" has steps:
- WALL: "Hash password" → expect `hashPassword` export
- WALL: "Verify password" → expect `verifyPassword` export
- DOOR: "Validate email format" → expect `validateEmail` export

Pulse check for `auth.ts`: `["file exists", "exports hashPassword", "exports verifyPassword", "exports validateEmail", "no syntax errors"]`

## Seam Check Template (At Connection Points)

Place ONLY where two mechanisms interface. Derive placement from `stage_4.mechanism_dependencies`.

### Pattern: Identify the connection

1. Find the dependency edge: `from_id → to_id` (from provides, to consumes)
2. Find which file in the build_order belongs to the consumer mechanism
3. The seam check goes AFTER that consumer file

### Verification content

The verification string must name BOTH sides and the specific connection:

- Import check: `"[Consumer] imports [specific function/component] from [Provider]"`
- Data flow: `"[Consumer] passes [specific data] received from [Provider]"`
- Route wiring: `"Route [path] points to [PageComponent] which imports [required context]"`

### When NO seam checks apply

A phase with a single mechanism and no cross-mechanism dependencies within it gets zero seam checks. This is correct — not an error. Pulse checks and the full checkpoint still provide coverage.

## Full Checkpoint Template (Phase Boundary Gate)

Always placed at the END of each phase. Three mandatory parts:

### Pattern Checks (git diff verification)

Always include these 5 checks:
1. `"Run git diff --name-only $PHASE_N_BASELINE to list all actually modified files"`
2. `"Compare actual modified files against this phase's files_allowed list"`
3. `"FLAG: any file modified that is NOT in files_allowed"`
4. `"FLAG: any file in build_order that was NOT created or modified"`
5. `"FLAG: any new imports from files outside this phase's sandbox"`

### Functional Checks (runtime verification)

Determine from `stage_0.tech_stack`:

| Stack | Compile Check | Test Check | Render Check |
|-------|--------------|------------|--------------|
| Node/React | `npm run build` | `npm run test` (if tests exist) | Navigate to new routes |
| Python/Django | `python manage.py check` | `python manage.py test` | Hit new endpoints |
| Rust | `cargo build` | `cargo test` | Run binary with args |
| Flutter | `flutter analyze` | `flutter test` | Launch on emulator |
| Go | `go build ./...` | `go test ./...` | Run binary |

Add phase-specific checks: name the exact pages/routes/features this phase adds.

### Gate Condition

Always this format (customize the specifics):
`"ALL pattern_checks pass (zero unauthorized file modifications) AND ALL functional_checks pass ([compile command] succeeds, [specific pages] render, existing features still work). If ANY check fails, fix before Phase N+1 starts."`

The gate is BINARY: pass or fail. No "proceed with warnings" at the gate level — that's what violation severity handles.
