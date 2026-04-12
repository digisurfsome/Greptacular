# Operating System Creator — Wizard Questionnaire

> **Purpose:** These are the exact questions you ask about ANY manual business process to gather the information needed to turn it into a Claude-powered operating system. This is the intake form — the "wizard" that walks someone through decomposing their process into the 6-step pattern.

---

## How This Works

You sit down with a business owner (or yourself) and walk through these questions. By the end, you have everything needed to map their process to the 6-step pattern (INPUT → PROCESS → OUTPUT → STATE → NOTIFY → SCHEDULE) and build the CLAUDE.md files.

The questionnaire has 4 sections:
- **Section A:** Understand the big picture
- **Section B:** Break down each step
- **Section C:** Plan the operations layer
- **Section D:** Define success criteria

---

## Section A: The Big Picture

These questions map the overall process before breaking it into steps.

### A1. What is this process called?
> Give it a simple name. "Lead generation." "Invoice processing." "Content publishing." "Customer onboarding."

### A2. Walk me through what a human does today, step by step.
> Pretend you're training someone brand new. What's step 1? Then what? Then what? Be specific about what they look at, what they click, what they type, what decisions they make. Don't skip the boring parts.

### A3. How often does this process run?
> - [ ] Multiple times per day
> - [ ] Once a day
> - [ ] A few times per week
> - [ ] Weekly
> - [ ] Monthly
> - [ ] On-demand (when something triggers it)
> - [ ] Continuously (always running)

### A4. How long does the full process take a human?
> From start to finish, how many minutes/hours does one complete run take?

### A5. How many items get processed per run?
> Examples: "50 leads per day", "10 invoices per week", "3 blog posts per month"

### A6. Where does the starting data come from?
> - [ ] A website or web app (which one?)
> - [ ] A spreadsheet (Google Sheets, Excel, CSV?)
> - [ ] An email inbox
> - [ ] A database
> - [ ] An API or software tool (which one?)
> - [ ] Manual research (Google, LinkedIn, etc.)
> - [ ] Someone sends it to you (how?)
> - [ ] Other: ___

### A7. Where does the end result go?
> - [ ] Into a software tool (which one?)
> - [ ] Sent to a person (email, Slack, text?)
> - [ ] Published somewhere (website, social media?)
> - [ ] Saved to a file or spreadsheet
> - [ ] Into a database
> - [ ] Delivered to a client
> - [ ] Other: ___

### A8. What tools and services are already being used?
> List every tool, software, website, or service involved in this process today. For each one, note whether it has an API (check their docs or Google "[tool name] API").

| Tool/Service | What it's used for | Has API? | API docs URL |
|---|---|---|---|
| | | | |
| | | | |
| | | | |

### A9. What breaks most often?
> What goes wrong? Where do errors happen? What takes the most time? What's the most tedious part? What do people complain about?

### A10. Are there any legal or compliance requirements?
> Examples: CAN-SPAM for email, HIPAA for healthcare, GDPR for EU data, PCI for payments, industry-specific regulations, client contracts with specific terms.

---

## Section B: Step-by-Step Breakdown

**Repeat this entire section for EACH step identified in A2.**

Take the human process from A2 and break it into discrete steps. Each step should be one action: "search for prospects", "verify their email", "write the outreach email", "send the email", etc.

---

### Step #___: [Name this step]

#### B1. What does the human do in this step?
> Describe the exact action. "They search Apollo for companies in the construction industry with 10-50 employees." Be specific.

#### B2. What data does this step need to start? (INPUT)
> What information must be available before this step can begin? Where does it come from — the previous step, a tool, a file, a person?

#### B3. What decisions does the human make?
> What judgment calls happen here? Examples: "They decide if this lead is a good fit based on company size and industry." "They choose which template to use based on the prospect's role." "They skip leads that don't have an email."

#### B4. Could Claude make this decision instead?
> For each decision in B3:
> - [ ] Yes, with clear rules (write them out)
> - [ ] Yes, but needs judgment (describe what "good" looks like)
> - [ ] No, must stay human (why?)

#### B5. What's the output of this step? (OUTPUT)
> What gets produced? A list of names? An email draft? A score? A file? A decision (yes/no/maybe)?

#### B6. Where does that output go?
> - [ ] Into the next step (which one?)
> - [ ] Into a database
> - [ ] Into an external tool via API
> - [ ] Into a file
> - [ ] To a person
> - [ ] Multiple destinations

#### B7. Is there an API-first tool that could handle the data source?
> Search for "[what you need] API" — example: "email verification API" finds MillionVerifier, ZeroBounce, NeverBounce. List what you find:

| Tool | API? | Cost | Notes |
|---|---|---|---|
| | | | |

#### B8. What's the error case?
> What happens when this step fails? API returns nothing? Data is malformed? Service is down? What should happen — skip, retry, alert a human, stop everything?

#### B9. How long does this step take a human?
> Minutes per item. This helps prioritize which steps to automate first (longest = most value).

---

## Section C: Operations Layer

These questions define the STATE, NOTIFY, and SCHEDULE layers.

### State Tracking

#### C1. What statuses does an item move through?
> Map the lifecycle. Example for a lead: `new → enriched → scored → emailed → replied → booked → closed`
>
> Your statuses: ___ → ___ → ___ → ___ → ___ → ___

