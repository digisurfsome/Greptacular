# Platform Wrappers — Execution Instructions Per Platform

> Phase file CONTENT is identical across all platforms.
> Only the execution method and wrapper instructions change.
> This file provides per-platform instructions included in README.md.

---

## Platform Matrix

| Platform | Enum Value | Terminal? | Automation | Agent Command |
|----------|-----------|-----------|-----------|---------------|
| Claude Code CLI | `claude_cli` | Yes | Full | `claude --print "$(cat phase-N.md)"` |
| Claude Code Web | `claude_web` | No | Manual | Copy-paste phase-N.md content |
| Codex CLI | `codex_cli` | Yes | Full | `codex run --prompt-file phase-N.md` |
| Gemini CLI | `gemini_cli` | Yes | Full | `gemini code --prompt-file phase-N.md` |
| Cursor | `cursor` | Yes | Semi | Paste into Cursor terminal/chat |
| Windsurf | `windsurf` | Yes | Semi | Paste into Windsurf terminal/chat |
| Bolt | `bolt` | No | Manual | Paste into Bolt chat interface |
| Lovable | `lovable` | No | Manual | Paste into Lovable chat interface |
| Generic | `generic` | Varies | Manual | Paste into any coding agent |

---

## Per-Platform README Instructions

### claude_cli

```markdown
## How to Build

### Automated (Recommended)
```bash
chmod +x build.sh
bash build.sh
```

The build script will:
1. Take a git snapshot before each phase
2. Run pre-build validation (build + lint)
3. Execute the phase via Claude Code CLI
4. Run post-build validation
5. Check for forbidden file modifications
6. Commit and continue to the next phase
7. Auto-retry failed phases (2 attempts max)

### Manual (If build.sh fails)
If the script stops at Phase N:
1. Open `phases/phase-N.md`
2. Run: `claude --print "$(cat phases/phase-N.md)"`
3. After completion, run build + lint manually
4. Continue with Phase N+1

### Hybrid
Run `build.sh`. If it crashes at Phase 3, open `phases/phase-3.md`
and pick up manually from there. Each phase is self-contained.
```

---

### claude_web

```markdown
## How to Build

1. Open Claude Code in your browser
2. Open `phases/phase-1.md`
3. Copy the ENTIRE contents and paste into the chat
4. Wait for the agent to complete Phase 1
5. Verify: run `{build_command}` and `{lint_command}` in your terminal
6. If both pass, proceed to Phase 2
7. Repeat for each phase in order

**Important**: Each phase is self-contained. The agent does not need
context from previous phases — each phase file includes everything needed.

**Between phases**: Wait 2-3 minutes for rate limits to reset.
```

---

### codex_cli

```markdown
## How to Build

### Automated
```bash
chmod +x build.sh
bash build.sh
```

### Manual
```bash
codex run --prompt-file phases/phase-1.md
{build_command} && {lint_command}
# If passes, continue:
codex run --prompt-file phases/phase-2.md
{build_command} && {lint_command}
# ... repeat for all phases
```
```

---

### gemini_cli

```markdown
## How to Build

### Automated
```bash
chmod +x build.sh
bash build.sh
```

### Manual
```bash
gemini code --prompt-file phases/phase-1.md
{build_command} && {lint_command}
# If passes, continue:
gemini code --prompt-file phases/phase-2.md
{build_command} && {lint_command}
# ... repeat for all phases
```
```

---

### cursor

```markdown
## How to Build

1. Open the project in Cursor
2. Open `phases/phase-1.md`
3. Copy the contents and paste into Cursor's AI chat (Cmd+L / Ctrl+L)
4. Let the agent implement Phase 1
5. Open terminal (Ctrl+`) and verify:
   ```bash
   {build_command} && {lint_command}
   ```
6. If both pass, proceed to Phase 2
7. Repeat for each phase

**Tip**: Use Cursor's terminal to run verification commands between phases.
```

---

### windsurf

```markdown
## How to Build

1. Open the project in Windsurf
2. Open `phases/phase-1.md`
3. Copy the contents and paste into Windsurf's Cascade chat
4. Let the agent implement Phase 1
5. Open terminal and verify:
   ```bash
   {build_command} && {lint_command}
   ```
6. If both pass, proceed to Phase 2
7. Repeat for each phase
```

---

### bolt

```markdown
## How to Build

Bolt does not have terminal access. Follow these steps:

1. Open Bolt and start a new project
2. Open `phases/phase-1.md` in a text editor
3. Copy the ENTIRE contents and paste into Bolt's chat
4. Wait for the agent to complete Phase 1
5. Download the project and verify locally:
   ```bash
   {build_command} && {lint_command}
   ```
6. If verification passes, go back to Bolt
7. Open `phases/phase-2.md` and paste into chat
8. Repeat for each phase

**Important**: Since Bolt has no terminal, you must download and
verify locally between phases. Do NOT skip verification.
```

---

### lovable

```markdown
## How to Build

Lovable does not have terminal access. Follow these steps:

1. Open Lovable and start a new project
2. Open `phases/phase-1.md` in a text editor
3. Copy the ENTIRE contents and paste into Lovable's prompt
4. Wait for the agent to complete Phase 1
5. Use Lovable's preview to visually verify the output
6. Export to GitHub and verify locally:
   ```bash
   git clone {repo_url}
   cd {project_name}
   {build_command} && {lint_command}
   ```
7. If verification passes, continue to Phase 2
8. Repeat for each phase

**Important**: Export and verify locally between phases.
```

---

### generic

```markdown
## How to Build

This build package works with any coding agent.

### Steps
1. Open `phases/phase-1.md` in a text editor
2. Copy the ENTIRE contents
3. Paste into your coding agent of choice
4. Wait for completion
5. Verify in terminal:
   ```bash
   {build_command} && {lint_command}
   ```
6. If both pass, continue to Phase 2
7. Repeat for each phase in order

### Key Points
- Each phase file is self-contained (no cross-references)
- Phases must be executed in order (1, 2, 3...)
- Verify build + lint between every phase
- If a phase fails, re-run it from scratch (don't try to fix partial work)
- `CLAUDE.md` stays in the repo forever — any future agent interaction will read it
```

---

## Rendering Rules

1. Replace `{build_command}` and `{lint_command}` with actual commands from `stage_0.tech_stack`
2. Replace `{project_name}` with `stage_3.concept_and_context.name`
3. Include ONLY the section matching `platform_target` in the final README.md
4. For automated platforms (`claude_cli`, `codex_cli`, `gemini_cli`), always include BOTH automated and manual fallback instructions
5. For no-terminal platforms (`bolt`, `lovable`), emphasize local verification between phases
6. The `build.sh` file is always generated regardless of platform (serves as documentation even if not executable on the target platform)
