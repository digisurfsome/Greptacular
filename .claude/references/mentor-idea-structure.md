# Mentor's App Idea Generator Structure

## Source
From mentor's "IDEA CODE: App Idea Generator" prompt. This is the structural framework
for how features should be conceived, scoped, and described before building.

## Key Principles

### 1. Identity Before Features
Every app starts with 4 questions answered:
- **App Name**: Short, memorable
- **One-Line Description**: What it does in one sentence (specific)
- **Target User**: Who is this for? Be specific about their situation
- **Core Problem**: What pain point does this eliminate?

### 2. MVP Scoping Rules
- **Maximum 5 core features** - this is an MVP
- Each feature is **one clear thing**, not multiple things bundled
- Don't include infrastructure features (auth, responsive, dark mode) - those are assumed
- Focus on what makes the app **unique and useful**

### 3. Feature Description Format
Features are described two ways:
1. **Core Features (3-5)**: What the system does (technical capability)
2. **What Users Can Do**: Plain English actions (user perspective)

Example:
- Feature: "Scale recipe servings up or down with auto-calculated ingredients"
- User action: "Adjust serving sizes and see updated measurements"

### 4. Clarification Protocol
- If idea is **vague** → ask 2-3 clarifying questions first
- If idea is **too complex** → help simplify to MVP
- If idea is **clear** → go straight to structured output

### 5. Quality Indicators
**Good input** (specific enough to build):
- "An app for meal planning that suggests recipes based on what's in my fridge"
- "I want to track my guitar practice and see streaks"

**Too vague** (needs clarification):
- "A productivity app"
- "Something with AI"

**Too complex** (needs simplification):
- "A full social network with marketplace, messaging, stories, live streaming"

## How This Maps to AutoForge

### Current AutoForge Spec Format (app_spec.txt)
AutoForge uses XML-formatted specs with features that become "test cases" for the
initializer agent. The initializer creates 165-405+ features across 20 categories.

### What the Mentor's Structure Adds
1. **Force identity clarity BEFORE features** - the spec creation chat should require
   App Name, One-Line Description, Target User, and Core Problem before allowing
   feature definition
2. **MVP gating** - warn when spec has > 5 core features, suggest simplification
3. **Dual description** - each feature gets both a technical description AND a
   plain-English user action (improves verification steps)
4. **Feature atomicity** - enforce one feature = one thing (the initializer already
   breaks features into test cases, but starting atomic is better)
5. **Assumed features** - Auth, responsive, dark mode, error handling should be
   built into the boilerplate, not listed as features

### Integration Points
- `create-spec` slash command → add identity questions first
- `spec_creation.py` WebSocket → enforce the 4 identity fields
- PRD Quality Scoring (from build-intelligence-handoff) → score against these criteria
- Initializer prompt → reference identity when creating features
