# Greptacular Knowledge Vaults

## What Is This?

This is your personal knowledge system based on the Karpathy LLM Wiki pattern.
Instead of one big messy pile, your knowledge lives in **separate vaults** -
each vault is its own walled-off brain.

## How It Works (Plain English)

1. **You drop stuff into `raw/`** - articles, transcripts, notes, PDFs, whatever
2. **You tell Claude to ingest it** - Claude reads it, breaks it into pieces, and files everything into `wiki/`
3. **The wiki builds itself** - pages link to each other, an index tracks everything, contradictions get flagged
4. **You ask questions** - Claude searches the wiki and gives you answers with sources
5. **It gets smarter over time** - every new source connects to everything already there

## Your Vaults

| Vault | What It's For | Path |
|-------|--------------|------|
| **Personal** | Your generalist brain - business ideas, app ideas, repos, everything | `vaults/personal/` |
| **NLP Practitioner** | NLP techniques, patterns, scripts for the NLP bot | `vaults/practitioners/nlp/` |
| **Hypnosis** | Hypnosis inductions, techniques, scripts for the hypnosis bot | `vaults/practitioners/hypnosis/` |
| **EFT** | EFT tapping sequences, protocols, scripts for the EFT bot | `vaults/practitioners/eft/` |
| **Jeremy Minor Sales** | 8-step sales process, objection handling, NEPQ questions | `vaults/sales/jeremy-minor/` |

## Why Separate Vaults?

- **Walled off** - A sales bot never accidentally pulls NLP therapy techniques
- **Each bot only sees its vault** - you point each bot at its own folder
- **Easy to add more** - want a 6th practitioner? Just copy the pattern
- **Your personal brain stays private** - bots never touch it

## How to Add a New Vault

1. Create the folder: `vaults/practitioners/new-thing/`
2. Create `raw/` and `wiki/` inside it
3. Copy any existing vault's `CLAUDE.md` and edit it for the new topic
4. Create an empty `wiki/index.md` and `wiki/log.md`
5. Start dropping sources into `raw/`

## Quick Commands (What to Say to Claude)

### Setting up
- "Read vaults/personal/CLAUDE.md and set up my personal brain"

### Ingesting new content
- "I just put [article name] in vaults/personal/raw/ - please ingest it"
- "Here's a transcript about NLP anchoring - ingest it into the NLP vault"

### Asking questions
- "Search my personal brain for everything about [topic]"
- "What does the Jeremy Minor vault say about handling price objections?"

### Maintenance
- "Run a lint check on the NLP vault"
- "What's missing from the hypnosis vault?"

### Batch ingest
- "I dropped 5 files into vaults/practitioners/eft/raw/ - ingest them all"
