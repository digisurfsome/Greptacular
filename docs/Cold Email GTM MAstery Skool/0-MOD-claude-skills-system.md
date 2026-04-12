# Claude Skills & CLAUDE.md Mastery — Teach Claude Your Voice and Rules

## What You'll Build

A complete system of CLAUDE.md project files and Claude Skills that make Claude behave exactly the way you need — following your rules, writing in your voice, and never repeating mistakes. By the end, you'll have production-ready templates for both.

## Prerequisites

- Claude Pro or Max subscription
- Claude Code installed (see claude-code-setup.md)
- At least one active project to apply these to
- 2-3 examples of your writing style or previous work

## Estimated Time

45-60 minutes to create your first CLAUDE.md and 2-3 Skills.

---

## What Is CLAUDE.md

`CLAUDE.md` is a file you place in the root of any project directory. Claude Code reads it automatically every time it starts in that directory. It's your project's permanent memory — the rules, context, and constraints Claude follows without you repeating them.

Think of it as an employee handbook for Claude, specific to one project.

---

## What Are Skills

Skills are reusable instruction sets you create in Claude Projects (the web interface). They're on-demand — you load them when you need a specific capability. A CLAUDE.md is always loaded. A Skill is loaded when the task calls for it.

---

## Full Build Instructions

### CLAUDE.md Anatomy

Every effective CLAUDE.md has these sections:

#### 1. Mission

What this project does. One paragraph. Claude uses this to understand intent behind every request.

```markdown
## Mission
This is the lead generation pipeline for Cenra. It scrapes prospects from Apollo,
researches them via Perplexity, scores them against client ICPs, generates
personalized cold emails, and pushes them to SmartLead for sending. It runs daily
for 8 active clients.
```

#### 2. API Keys

Where they live, how to load them, which ones exist. Claude needs this to avoid breaking things.

```markdown
## API Keys
All keys live in `.env`. Never commit this file. Never log key values.

- ANTHROPIC_API_KEY — Claude API for email generation and scoring
- SUPABASE_URL — Database connection
- SUPABASE_KEY — Database auth (service role)
- SMARTLEAD_API_KEY — Email sending platform
- APIFY_API_KEY — Web scraping
- PERPLEXITY_API_KEY — Company research
```

#### 3. Pipeline / System

How the system works step by step. Claude uses this to understand what changes affect what.

```markdown
## Pipeline
1. Cron triggers at 7am EST daily
2. Fetch active clients from Supabase `clients` table
3. For each client:
   a. Pull unprocessed prospects from `prospects` table (status: new)
   b. Research each prospect via Perplexity (company + person)
   c. Score against client's ICP (1-10 scale)
   d. If score >= 7: generate personalized email using client's template
   e. Push email to SmartLead campaign via API
   f. Update prospect status to "sent" in Supabase
4. Send summary to Telegram (total processed, total sent, errors)
```

#### 4. Rules

Non-negotiable constraints. Use "Never" and "Always" statements. These prevent costly mistakes.

```markdown
## Rules
- Never run any script without checking .env variables are present first
- Never send emails without a client_id — every outreach must be attributed
- Always deduplicate prospects before processing (check email in outreach_log)
- Never include signatures or sign-offs in generated emails
- Always log errors to Supabase error_log table, not just console
- Never modify the scoring prompt without approval
- Always run in dry-run mode first when testing new clients
```

#### 5. Active Clients / Work

Current state so Claude knows what's live and what's in progress.

```markdown
## Active Work
- 8 clients active in pipeline
- Client "Acme Corp" onboarding — ICP not finalized, do not activate
- Bug: SmartLead API returning 429 on bulk pushes — need to add retry logic
- Next: Add Instantly as alternative sender for clients who request it
```

#### 6. Key Lessons

Gotchas that cost you hours. Save future-you (and Claude) from repeating them.

```markdown
## Key Lessons
- SmartLead API rate limit is 10 requests/second — always use delay between calls
- Perplexity returns markdown formatting — strip it before storing in Supabase
- The "blitz_cascade" field in campaign config must be an array of strings, not objects
- Apollo enrichment sometimes returns null emails — always null-check before processing
- Supabase RLS is enabled — use service role key for server-side operations
```

### Full CLAUDE.md Template

```markdown
# [Project Name]

## Mission
[One paragraph: what this project does, who it's for, what it delivers]

## Tech Stack
- Runtime: [Node.js 18 / Python 3.11 / etc.]
- Framework: [Next.js / Express / FastAPI / etc.]
- Database: [Supabase / Postgres / etc.]
- Hosting: [Vercel / Railway / VPS]
- Key APIs: [list them]

## API Keys
All keys live in `.env`. Never commit this file.
- KEY_NAME — what it's for
- KEY_NAME — what it's for

## System / Pipeline
1. Step one
2. Step two
3. Step three

## Rules
- Never [constraint]
- Always [requirement]
- Never [constraint]

## Active Work
- [ ] Current task
- [ ] Known issues
- [ ] Next milestone

## Key Lessons
- [Gotcha that cost you time]
- [Non-obvious behavior]
- [Integration quirk]
```

---

### Building Skills

Skills live in Claude Projects (web interface) as custom instructions. Each Skill has 5 parts:

#### Part 1: Role

```
You are a cold email copywriter who writes in a direct, conversational tone.
You write for B2B SaaS founders selling to mid-market companies.
```

#### Part 2: Rules

```
Rules:
- Maximum 85 words per email
- No buzzwords: "synergy," "leverage," "unlock," "revolutionize"
- No signatures or sign-offs
- No "Subject:" line in the output
- Every email must reference something specific about the prospect
- First line must be about them, not about you
```

#### Part 3: Format

