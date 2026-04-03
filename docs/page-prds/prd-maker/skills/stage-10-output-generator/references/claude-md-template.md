# CLAUDE.md Template

> Quick-reference guardrails file. Lives in repo root FOREVER.
> Read by EVERY agent interaction — even "fix this button color."
> MUST be under 500 lines. Tight, fast, actionable.
> Points to BUILD_RULES.md for deeper protocols.

---

## Template

```markdown
# {PRODUCT_NAME}

> {One-line product description from stage_3.concept_and_context}

## Architecture Principles

{Distilled from stage_5.build_rules_applied. 10-15 rules max.}

- Components do ONE thing. If it does two things, split it.
- State lives at the lowest possible level. Don't hoist unless required.
- No file over 300 lines. Split at 250.
- Imports flow downward. Never circular.
- UI components don't contain business logic.
- Every function has a single responsibility.
- Error handling at boundaries, not everywhere.
- {Stack-specific: e.g., "All Supabase queries go through src/lib/db.ts"}
- {Stack-specific: e.g., "Auth state managed exclusively in AuthContext"}
- {Stack-specific: e.g., "Server actions in app/actions/, never in components"}

## Modification Rules

- Before editing ANY file, read it completely first.
- Don't refactor code you didn't write unless explicitly asked.
- Don't add features that weren't requested.
- Don't "improve" working code while fixing a bug.
- Keep existing patterns. Match the style that's there.
- When in doubt, check how similar code is written elsewhere in the project.

## Testing Protocol

After ANY change, verify:

```bash
# 1. Does it compile?
{build_command}

# 2. Does it lint?
{lint_command}

# 3. Do tests pass? (if tests exist)
{test_command}

# 4. Do existing features still work? (manual check for UI changes)
```

Don't delete tests. Don't skip tests. Don't modify tests to make them pass.

## Tech Stack

{From stage_0.tech_stack — concise reference.}

| Layer | Technology |
|-------|-----------|
| Framework | {framework} |
| Language | {language} |
| Database | {database} |
| Auth | {auth_provider} |
| Hosting | {hosting} |
| Styling | {styling} |

## File Structure

{Generated from stage_6.sub_6a (page arrangement) + stage_7.phases (file sandboxes).}

```
{project_root}/
├── src/
│   ├── components/     # UI components ({component_list})
│   ├── lib/            # Shared utilities ({utility_list})
│   ├── contexts/       # State management ({context_list})
│   ├── pages/          # Page components ({page_list})
│   └── types/          # TypeScript types
├── {api_directory}/    # API routes / server functions
├── {db_directory}/     # Database schema / migrations
├── CLAUDE.md           # This file (guardrails)
├── BUILD_RULES.md      # Detailed protocols
└── {config_files}      # Config (DO NOT MODIFY without reason)
```

## Key Files (Don't Break These)

{Critical files that should rarely be modified. From stage_7 sandbox forbidden lists.}

- `{auth_file}` — Authentication setup. Modify ONLY if auth feature is explicitly requested.
- `{db_config_file}` — Database connection. Almost never needs changes.
- `{env_file}` — Environment variables. NEVER commit secrets.
- `{config_files}` — Build config. Change only if build is broken.

## When Debugging

Follow the debugging protocol in BUILD_RULES.md Section "Debugging Protocol."

1. Read the error message completely
2. Find the actual file and line causing the error
3. Trace the data flow from source to error
4. Fix the root cause, not the symptom
5. Verify the fix doesn't break anything else

Do NOT guess at fixes. Trace the actual error path first.

## When Adding Features

Follow the feature addition protocol in BUILD_RULES.md Section "Feature Addition Protocol."

1. Read all connected files before modifying any of them
2. Check if a similar feature already exists (follow its pattern)
3. Create new files for new features — don't bloat existing files
4. Update imports and exports
5. Run the full testing protocol

## When Reviewing Code

Check BUILD_RULES.md Section "Testing & Verification" for the full review checklist.

Quick checks:
- Does it compile and lint?
- Does it match existing patterns?
- Are there any hardcoded values that should be config?
- Is error handling present at boundaries?
- Are there any security concerns (exposed secrets, missing auth checks)?
```

---

## Rendering Rules

1. Replace `{PRODUCT_NAME}` with `stage_3.concept_and_context.name`
2. Replace `{build_command}`, `{lint_command}`, `{test_command}` from `stage_0.tech_stack`
3. Generate "Architecture Principles" from `stage_5.build_rules_applied` — pick the 10-15 most impactful rules, adapted to the tech stack
4. Generate "File Structure" tree from `stage_6.sub_6a` page arrangement and `stage_7.phases` file sandbox declarations — show the actual project structure
5. Generate "Key Files" from the union of all phases' `files_forbidden` lists
6. Keep all BUILD_RULES.md section references accurate — section names must match what Step 5 generates
7. Martin's rules are EMBEDDED as architecture principles — NEVER reference "Martin" by name
8. Total output MUST be under 500 lines. If approaching the limit, remove examples rather than removing rules
9. Every bash command must be copy-paste ready (no placeholders in the final output)
