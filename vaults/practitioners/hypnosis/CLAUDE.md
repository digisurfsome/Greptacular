# Hypnosis Practitioner Bot - Knowledge Vault Schema

## What This Vault Is

This is the brain for a Hypnosis practitioner bot.
It knows inductions, deepeners, suggestions, scripts,
and how to guide someone through hypnotic processes.

## Bot Personality

This vault powers a bot that acts as a hypnosis practitioner. It should:
- Guide clients through hypnotic inductions and processes
- Have word-for-word scripts for different induction styles
- Know which induction to use based on client responsiveness
- Understand safety, ethics, and when to refer out
- Speak in calm, measured, practitioner-appropriate language

## Rules

1. **NEVER read from or write to other vaults.** This vault is `vaults/practitioners/hypnosis/` only.
2. **Raw sources are immutable.** Never edit anything in `raw/`.
3. **Always update the index** after creating or modifying wiki pages.
4. **Always append to the log** after any operation.
5. **Use wikilinks** like [[Page Name]] to connect related pages.
6. **Scripts must be word-for-word.** Include exact language for inductions.
7. **Safety first.** Always include contraindications and ethical guidelines.

## Directory Structure

```
vaults/practitioners/hypnosis/
  raw/                    <- Source material (books, transcripts, training notes)
  wiki/
    index.md              <- Master catalog of all wiki pages
    log.md                <- Operation history
    hot.md                <- Recent context cache
    techniques/           <- Inductions, deepeners, emergence scripts
    concepts/             <- Hypnosis theory, trance states, suggestibility
    scripts/              <- Full word-for-word session scripts
    entities/             <- Key figures (Erickson, Elman, etc.)
```

## Wiki Page Template - Induction/Technique

```markdown
# Technique Name

**Tags:** #hypnosis #induction|#deepener|#suggestion|#emergence
**Style:** Direct / Indirect / Conversational / Ericksonian
**Duration:** Approximate time
**Suggestibility Type:** Best for physical/emotional suggestibility
**Related:** [[Related Technique]], [[Underlying Concept]]

## What It Does
(1-2 sentences)

## When to Use It
(Client type, situation, suggestibility indicators)

## When NOT to Use It
(Contraindications, ethical boundaries)

## Full Script
(Exact words, with [bracketed stage directions])

## Deepening Options
(How to deepen trance after this induction)

## Emergence
(How to bring client out safely)

## Connections
- Pairs well with [[Other Technique]]
- Variation of [[Base Technique]]
```
