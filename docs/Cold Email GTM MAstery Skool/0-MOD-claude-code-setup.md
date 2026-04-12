# Claude Code — Your AI Build Environment

## What You'll Build

A fully configured Claude Code environment that lets you go from idea to deployed product using a terminal AI agent. By the end, you'll have Claude Code installed, connected to external services via MCP, and a CLAUDE.md template ready for any project.

## Prerequisites

- macOS, Linux, or WSL on Windows
- Node.js 18+ installed (`node --version` to check)
- Claude Pro ($20/mo), Claude Max ($100/mo), or an Anthropic API key for pay-per-use
- A terminal you're comfortable typing in (Terminal, iTerm2, Warp, etc.)
- Git installed (`git --version` to check)

## Estimated Time

20-30 minutes for full setup including MCP connections.

---

## What Is Claude Code

Claude Code is a terminal-based AI agent made by Anthropic. It's not a chatbot in a browser. It runs in your terminal, reads your entire project directory, writes and edits files, runs commands, installs packages, debugs errors, and deploys — all from natural language instructions.

You describe what you want. Claude Code builds it. You review, refine, and ship.

---

## Full Build Instructions

### Step 1: Install Claude Code

```bash
npm install -g @anthropic-ai/claude-code
```

Verify the installation:

```bash
claude --version
```

You should see a version number. If you get "command not found," make sure your Node.js global bin directory is in your PATH.

### Step 2: Start Your First Project

```bash
mkdir my-project && cd my-project
claude
```

Claude Code will start an interactive session in the current directory. It reads all files in the directory for context.

### Step 3: API Key Setup (Pay-Per-Use)

If you're using an API key instead of Claude Pro/Max:

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

Make it permanent by adding to your shell config:

```bash
echo 'export ANTHROPIC_API_KEY="sk-ant-..."' >> ~/.zshrc
source ~/.zshrc
```

For bash users, replace `~/.zshrc` with `~/.bashrc`.

### Step 4: MCP Connections

MCP (Model Context Protocol) lets Claude Code connect to external services — databases, GitHub, file systems, and more. Each connection gives Claude new capabilities.

**Filesystem Access:**

```bash
claude mcp add filesystem -- npx -y @modelcontextprotocol/server-filesystem /path/to/your/directory
```

Replace `/path/to/your/directory` with the actual path you want Claude to access.

**GitHub:**

```bash
claude mcp add github -- npx -y @modelcontextprotocol/server-github
```

Requires a `GITHUB_TOKEN` environment variable. Create a personal access token at GitHub > Settings > Developer Settings > Personal Access Tokens.

**Supabase:**

```bash
claude mcp add supabase -- npx -y @supabase/mcp-server --supabase-url YOUR_SUPABASE_URL --supabase-key YOUR_SUPABASE_KEY
```

Replace with your actual Supabase project URL and service role key from your Supabase dashboard.

**Verify all connections:**

```bash
claude mcp list
```

You should see all three connections listed and active.

### Step 5: Create Your CLAUDE.md

Every project should have a `CLAUDE.md` file in the root directory. Claude Code reads this automatically every time it starts. This is how you give Claude permanent context about your project.

Create `CLAUDE.md` in your project root with this template:

```markdown
# Project Name

## Overview
One paragraph describing what this project does, who it's for, and the core value it delivers.

## Tech Stack
- Runtime: Node.js 18
- Framework: Next.js 14 / Express / etc.
- Database: Supabase (Postgres)
- Hosting: Vercel / Railway / etc.
- APIs: list external APIs used

## API Keys
All keys live in `.env` (never commit this file).
- ANTHROPIC_API_KEY — Claude API access
- SUPABASE_URL — database connection
- SUPABASE_KEY — database auth
- (add others as needed)

## Coding Standards
- Use ES modules (import/export)
- All async functions must have try/catch with meaningful error messages
- No console.log in production code — use a logger
- Prefer named exports over default exports

## Rules
- Never commit .env files
- Never run destructive database operations without confirmation
- Always validate input before processing
- (add project-specific rules)

## Active Work
- [ ] Current feature being built
- [ ] Known bugs to fix
- [ ] Next milestone
```

### Step 6: The Build Loop

This is the core workflow with Claude Code:

1. **Describe the outcome** — Tell Claude what you want in plain language. Be specific about the end result, not the implementation steps.
2. **Claude writes code** — It creates files, installs dependencies, writes functions, sets up configs.
3. **Preview** — Run the code, check the output, open it in a browser if it's a web app.
4. **Refine** — Tell Claude what to change. "Make the button blue." "Add error handling for empty inputs." "The API returns a different format, here's an example."
5. **Deploy** — Tell Claude to deploy. It can push to GitHub, deploy to Vercel, set up Railway, etc.

### Step 7: Your First Build

Paste this into Claude Code to test your setup:

```
Build me a customer FAQ bot that reads from FAQ.md, has a web interface,
uses Claude to match questions to answers, runs on port 3000.

Create a FAQ.md with 10 sample questions and answers about a SaaS product.
The web interface should have a search bar, show the matched answer,
and have a clean minimal design. Use Express for the backend.
```

Claude will create all the files, install dependencies, and start the server. Open `http://localhost:3000` to see it.

---

## Environment Variables

```
ANTHROPIC_API_KEY=sk-ant-...        # Required for API access
GITHUB_TOKEN=ghp_...                # Required for GitHub MCP
SUPABASE_URL=https://xxx.supabase.co  # Required for Supabase MCP
SUPABASE_KEY=eyJ...                 # Required for Supabase MCP
```

---

## Testing Steps

1. Run `claude --version` — should return a version number
2. Run `claude` in a project directory — should start an interactive session
3. Run `claude mcp list` — should show your configured connections
4. Ask Claude to "create a file called test.txt with the text hello world" — file should appear
5. Ask Claude to "read test.txt and tell me what it says" — should respond with "hello world"
6. Ask Claude to "delete test.txt" — file should be removed
7. Run the FAQ bot build from Step 7 — should produce a working web app

---

## Success Criteria

- Claude Code installed and responding to commands
- At least one MCP connection configured and verified
- CLAUDE.md template created in a project directory
- Successfully built and ran the FAQ bot example
- Understand the describe-build-preview-refine-deploy loop

---

## Pro Tips

- **Build one feature at a time.** Don't ask Claude to build an entire app in one prompt. Break it into features and build each one.
- **Use screenshots for visual feedback.** If a UI looks wrong, take a screenshot and share it with Claude.
- **Commit after every working milestone.** Ask Claude to commit after each feature works. This gives you rollback points.
- **Use /compact for long sessions.** When the conversation gets long, type `/compact` to compress the context and keep Claude focused.
- **Be specific about what you want.** "Build a landing page" is vague. "Build a landing page with a hero section, 3 feature cards, a pricing table with 2 tiers, and a footer" is actionable.

---

## The Power Stack

The full stack for going from zero to live product:

```
Claude Code  →  writes all code, handles deployment
Supabase     →  database, auth, storage, edge functions
n8n          →  workflow automation, API orchestration
Vercel       →  frontend hosting, serverless functions
```

Claude Code is the builder. Supabase is the backend. n8n is the automation layer. Vercel is where it goes live. Together, they let a single person ship production software.
