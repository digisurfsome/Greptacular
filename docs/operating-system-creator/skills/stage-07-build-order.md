# OS Automation Skills — Stage 7: Build Order

> **What this does:** Determines what gets built first, what depends on what, and the exact sequence for construction and testing.

---

## When to Use

After Stage 6. Everything is designed. Now plan the build sequence.

## Input

All previous stages — steps, environment, error handling, dashboard.

## Process

### Step 1: Map Dependencies

For each module/file that needs to be built, identify what it depends on:

| Module | Depends On | Why |
|--------|-----------|-----|
| config.js | nothing | Foundation — env vars and constants |
| db.js | config.js | Needs env vars to connect |
| notify.js | config.js | Needs Telegram token |
| [api-client].js | config.js | Needs API keys |
| [step-1].js | db.js, [api-client].js | Needs data access + API |
| [step-2].js | db.js, [step-1].js output | Depends on step 1 completing |
| report.js | db.js | Reads from database |
| main.js (CLI) | everything | Wires it all together |

### Step 2: Define Build Phases

Group modules into build phases. Each phase should be independently testable:

| Phase | What Gets Built | Test Criteria |
|-------|----------------|---------------|
| 1 | config + db | `node -e "require('./src/db')"` succeeds |
| 2 | notify | Test Telegram message sends |
| 3 | API client(s) | Test one API call returns data |
| 4 | Core steps (1 at a time) | Test each step with real or mock data |
| 5 | Report/dashboard | Test CLI output displays correctly |
| 6 | Main CLI | Full pipeline runs end-to-end |
| 7 | Scheduling | Cron/watcher installed and verified |

### Step 3: File Structure

Define the exact file structure:

```
project-name/
├── .env
├── package.json (or requirements.txt)
├── CLAUDE.md
├── src/
│   ├── config.js          (phase 1)
│   ├── db.js              (phase 1)
│   ├── notify.js          (phase 2)
│   ├── [api-client].js    (phase 3)
│   ├── [step-1].js        (phase 4)
│   ├── [step-2].js        (phase 4)
│   ├── [step-N].js        (phase 4)
│   ├── report.js          (phase 5)
│   └── export.js          (phase 5)
├── [main-cli].js          (phase 6)
└── [scheduler-setup].sh   (phase 7)
```

### Step 4: Module Specifications

For each file, define:

| Field | What to Specify |
|-------|----------------|
| **Functions** | List every function with signature and return type |
| **Dependencies** | What it imports |
| **Constants** | Any config values it uses |
| **Rate limiting** | If it calls APIs, what delay between calls |
| **Error handling** | How it handles failures (from Stage 5) |

### Step 5: MVP Path

Identify the minimum viable path — the fewest modules needed to get value:

1. config + db (always needed)
2. The ONE step that provides the most value (from Stage 2 MVP)
3. Basic CLI to trigger it
4. notify (so you know it ran)

Everything else is enhancement after MVP works.

## Output

```json
{
  "stage_7": {
    "dependency_graph": [
      {"module": "string", "depends_on": ["string"]}
    ],
    "build_phases": [
      {
        "phase": 1,
        "modules": ["string"],
        "test_criteria": "string"
      }
    ],
    "file_structure": "string (tree diagram)",
    "module_specs": [
      {
        "file": "string",
        "functions": ["string"],
        "dependencies": ["string"],
        "phase": "number"
      }
    ],
    "mvp_path": ["string"],
    "total_files": "number",
    "estimated_build_phases": "number"
  }
}
```

## Rules

1. Build foundation first, always. Config and database before anything else.
2. Test each phase before moving to the next. Don't build 7 modules and debug them all at once.
3. The MVP path must produce usable value with the minimum number of modules. Ship that first.
