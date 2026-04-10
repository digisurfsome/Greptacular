# NLP Practitioner Bot - Knowledge Vault Schema

## What This Vault Is

This is the brain for an NLP (Neuro-Linguistic Programming) practitioner bot.
It knows how to do NLP as a practitioner - techniques, patterns, scripts,
and how to teach/guide someone through NLP processes.

## Bot Personality

This vault powers a bot that acts as an NLP practitioner. It should:
- Guide clients through NLP techniques step by step
- Explain concepts in simple, accessible language
- Know when to use which technique based on what the client describes
- Have scripts and word-for-word guides for each technique
- Understand contraindications (when NOT to use a technique)

## Rules

1. **NEVER read from or write to other vaults.** This vault is `vaults/practitioners/nlp/` only.
2. **Raw sources are immutable.** Never edit anything in `raw/`.
3. **Always update the index** after creating or modifying wiki pages.
4. **Always append to the log** after any operation.
5. **Use wikilinks** like [[Page Name]] to connect related pages.
6. **Scripts must be word-for-word.** When a technique has a script, include the exact words.
7. **Always include contraindications.** Note when a technique should NOT be used.

## Directory Structure

```
vaults/practitioners/nlp/
  raw/                    <- Source material (books, transcripts, training notes)
  wiki/
    index.md              <- Master catalog of all wiki pages
    log.md                <- Operation history
    hot.md                <- Recent context cache
    techniques/           <- NLP techniques with full scripts
    concepts/             <- Core NLP concepts and models
    scripts/              <- Word-for-word practitioner scripts
    entities/             <- Key people, organizations, certifications
```

## Wiki Page Template - Technique

```markdown
# Technique Name

**Tags:** #nlp #technique #category
**Difficulty:** Beginner / Intermediate / Advanced
**Duration:** Approximate time needed
**Related:** [[Related Technique]], [[Underlying Concept]]

## What It Does
(1-2 sentences - what problem does this solve?)

## When to Use It
(Situations where this technique is appropriate)

## When NOT to Use It
(Contraindications - critical safety info)

## Prerequisites
(What the client/practitioner needs to know first)

## Step-by-Step Script
1. (Exact words and actions)
2. ...

## Variations
(Different versions of this technique)

## Connections
- Builds on [[Foundation Technique]]
- Often combined with [[Other Technique]]
- Part of [[Broader Framework]]
```

## Ingest Priority

When ingesting NLP material, prioritize:
1. Techniques with step-by-step scripts (most valuable for the bot)
2. When-to-use decision trees (helps bot pick the right technique)
3. Contraindications and safety info (prevents harm)
4. Theoretical models (background knowledge)
5. History and people (least priority)
