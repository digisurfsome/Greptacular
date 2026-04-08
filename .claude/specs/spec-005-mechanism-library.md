# Spec 005 — Mechanism Library

## What This Is
A folder of tested, tagged, reusable code patterns. Every time a Code Module node is built, tested, and works — the useful parts get saved here with metadata. Before Claude writes any new code for a node, it searches here first. If something matches, it uses it directly. This is how you never write the same pattern twice.

## Why It Matters
Over time this becomes the most valuable part of the whole system. Every pattern you've ever built — deduplicate a list, retry an API call, chunk long text for an LLM, extract structured JSON — lives here, tested and tagged. New nodes assemble from these building blocks. You stop writing code from scratch and start wiring proven pieces together.

---

## Folder Structure

```
mechanisms/
├── README.md                    # What this folder is, how to use it
├── data-transform/
│   ├── flatten-array.ts
│   ├── deduplicate-by-key.ts
│   ├── normalize-text.ts
│   └── map-fields.ts
├── api-handling/
│   ├── retry-with-backoff.ts
│   ├── paginator.ts
│   ├── rate-limiter.ts
│   └── mock-response.ts
├── llm-ops/
│   ├── chunk-long-text.ts
│   ├── structured-extractor.ts
│   ├── batch-llm-calls.ts
│   └── prompt-builder.ts
├── control-flow/
│   ├── gate-by-condition.ts
│   ├── timeout-guard.ts
│   └── parallel-executor.ts
├── validation/
│   ├── check-required-fields.ts
│   ├── validate-url.ts
│   └── validate-json-shape.ts
└── output/
    ├── format-as-markdown.ts
    └── build-email-html.ts
```

---

## The Metadata Header (Every File Must Have This)

```typescript
/**
 * @mechanism flatten-array
 * @description Flattens an array of arrays into a single flat array. Handles null/undefined items.
 * @tags array, transform, data, flatten
 * @input any[][] — array of arrays (nulls and undefineds are filtered)
 * @output any[] — single flat array with no nulls
 * @source youtube-batch-processor node (step_3)
 * @tested true
 * @test-cases
 *   input: [[1,2],[3,null],[4]] → output: [1,2,3,4]
 *   input: [] → output: []
 *   input: [[null, undefined]] → output: []
 * @used-in [youtube-processor, news-aggregator]
 * @quality stable
 */
export function flattenArray(input: (unknown[] | null | undefined)[]): unknown[] {
  return (input || [])
    .flat()
    .filter(item => item !== null && item !== undefined)
}
```

### Required Fields in Every Header

| Field | What It Contains |
|-------|-----------------|
| `@mechanism` | Short name (used for search) |
| `@description` | What it does in one sentence |
| `@tags` | Comma-separated searchable tags |
| `@input` | Input type + description |
| `@output` | Output type + description |
| `@source` | Which node it came from |
| `@tested` | `true` or `false` |
| `@test-cases` | At least 2 concrete examples |
| `@used-in` | Which nodes currently use it |
| `@quality` | `draft`, `stable`, or `promoted` |

---

## How Claude Searches the Library

Before generating code for any Code Module node, Claude runs this search:

```python
# copilot/mechanism_search.py
import os
import re
from pathlib import Path

def search_mechanisms(tags: list[str], input_type: str, output_type: str) -> list[dict]:
    """
    Search /mechanisms/ for patterns matching the requested tags and types.
    Returns list of matching mechanism metadata + code.
    """
    mechanisms = []
    root = Path("mechanisms")

    for ts_file in root.rglob("*.ts"):
        content = ts_file.read_text()
        header = extract_header(content)

        if not header:
            continue

        # Score by tag overlap
        file_tags = set(t.strip() for t in header.get("tags", "").split(","))
        requested_tags = set(tags)
        overlap = len(file_tags & requested_tags)

        if overlap > 0:
            mechanisms.append({
                "name": header["mechanism"],
                "description": header["description"],
                "tags": header["tags"],
                "input": header["input"],
                "output": header["output"],
                "quality": header["quality"],
                "code": content,
                "score": overlap
            })

    # Sort by relevance score
    return sorted(mechanisms, key=lambda x: x["score"], reverse=True)[:5]


def extract_header(content: str) -> dict | None:
    """Parse the @tag metadata from a mechanism file header."""
    header = {}
    for line in content.split('\n'):
        if line.strip().startswith('* @'):
            parts = line.strip().lstrip('* @').split(' ', 1)
            if len(parts) == 2:
                header[parts[0]] = parts[1]
    return header if header else None
```

### How It Feeds Into Claude's Prompt

```python
def build_code_generation_prompt(form_answers: dict) -> str:
    # Extract likely tags from the form answers
    tags = extract_tags_from_description(form_answers["purpose"])
    matches = search_mechanisms(tags, form_answers["input_description"], form_answers["output_description"])

    mechanism_context = ""
    if matches:
        mechanism_context = "MECHANISM LIBRARY MATCHES:\n"
        for m in matches:
            mechanism_context += f"\n--- {m['name']} ({m['quality']}) ---\n"
            mechanism_context += f"Does: {m['description']}\n"
            mechanism_context += f"Tags: {m['tags']}\n"
            mechanism_context += f"Code:\n{m['code']}\n"
    else:
        mechanism_context = "MECHANISM LIBRARY: No matches found. Write from scratch."

    return SCOPED_CODE_PROMPT.format(
        **form_answers,
        matching_mechanisms=mechanism_context
    )
```

---