```
Format:
- Output the email body only, no subject line
- Use short paragraphs (1-2 sentences each)
- End with a low-friction CTA (question, not a demand)
```

#### Part 4: Examples

```
Example of good output:
"Saw you just raised a Series A — congrats. Most teams at your stage
are still manually qualifying inbound leads, which means your SDRs
are spending 60% of their time on prospects who'll never close.

We built an AI qualifier that scores leads in real-time and only
routes the ones worth talking to. Cut our client's SDR waste by 40%.

Worth a 15-min look?"
```

#### Part 5: Context

```
Context:
- Target audience: B2B SaaS founders, VPs of Sales, Heads of Growth
- Product: AI-powered lead qualification tool
- Key differentiator: real-time scoring, not batch processing
- Price range: $500-2000/mo
- Competitors: Clay, Apollo, ZoomInfo (never mention these by name)
```

---

### 6 Skill Templates

#### 1. Content Writer

```
Role: You are a content writer for [brand]. You write in [tone: conversational/authoritative/casual].
Audience: [who reads this]
Format: [blog post / social post / email / script]
Rules:
- Write at a [grade level] reading level
- Use [short/medium/long] paragraphs
- Never use [banned words/phrases]
- Always include [required elements]
Examples: [paste 2-3 examples of writing you like]
```

#### 2. Code Reviewer

```
Role: You are a senior code reviewer for a [stack] codebase.
Priorities: Security > Correctness > Performance > Readability
Rules:
- Flag any hardcoded secrets or credentials
- Flag missing error handling in async functions
- Flag SQL injection vulnerabilities
- Suggest, don't rewrite — explain what's wrong and why
Format: List issues as: [CRITICAL], [WARNING], [SUGGESTION]
```

#### 3. Client Proposal Writer

```
Role: You write B2B service proposals for [company name].
Company: [what you do, key differentiators]
Pricing: [tier 1: $X, tier 2: $X, tier 3: $X]
Sections: Executive Summary, Problem, Solution, Process, Timeline, Pricing, Next Steps
Rules:
- Never discount below [minimum price]
- Always include a timeline
- Frame everything as ROI, not features
```

#### 4. Data Analyzer

```
Role: You analyze [type] data for [audience].
Metrics: [list the KPIs that matter]
Output format: Summary (3 bullets) → Key Findings → Recommendations → Raw Data
Rules:
- Always compare to previous period
- Flag anomalies (>20% change)
- Use plain language, not jargon
- Round percentages to one decimal
```

#### 5. Email Responder

```
Role: You draft email responses for [person/company].
Categories:
- Client inquiry → respond within [tone], offer [next step]
- Support request → acknowledge, provide solution or escalate
- Sales pitch (inbound) → polite decline or redirect
Tone: [professional but warm / direct / casual]
Rules:
- Never commit to timelines without checking
- Always end with a clear next action
- Keep under [word count] words
```

#### 6. Meeting Notes Processor

```
Role: You process meeting transcripts into structured notes.
Format:
## Summary (3 sentences max)
## Decisions Made
- [decision]: [owner]
## Action Items
- [ ] [task] — [owner] — [deadline]
## Key Discussion Points
- [topic]: [outcome]
## Parking Lot (unresolved)
- [item]
Rules:
- Capture every action item with an owner
- Flag decisions that contradict previous decisions
- Note any deadlines mentioned
```

---

### CLAUDE.md vs Skills: When to Use Which

| CLAUDE.md | Skills |
|---|---|
| Always loaded automatically | Loaded on demand |
| One per project directory | Unlimited, reusable |
| Project-specific context | Task-specific capability |
| Rules and constraints | Voice and format |
| System architecture | Output templates |
| Use for: pipelines, codebases, active projects | Use for: writing, analysis, formatting, reviewing |

---

### Memory System

Claude has multiple memory layers:

- **User memories**: things Claude remembers about you across all conversations (preferences, background, communication style)
- **Feedback memories**: corrections you've made that Claude stores to avoid repeating mistakes
- **Project memories**: CLAUDE.md and project-level context loaded per directory
- **Reference memories**: files you upload or link that Claude can reference during a session

The hierarchy: User memories are global. Project memories (CLAUDE.md) are per-project. Feedback memories are corrections. Reference memories are session-specific.

---

## Testing Steps

1. Create a CLAUDE.md in one of your project directories
2. Start Claude Code in that directory — it should reference the CLAUDE.md contents
3. Ask Claude to do something that would violate one of your Rules — it should refuse or flag it
4. Create a Skill in Claude Projects (web interface)
5. Test the Skill with a real task — output should match your format and tone
6. Update the CLAUDE.md with a new Key Lesson — verify Claude references it in future sessions

---

## Success Criteria

- CLAUDE.md created and automatically loaded by Claude Code
- Rules section prevents Claude from making specified mistakes
- At least 2 Skills created and producing correct output format
- Claude writes in your specified tone and follows your constraints
- Key Lessons section prevents repeat of documented gotchas

---

## Pro Tips

- **One project, one purpose.** Don't make a CLAUDE.md that covers multiple unrelated systems. Split them into separate directories.
- **Upload real examples, not descriptions.** Show Claude what good output looks like. Paste actual emails, actual code, actual proposals.
- **Use "Never" statements.** They're clearer than positive instructions. "Never use passive voice" is stronger than "Use active voice."
- **Version your Skills.** When you improve a Skill, save the old version. You might want to revert.
- **Test with edge cases.** Ask Claude to handle the weird scenarios — not just the happy path. That's where rules matter most.
- **Update CLAUDE.md as you learn.** Every time something goes wrong, add it to Key Lessons. Your CLAUDE.md should grow over time.
