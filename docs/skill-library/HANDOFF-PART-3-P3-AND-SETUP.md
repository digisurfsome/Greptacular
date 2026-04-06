# Skill Generation Handoff — Part 3: P3 Skills (46-53) + Execution Plan

> Run `npx ctx7 skills generate`, paste the prompt, save output to the listed path.
> See Part 1 for setup instructions.

---

## P3 SKILLS — Nice-to-Have

### REALTIME (3 skills)

---

### 46. supabase-realtime

**Save to:** `skills/realtime/supabase-realtime.md`

**Prompt:**
> Generate a skill for Supabase Realtime covering real-time database change subscriptions, presence tracking, and broadcast messaging. Must include: supabase.channel() creation, .on('postgres_changes') with filter by table/event/schema, presence with track() and presenceState(), broadcast for custom events between clients, channel subscription with subscribe(), unsubscribe cleanup in useEffect return, RealtimeChannel type, handling INSERT/UPDATE/DELETE event types separately, payload.new and payload.old for change data, error handling on subscription status callback.

**Tips:**
- When it asks about scope: focus on the JavaScript/TypeScript client, not the server config
- Make sure it covers the difference between postgres_changes (DB-driven) vs broadcast (client-driven) vs presence (user awareness)
- Should include the subscribe() status callback pattern: `channel.subscribe((status) => { if (status === 'SUBSCRIBED') ... })`

---

### 47. socket-io

**Save to:** `skills/realtime/socket-io.md`

**Prompt:**
> Generate a skill for Socket.io covering both server and client setup for real-time bidirectional communication. Must include: new Server(httpServer) setup with CORS config, io.on('connection') handler, socket.emit() and socket.on() for events, socket.join() for rooms and io.to(room).emit() for room broadcasts, namespaces with io.of('/admin'), middleware with io.use() and socket.use() for auth, acknowledgment callbacks (third arg to emit), socket.disconnect event handling, socket.data for per-connection state, volatile.emit for fire-and-forget, io.engine.on('connection_error') for debugging.

**Tips:**
- When it asks about version: target Socket.io v4.x (current)
- Emphasize the CORS config — it trips up most people (`cors: { origin: "http://localhost:3000" }`)
- Make sure it includes the client-side `io("http://localhost:3001")` connection pattern too

---

### 48. pusher

**Save to:** `skills/realtime/pusher.md`

**Prompt:**
> Generate a skill for Pusher Channels covering server-side event triggering and client-side subscription. Must include: new Pusher() server instantiation with appId/key/secret/cluster, pusher.trigger(channel, event, data) for sending events, client-side new Pusher(key) with cluster config, channel.subscribe() and channel.bind() for receiving, private channels with private- prefix and auth endpoint, presence channels with presence- prefix for user awareness (members.count, members.each, member_added/member_removed events), pusher.webhook() for server-side channel event webhooks, client events with client- prefix on private channels, connection state change handling.

**Tips:**
- When it asks about scope: cover both the pusher (server) and pusher-js (client) packages
- Presence channels are the key differentiator — make sure it covers the members API thoroughly
- Should include the auth endpoint pattern for private/presence channels

---

### DEVTOOLS (5 skills)

---

### 49. typescript-5

**Save to:** `skills/devtools/typescript-5.md`

**Prompt:**
> Generate a skill for TypeScript 5.5+ covering modern type system features and strict configuration. Must include: stage 3 decorators syntax (@decorator on classes/methods/fields), satisfies operator for type narrowing while preserving literal types, const type parameters for immutable inference, conditional types with infer keyword for type extraction, template literal types for string manipulation (uppercase/lowercase/capitalize), utility types Record/Partial/Required/Pick/Omit/Exclude/Extract/ReturnType/Parameters, strict tsconfig options (strict, noUncheckedIndexedAccess, exactOptionalPropertyTypes), verbatimModuleSyntax for explicit type imports, using keyword for disposable resources, NoInfer utility type.

**Tips:**
- When it asks about scope: focus on the type system and compiler features, not runtime
- Make sure satisfies includes the key pattern: `const config = { ... } satisfies Config` (preserves literal types unlike annotation)
- The using/DisposableStack pattern is new — make sure it shows the Symbol.dispose protocol

---

### 50. eslint-flat-config

**Save to:** `skills/devtools/eslint-flat-config.md`

**Prompt:**
> Generate a skill for ESLint 9+ flat config system covering the new configuration format. Must include: eslint.config.js with default export array of config objects, @eslint/js recommended rules import, typescript-eslint.configs.recommended integration, plugin integration without extends (direct plugin object in config), languageOptions.parser and languageOptions.parserOptions, custom rule objects with meta and create, ignores patterns (replaces .eslintignore), files array for targeting specific globs, global variables via languageOptions.globals, migrating from .eslintrc (no more extends/env/overrides), linterOptions.reportUnusedDisableDirectives.

