# Jeremy Minor Sales Bot - Knowledge Vault Schema

## What This Vault Is

This is the brain for a sales bot based on Jeremy Minor's NEPQ
(Neuro-Emotional Persuasion Questioning) sales methodology.
It knows all 8 steps, the specific questions, objection handling,
and how to guide someone through the sales process.

## Bot Personality

This vault powers a bot that acts as a Jeremy Minor-trained sales coach. It should:
- Know all 8 steps of the NEPQ process cold
- Have the exact questions for each step
- Know every common objection and the NEPQ response
- Coach salespeople in real-time on what to say next
- Speak in Jeremy Minor's direct, confident style
- Focus on asking questions, not pitching

## Rules

1. **NEVER read from or write to other vaults.** This vault is `vaults/sales/jeremy-minor/` only.
2. **Raw sources are immutable.** Never edit anything in `raw/`.
3. **Always update the index** after creating or modifying wiki pages.
4. **Always append to the log** after any operation.
5. **Use wikilinks** like [[Page Name]] to connect related pages.
6. **Questions must be word-for-word.** The exact phrasing matters in NEPQ.
7. **Objection responses must include tone notes.** How you say it matters as much as what you say.

## Directory Structure

```
vaults/sales/jeremy-minor/
  raw/                    <- Source material (courses, transcripts, training)
  wiki/
    index.md              <- Master catalog of all wiki pages
    log.md                <- Operation history
    hot.md                <- Recent context cache
    steps/                <- The 8 steps of NEPQ (one page per step)
    objections/           <- Every objection with NEPQ response
    scripts/              <- Full call scripts and role-play scenarios
    concepts/             <- NEPQ theory, psychology, principles
    entities/             <- Key people, companies, case studies
```

## Wiki Page Template - Sales Step

```markdown
# Step [N]: Step Name

**Tags:** #nepq #step-N #sales-process
**Position:** Step N of 8
**Goal:** What this step accomplishes
**Previous:** [[Step N-1: Name]]
**Next:** [[Step N+1: Name]]

## Purpose
(Why this step exists in the process)

## The Questions
1. "Exact question word-for-word?"
   - **Why it works:** (Psychology behind it)
   - **Listen for:** (What the prospect's answer tells you)
   - **If they say X:** (Branch to specific follow-up)

2. "Next question?"
   ...

## Transition to Next Step
(How to smoothly move to the next step)

## Common Mistakes
(What salespeople get wrong at this step)
```

## Wiki Page Template - Objection

```markdown
# Objection: "[Exact objection words]"

**Tags:** #objection #category
**Frequency:** How often this comes up
**Step Where It Appears:** Usually during [[Step N]]
**Related:** [[Similar Objection]]

## The Objection
"I need to think about it" (or whatever the exact words are)

## What They're Really Saying
(The psychology - what's actually going on)

## The NEPQ Response
"Exact words to say back?"
[Tone: curious, not defensive]
[Pace: slow down here]

## Follow-Up Questions
1. "Next question if they push back?"
2. ...

## If They Still Object
(Escalation path - what to do if the first response doesn't work)
```

## Ingest Priority

When ingesting Jeremy Minor material, prioritize:
1. The 8 steps with exact questions (core of the system)
2. Objection handling scripts (most used in real calls)
3. Tone and delivery notes (how to say things)
4. Psychology and principles (why things work)
5. Case studies and examples (supporting material)
