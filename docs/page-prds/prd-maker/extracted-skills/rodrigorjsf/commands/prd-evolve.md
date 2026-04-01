# /prd-evolve — PRD Evolution

You are orchestrating incremental PRD evolution. Update ONLY artifacts impacted by scope changes, preserving valid existing decisions.

## Critical Rules
- All generated files must remain in English
- Do NOT regenerate unaffected artifacts
- Update every skill header with new `prd_version`
- Respond to users in their language

**Input:** `$1` — description of what changed (required)

---

## Phase 0: Read Current State

**Pre-flight Check:**
Verify `docs/prd/PRD.md` exists. If missing, error: "No PRD found. Run `/prd-new` first."

Read these files:
- `docs/prd/PRD.md` — extract version
- `docs/prd/ARCHITECTURE.md`
- `docs/prd/ER.md` (if exists)
- `.claude/skills/project-guardian/SKILL.md` — check `prd_version`
- `.claude/skills/project-architecture/SKILL.md`
- `.claude/skills/project-domain-rules/SKILL.md`
- `.claude/skills/project-compliance/SKILL.md`
- `.claude/skills/project-cicd/SKILL.md` — read `vcs` and `pipeline_file`
- Identify pipeline file: `.github/workflows/ci.yml`, `.gitlab-ci.yml`, or `bitbucket-pipelines.yml`

Warn if any skill's `prd_version` already lags behind PRD's version.

---

## Phase 1: Delta Analysis

Dispatch `requirements-analyst` agent:
```json
{
  "mode": "delta",
  "change_description": "$1",
  "current_prd_summary": "<key PRD sections>",
  "current_architecture_summary": "<stack + ADRs>"
}
```

Returns:
```json
{
  "delta_type": ["new_feature" | "removed_feature" | "new_tech" | "compliance_change" | "architecture_change"],
  "new_prd_version": "X.Y",
  "affected_artifacts": ["PRD.md §2", "project-domain-rules", ...],
  "pending_research": ["<new tech>"],
  "clarifications_needed": ["<questions>"]
}
```

If clarifications exist, ask user via `AskUserQuestion` before proceeding.

---

## Phase 2: Research & Validation (Conditional)

If `pending_research` is non-empty, dispatch `official-researcher` agents in parallel, then `research-validator` to approve findings (max 3 iterations until `approved: true` or `partially_validated`).

---

## Phase 3: Artifact Updates (Selective Parallel)

Update only affected artifacts:

- **PRD.md sections:** Dispatch `prd-writer` with sections, version, and delta
- **Architecture:** Dispatch `architecture-designer` with current architecture and new decisions (present for user approval first)
- **Stack changes:** Dispatch `stack-guide-generator` with affected layers
- **Tech/architecture changes:** Dispatch `cicd-generator` with VCS, infrastructure, and affected services
- **Skills:** Dispatch `skills-generator` with affected skills list and new version
- **Documentation:** Invoke `project-docs` skill UPDATE mode to refresh docs against new PRD

---

## Phase 4: Commit

```bash
git add docs/prd/ docs/stack/ .claude/skills/ .github/ .gitlab-ci.yml bitbucket-pipelines.yml
git commit -m "feat(prd): evolve to v<version> — $1

Updated artifacts: <list>
prd-generator-plugin: /prd-evolve"
```

---

## Completion Summary

Report (in user's language):
1. PRD version updated
2. Artifacts changed with reasons
3. Artifacts preserved unchanged
4. Any partial validation issues flagged
