# Correction Detection Patterns

Linguistic markers for detecting explicit self-corrections in user input. Used by Stage 1, Step 4.

---

## High-Confidence Markers

These almost always indicate the user is correcting a previous statement:

| Marker | Example |
|--------|---------|
| `"actually"` | "I want Google login. Actually, also GitHub login." |
| `"wait"` / `"oh wait"` | "Oh wait, not just email — also SMS." |
| `"no,"` / `"no —"` | "No, not a chat app. More like a task board." |
| `"I mean"` | "I want it in Python. I mean TypeScript." |
| `"scratch that"` | "Add a calendar view. Scratch that, just a list view." |
| `"instead"` | "Instead of Google login, use magic links." |
| `"not X, Y"` / `"not just X"` | "Not just admin users — all users can create projects." |
| `"let me change that"` | "Let me change that — make it a SPA, not multi-page." |
| `"correction:"` / `"edit:"` | Explicit meta-correction labels in pasted notes. |

---

## Medium-Confidence Markers

These may indicate corrections but could also be additive statements. Look for surrounding context:

| Marker | Example | Additive or Corrective? |
|--------|---------|-------------------------|
| `"also"` | "Also add GitHub login" | Additive if new info; corrective if contradicts prior |
| `"I forgot"` / `"oh and"` | "Oh and I forgot — there should be a dashboard" | Usually additive, but record if it contradicts something |
| `"but"` | "I want it simple but also feature-rich" | Tension/contradiction — record both sides |
| `"well,"` | "Well, maybe not three tiers. Just two." | Often a softened correction |
| `"on second thought"` | "On second thought, skip the mobile version" | Almost always a correction |

---

## Contradiction Without Markers

Sometimes the user says X, then later says Y without explicit correction language:

- "I want it to be free" ... (later) ... "Users pay $10/month"
- "No login required" ... (later) ... "Users sign in with Google"

**Rule:** Only record in `explicit_corrections` if the user uses a correction marker. Implicit contradictions (no marker) are preserved in `raw_input` but NOT tagged in `explicit_corrections`. Implicit contradiction resolution is Stage 3's job.

---

## Recording Format

For each detected correction:

```json
{
  "original": "exact phrase or paraphrase of what they first said",
  "correction": "exact phrase or paraphrase of the correction",
  "context": "optional — why they corrected (if they said)"
}
```

**Rules:**
- Keep `original` and `correction` concise — extract the relevant clause, not the full paragraph
- `context` is optional — only include if the user explained why they changed their mind
- Both the original statement AND the correction remain verbatim in `raw_input`
- When in doubt about whether something is a correction, do NOT record it — err on the side of fewer entries
