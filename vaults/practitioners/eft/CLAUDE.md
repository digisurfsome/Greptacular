# EFT Practitioner Bot - Knowledge Vault Schema

## What This Vault Is

This is the brain for an EFT (Emotional Freedom Techniques) practitioner bot.
It knows tapping sequences, protocols, setup statements,
and how to guide someone through EFT sessions.

## Bot Personality

This vault powers a bot that acts as an EFT practitioner. It should:
- Guide clients through tapping sequences step by step
- Know the tapping points and their order
- Create appropriate setup statements based on the client's issue
- Adapt the basic recipe for different emotional/physical issues
- Understand when EFT is appropriate vs. when to refer out

## Rules

1. **NEVER read from or write to other vaults.** This vault is `vaults/practitioners/eft/` only.
2. **Raw sources are immutable.** Never edit anything in `raw/`.
3. **Always update the index** after creating or modifying wiki pages.
4. **Always append to the log** after any operation.
5. **Use wikilinks** like [[Page Name]] to connect related pages.
6. **Scripts must include exact tapping points and words.**
7. **Always include SUDS ratings.** Track subjective units of distress.

## Directory Structure

```
vaults/practitioners/eft/
  raw/                    <- Source material (books, transcripts, training notes)
  wiki/
    index.md              <- Master catalog of all wiki pages
    log.md                <- Operation history
    hot.md                <- Recent context cache
    techniques/           <- EFT protocols and variations
    concepts/             <- Theory, meridians, energy psychology
    scripts/              <- Full session scripts for common issues
    entities/             <- Key figures (Gary Craig, etc.)
```

## Wiki Page Template - Protocol

```markdown
# Protocol Name

**Tags:** #eft #protocol #category
**Issue Type:** Anxiety / Phobia / Pain / Trauma / Performance
**Duration:** Approximate time
**Related:** [[Related Protocol]], [[Underlying Concept]]

## What It Addresses
(1-2 sentences - what issue does this protocol target?)

## Setup Statement
"Even though [specific issue], I deeply and completely accept myself."

## Tapping Sequence
1. **Karate Chop (KC):** Setup statement x3
2. **Eyebrow (EB):** Reminder phrase
3. **Side of Eye (SE):** Reminder phrase
4. **Under Eye (UE):** Reminder phrase
5. **Under Nose (UN):** Reminder phrase
6. **Chin Point (CH):** Reminder phrase
7. **Collarbone (CB):** Reminder phrase
8. **Under Arm (UA):** Reminder phrase
9. **Top of Head (TH):** Reminder phrase

## SUDS Check
- Before: Ask client to rate intensity 0-10
- After each round: Re-rate
- Target: Get to 2 or below

## When NOT to Use
(Contraindications, when to refer to licensed therapist)

## Variations
(Modifications for different situations)
```
