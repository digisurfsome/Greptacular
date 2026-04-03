# Ambiguity Resolution Rules

> Stage 3 must resolve or flag every ambiguity before passing output to Stage 4.
> Unresolved ambiguity causes downstream mechanism extraction to split or miss concepts.

## Rule 1: Later Statements Override Earlier Ones

If the user said something, then later contradicted it, the LATER statement wins.

**Example:**
- Early: "This is for enterprise teams"
- Later: "Actually, I'm targeting freelancers"
- Resolution: Target user is freelancers

**Log as:**
```json
{
  "ambiguity": "Target user: 'enterprise teams' vs 'freelancers'",
  "resolution": "Freelancers — later statement overrides earlier",
  "source": "Chronological ordering in combined_raw"
}
```

## Rule 2: Explicit Corrections Always Win

Entries in `stage_1.explicit_corrections` are pre-identified contradictions. Always apply the corrected version.

**Log as:**
```json
{
  "ambiguity": "[original statement]",
  "resolution": "[corrected statement]",
  "source": "Explicit correction from Stage 1"
}
```

## Rule 3: Merge Duplicate Concepts

If the user described the same feature two different ways, unify them into one description that captures both phrasings.

**Example:**
- "Users can drag tasks between columns" AND "There's a board where you move items through stages"
- Resolution: One concept — kanban board with drag-and-drop task movement

**Log as:**
```json
{
  "ambiguity": "Two descriptions of the same feature: drag-between-columns and board-with-stages",
  "resolution": "Unified as kanban board with drag-and-drop task movement between status columns",
  "source": "Both descriptions reference the same UI pattern"
}
```

## Rule 4: Separate Bundled Concepts

If the user lumped two distinct things together, acknowledge both but keep them logically separate in the structured output.

**Example:**
- "I want a dashboard with charts and also a way to export reports"
- These are two separate concepts: dashboard visualization and report export

**Do NOT merge them. Do NOT decompose them into mechanisms (that's Stage 4). Mention both in the relevant section as related but distinct capabilities.**

## Rule 5: Unresolvable Ambiguities

If an ambiguity CANNOT be resolved from available information:

1. Do NOT guess
2. Log it with a specific question for the human
3. Use the most conservative interpretation for structuring

**Log as:**
```json
{
  "ambiguity": "User mentions both B2B and B2C use cases with equal emphasis",
  "resolution": "Cannot resolve — both appear equally intended. Structured with B2B as primary based on team features, but this needs confirmation.",
  "source": "unresolvable — needs human input: Is your primary market B2B (teams/companies) or B2C (individual users)?"
}
```

**Threshold:** If more than 3 unresolvable ambiguities affect core identity (product name, target user, or primary problem), trigger the escape hatch.

## Rule 6: Gap Answers Override Raw Input

If a gap question in Stage 2 asked about something vague in the raw input, and the user gave a specific answer, the gap answer is authoritative.

**Example:**
- Raw: "Some kind of login"
- Gap answer: "Email/password and Google OAuth"
- Resolution: Auth is email/password + Google OAuth

## Priority Order

When rules conflict:
1. Explicit corrections (Rule 2) — highest priority
2. Gap answers (Rule 6)
3. Later statements (Rule 1)
4. Merge duplicates (Rule 3)
5. Separate bundles (Rule 4)
6. Flag unresolvable (Rule 5) — last resort
