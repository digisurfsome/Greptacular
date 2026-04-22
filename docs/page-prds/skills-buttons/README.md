# Skills Buttons — AutoForge UI Feature PRD

> **Status:** Draft — owner + agent collaboration pending
> **Owner:** lober (digisurfsome)
> **Created:** 2026-04-22

---

## Problem

Claude skills are powerful (archon, archon-dev, pdf, docx, ~20 others), but invoking them requires either:
- **Claude Code:** typing trigger phrases that match a skill's description (invisible, no feedback).
- **Claude.ai web/desktop:** typing `/skill-name` slash commands or setting up Projects.

In **AutoForge** (which the owner built himself), there's no skill-activation UI at all. The owner:
- Can't remember 20+ slash command names
- Doesn't get visual feedback when a skill auto-activates
- Wants control over which skills are on for a given task
- Works almost exclusively in AutoForge, so this is the main interface that needs it

## Goal

Add a **Skills panel** to the AutoForge workspace UI that:
1. Lists every installed skill (reads from `~/.claude/skills/` on disk)
2. Renders each as a clickable button/chip
3. Click = toggle that skill on/off for the current session
4. When ON, skill content is injected into the agent's system prompt
5. When skill auto-activates from a message trigger, shows visual indicator ("Archon skill activated")

## Non-goals (out of scope for v1)

- Skill creation/editing from UI (that's Claude's skill-creator tool's job)
- Skill marketplace or discovery
- Per-page preferences (later)
- Usage analytics (later)

## User stories

**US1:** As the owner, when I start a workspace session, I see a panel showing all installed skills as buttons. I can click any to toggle on.

**US2:** As the owner, when I type a message that matches a skill's trigger phrase (e.g. "use archon to fix issue"), the corresponding button lights up automatically showing "auto-activated."

**US3:** As the owner, I can hover a skill button to see a short description of what it does (pulled from the skill's `SKILL.md` description field).

**US4:** As the owner, I can toggle a skill OFF mid-session if it's adding noise to the context.

## Size estimate

**Small version** (recommended v1): 4/10 difficulty, ~10-15 minutes of agent time.
- List + toggle + context injection. No hover preview, no auto-activation indicator.

**Medium version** (v2): 6/10 difficulty, ~25 minutes.
- Small + hover previews + auto-activation visual indicator + persist per-page preferences.

**Large version** (v3): 8/10 difficulty, 1+ hour.
- Medium + skill creation/edit from UI + metrics.

## Architecture sketch

### Backend (new)
- `server/routers/skills.py` — new router:
  - `GET /api/skills` — returns list of installed skills with `{name, description, triggers, path}` per skill, read from `~/.claude/skills/*/SKILL.md` frontmatter.
  - `POST /api/sessions/{id}/skills` — enable a skill for a session (stores in session state).
  - `DELETE /api/sessions/{id}/skills/{name}` — disable a skill.

### Frontend (new)
- `ui/src/components/workspace/SkillsPanel.tsx` — renders the button/chip row.
- `ui/src/hooks/useSkills.ts` — TanStack Query hook that fetches skill list and toggles.
- Added to `ui/src/pages/WorkspacePage.tsx` as a collapsible panel in the sidebar.

### SDK injection
- When `POST /api/sessions/{id}/messages` fires, server includes enabled skills' `SKILL.md` contents in the system prompt (or uses the SDK's built-in skill registration if available).
- Verify current SDK supports dynamic skill list per session — if not, use system-prompt injection as fallback.

## Files that will be touched (v1 Small)

**New files:**
- `server/routers/skills.py`
- `ui/src/components/workspace/SkillsPanel.tsx`
- `ui/src/hooks/useSkills.ts`

**Modified files (minimal):**
- `server/main.py` — register new router
- `ui/src/pages/WorkspacePage.tsx` — mount SkillsPanel in sidebar
- `ui/src/lib/api.ts` — add skill endpoints
- `ui/src/lib/types.ts` — add Skill type

## Open questions

1. **SDK skill support:** does our current Claude Agent SDK version support per-session skills via an API, or do we need to inject into system prompt manually? Verify before implementation.
2. **Skill discovery scope:** only `~/.claude/skills/` (global), or also project-local `.claude/skills/`? v1 recommendation: global only.
3. **Session persistence:** if session restarts, do enabled skills persist? v1 recommendation: persist via DB column on sessions table.
4. **UI placement:** sidebar panel (visible always) or floating toolbar (hidden until expanded)? v1 recommendation: sidebar panel.

## Success criteria

- Owner can click a button to turn on the Archon skill and feel the difference in agent behavior on the next message.
- Owner never has to remember a slash command again for skill activation.
- At least 5 skills from `~/.claude/skills/` render correctly in the panel.
- Toggling a skill off actually removes it from the agent's context (verify via debug endpoint or observed behavior).

## Rollout plan

1. **Phase 1:** build v1 Small in a worktree branch, test with archon + archon-dev + pdf skills.
2. **Phase 2:** ship behind a feature flag on main.
3. **Phase 3:** expand to medium version once v1 is stable.

## Next step for this PRD

Owner to review + provide feedback. Then either:
- Delegate to a Sonnet agent to implement v1 Small
- Continue refining scope with Opus in a follow-up session

---

*This PRD lives at `docs/page-prds/skills-buttons/README.md` per the "Where Docs Go" rule in `CLAUDE.md`.*
