# File Sandbox Template — Phase Sequencing Reference

## The Three Tiers

Every phase MUST have all three tiers defined. No exceptions.

### Tier 1: FILES ALLOWED

Exact file paths this phase can create or modify. Be explicit — list every file path with its operation status.

```
files_allowed:
  - src/lib/auth.ts              (NEW — create from scratch)
  - src/contexts/AuthContext.tsx  (NEW — create from scratch)
  - src/pages/SignIn.tsx          (NEW — create from scratch)
  - src/pages/SignUp.tsx          (NEW — create from scratch)
  - src/App.tsx                   (MODIFY — add routes only)
  - supabase/migrations/00001_auth.sql (NEW — create migration)
```

**Rules:**
- Every file in `build_order` MUST appear here
- Mark each as NEW (create) or MODIFY (change existing)
- MODIFY files should specify WHAT is allowed (e.g., "add routes only", "add export")
- Keep the list precise — "src/components/*" is NOT acceptable, list each file

### Tier 2: FILES READ-ONLY

Files the phase can reference for patterns but MUST NOT modify. These are typically files from prior phases or global config.

```
files_read_only:
  - CLAUDE.md                     (global — always read-only)
  - package.json                  (reference for dependencies)
  - tsconfig.json                 (reference for paths)
  - src/lib/supabase.ts           (reference for DB pattern)
  - src/components/ui/Button.tsx  (reference for component pattern)
```

**Rules:**
- Always include CLAUDE.md
- Include files from prior phases that this phase needs to reference
- Include configuration files the agent might need to check
- A file can be READ-ONLY in one phase and ALLOWED in another (the phase that creates it has ALLOWED, subsequent phases have READ-ONLY)

### Tier 3: FILES FORBIDDEN

Everything not in ALLOWED or READ-ONLY. For critical files, list them explicitly even though "everything else" covers them.

```
files_forbidden:
  - .env                          (NEVER — contains secrets)
  - .env.local                    (NEVER — contains secrets)
  - supabase/migrations/00000_*.sql (existing migrations — never modify)
  - src/lib/credits.ts            (owned by Phase 2 — do not touch)
  - src/pages/Dashboard.tsx       (owned by Phase 2 — do not touch)
  - ANY files in node_modules/
  - ANY files in .git/
```

**Rules:**
- Explicitly list `.env` and `.env.local` (critical, never touch)
- Explicitly list existing migration files
- Explicitly list files owned by other phases
- Include `node_modules/` and `.git/`
- Use "ANY files not listed above" as the catch-all at the end

## DO NOT CHANGE Protections

Some files must NEVER be modified by ANY phase. These appear in every phase's `do_not_change` array AND in every phase's `files_forbidden`:

```
do_not_change (global):
  - CLAUDE.md
  - .env
  - .env.local
  - BUILD_RULES.md
  - package-lock.json (modify only via npm install, not directly)
  - Any existing migration files (those with numbers lower than this phase's migrations)
```

## Enforcement Model

The sandbox is an **alarm system, not a fence**. The agent CAN touch any file during the build. After it finishes:

1. `git diff --name-only $SNAPSHOT` captures every file created, modified, or deleted
2. The diff is compared against the phase's `files_allowed` list
3. Unauthorized changes trigger violation handling:
   - **LOW**: Touched shared types/config → log and proceed
   - **MEDIUM**: Modified another phase's file → review and decide (additive = proceed with caution, destructive = revert)
   - **HIGH**: Modified `.env`, deleted files, touched forbidden core → halt and revert

## Complete Phase Sandbox Example

```json
{
  "phase_number": 2,
  "name": "Dashboard & Analytics",
  "files_allowed": [
    "src/lib/dashboard.ts",
    "src/lib/analytics.ts",
    "src/contexts/DashboardContext.tsx",
    "src/pages/Dashboard.tsx",
    "src/pages/Analytics.tsx",
    "src/components/charts/BarChart.tsx",
    "src/components/charts/LineChart.tsx",
    "src/App.tsx"
  ],
  "files_read_only": [
    "CLAUDE.md",
    "package.json",
    "tsconfig.json",
    "src/lib/auth.ts",
    "src/contexts/AuthContext.tsx",
    "src/lib/supabase.ts"
  ],
  "files_forbidden": [
    ".env",
    ".env.local",
    "supabase/migrations/00001_auth.sql",
    "src/pages/SignIn.tsx",
    "src/pages/SignUp.tsx",
    "src/contexts/AuthContext.tsx",
    "node_modules/**",
    ".git/**"
  ],
  "do_not_change": [
    "CLAUDE.md",
    ".env",
    ".env.local",
    "BUILD_RULES.md"
  ]
}
```
