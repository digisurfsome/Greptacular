# [VAULT NAME] - Knowledge Vault Schema
# 
# HOW TO USE THIS TEMPLATE:
# 1. Copy this entire folder to: vaults/[category]/[vault-name]/
#    Examples:
#      vaults/practitioners/reiki/
#      vaults/sales/grant-cardone/
#      vaults/personal/fitness/
#      vaults/bots/customer-support/
#
# 2. Find-and-replace these placeholders in THIS file:
#      [VAULT NAME]     -> Your vault's display name (e.g., "Reiki Practitioner")
#      [VAULT PATH]     -> The folder path (e.g., "vaults/practitioners/reiki/")
#      [BOT ROLE]       -> What the bot does (e.g., "a Reiki energy healing practitioner")
#      [CATEGORY1-4]    -> Your wiki subfolder names (e.g., "techniques", "protocols")
#      [CATEGORY1-4 DESCRIPTION] -> What goes in each folder
#
# 3. Create the wiki subfolders to match your categories:
#      mkdir wiki/[category1] wiki/[category2] wiki/[category3] wiki/[category4]
#
# 4. Done. Start dropping sources into raw/
#
# DELETE EVERYTHING ABOVE THIS LINE AFTER SETUP
# -----------------------------------------------

## What This Vault Is

This is the brain for [VAULT NAME].
It contains all the knowledge, scripts, techniques, and reference material
needed to power this bot or knowledge base.

## Bot Personality

This vault powers a bot that acts as [BOT ROLE]. It should:
- (Describe how it talks to people)
- (Describe what it knows)
- (Describe what it helps people do)
- (Describe its tone and style)
- (Describe any safety/ethical boundaries)

## Rules

1. **NEVER read from or write to other vaults.** This vault is `[VAULT PATH]` only.
2. **Raw sources are immutable.** Never edit anything in `raw/`.
3. **Always update the index** after creating or modifying wiki pages.
4. **Always append to the log** after any operation.
5. **Use wikilinks** like [[Page Name]] to connect related pages.
6. (Add any vault-specific rules here)

## Directory Structure

```
[VAULT PATH]
  raw/                    <- Source material (drop files here, never modified)
  wiki/
    index.md              <- Master catalog of all wiki pages
    log.md                <- Operation history
    hot.md                <- Recent context cache (~500 words)
    [CATEGORY1]/          <- [CATEGORY1 DESCRIPTION]
    [CATEGORY2]/          <- [CATEGORY2 DESCRIPTION]
    [CATEGORY3]/          <- [CATEGORY3 DESCRIPTION]
    [CATEGORY4]/          <- [CATEGORY4 DESCRIPTION]
```

## How to Ingest a New Source

1. Read the source from `raw/`
2. Discuss key takeaways with the owner (ask 2-3 clarifying questions)
3. Create a source summary page in the appropriate wiki subfolder
4. Create or update related pages across the wiki
5. Add wikilinks between all related pages
6. Update `wiki/index.md` with new pages
7. Append operation to `wiki/log.md`
8. Update `wiki/hot.md` with what just happened

## How to Answer a Query

1. Read `wiki/hot.md` first (recent context)
2. Read `wiki/index.md` to find relevant pages
3. Read the relevant wiki pages
4. Synthesize an answer with [[wikilinks]] as citations
5. If the answer reveals a useful insight, offer to save it as a new wiki page
6. Append the query to `wiki/log.md`

## How to Lint

Check for:
- Orphan pages (no inbound links)
- Dead wikilinks (links to pages that don't exist)
- Contradictions between pages
- Missing pages (mentioned but never created)
- Stale content that needs updating
- Index entries that don't match actual pages

## Wiki Page Template

Every wiki page should follow this structure:

```markdown
# Page Title

**Tags:** #tag1 #tag2
**Related:** [[Related Page 1]], [[Related Page 2]]
**Sources:** [[Source that mentioned this]]

## Summary
(2-3 sentence overview)

## Details
(The actual content)

## Connections
- Related to [[Other Page]] because...
- Builds on [[Foundation Page]]
```

## Ingest Priority

When ingesting material for this vault, prioritize:
1. (Most important type of content for this bot)
2. (Second most important)
3. (Third)
4. (Fourth)
5. (Least priority)

## Hot Cache

The file `wiki/hot.md` stores ~500 words of the most recent session context.
Update it after every interaction. It should contain:
- What was just worked on
- Key decisions made
- Which pages were created/updated
- Open questions or next steps
