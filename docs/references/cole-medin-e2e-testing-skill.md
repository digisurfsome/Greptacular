# Cole Medin's E2E Testing Skill (Reference)

Source: https://github.com/coleam00/link-in-bio-page-builder/blob/main/.claude/skills/e2e-test/SKILL.md

This is the original testing protocol from Cole Medin's link-in-bio page builder project.
It uses Vercel's `agent-browser` CLI for browser automation. Saved here as reference
for when we build the full swarm/rule-agent system.

## What We Adapted

Our `e2e_verification_prompt.template.md` adapts this protocol for use as a text prompt
that works with or without browser tooling. Key changes:

- **Removed agent-browser dependency** — works with Playwright MCP, agent-browser, or no browser tools at all
- **Added static analysis phase** — lint, type check, dependency audit before touching the browser
- **Added cross-feature integration testing** — features don't exist in isolation
- **Made database validation mandatory** — not optional
- **Kept the parallel research pattern** — 3 simultaneous investigations (structure, schema, bugs)
- **Kept the fix-as-you-go pattern** — don't just document, fix immediately
- **Kept the structured report format** — clear summary at the end

## Future Integration Points

When building the full swarm system with rule agents:

1. **Phase 1 parallel research** maps perfectly to spawning 3 sub-agents
2. **The bug hunting investigation** could become a dedicated "code auditor" agent role
3. **Database validation** could be its own agent that runs after every feature completion
4. **The report format** standardizes how agents communicate test results
5. **Responsive testing** would use agent-browser or Playwright MCP when available in the CLI

## Original Protocol Summary

- Pre-flight: Platform check, frontend detection, agent-browser install
- Phase 1: 3 parallel sub-agents (structure, database, bugs)
- Phase 2: Start app, take initial screenshot
- Phase 3: Create task list from user journeys
- Phase 4: Browser testing + DB validation + issue fixing + responsive testing
- Phase 5: Cleanup (stop server, close browser)
- Phase 6: Report (text summary + optional markdown export)
