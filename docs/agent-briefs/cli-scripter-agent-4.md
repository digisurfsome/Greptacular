# Agent Brief 4: Post-Build Verification & Testing

**Phases:** Package 4 from `docs/prd-cli-scripter-v2.md`
**Scope:** Testing ONLY — no new features. Find bugs, fix them, verify everything works.
**Estimated Tokens:** ~60-80k
**Dependencies:** Packages 1, 2, and 3 must ALL be complete

---

## YOUR JOB

Packages 1, 2, and 3 have been built. Your job is to TEST everything, find bugs, and fix what you can.

First, understand what was built:
```bash
git log --oneline -30
```

Then read the full PRD at `docs/prd-cli-scripter-v2.md` — especially the "Package 4: Post-Build Verification & Testing" section.

## VERIFICATION PROTOCOL (8 test phases)

### V1: INVESTIGATION
1. Map the application: startup commands, every route/page, every user journey, key UI components
2. Document DB schema and data flows (SQLite tables for build configs, rule blocks)
3. Bug hunt via code analysis: logic errors, UI issues, data integrity risks, security concerns
4. Return a prioritized list with file paths and line numbers

### V2: STATIC VERIFICATION
```bash
cd ui && npm run lint && npm run build    # Must pass — fix if broken
ruff check .                              # Python backend
```
Check for unused imports, circular dependencies, missing package.json entries.

### V3: FUNCTIONAL VERIFICATION
- Start the dev server, verify clean startup
- Test EVERY user journey end-to-end:
  - Persistence: fill fields → reload → verify data survives
  - Rules Library: create block → add tags → check combiner binding → save → reload → verify
  - Build Library: save config → load config → delete config
  - Queue: add items → reorder → start queue
  - Gate popup: test New Build vs Edit mode, Single vs Split phase
  - Pipeline cards: verify phase visualization
  - File browser: navigate project dirs
  - Prompt bars: edit → lock → reset to default
  - Dashboard: start build → verify progress tracking
  - Terminal: verify log streaming
- Database validation: query SQLite to verify records after each data action

### V4: EDGE CASES
- Empty states: what happens with no data?
- Invalid input: submit forms with missing/malformed data
- Rapid clicks / duplicate submissions
- Network failures: what if API calls fail?

### V5: CROSS-FEATURE INTEGRATION
- Does Rules Library → Combiner → Gate → Scripts flow work end-to-end?
- Does localStorage + backend data survive page reloads?
- Do shared components (PromptBar, ClearButton) work consistently everywhere?

### V6: RESPONSIVE CHECK
- Mobile (375×812), Tablet (768×1024), Desktop (1440×900)
- Look for overflow, overlapping elements, unreadable text

### V7: FIX ISSUES
- Fix critical and high immediately, re-verify each fix
- Document medium/low for follow-up

### V8: REPORT
Output a structured Verification Report (see PRD for exact format).

## RULES

- **Fix as you go** — don't just document issues, fix them
- **Commit fixes** with clear messages: `fix(cli-scripter): [what was fixed]`
- **Zero console errors**, zero unhandled warnings
- **Never skip database validation** — UI looking right ≠ data is right
- Stay under 50% context window (100k tokens)

## WHEN DONE

Commit with: `feat(cli-scripter): Package 4 verification — [X] issues found, [Y] fixed`
Do NOT push to remote.