## How Mechanisms Get Added (The Post-Test Commit Flow)

When a Code Module node passes all tests and gets promoted to `stable`:

1. The useful sub-functions inside the node code get extracted
2. Each gets a metadata header written (Claude can auto-generate this from the 7-step form answers)
3. Saved to the appropriate `/mechanisms/` subfolder
4. Committed to the repo: `git commit -m "Add mechanism: [name] from [node name]"`

### Auto-Extract Prompt

```
Look at this Code Module node code:
{node_code}

It was built with this purpose: {purpose}
Input: {input_description}
Output: {output_description}

Identify any sub-functions that are general-purpose and reusable (not specific to this
one use case). For each one, write the complete mechanism file with the full @metadata
header. Save path: mechanisms/{category}/{function-name}.ts

Categories: data-transform, api-handling, llm-ops, control-flow, validation, output
```

---

## The `mechanisms/README.md`

Include this at the root of the mechanisms folder:

```markdown
# Mechanism Library

Every file here is a tested, reusable code pattern extracted from working Code Module nodes.

## How to Use
When building a new Code Module node, Claude automatically searches this library.
If it finds a match, it uses the existing code directly instead of rewriting it.

## How to Add
After a node's code passes all tests and reaches "stable" status:
1. Extract general-purpose sub-functions
2. Add the @metadata header (see any existing file for format)
3. Save to the appropriate subfolder
4. Commit: git commit -m "Add mechanism: [name]"

## Categories
- data-transform/ — array operations, field mapping, normalization
- api-handling/ — retry logic, pagination, rate limiting, mocking
- llm-ops/ — text chunking, structured extraction, batch calling
- control-flow/ — gates, timeouts, parallel execution
- validation/ — field checking, URL/JSON validation
- output/ — formatting helpers

## Quality Levels
- draft: built, not thoroughly tested
- stable: passed all test cases
- promoted: used in production, battle-tested
```

---

## Success Criteria

- [ ] `/mechanisms/` folder exists with the category subfolders
- [ ] At least 5 starter mechanisms seeded (flat-array, retry-backoff, chunk-text, validate-url, format-markdown)
- [ ] `search_mechanisms()` returns relevant results for tag queries
- [ ] The mechanism context appears in Claude's code generation prompt
- [ ] When a stable node is built, at least one mechanism is extracted and saved
- [ ] All mechanism files have complete @metadata headers
- [ ] Claude uses an existing mechanism (vs rewriting from scratch) at least once

---

## Protocol Checkpoints (Stage 08 Injection)

### Pulse Checks — After Each File
| File | Assertions |
|------|-----------|
| `mechanisms/README.md` | File exists; contains "How to Use", "How to Add", "Categories", "Quality Levels" sections |
| Each starter mechanism (5 files) | File exists; `@mechanism`, `@tags`, `@input`, `@output`, `@tested`, `@quality` metadata headers all present; exported function has matching name |
| `copilot/mechanism_search.py` | File exists; `search_mechanisms(tags, input_type, output_type)` function defined; `extract_header()` helper present; returns a list |

### Seam Checks — Connection Points
**Seam 1: mechanism files → search_mechanisms()**
- `search_mechanisms(["array", "transform"], "any[][]", "any[]")` returns at least 1 result containing `flatten-array`
- Returned objects have `name`, `description`, `tags`, `code`, `score` keys

**Seam 2: search_mechanisms() → code generation prompt**
- `build_code_generation_prompt()` (or equivalent) includes mechanism search results in the prompt string
- When a match is found, the prompt contains "MECHANISM LIBRARY MATCHES:" followed by mechanism code
- When no match, prompt contains "No matches found. Write from scratch."

**Seam 3: stable node → mechanism extraction**
- After a node passes all tests, the extraction prompt correctly identifies sub-functions
- At least one mechanism file is created with proper metadata header
- New file passes `search_mechanisms()` for its own tags

### Full Checkpoint (Phase 5 Gate)
**Pattern checks (git diff):**
```
Expected new directory: mechanisms/ with category subfolders
Expected new files: mechanisms/README.md, 5 starter .ts files, copilot/mechanism_search.py
No modification to pieces/ or skin/ files.
```

**Functional checks:**
```bash
python -c "
from copilot.mechanism_search import search_mechanisms
results = search_mechanisms(['array', 'transform'], 'any[][]', 'any[]')
assert len(results) > 0, 'No results for array/transform search'
assert results[0]['name'] == 'flatten-array', f'Wrong result: {results[0][\"name\"]}'
print('✓ Mechanism search working')
results2 = search_mechanisms(['retry', 'api'], 'any', 'any')
assert len(results2) > 0, 'No results for retry/api search'
print('✓ Found retry mechanism:', results2[0]['name'])
"
```

**Gate condition:** `search_mechanisms()` returns correct results for at least 2 different category queries. Mechanism context appears in the code generation prompt. PASS or FAIL.

### Violation Rules
| Level | Trigger | Action |
|-------|---------|--------|
| LOW | Search returns mechanisms but score ordering is slightly off | Log, improve scoring later |
| MEDIUM | Metadata header parsing fails for one mechanism file | Fix that file's header format |
| HIGH | `search_mechanisms()` raises exception or returns empty for all queries | Fix extract_header() parsing, verify file format |
| CRITICAL | Mechanism library causes circular imports with flow_generator | Stop — restructure imports before continuing |

### Two-Strike Rule
Max 2 attempts at fixing search failures. If results are still wrong after 2 fixes, stop for human review — the metadata header format or glob pattern may need redesign.