**Tips:**
- When it asks about scope: focus exclusively on the flat config format, not the legacy .eslintrc format
- The biggest change is no more "extends" — make sure it shows how plugins are imported and spread directly
- Should show the typescript-eslint v8 flat config helper: `tseslint.config(...configs)`

---

### 51. prettier

**Save to:** `skills/devtools/prettier.md`

**Prompt:**
> Generate a skill for Prettier covering configuration, plugin integration, and workflow automation. Must include: .prettierrc JSON config with printWidth/tabWidth/singleQuote/trailingComma/semi options, prettier-plugin-tailwindcss for automatic class sorting, .prettierignore for excluding files, eslint-config-prettier to disable conflicting ESLint rules, pre-commit hooks with husky (npx husky init, .husky/pre-commit) and lint-staged (lint-staged config in package.json), editor integration settings for VS Code (formatOnSave, defaultFormatter), overrides array for per-file-type config, CLI usage (prettier --write --check), prettier.resolveConfig() API for programmatic use.

**Tips:**
- When it asks about scope: cover the config file, CLI, and integration with other tools
- The husky + lint-staged setup is the most valuable part — make sure the exact commands are included
- Should mention that prettier-plugin-tailwindcss is auto-detected (no config needed beyond installing it)

---

### 52. turborepo

**Save to:** `skills/devtools/turborepo.md`

