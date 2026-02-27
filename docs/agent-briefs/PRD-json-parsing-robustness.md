# PRD: Fix YT Lab JSON Parsing Robustness + Add Diagnostic Logging

> **Priority:** High — blocks normal usage
> **Complexity:** Medium — JSON repair logic + logging throughout pipeline
> **Root Cause:** Claude returns malformed/creative JSON that the parser can't handle

---

## Problem

When YT Lab processing runs, Claude sometimes returns JSON that is:
1. **Syntactically broken** — e.g. `"prompt","conductingPrompting"` (missing colon/value)
2. **Wrong key names** — `"Project"` instead of `"project"`, `"Frame"` instead of `"name"`
3. **Truncated** — response cut off before the closing `}`

The current `_parse_ai_response()` method tries 3 strategies (direct parse, strip fences, find braces) but ALL require the JSON to be syntactically valid. If it's not, the user gets a raw error with no way to debug what happened.

Additionally, when the SDK call fails and falls back to API key billing, the **actual SDK error is silently swallowed** — the user just sees "SDK unavailable" with no details about WHY.

### Error from user's screenshot:
```
AI response was not valid JSON: Could not extract JSON from response.
Preview: {"Project":{"Frame":"AI Prompt Morpher - 4 Disciplines Framework App",
"Name":"AI Productivity / Prompt Engineering","description":"...","prompt",
"conductingPrompting","TimeStamp"...
```

The JSON has `"prompt","conductingPrompting"` which is a syntax error (looks like the model tried to make an array but forgot the brackets), and uses capitalized keys.

---

## Solution

### 1. Add JSON Repair to `_parse_ai_response()` (both yt_processor.py AND yt_discovery.py)

After the 3 existing parse attempts fail, add a 4th attempt that tries to repair common issues:

```python
# Try 4: Attempt basic JSON repair for common LLM mistakes
import re

def _try_repair_json(text: str) -> dict | None:
    """Attempt to repair common JSON issues from LLM output."""
    repaired = text

    # Fix trailing commas before } or ]
    repaired = re.sub(r',\s*([}\]])', r'\1', repaired)

    # Fix missing values: "key","nextkey" -> "key":"","nextkey"
    # Pattern: "word" immediately followed by comma and another "word"
    repaired = re.sub(r'"(\w+)"\s*,\s*"(\w+)"\s*,', r'"\1":"","\2",', repaired)
    repaired = re.sub(r'"(\w+)"\s*,\s*"(\w+)"\s*}', r'"\1":"","\2":""}', repaired)

    # Fix single quotes to double quotes
    # (only outside of already-double-quoted strings)

    # Try parsing the repaired version
    try:
        return json.loads(repaired)
    except (json.JSONDecodeError, ValueError):
        pass

    # If still failing, try truncating at the last valid closing brace
    # (handles responses cut off mid-stream)
    for i in range(len(repaired) - 1, 0, -1):
        if repaired[i] == '}':
            try:
                return json.loads(repaired[:i+1])
            except (json.JSONDecodeError, ValueError):
                continue

    return None
```

### 2. Add Case-Insensitive Key Normalization

After successful JSON parsing (in the validation section around line 400), normalize keys to lowercase:

```python
def _normalize_keys(obj):
    """Recursively lowercase all dictionary keys."""
    if isinstance(obj, dict):
        return {k.lower(): _normalize_keys(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_normalize_keys(item) for item in obj]
    return obj

result = _normalize_keys(result)
```

This handles `"Project"` → `"project"`, `"Name"` → `"name"`, `"Frame"` → `"frame"`, etc.

Then also map known wrong key names:
```python
# Map common AI-generated key variations to expected names
KEY_ALIASES = {
    "frame": "name",        # AI sometimes uses "Frame" for project name
    "niche_area": "niche",
    "step_title": "title",
    "expected_result": "expectedOutput",
    "expected_output": "expectedOutput",
    "enhancement": "notes",
    "enhancement_notes": "notes",
}
```

### 3. Add Diagnostic Logging Throughout the Pipeline

In BOTH `yt_processor.py` and `yt_discovery.py`:

**a) Make SDK errors visible to the user:**

Find the except block that catches SDK errors (~line 319 in processor, ~line 358 in discovery):
```python
# BEFORE (error swallowed):
except Exception as cli_err:
    logger.info("Claude SDK unavailable (%s), falling back to Anthropic SDK", cli_err)
    log("SDK unavailable — falling back to API key billing...")

# AFTER (error visible):
except Exception as cli_err:
    logger.warning("Claude SDK failed: %s", cli_err)
    log(f"SDK failed: {cli_err}")
    log("Falling back to API key billing...")
```

**b) Log the raw response length and first 200 chars on success:**

After getting `raw_text` from either SDK or API, before parsing:
```python
log(f"Got response: {len(raw_text):,} chars")
logger.info("Raw response preview (first 500 chars): %s", raw_text[:500])
```

