---
description: "Compound Engineering — Existing Code Intake: Analyze an existing codebase for improvements"
argument-hint: <path to codebase root, or describe what you want analyzed>
---

# Compound Engineering: Existing Code Analysis Intake

**Artifacts Directory**: $ARTIFACTS_DIR
**User Input**: $ARGUMENTS

## Context Loading

Before executing, check if `$ARTIFACTS_DIR/context-packet/` exists. Read any prior outputs if present.

---

## Mode Declaration

You are operating in **Existing Code Analysis Mode**. This means: the user has a codebase they want analyzed, improved, or refactored. There is no specific new feature request — the goal is to assess and improve what already exists.

State this clearly:
> "Running in Existing Code Analysis mode. I'll scan your codebase, identify what it does and how it's structured, then ask what areas you want to focus on."

---

## Process

### Step 1: Locate the Codebase

Check `$ARGUMENTS` for a path. If provided, use it. If not, check the current working directory for common project indicators (package.json, requirements.txt, Cargo.toml, go.mod, etc.).

If no codebase can be found, ask:
> "I need the path to your project root. Where is the codebase located?"

### Step 2: Scan the Codebase

Perform a structured scan. Read these files/directories IN THIS ORDER (stop if a category doesn't apply):

**Project Identity** (read first):
- `package.json` or `requirements.txt` or `Cargo.toml` or `go.mod` or `pyproject.toml`
- `README.md` or `README` (first 200 lines only)
- `.env.example` or `.env.sample` (NOT `.env` — never read actual env files)

**Architecture Indicators** (read next):
- List the top-level directory structure (1 level deep)
- Count total files by extension (e.g., 45 .ts files, 12 .py files)
- Identify the main entry point (e.g., `src/index.ts`, `main.py`, `cmd/main.go`)

**Key Source Files** (read selectively):
- The main entry point file (first 100 lines)
- The main router/routes file if it exists
- Any config/settings file
- Up to 3 representative source files from the most populated directory

**Infrastructure** (note existence only):
- Docker files (Dockerfile, docker-compose.yml)
- CI/CD configs (.github/workflows/, .gitlab-ci.yml)
- Test directories and test runner config

### Step 3: Produce Codebase Summary

Compile findings into a structured assessment:

```
## Codebase Summary

**What the app does**: [1-2 sentences based on README + code scan]
**Tech Stack**: [language, framework, database, notable libraries]
**Approximate Size**: [file count, estimated lines of code]
**Project Maturity**: [prototype / early development / production-ready / legacy]

### Architecture Pattern
[monolith / microservice / serverless / static site / etc.]
[MVC / clean architecture / ad-hoc / etc.]

### Code Quality Signals
- [ ] Has tests: [yes/no, approximate coverage]
- [ ] Has linting config: [yes/no, tool name]
- [ ] Has type checking: [yes/no, strict mode]
- [ ] Has CI/CD: [yes/no, platform]
- [ ] Has documentation: [yes/no, quality]
- [ ] Has dependency lock file: [yes/no]

### Obvious Issues (from scan)
1. [issue spotted during scan]
2. [issue spotted during scan]
...

### Strengths
1. [positive pattern noticed]
2. [positive pattern noticed]
...
```

### Step 4: Ask User Focus Questions

Present the summary, then ask:

> "Based on my scan, here's what I found. Now I need to know what YOU want to focus on:"
>
> 1. "What areas concern you most about this codebase?"
> 2. "What's your goal — improve code quality, add test coverage, refactor architecture, fix specific bugs, or something else?"
> 3. "Are there any parts of the code I should NOT touch?"

### Step 5: Write Context Packet

Create `$ARTIFACTS_DIR/context-packet/context-packet.json`:

```json
{
  "mode": "existing-code",
  "app_description": "what the app does based on scan",
  "tech_stack": {
    "language": "primary language",
    "frontend": "framework or null",
    "backend": "framework or null",
    "database": "type or null",
    "notable_libraries": ["lib1", "lib2"]
  },
  "codebase_summary": {
    "total_files": 0,
    "estimated_loc": 0,
    "maturity": "prototype | early | production | legacy",
    "architecture": "pattern description",
    "has_tests": false,
    "has_linting": false,
    "has_types": false,
    "has_ci": false
  },
  "key_files_found": [
    {"path": "relative/path", "purpose": "what it does"}
  ],
  "obvious_issues": ["issue 1", "issue 2"],
  "strengths": ["strength 1", "strength 2"],
  "user_concerns": ["concern from user"],
  "improvement_goals": ["goal from user"],
  "do_not_touch": ["paths or areas user wants preserved"],
  "codebase_root": "absolute path to project root",
  "captured_at": "ISO 8601 timestamp"
}
```

Ensure the directory exists before writing. Create `$ARTIFACTS_DIR/context-packet/` if needed.

### Step 6: Validate and Signal

Validate:
1. `app_description` is non-empty
2. `tech_stack.language` is identified
3. `codebase_summary` has real data from the scan
4. `key_files_found` has at least 1 entry
5. `improvement_goals` has at least 1 entry

If validation passes, emit:
<promise>INTAKE_COMPLETE</promise>

If the codebase could not be found or scanned, report the error clearly and still emit the promise with whatever partial data was captured.
