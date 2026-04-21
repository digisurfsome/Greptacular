---
description: "Compound Engineering — Add Feature Intake: Analyze existing codebase and capture new feature requirements"
argument-hint: <describe the feature you want to add, or say "interactive" to be guided>
---

# Compound Engineering: Add Feature Intake

**Artifacts Directory**: $ARTIFACTS_DIR
**User Input**: $ARGUMENTS

## Context Loading

Before executing, check if `$ARTIFACTS_DIR/context-packet/` exists. Read any prior outputs if present.

---

## Mode Declaration

You are operating in **Add Feature Mode**. This means: the user has an existing codebase AND wants to add a specific new feature to it. You need to understand both the existing code and the new feature requirements.

State this clearly:
> "Running in Add Feature mode. I'll scan your existing codebase to understand the architecture, then capture your feature requirements and identify integration points."

---

## Process

### Step 1: Scan the Existing Codebase

Perform the same codebase scan as Existing Code mode. Read in this order:

**Project Identity**:
- `package.json` / `requirements.txt` / `Cargo.toml` / `go.mod` / `pyproject.toml`
- `README.md` (first 200 lines)
- Top-level directory structure (1 level deep)

**Architecture**:
- Main entry point (first 100 lines)
- Router/routes file if present
- Config/settings file
- Count files by extension

**Patterns** (critical for feature addition):
- How are existing features structured? (folder-per-feature, layer-based, etc.)
- What patterns do existing components follow? (naming, imports, exports)
- Where do new files typically go based on existing structure?
- What testing patterns exist?

Produce a condensed summary (NOT a full report — just enough for planning):

```
## Existing App Summary
- **What it does**: [1-2 sentences]
- **Stack**: [language, framework, database]
- **Structure pattern**: [how features are organized]
- **Entry points for new features**: [where new routes/components/modules typically go]
- **Test pattern**: [how existing tests are structured, if any]
```

### Step 2: Capture Feature Requirements

Check `$ARGUMENTS` for the feature description. If provided, use it. If not, ask:

> "What feature do you want to add? Describe it in as much detail as you can — what it does, who uses it, what it should look like, and any specific requirements."

### Step 3: Ask Feature-Specific Clarifying Questions

Based on the codebase scan and feature description, ask 3-5 targeted questions. Select from:

**Architecture Fit** (always ask):
- "Based on the existing code structure, this feature would naturally fit in [location]. Does that match your expectation, or did you have a different structure in mind?"

**Component Interactions** (ask if feature touches existing code):
- "This feature will need to interact with [existing component/module]. Are there any constraints on how those should be modified?"

**Acceptance Criteria** (always ask):
- "What does 'done' look like? Give me 2-3 specific things that should work when this feature is complete."

**Data Requirements** (ask if feature involves data):
- "Does this feature need new database tables/models, or does it work with existing data?"

**UI Requirements** (ask if feature has a frontend):
- "Should this follow the existing UI patterns exactly, or is there a different design direction for this feature?"

Do NOT ask more than 5 questions. Skip questions where the answer is obvious from the input.

### Step 4: Identify Risks and Integration Points

Based on your codebase scan and the feature requirements, identify:

**Integration Points** — where the new feature connects to existing code:
- Files that need modification (not just new files)
- Shared utilities or services the feature will use
- Database migrations or schema changes needed
- Route/navigation changes needed

**Risks** — things that could go wrong:
- Conflicts with existing functionality
- Missing dependencies or infrastructure
- Areas where the existing code is fragile or poorly tested
- Performance concerns if the feature adds load

Present these to the user:
> "Here are the integration points and risks I've identified. Flag anything that looks wrong."

### Step 5: Write Context Packet

Create `$ARTIFACTS_DIR/context-packet/context-packet.json`:

```json
{
  "mode": "add-feature",
  "existing_app_summary": {
    "description": "what the app does",
    "structure_pattern": "how features are organized",
    "entry_points": ["where new routes/components go"]
  },
  "tech_stack": {
    "language": "primary language",
    "frontend": "framework or null",
    "backend": "framework or null",
    "database": "type or null",
    "notable_libraries": ["lib1", "lib2"]
  },
  "feature_description": "full description of the new feature",
  "feature_requirements": {
    "must_have": ["requirement 1", "requirement 2"],
    "acceptance_criteria": ["criterion 1", "criterion 2"]
  },
  "integration_points": [
    {
      "file": "path/to/file",
      "change_type": "modify | create | delete",
      "description": "what changes are needed"
    }
  ],
  "risks": [
    {
      "area": "what area",
      "risk": "what could go wrong",
      "severity": "high | medium | low",
      "mitigation": "how to avoid it"
    }
  ],
  "do_not_touch": ["paths or areas to preserve"],
  "codebase_root": "absolute path to project root",
  "captured_at": "ISO 8601 timestamp"
}
```

Ensure the directory exists before writing. Create `$ARTIFACTS_DIR/context-packet/` if needed.

### Step 6: Validate and Signal

Validate:
1. `feature_description` is non-empty
2. `feature_requirements.must_have` has at least 1 item
3. `feature_requirements.acceptance_criteria` has at least 1 item
4. `integration_points` has at least 1 entry
5. `tech_stack.language` is identified

If validation passes, emit:
<promise>INTAKE_COMPLETE</promise>

If validation fails, report what's missing, ask once more, then emit the promise with whatever data was captured.
