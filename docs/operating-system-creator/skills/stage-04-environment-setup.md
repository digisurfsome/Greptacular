# OS Automation Skills — Stage 4: Environment Setup

> **What this does:** Captures everything needed to actually RUN this system — runtime, dependencies, API keys, credentials, database setup, and prerequisite steps.

---

## When to Use

After Stage 3. You now know what tools and APIs are involved. This stage nails down the exact setup requirements.

## Input

`stage_3` output — classifications with API tools, models, external services identified.

## Process

### Step 1: Runtime & Dependencies

| Question | Answer Format |
|----------|--------------|
| What runtime? | Node.js 18+ / Python 3.11+ / Bash / Other |
| What package manager? | npm / pip / other |
| Core dependencies? | List every package needed with version |
| System requirements? | Docker? Specific OS? Min RAM/disk? |

### Step 2: API Keys & Credentials Checklist

For EACH external service identified in Stages 0-3:

| Field | What to Capture |
|-------|----------------|
| **Service name** | e.g., "SmartLead" |
| **What key is needed** | API key / OAuth token / Service account / App password |
| **Where to get it** | Step-by-step: "Log in → Settings → API → Copy key" |
| **Plan required** | Free tier works? Or need paid plan? Which tier? |
| **Cost** | Monthly cost for the plan needed |
| **Env var name** | What to call it in .env (e.g., `SMARTLEAD_API_KEY`) |
| **Setup steps** | Any configuration beyond just getting the key (DNS records, webhook URLs, domain verification) |

### Step 3: Database Setup

| Question | Answer |
|----------|--------|
| Database type? | Supabase / SQLite / PostgreSQL / JSON files / None |
| Tables needed? | List from Stage 2 state tracking |
| Schema ready? | Full SQL or will be generated |
| Seed data needed? | Any initial data required before first run? |

### Step 4: Prerequisite Dependencies

What MUST be done before the system can run for the first time?

List in order:
1. "Create Supabase project and run schema SQL"
2. "Set up Google Workspace on sending domains"  
3. "Configure DNS records for each domain"
4. etc.

Mark each as: **one-time setup** or **per-instance setup** (done each time you add a new domain/mailbox/project).

### Step 5: Cost-Per-Run Math

| Item | Cost Per Call | Calls Per Run | Cost Per Run | Monthly Estimate |
|------|-------------|---------------|-------------|-----------------|
| Claude Haiku | $0.001 | 50 | $0.05 | $1.50 |
| SmartLead API | free | 20 | $0.00 | $0.00 |
| etc. | | | | |
| **Total** | | | **$X.XX** | **$XX/mo** |

### Step 6: Rate Limits

For each API:

| Service | Rate Limit | Our Usage Pattern | Buffer Strategy |
|---------|-----------|-------------------|----------------|
| Reddit API | 60 req/min | ~10 req/run | 1100ms delay between calls |
| Claude API | 50 req/min | ~20 req/run | 500ms delay |

## Output

```json
{
  "stage_4": {
    "runtime": "string",
    "dependencies": [{"name": "string", "version": "string"}],
    "api_keys": [
      {
        "service": "string",
        "key_type": "string",
        "how_to_get": "string",
        "plan_required": "string",
        "monthly_cost": "string",
        "env_var": "string",
        "setup_steps": ["string"]
      }
    ],
    "database": {
      "type": "string",
      "tables": ["string"],
      "schema_sql": "string"
    },
    "prerequisites": [
      {"step": "string", "type": "one_time | per_instance"}
    ],
    "cost_per_run": "string",
    "monthly_estimate": "string",
    "rate_limits": [
      {"service": "string", "limit": "string", "our_usage": "string", "buffer": "string"}
    ]
  }
}
```

## Rules

1. Every API key gets a "how to get it" walkthrough. Assume the user has never used the service before.
2. Cost math is mandatory. No "it's cheap" hand-waving. Exact numbers.
3. Prerequisites must be ordered. Step 3 might depend on step 1 being done first.