**c) Log which parse strategy succeeded:**

Add a log message in each try block of `_parse_ai_response`:
```python
# Try 1:
logger.info("JSON parse: direct parse succeeded")
# Try 2:
logger.info("JSON parse: markdown fence extraction succeeded")
# Try 3:
logger.info("JSON parse: brace extraction succeeded")
# Try 4 (new):
logger.info("JSON parse: repair succeeded")
```

**d) Log the full raw response on parse failure (not just 500 chars):**

Change the error handler to log more context:
```python
except (json.JSONDecodeError, ValueError) as exc:
    logger.error("Failed to parse AI response as JSON: %s", exc)
    logger.error("Full raw AI response (%d chars):\n%s", len(raw_text), raw_text[:5000])
    log(f"JSON parse failed — response was {len(raw_text):,} chars. See server logs for full output.")
    raise ValueError(f"AI response was not valid JSON: {exc}")
```

### 4. Add a Retry on Parse Failure

If JSON parsing fails, retry the API call ONCE with a stronger instruction prepended:

```python
RETRY_PREFIX = "IMPORTANT: Your previous response was not valid JSON. You MUST respond with ONLY a JSON object. No text before or after. Start with { and end with }. Use the EXACT key names from the schema (lowercase: project, steps, name, niche, description, etc).\n\n"
```

This gives the model a second chance instead of immediately failing the user.

---

## Files to Modify

| File | Changes |
|------|---------|
| `server/services/yt_processor.py` | JSON repair, key normalization, diagnostic logging, retry logic |
| `server/services/yt_discovery.py` | Same changes (both services have identical parse/call patterns) |

**No frontend changes needed** — this is all backend resilience.

---

## Agent Handoff

```
## MANDATORY: Context Efficiency Rules
1. Read `AGENT_BRIEFING.md` first
2. Read `docs/agent-briefs/yt-lab-discovery.md` second
3. Read ONLY the two files you will modify

## Your Task

Fix JSON parsing robustness and add diagnostic logging in YT Lab's processing
and discovery services. The AI sometimes returns malformed JSON (syntax errors,
wrong key names, truncated responses) and the parser gives up immediately.
The SDK error path also silently swallows the actual error message.

Both files have IDENTICAL patterns — every change you make in one, make in the other.

## Files You Will Modify
- server/services/yt_processor.py
- server/services/yt_discovery.py

## Changes Required (apply to BOTH files)

### Change 1: Add JSON repair as Try 4 in _parse_ai_response()
After the existing 3 parse attempts (direct, fence strip, brace extract), add:
- Fix trailing commas before } or ]
- Fix missing values: "key","nextkey" patterns
- Try truncating at last valid closing brace for cut-off responses
- Log which strategy succeeded

### Change 2: Add key normalization after successful parse
- Recursively lowercase all dict keys
- Map known wrong key names to expected names:
  "frame" -> "name", "niche_area" -> "niche", "step_title" -> "title",
  "expected_result" -> "expectedOutput", "expected_output" -> "expectedOutput",
  "enhancement" -> "notes", "enhancement_notes" -> "notes"
- Apply BEFORE the key validation check

### Change 3: Make SDK errors visible
In the except block around line 319 (processor) / 358 (discovery):
- Change log() to include the actual error: log(f"SDK failed: {cli_err}")
- Change logger.info to logger.warning

### Change 4: Add diagnostic logging
- Log raw response length + first 500 chars after receiving response
- Log which parse strategy succeeded
- On parse failure, log up to 5000 chars of raw response (not just 500)
- Send a user-visible log with response char count on failure

### Change 5: Add one retry on parse failure
If _parse_ai_response fails, retry the Claude call ONCE with a prefix message:
"IMPORTANT: Your previous response was not valid JSON. Respond with ONLY a JSON
object starting with { and ending with }. Use exact lowercase key names from schema."
Log that a retry is happening so the user can see it.

## Do NOT Change
- Default model settings (leave Opus as default — that's intentional)
- Frontend code
- Any other files

## Acceptance Criteria
- Malformed JSON like {"Project":{"Frame":"..."}} parses successfully via repair + key normalization
- SDK errors show the actual error message in the UI log, not just "SDK unavailable"
- Parse failures log the full response to server logs for debugging
- One automatic retry happens before giving up on bad JSON
- All changes applied to BOTH yt_processor.py AND yt_discovery.py identically
```

---

## Why This Fixes It

The user's specific error (`"prompt","conductingPrompting"`) is a missing-value pattern that the JSON repair catches. The `"Project"` vs `"project"` issue is caught by key normalization. And even if repair fails, the retry gives Claude a second shot with stronger formatting instructions. The diagnostic logging means next time something unexpected happens, we can see exactly what Claude returned instead of guessing.