**Prompt:**
> Generate a skill for Turborepo covering monorepo build orchestration and caching. Must include: turbo.json pipeline configuration with tasks object, dependsOn for task ordering (^build for topological, build for same-package), outputs array for cache artifacts, inputs for cache key customization, remote caching setup with Vercel (npx turbo login, npx turbo link), --filter flag for targeting specific packages (--filter=web, --filter=./packages/*), env and globalEnv for environment variable handling in cache keys, turbo.json extends for package-level config, turbo run with --parallel and --concurrency flags, package.json workspaces integration, turbo prune for deployment-ready subsets.

**Tips:**
- When it asks about version: target Turborepo 2.x (current)
- The cache invalidation via env/globalEnv is critical — missing env vars in the config means stale caches
- Make sure it covers the ^ prefix in dependsOn (topological dependency vs same-package dependency)

---

### 53. pnpm

**Save to:** `skills/devtools/pnpm.md`

**Prompt:**
> Generate a skill for pnpm covering package management and monorepo workspace configuration. Must include: pnpm-workspace.yaml for defining workspace packages, pnpm add/remove/install commands with workspace protocol (workspace:*), overrides in package.json for version pinning, catalogs for shared dependency versions across workspace, --filter flag for targeting specific packages (--filter package-name, --filter ./apps/*), pnpm run for scripts with --recursive and --parallel, .npmrc config options (shamefully-hoist, strict-peer-dependencies, auto-install-peers), pnpm deploy for production-only installs, pnpm patch for patching dependencies, pnpm dlx (equivalent to npx), pnpm store management (store path, store prune).

**Tips:**
- When it asks about version: target pnpm 9.x (current)
- Catalogs are new and powerful — make sure they show the pnpm-workspace.yaml catalog syntax
- The workspace: protocol is the key monorepo feature — `"shared-utils": "workspace:*"` in package.json

---

## COMPLETE EXECUTION PLAN

### Phase 1: One-Time Setup (5 minutes)

```bash
# Install Context7
npx ctx7 setup

# When browser opens, sign in (free account)
# API key is generated automatically
# Skill for your IDE is installed automatically
```

### Phase 2: Generate P1 Skills First (23 skills, ~1 hour)

Work through Part 1 of this handoff. For each skill:

1. Open terminal
2. Run `npx ctx7 skills generate`
3. When it asks "What expertise should the AI develop?" — paste the prompt from this doc
4. When it shows matching documentation sources — select the one that matches the library name
5. When it asks clarifying questions — use the tips from this doc
6. When it shows the generated skill — review it:
   - Does it cover all the "Must include" patterns listed here?
   - Does it reference current API methods (not deprecated ones)?
   - Is it specific (actual function names) not vague ("use the API")?
7. If it looks good — accept it
8. If something's missing — click "regenerate with feedback" and tell it what to add
9. Save the generated SKILL.md to the path listed for that skill

After every 5 skills: commit and push to your private repo.

### Phase 3: Generate P2 Skills (25 skills, ~1 hour)

Same process using Part 2 of this handoff.

### Phase 4: Generate P3 Skills (13 skills, ~30 minutes)

Same process using Part 3 (this file).

### Phase 5: Quality Review (30 minutes)

Pick 5 random skills across categories. For each:
1. Install it in Claude Code (copy to `.claude/skills/`)
2. Ask Claude Code to write a small feature using that library
3. Check: did it use current patterns from the skill, or fall back to training data?
4. If the skill didn't influence the output, the skill needs more specific patterns

### Phase 6: Create Version Tracking

Create `skill-versions.json` in your repo root:

```json
{
  "skills": [
    {
      "name": "next-js-app-router",
      "library": "next",
      "registry": "npm",
      "version_when_generated": "16.1.6",
      "generated_date": "2026-04-06",
      "last_checked": "2026-04-06"
    }
  ]
}
```

Add an entry for every generated skill with the library version that was current when you generated it.

### Phase 7: Set Up Auto-Update Check

Create `.github/workflows/check-skill-freshness.yml`:

```yaml
name: Check Skill Freshness
on:
  schedule:
    - cron: '0 0 * * 0'  # Every Sunday midnight
  workflow_dispatch:       # Manual trigger

jobs:
  check-versions:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Check npm packages for updates
        run: |
          echo "Checking skill freshness..."
          node -e "
          const fs = require('fs');
          const versions = JSON.parse(fs.readFileSync('skill-versions.json'));
          const stale = [];

          (async () => {
            for (const skill of versions.skills) {
              if (skill.registry !== 'npm') continue;
              try {
                const res = await fetch('https://registry.npmjs.org/' + skill.library + '/latest');
                const data = await res.json();
                const current = data.version;
                const [curMaj, curMin] = current.split('.').map(Number);
                const [genMaj, genMin] = skill.version_when_generated.split('.').map(Number);
                if (curMaj > genMaj || curMin > genMin) {
                  stale.push(skill.name + ': generated for ' + skill.version_when_generated + ', latest is ' + current);
                }
              } catch(e) { console.error('Failed to check ' + skill.library); }
            }

            if (stale.length > 0) {
              console.log('STALE SKILLS:\n' + stale.join('\n'));
              fs.writeFileSync('stale-skills.txt', stale.join('\n'));
            } else {
              console.log('All skills are current!');
            }
          })();
          "

      - name: Create issue for stale skills
        if: hashFiles('stale-skills.txt') != ''
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            const stale = fs.readFileSync('stale-skills.txt', 'utf8');
            await github.rest.issues.create({
              owner: context.repo.owner,
              repo: context.repo.repo,
              title: 'Stale skills detected - libraries have updated',
              body: 'The following skills need regeneration:\n\n' + stale + '\n\nRun `npx ctx7 skills generate` for each and update skill-versions.json.',
              labels: ['maintenance']
            });
```

### Phase 8: Delivery Setup (MVP)

For day 1, use the simplest possible delivery:

**Option A: Gumroad / LemonSqueezy**
- Create a product listing
- Set up tiers: Free (3 skills for email), Pro ($9/mo), Lifetime ($79)
- Deliver via password-protected page or Notion
- Skills listed individually — buyer copies one at a time

**Option B: Private Discord**
- Skills posted as individual messages in category channels
- Subscriber role required to access skill channels
- Free channel with 3 sample skills for anyone who joins

**Either way:**
- Never give bulk download
- Watermark each skill with buyer's email (add as comment at bottom of file)
- Rate limit: no more than 5 skill copies per hour per user

---

## BUNDLE REFERENCE

Pre-built combinations for common stacks:

**Web SaaS (D2D Boilerplate) — 16 skills:**
1, 6, 9, 11, 12, 14, 18, 22, 24, 26, 29, 35, 43, 49, 57

**Mobile Flutter — 6 skills:**
40, 45, 14, 18, 29, 17

**Full Stack Dual — 20 skills:**
Web SaaS + Mobile Flutter combined (deduplicated)

**Indie Hacker Minimal — 8 skills:**
1, 6, 9, 11, 14, 18, 22, 35

---

## SUMMARY

| Phase | What | Time | Skills |
|-------|------|------|--------|
| 1 | Setup ctx7 | 5 min | 0 |
| 2 | Generate P1 | 1 hour | 23 |
| 3 | Generate P2 | 1 hour | 25 |
| 4 | Generate P3 | 30 min | 13 |
| 5 | Quality review | 30 min | -- |
| 6 | Version tracking | 15 min | -- |
| 7 | Auto-update action | 15 min | -- |
| 8 | Delivery setup | 1 hour | -- |
| **TOTAL** | | **~4.5 hours** | **61** |
