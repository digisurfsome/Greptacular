# Personal Brain - Knowledge Vault Schema

## What This Vault Is

This is the owner's generalist second brain. It holds everything:
business ideas, app ideas, notes from all repos, meeting notes,
research, personal goals, and anything else that matters.

## Rules

1. **NEVER read from or write to other vaults.** This vault is `vaults/personal/` only.
2. **Raw sources are immutable.** Never edit anything in `raw/`. Read only.
3. **The wiki is yours to maintain.** Create, update, and link pages in `wiki/`.
4. **Always update the index** after creating or modifying wiki pages.
5. **Always append to the log** after any operation (ingest, query, lint).
6. **Use wikilinks** like [[Page Name]] to connect related pages.
7. **Keep it simple.** The owner is not technical. Write in plain language.

## Directory Structure

```
vaults/personal/
  raw/                    <- Drop source material here (never modified)
  wiki/
    index.md              <- Master catalog of all wiki pages
    log.md                <- Chronological record of all operations
    hot.md                <- Recent context cache (~500 words)
    entities/             <- People, companies, tools, apps
    concepts/             <- Ideas, frameworks, patterns, strategies
    sources/              <- Summaries of ingested raw materials
    analysis/             <- Comparisons, insights, syntheses
```

## How to Ingest a New Source

1. Read the source from `raw/`
2. Discuss key takeaways with the owner (ask 2-3 clarifying questions)
3. Create a source summary page in `wiki/sources/`
4. Create or update entity pages in `wiki/entities/` for people, tools, companies mentioned
5. Create or update concept pages in `wiki/concepts/` for ideas, frameworks, patterns
6. Add wikilinks between all related pages
7. Update `wiki/index.md` with new pages
8. Append operation to `wiki/log.md`
9. Update `wiki/hot.md` with what just happened

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

Every wiki page should have this structure:

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
- Contradicts [[Another Page]] on...
- Builds on [[Foundation Page]]
```

## Hot Cache

The file `wiki/hot.md` stores ~500 words of the most recent session context.
Update it after every interaction. It should contain:
- What was just worked on
- Key decisions made
- Which pages were created/updated
- Open questions or next steps
