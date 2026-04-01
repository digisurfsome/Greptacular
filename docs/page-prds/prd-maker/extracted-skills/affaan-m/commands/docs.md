# Docs - Documentation Lookup via Context7

> Source: https://github.com/affaan-m/everything-claude-code/blob/main/commands/docs.md

## Frontmatter

```yaml
---
description: Look up current documentation for a library or topic via Context7.
---
```

## Purpose

"Look up up-to-date documentation for a library, framework, or API and return a summarized answer with relevant code snippets. Uses the Context7 MCP (resolve-library-id and query-docs) so answers reflect current docs, not training data."

## Usage

```
/docs [library name] [question]
```

Multi-word argument example:

```
/docs "Next.js" "How do I configure middleware?"
```

**Conditional instructions**: If library or question is omitted, prompt user for:

1. The library or product name (e.g. Next.js, Prisma, Supabase)
2. The specific question or task (e.g. "How do I set up middleware?", "Auth methods")

## Workflow Steps

1. **Resolve library ID** - Call `resolve-library-id` with library name and user question to obtain Context7-compatible library ID (format example: `/vercel/next.js`)
2. **Query docs** - Call `query-docs` with library ID and user question
3. **Summarize** - Return concise answer with relevant code examples; mention library and version if relevant

## Output

User receives short, accurate answer from current docs plus code snippets.

**Fallback**: If Context7 unavailable, answer from training data with note that documentation may be outdated.
