# Product Lens — Think Before You Build

**Name**: product-lens
**Description**: Use this skill to validate the "why" before building, run product diagnostics, and convert vague ideas into specs.
**Origin**: ECC

## When to Use

- Before starting any feature — validate the "why"
- Weekly product review — are we building the right thing?
- When stuck choosing between features
- Before a launch — sanity check the user journey
- When converting a vague idea into a spec

## Four Operational Modes

### Mode 1: Product Diagnostic

Structured questioning framework with seven core inquiries:

1. **Who is this for?** (specific person, not "developers")
2. **What's the pain?** (quantify: how often, how bad, what do they do today?)
3. **Why now?** (what changed that makes this possible/necessary?)
4. **What's the 10-star version?** (if money/time were unlimited)
5. **What's the MVP?** (smallest thing that proves the thesis)
6. **What's the anti-goal?** (what are you explicitly NOT building?)
7. **How do you know it's working?** (metric, not vibes)

**Output:** `PRODUCT-BRIEF.md` containing answers, risks, and go/no-go recommendation.

### Mode 2: Founder Review

Assessment procedure:

1. Read README, CLAUDE.md, package.json, recent commits
2. Infer product direction
3. Score product-market fit signals (0-10 scale):
   - Usage growth trajectory
   - Retention indicators (repeat contributors, return users)
   - Revenue signals (pricing page, billing code, Stripe integration)
   - Competitive moat (what's hard to copy?)
4. Identify the singular lever for 10x growth
5. Flag features lacking strategic importance

### Mode 3: User Journey Audit

Implementation sequence:

1. Clone/install as new user
2. Document friction points (confusing steps, errors, missing docs)
3. Time each step
4. Compare to competitor onboarding
5. Score time-to-value
6. Recommend top 3 onboarding fixes

### Mode 4: Feature Prioritization

Methodology for selecting from multiple candidates:

1. List candidate features
2. Score using formula: **impact (1-5) x confidence (1-5) / effort (1-5)**
3. Rank by ICE score
4. Apply constraints: runway, team size, dependencies
5. Output prioritized roadmap with rationale

## Output Standards

All modes output actionable docs, not essays. Every recommendation has a specific next step.

## Integration Partnerships

- `/browser-qa` for verifying user journey findings
- `/design-system audit` for visual assessment
- `/canary-watch` for post-launch monitoring