#### C2. Do you need an audit trail?
> Do you need to know exactly what happened to each item, when, and why? Or is just the current status enough?
> - [ ] Just current status (status field on the record)
> - [ ] Full audit trail (event log with timestamps)
> - [ ] Both

#### C3. Do you need to prevent duplicate processing?
> Could the same item get processed twice? If so, what field makes each item unique? (email address, order number, URL, etc.)
>
> Unique identifier: ___

### Notifications

#### C4. Who needs to know when this runs?
> - [ ] Just me (solo operator)
> - [ ] My team
> - [ ] A client
> - [ ] Nobody — fully silent autopilot

#### C5. What do they need to know?
> - [ ] "It ran successfully" (completion alert)
> - [ ] "It failed" (error alert)
> - [ ] Summary stats ("processed 200 leads, 15 skipped, 3 errors")
> - [ ] Individual item alerts ("hot lead just replied!")
> - [ ] Daily/weekly digest

#### C6. How should they be notified?
> - [ ] Telegram (fastest for solo operators — recommended)
> - [ ] Slack (team environments)
> - [ ] Email (formal, client-facing)
> - [ ] Dashboard (ongoing visibility)
> - [ ] SMS (urgent alerts only)

### Scheduling

#### C7. When should this run?
> - [ ] Every X minutes/hours (real-time monitoring)
> - [ ] Once per day at a specific time
> - [ ] On specific days (M/W/F, weekdays only, etc.)
> - [ ] When triggered by an event (what event?)
> - [ ] Manually for now, automate later

#### C8. What happens if it fails mid-run?
> - [ ] Start over from the beginning (simple, acceptable for small batches)
> - [ ] Resume from where it left off (requires checkpoint/state tracking)
> - [ ] Alert a human and wait (safety-critical processes)

#### C9. What's the infrastructure?
> - [ ] My personal computer (simplest, but stops when you sleep)
> - [ ] A cloud server / VPS (always on — DigitalOcean, Hetzner, Railway)
> - [ ] A workflow platform (n8n cloud, Make, Zapier)
> - [ ] Don't know yet / need recommendation

---

## Section D: Success Criteria

### D1. How do you measure success today?
> What metrics matter? Examples: "leads generated per day", "reply rate", "invoices processed per hour", "error rate", "time saved"

| Metric | Current Value | Target Value |
|---|---|---|
| | | |
| | | |
| | | |

### D2. What's the human cost being replaced?
> How much time does this process cost in human hours per week/month? What's that worth in salary or contractor fees?
>
> Hours per week: ___
> Cost per month: $___

### D3. What's the budget for tools and APIs?
> - [ ] Free/minimal (< $50/month)
> - [ ] Moderate ($50-200/month)
> - [ ] Investment level ($200-500/month)
> - [ ] Enterprise (> $500/month)

### D4. What's the MVP?
> If you could only automate ONE step to start, which step from Section B would give you the most relief? That's where we build first.
>
> MVP step: ___

---

## After the Questionnaire: What Happens Next

Once all sections are filled out, you have everything needed to:

1. **Map each step to the 6-step pattern** — Each step from Section B maps to INPUT → PROCESS → OUTPUT. Section C maps to STATE → NOTIFY → SCHEDULE.

2. **Select tools** — Section B7 identifies the API-first tools for each step. Fill any gaps by searching "[need] API" or checking lists of popular APIs in that domain.

3. **Write the architecture** — Draw the pipeline: Step 1 output → Step 2 input → Step 3 output, with the database, notifications, and scheduler wrapped around it.

4. **Write the CLAUDE.md files** — One MD file per major component. Each file follows this structure:
   - Mission statement (what this component does)
   - API connections (keys, endpoints, rate limits)
   - Pipeline steps (INPUT → PROCESS → OUTPUT for this component)
   - Rules and constraints (what Claude must/must not do)
   - Error handling (what happens when things fail)
   - Testing checklist (how to verify it works)

5. **Build in order** — Start with the MVP step (D4). Get it working. Add the next step. Connect them. Add state tracking. Add notifications. Add scheduling. Ship.

---

## Quick Reference: Mapping Questionnaire to the 6 Steps

| Questionnaire Section | Maps To | What It Produces |
|---|---|---|
| A2 (step-by-step process) | Overall pipeline architecture | The sequence of steps |
| A6 (where data comes from) | Step 1 INPUT | Data source identification |
| A7 (where results go) | Final step OUTPUT | Delivery destination |
| A8 (existing tools) | Tool selection | API-first tool list |
| B2 (what each step needs) | Per-step INPUT | Data flow between steps |
| B3-B4 (decisions made) | Per-step PROCESS | Claude prompt design |
| B5-B6 (step output) | Per-step OUTPUT | Where results flow |
| B7 (API tools) | Tool selection | Specific services to use |
| C1-C3 (statuses, audit, dedup) | STATE | Database schema design |
| C4-C6 (who, what, how notified) | NOTIFY | Notification setup |
| C7-C9 (when, failure, infra) | SCHEDULE | Automation setup |
| D1-D4 (metrics, cost, MVP) | Prioritization | What to build first |
