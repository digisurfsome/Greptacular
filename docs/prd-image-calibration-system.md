# PRD: Image Generation Calibration System

**Status:** Draft
**Priority:** High
**Route:** `/#/image-lab`
**Backend Prefix:** `/api/image-lab`

---

## 1. Problem Statement

When creating marketing images with AI (models wearing branded shirts, specific ethnicities, professional lighting, logos), the AI gets about 80% of the way there but can't nail the last 20%. The "finite detail" problem.

Manual iteration plateaus. You tell the AI "fix the face," it shifts something else. You tell it "make the logo bigger," and the lighting changes. Each correction drifts the baseline. After 5-10 rounds of back-and-forth, you're stuck at the same quality level, burning API credits and time.

**The root cause:** When you give the AI corrective feedback directly ("that looks wrong, fix it"), it changes its internal defaults. Now you're calibrating against an already-shifted baseline. The corrections compound, the model drifts, and quality stalls.

**What's needed:**

1. An **autonomous generation loop** that generates, evaluates, refines, and regenerates without human intervention -- until the image meets criteria.
2. A **calibration system** (like an audio EQ board) that aligns the AI's idea of "perfect" with the human's idea of "perfect" -- without biasing the generation agent.

---

## 2. Core Design Principle: Stateless Agent, External Calibration

This is the single most important architectural decision in the system. Getting this wrong ruins everything.

### The Anti-Pattern (What NOT To Do)

```
User: "The skin tone is too warm"
Agent: *internally adjusts its concept of skin tone*
Agent: *generates with shifted baseline*
User: "Now it's too cool"
Agent: *shifts again*
Result: Compounding drift. The agent's baseline is now unpredictable.
```

### The Correct Pattern

```
Agent generates with VANILLA DEFAULTS every time (stateless).
Calibration is applied as EXTERNAL PROMPT MODIFIERS after generation.
The agent never "learns" preferences.
Calibration is a separate, transparent layer.

Prompt = Base Template + Criteria + Calibration Modifiers
         (never changes)  (per-job)   (separate layer, human-controlled)
```

**Why this works:** The agent always starts from the same known baseline. Calibration adjustments are additive text injected into the prompt, not behavioral changes to the agent. You can reset calibration to zero and get back to the exact same vanilla output. Reproducible, predictable, debuggable.

---

## 3. Two Types of Corrections

### Hard Constraints (Base Prompt Template)

Non-negotiable requirements that go in the base prompt template. These are binary: either present or not.

| Constraint | Example |
|-----------|---------|
| Ethnicity | "African American male, mid-30s" |
| Gender | "Female" |
| Clothing | "Wearing a navy blue polo shirt with collar" |
| Logo | "Company logo clearly visible on left chest, 3 inches wide" |
| Setting | "Modern office environment with natural lighting" |
| Composition | "Upper body shot, subject centered, slight angle" |
| Exclusions | "No watermark, no extra text, no background people" |

These are NOT calibrated. They're either correct or wrong. If the model generates the wrong ethnicity, that's a prompt template fix, not a calibration adjustment.

### Soft Calibration (EQ Sliders)

The nuanced stuff where the AI gets close but not quite right. These are continuous values on a spectrum.

| Dimension | Range | Low End | High End |
|-----------|-------|---------|----------|
| Face Realism | -5 to +5 | Slightly stylized, soft features | Hyper-realistic pores, texture |
| Skin Tone Accuracy | -5 to +5 | Cooler/lighter shift | Warmer/deeper shift |
| Lighting Mood | -5 to +5 | Flat, even, corporate | Dramatic, directional, cinematic |
| Logo Crispness | -5 to +5 | Subtle, fabric-integrated | Sharp, prominent, high-contrast |
| Pose Naturalness | -5 to +5 | Stiff, posed, stock-photo | Candid, relaxed, natural |
| Background Detail | -5 to +5 | Minimal, clean, blurred | Rich, detailed, contextual |
| Clothing Fit | -5 to +5 | Loose, relaxed fit | Tailored, form-fitting |
| Color Saturation | -5 to +5 | Muted, desaturated palette | Vivid, saturated colors |
| Depth of Field | -5 to +5 | Everything in focus | Strong bokeh, shallow DOF |
| Professional Polish | -5 to +5 | Raw, authentic feel | Magazine-quality retouching |

Each slider value maps to specific prompt modifier text. This mapping is the core of the calibration system.

---

## 4. User Stories

### US-1: First-Time Calibration

> As a marketing manager, I want to generate a test batch of images using vanilla defaults, then adjust sliders until the output matches my brand's visual standards, so I can save this calibration profile and reuse it for all future shoots.

**Acceptance criteria:**
- Can generate an image with zero calibration (vanilla)
- Can adjust individual sliders and see the effect on the next generation
- Can save a named calibration profile
- Can load a saved profile and generate immediately

### US-2: Autonomous Generation Loop

> As a content creator, I want to describe what an image should show, press "Auto-Iterate," and have the system autonomously refine the image until it matches my criteria -- without me touching anything.

**Acceptance criteria:**
- Can enter criteria in plain text
- System generates, self-evaluates, and refines automatically
- Can see each iteration as it happens (live thumbnails)
- System stops when it evaluates the image as meeting criteria
- Can set a max iteration limit (default: 10)
- Can stop the loop manually at any time

### US-3: Post-Loop Calibration Adjustment

> As a brand manager, after the autonomous loop produces its best result, I want to make fine-tuning adjustments via the EQ sliders to close the gap between the AI's "perfect" and my "perfect."

**Acceptance criteria:**
- After auto-iteration completes, sliders are available for adjustment
- Adjusting a slider regenerates with the new calibration applied
- Can compare before/after calibration side by side
- Slider adjustments do NOT affect the autonomous loop's evaluation logic

### US-4: Template Management

> As a team lead, I want to create and save prompt templates for different shoot types (headshots, full-body, product placement), each with their own hard constraints, so the team can generate consistent images.

**Acceptance criteria:**
- Can create named prompt templates with hard constraints
- Can select a template before generating
- Templates are separate from calibration profiles (mix and match)
- Can duplicate and modify existing templates

### US-5: Batch Generation

> As a marketing team member, I want to generate multiple variations from the same criteria + calibration (different poses, angles, or slight variations), so I can pick the best one.

**Acceptance criteria:**
- Can request N variations in one batch (1-8)
- All variations use the same prompt + calibration
- Can select a winner from the batch
- Can regenerate individual images from the batch

### US-6: Image History and Comparison

> As a user, I want to see the full history of generated images for a session, compare any two side by side, and understand what changed between iterations.

**Acceptance criteria:**
- Iteration history shows thumbnails with iteration number
- Can click any thumbnail to view full-size
- Can select two images for side-by-side comparison
- Each image shows the prompt and calibration values used

---

## 5. Architecture Overview

### Where This Lives in AutoForge

This is a new top-level page, like DunkStack or YT Lab. It does NOT live inside a project -- it's a standalone tool.

```
main.tsx:  if (hash === '#/image-lab' || hash.startsWith('#/image-lab/')) {
             return <ImageLabPage />
           }

App.tsx header:  New nav button: ImageLab (Camera icon from Lucide)
```

### System Architecture

```
+------------------------------------------------------------------+
|                        FRONTEND (React)                           |
|                                                                   |
|  ImageLabPage.tsx                                                 |
|  +------------------------------------------------------------+  |
|  |  ImageCanvas    |  CalibrationPanel   |  IterationHistory   |  |
|  |  (current img)  |  (EQ sliders)       |  (thumbnails)       |  |
|  +------------------------------------------------------------+  |
|  |  PromptEditor   |  TemplateSelector   |  ProfileSelector    |  |
|  +------------------------------------------------------------+  |
|                              |                                    |
|                     React Query + WebSocket                       |
+------------------------------------------------------------------+
                               |
                          REST + WS
                               |
+------------------------------------------------------------------+
|                      BACKEND (FastAPI)                             |
|                                                                   |
|  server/routers/image_lab.py     (REST endpoints)                 |
|  server/routers/image_lab.py     (WebSocket for live updates)     |
|                                                                   |
|  server/services/                                                 |
|  +------------------------------------------------------------+  |
|  |  image_lab_service.py                                       |  |
|  |  - Prompt assembly (template + criteria + calibration)      |  |
|  |  - OpenAI API calls (gpt-image-1.5)                        |  |
|  |  - Image evaluation (multimodal: send image back to LLM)   |  |
|  |  - Autonomous loop orchestration                            |  |
|  +------------------------------------------------------------+  |
|  |  image_lab_database.py                                      |  |
|  |  - SQLAlchemy models for profiles, templates, sessions      |  |
|  |  - Image metadata storage                                   |  |
|  +------------------------------------------------------------+  |
|  |  calibration_engine.py                                      |  |
|  |  - Slider value -> prompt modifier text mapping             |  |
|  |  - Profile load/save                                        |  |
|  |  - Modifier composition logic                               |  |
|  +------------------------------------------------------------+  |
+------------------------------------------------------------------+
                               |
                      OpenAI API (external)
                      - gpt-image-1.5 (image generation)
                      - GPT-5.2 or similar (image evaluation)
```

### Key Technology Choices

| Component | Technology | Reason |
|-----------|-----------|--------|
| Image generation | OpenAI `gpt-image-1.5` | Latest model, best quality, text rendering, brand preservation |
| Image evaluation | OpenAI GPT-5.2 (multimodal) | Can see and evaluate generated images against criteria |
| Image storage | Local filesystem + DB metadata | Images saved to `~/.autoforge/image-lab/images/` |
| Real-time updates | WebSocket | Live iteration progress during autonomous loop |
| Database | SQLite (shared with AutoForge) | Calibration profiles, templates, image history |

---

## 6. Detailed Feature Specs

### 6.1 The Prompt Assembly Pipeline

Every generated image uses a prompt built from three layers. These layers NEVER mix. The agent sees one final prompt string but has no awareness of which parts came from where.

```
FINAL PROMPT = BASE_TEMPLATE + CRITERIA + CALIBRATION_MODIFIERS

Layer 1 - BASE_TEMPLATE (hard constraints):
  "Professional marketing photograph. [SUBJECT]. [CLOTHING]. [SETTING].
   [COMPOSITION]. [EXCLUSIONS]. High-quality commercial photography."

Layer 2 - CRITERIA (per-job specifics):
  "African American male, mid-30s, confident smile, wearing navy polo
   with TechCorp logo on left chest, modern open-plan office, upper
   body shot, natural window light from the left."

Layer 3 - CALIBRATION_MODIFIERS (from EQ sliders):
  "Hyper-realistic skin texture with visible pores. Slightly warm
   skin tones. Soft directional lighting with gentle shadows. Logo
   rendered with sharp edges and high contrast. Natural relaxed pose.
   Shallow depth of field with soft bokeh background."
```

**Implementation: `calibration_engine.py`**

The calibration engine maps slider values to prompt text fragments. Each dimension has a lookup table:

```python
CALIBRATION_MAP = {
    "face_realism": {
        -5: "Slightly stylized facial features, soft skin texture",
        -4: "Gently smoothed skin, minimal texture detail",
        -3: "Clean skin with subtle texture",
        -2: "Natural skin with light smoothing",
        -1: "Realistic skin with gentle softening",
         0: "",  # vanilla - no modifier
        +1: "Detailed skin texture, visible pores",
        +2: "High-detail skin with natural imperfections",
        +3: "Hyper-realistic skin texture with visible pores",
        +4: "Photorealistic skin detail, fine wrinkles and texture",
        +5: "Ultra-realistic skin with every pore and micro-texture visible",
    },
    "skin_tone_accuracy": {
        -5: "Noticeably cooler, lighter skin tone shift",
        # ... through to ...
        +5: "Rich, warm, deep skin tones with golden undertones",
    },
    # ... all 10 dimensions
}
```

**Modifier composition:** All non-zero slider values are collected, their text fragments joined with periods, and appended as a paragraph at the end of the prompt. Zero-value sliders contribute nothing (vanilla behavior).

### 6.2 The Autonomous Generation Loop

The loop runs entirely on the backend. The frontend receives WebSocket updates for each iteration.

**Loop Algorithm:**

```
1. ASSEMBLE prompt (template + criteria + calibration modifiers)
2. CALL OpenAI gpt-image-1.5 to generate image
3. SAVE image to disk, record metadata in DB
4. SEND image + original criteria to evaluator LLM (multimodal)
5. EVALUATOR returns structured assessment:
   {
     "overall_match": 0.0-1.0,     // how well it matches criteria
     "issues": [                    // what's wrong
       {"dimension": "logo", "severity": "minor", "description": "Logo slightly too small"},
       {"dimension": "lighting", "severity": "major", "description": "Too flat, needs more direction"}
     ],
     "suggestions": [               // how to fix it
       "Increase logo size specification",
       "Add directional lighting from upper left"
     ],
     "meets_threshold": true/false   // does it pass?
   }
6. IF meets_threshold OR iteration >= max_iterations:
     STOP, present final image to user
7. ELSE:
     REFINE the CRITERIA portion of the prompt based on suggestions
     (NOT the template, NOT the calibration -- only the criteria)
     GO TO step 1
```

**Critical rule:** The loop only modifies the CRITERIA layer. It never touches the base template or calibration modifiers. This means the calibration stays stable across iterations while the loop zeroes in on the specifics.

**Evaluator Prompt:**

```
You are an image quality evaluator for professional marketing photography.

CRITERIA (what was requested):
{criteria_text}

HARD CONSTRAINTS (must be exactly right):
{template_constraints}

Evaluate the attached image against these criteria. Return a JSON object with:
- overall_match: float 0.0-1.0 (1.0 = perfect match)
- issues: array of {dimension, severity, description}
- suggestions: array of strings (specific prompt changes to fix issues)
- meets_threshold: boolean (true if overall_match >= {threshold})

Be precise. Focus on: subject accuracy, clothing/branding, lighting quality,
composition, facial realism, and overall professional quality.
Do NOT comment on artistic style preferences -- only factual accuracy.
```

**Match threshold:** Default 0.85 (configurable). The system considers an image "good enough" at 85% match. The remaining 15% is what calibration sliders handle.

### 6.3 The EQ Calibration Panel

**Visual Design:**

The calibration panel uses vertical sliders arranged side by side, like a physical audio mixing board or parametric EQ. Each slider:

- Has a label at the top (dimension name)
- Shows the current numeric value (-5 to +5)
- Has a center notch at 0 (vanilla)
- Color-coded: blue below center, neutral at center, orange above center
- Dragging updates the value in real-time
- Double-click resets to 0
- Value can also be typed directly (click on the number)

**Slider Dimensions (default set -- users can add custom dimensions later):**

1. **Face Realism** -- stylized vs. hyper-realistic
2. **Skin Tone** -- cooler/lighter vs. warmer/deeper
3. **Lighting Mood** -- flat/even vs. dramatic/directional
4. **Logo Crispness** -- subtle/integrated vs. sharp/prominent
5. **Pose Natural** -- stiff/posed vs. candid/relaxed
6. **Background** -- minimal/blurred vs. detailed/contextual
7. **Clothing Fit** -- loose/relaxed vs. tailored/fitted
8. **Saturation** -- muted/desaturated vs. vivid/saturated
9. **Depth of Field** -- deep (all sharp) vs. shallow (bokeh)
10. **Polish** -- raw/authentic vs. magazine-quality

**Calibration Flow:**

```
1. User starts with all sliders at 0 (vanilla)
2. Generate an image with vanilla defaults
3. User evaluates: "faces look too smooth"
4. User drags Face Realism slider from 0 to +3
5. System regenerates with same criteria + calibration modifier:
   "Hyper-realistic skin texture with visible pores"
6. User evaluates: "better, but skin tone too cool"
7. User drags Skin Tone slider from 0 to +2
8. System regenerates with both modifiers applied
9. Repeat until satisfied
10. Save as "TechCorp Brand Profile"
```

**Calibration Profiles:**

A named, saveable set of slider values. Profiles are independent of templates and criteria. You mix and match:

- Template: "Headshot - Upper Body"
- Profile: "TechCorp Brand Standards"
- Criteria: "Sarah, Marketing VP, red blouse, conference room"

### 6.4 Prompt Template System

Templates define the hard constraints -- the non-negotiable skeleton of the prompt.

**Template Structure:**

```json
{
  "id": "uuid",
  "name": "Professional Headshot",
  "description": "Upper body marketing photo with branded clothing",
  "category": "headshot",
  "template_text": "Professional marketing photograph. {subject_description}. Wearing {clothing_description} with {logo_description}. {setting_description}. {composition_description}. No watermarks, no extra text, no background people. High-quality commercial photography.",
  "variables": [
    {"name": "subject_description", "label": "Subject", "placeholder": "African American male, mid-30s, confident smile"},
    {"name": "clothing_description", "label": "Clothing", "placeholder": "navy blue polo shirt with collar"},
    {"name": "logo_description", "label": "Logo/Branding", "placeholder": "TechCorp logo on left chest, approximately 3 inches wide"},
    {"name": "setting_description", "label": "Setting", "placeholder": "modern open-plan office with natural lighting"},
    {"name": "composition_description", "label": "Composition", "placeholder": "upper body shot, subject centered, slight angle to camera"}
  ],
  "created_at": "2026-03-03T00:00:00Z",
  "updated_at": "2026-03-03T00:00:00Z"
}
```

**Built-in Templates (ship with the system):**

1. **Professional Headshot** -- upper body, branded clothing, office setting
2. **Full Body Brand Photo** -- standing, full outfit visible, environmental setting
3. **Product Placement** -- focus on a product being held/used by a model
4. **Team Photo** -- multiple subjects, consistent styling
5. **Lifestyle Shot** -- casual, authentic, less corporate

Users can create, duplicate, and edit templates. Templates are stored in the database.

---

## 7. API Design

### REST Endpoints

All endpoints under `/api/image-lab`.

#### Image Generation

```
POST /api/image-lab/generate
  Body: {
    "template_id": "uuid" | null,
    "criteria": "string (free-text criteria)",
    "calibration_profile_id": "uuid" | null,
    "calibration_overrides": {"face_realism": 3, "skin_tone": 2, ...} | null,
    "quality": "low" | "medium" | "high",
    "size": "1024x1024" | "1024x1536" | "1536x1024",
    "variations": 1
  }
  Response: {
    "generation_id": "uuid",
    "images": [{
      "id": "uuid",
      "url": "/api/image-lab/images/{id}",
      "prompt_used": "string (the assembled prompt)",
      "calibration_values": {...},
      "created_at": "ISO datetime"
    }]
  }

POST /api/image-lab/auto-iterate
  Body: {
    "template_id": "uuid" | null,
    "criteria": "string",
    "calibration_profile_id": "uuid" | null,
    "calibration_overrides": {...} | null,
    "quality": "low" | "medium" | "high",
    "size": "1024x1024" | "1024x1536" | "1536x1024",
    "max_iterations": 10,
    "match_threshold": 0.85
  }
  Response: {
    "session_id": "uuid",
    "status": "running"
  }
  (Progress delivered via WebSocket)

POST /api/image-lab/auto-iterate/{session_id}/stop
  Response: { "status": "stopped" }

GET /api/image-lab/images/{image_id}
  Response: image file (PNG/JPEG)

GET /api/image-lab/images/{image_id}/metadata
  Response: {
    "id": "uuid",
    "session_id": "uuid",
    "iteration": 1,
    "prompt_used": "string",
    "calibration_values": {...},
    "evaluation": {...} | null,
    "quality": "high",
    "size": "1024x1536",
    "created_at": "ISO datetime",
    "file_size_bytes": 1234567
  }
```

#### Calibration Profiles

```
GET    /api/image-lab/profiles
  Response: [{ "id": "uuid", "name": "string", "values": {...}, "created_at": "...", "updated_at": "..." }]

POST   /api/image-lab/profiles
  Body: { "name": "string", "values": {"face_realism": 3, ...} }
  Response: { "id": "uuid", "name": "...", ... }

GET    /api/image-lab/profiles/{id}
PUT    /api/image-lab/profiles/{id}
DELETE /api/image-lab/profiles/{id}

POST   /api/image-lab/profiles/{id}/duplicate
  Response: new profile with "(Copy)" appended to name
```

#### Prompt Templates

```
GET    /api/image-lab/templates
POST   /api/image-lab/templates
  Body: { "name": "string", "description": "string", "category": "string", "template_text": "string", "variables": [...] }

GET    /api/image-lab/templates/{id}
PUT    /api/image-lab/templates/{id}
DELETE /api/image-lab/templates/{id}

POST   /api/image-lab/templates/{id}/duplicate
```

#### Sessions and History

```
GET /api/image-lab/sessions
  Query: ?limit=20&offset=0
  Response: [{ "id": "uuid", "criteria": "...", "template_name": "...", "profile_name": "...", "image_count": 5, "created_at": "..." }]

GET /api/image-lab/sessions/{id}
  Response: {
    "id": "uuid",
    "criteria": "...",
    "template": {...},
    "calibration_profile": {...},
    "images": [{ iteration, image_id, evaluation, prompt_used, ... }],
    "status": "completed" | "running" | "stopped",
    "created_at": "...",
    "completed_at": "..."
  }

DELETE /api/image-lab/sessions/{id}
```

#### Calibration Dimensions (for custom sliders)

```
GET /api/image-lab/dimensions
  Response: [{ "key": "face_realism", "label": "Face Realism", "description": "...", "is_default": true, "mapping": {...} }]

POST /api/image-lab/dimensions
  Body: { "key": "string", "label": "string", "description": "string", "mapping": {"-5": "text", ..., "5": "text"} }
```

### WebSocket

```
WS /ws/image-lab/{session_id}

Messages from server:
  { "type": "iteration_start", "iteration": 2 }
  { "type": "image_generated", "iteration": 2, "image_id": "uuid", "image_url": "/api/image-lab/images/uuid" }
  { "type": "evaluation_complete", "iteration": 2, "evaluation": { "overall_match": 0.72, "issues": [...], "suggestions": [...] } }
  { "type": "prompt_refined", "iteration": 2, "new_criteria": "..." }
  { "type": "session_complete", "final_image_id": "uuid", "total_iterations": 5 }
  { "type": "session_stopped", "reason": "user" | "max_iterations" | "error" }
  { "type": "error", "message": "..." }
```

---

## 8. UI Layout

### Page Structure

Following `WORKSPACE_STANDARDS.md`, the page uses `h-screen flex flex-col` layout with a breadcrumb bar.

```
+----------------------------------------------------------------------+
| <- AutoForge / Image Lab              [Template v] [Profile v]  [?]  |  Breadcrumb bar (h-10)
+----------------------------------------------------------------------+
| [Generate]  [Auto-Iterate]  [Stop]  [Reset]    Quality:[H] Size:[v]  |  Control strip (h-12)
+----------------------------------------------------------------------+
|                              |                                        |
|                              |   CALIBRATION PANEL                    |
|   MAIN CANVAS                |                                        |
|                              |   Face Realism    [ |  ]  +3           |
|   +------------------------+ |   Skin Tone       [ | ]   +2           |
|   |                        | |   Lighting        [|   ]   0           |
|   |                        | |   Logo Crispness  [ | ]   +2           |
|   |    Current Image       | |   Pose Natural    [|   ]   0           |
|   |    (large preview)     | |   Background      [ |  ]  +1           |
|   |                        | |   Clothing Fit    [|   ]   0           |
|   |                        | |   Saturation      [  |]   -1           |
|   +------------------------+ |   Depth of Field  [ | ]   +1           |
|                              |   Polish          [ | ]   +2           |
|   Prompt:                    |                                        |
|   "African American male..." |   [Save Profile]  [Load Profile]       |
|                              |   [Reset All to 0]                     |
+------------------------------+----------------------------------------+
|                                                                       |
|   ITERATION HISTORY                                                   |
|   [#1 img] [#2 img] [#3 img] [#4 img] [#5 img]     Score: 0.92      |
|   Match: 0.45  0.62   0.78    0.85     0.92          Iterations: 5   |
|                                                                       |
+-----------------------------------------------------------------------+
```

### Component Breakdown

```
ui/src/
  pages/
    ImageLabPage.tsx              -- Top-level page (hash route target)
  components/workspace/
    image-lab/
      ImageCanvas.tsx             -- Large image preview with zoom/pan
      CalibrationPanel.tsx        -- EQ slider board
      CalibrationSlider.tsx       -- Individual vertical slider component
      IterationHistory.tsx        -- Bottom thumbnail strip with scores
      PromptEditor.tsx            -- Text area for criteria input
      TemplateSelector.tsx        -- Dropdown to select prompt template
      TemplateEditor.tsx          -- Modal for creating/editing templates
      ProfileSelector.tsx         -- Dropdown to select calibration profile
      ProfileEditor.tsx           -- Modal for creating/editing profiles
      ImageComparison.tsx         -- Side-by-side image compare view
      GenerationControls.tsx      -- Top control strip (generate, stop, etc.)
      EvaluationPanel.tsx         -- Shows evaluator feedback for current image
      SessionHistory.tsx          -- List of past sessions
  hooks/
    useImageLab.ts                -- React Query hooks for all image lab API calls
  lib/
    api.ts                        -- Add image lab API functions here
    types.ts                      -- Add image lab TypeScript interfaces here
```

### Layout Details

**Left Panel (Main Canvas) -- 60% width:**
- Large image display (fills available space, maintains aspect ratio)
- Below the image: the full assembled prompt (read-only, collapsible)
- When no image generated yet: empty state with Camera icon + "Generate your first image" CTA
- During generation: skeleton loading animation with progress indicator
- Evaluation results shown as an overlay badge (match score percentage)

**Right Panel (Calibration) -- 40% width:**
- Vertical sliders arranged in a row, EQ board style
- Each slider is a thin vertical track (~200px tall)
- Slider labels above, current value below
- Color gradient on the track: blue (negative) through neutral (zero) to orange (positive)
- "Save Profile" and "Load Profile" buttons at the bottom
- "Reset All" button to zero out all sliders
- Collapsible section for "Custom Dimensions" (add your own sliders)

**Bottom Strip (Iteration History) -- fixed height 120px:**
- Horizontal scrollable strip of thumbnail images
- Each thumbnail shows iteration number and match score
- Clicking a thumbnail loads that image into the main canvas
- Current/selected thumbnail has a highlight border
- When in auto-iterate mode, thumbnails appear in real-time as generated
- Right side shows summary stats: total iterations, final score, time elapsed

**Control Strip (Top):**
- **Generate** button (primary) -- single generation
- **Auto-Iterate** button (with play icon) -- start autonomous loop
- **Stop** button (destructive, only visible during auto-iterate)
- **Reset** button (outline) -- clear current session
- **Quality** selector: Low / Medium / High (pill buttons)
- **Size** selector: Square / Portrait / Landscape (pill buttons)
- **Variations** counter: 1-8 (number input, only for manual generate)

### Responsive Behavior

On screens narrower than 1280px, the layout shifts:
- Calibration panel moves to a collapsible side drawer (slide in from right)
- Toggle button appears to show/hide calibration
- Iteration history remains at bottom but with smaller thumbnails

---

## 9. Data Model

### SQLite Tables (in `image_lab_database.py`)

```sql
-- Calibration profiles
CREATE TABLE image_lab_profiles (
    id TEXT PRIMARY KEY,           -- UUID
    name TEXT NOT NULL,
    description TEXT DEFAULT '',
    values TEXT NOT NULL,           -- JSON: {"face_realism": 3, "skin_tone": 2, ...}
    created_at TEXT NOT NULL,       -- ISO datetime
    updated_at TEXT NOT NULL
);

-- Prompt templates
CREATE TABLE image_lab_templates (
    id TEXT PRIMARY KEY,           -- UUID
    name TEXT NOT NULL,
    description TEXT DEFAULT '',
    category TEXT DEFAULT 'general',
    template_text TEXT NOT NULL,    -- The prompt template with {variable} placeholders
    variables TEXT NOT NULL,        -- JSON array of variable definitions
    is_builtin BOOLEAN DEFAULT 0,  -- True for shipped defaults
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- Generation sessions
CREATE TABLE image_lab_sessions (
    id TEXT PRIMARY KEY,           -- UUID
    criteria TEXT NOT NULL,         -- The user's free-text criteria
    template_id TEXT,              -- FK to templates (nullable for freeform)
    profile_id TEXT,               -- FK to profiles (nullable for uncalibrated)
    calibration_values TEXT,        -- JSON snapshot of slider values at generation time
    quality TEXT DEFAULT 'high',
    size TEXT DEFAULT '1024x1536',
    mode TEXT DEFAULT 'manual',     -- 'manual' | 'auto_iterate'
    max_iterations INTEGER DEFAULT 10,
    match_threshold REAL DEFAULT 0.85,
    status TEXT DEFAULT 'running',  -- 'running' | 'completed' | 'stopped' | 'error'
    error_message TEXT,
    created_at TEXT NOT NULL,
    completed_at TEXT,
    FOREIGN KEY (template_id) REFERENCES image_lab_templates(id),
    FOREIGN KEY (profile_id) REFERENCES image_lab_profiles(id)
);

-- Individual generated images
CREATE TABLE image_lab_images (
    id TEXT PRIMARY KEY,           -- UUID
    session_id TEXT NOT NULL,      -- FK to sessions
    iteration INTEGER NOT NULL,    -- 1-based iteration number
    prompt_used TEXT NOT NULL,      -- The complete assembled prompt
    calibration_snapshot TEXT,      -- JSON of calibration values for this specific image
    evaluation TEXT,               -- JSON of evaluator response (null for manual mode)
    overall_match REAL,            -- 0.0-1.0 match score (null for manual)
    file_path TEXT NOT NULL,       -- Path on disk to the image file
    file_format TEXT DEFAULT 'png',
    file_size_bytes INTEGER,
    width INTEGER,
    height INTEGER,
    openai_usage TEXT,             -- JSON of token usage from OpenAI response
    created_at TEXT NOT NULL,
    FOREIGN KEY (session_id) REFERENCES image_lab_sessions(id)
);

-- Custom calibration dimensions (beyond the 10 defaults)
CREATE TABLE image_lab_dimensions (
    key TEXT PRIMARY KEY,          -- e.g. "hair_detail"
    label TEXT NOT NULL,           -- e.g. "Hair Detail"
    description TEXT DEFAULT '',
    mapping TEXT NOT NULL,          -- JSON: {"-5": "text", ..., "5": "text"}
    is_default BOOLEAN DEFAULT 0,
    sort_order INTEGER DEFAULT 0,
    created_at TEXT NOT NULL
);
```

### File Storage

```
~/.autoforge/image-lab/
  images/
    {session_id}/
      iter-001-{uuid}.png
      iter-002-{uuid}.png
      ...
  database.db                     -- SQLite database
```

Images are stored on disk, not in the database. The database stores the path. This keeps the DB lean and makes it easy to browse/export images.

---

## 10. OpenAI API Integration Details

### Image Generation Call

```python
import openai
import base64

async def generate_image(prompt: str, quality: str, size: str) -> tuple[bytes, dict]:
    """Generate an image using OpenAI gpt-image-1.5.

    Returns (image_bytes, usage_info).
    """
    client = openai.AsyncOpenAI()  # Uses OPENAI_API_KEY env var

    response = await client.images.generate(
        model="gpt-image-1.5",
        prompt=prompt,
        n=1,
        size=size,           # "1024x1024", "1024x1536", "1536x1024"
        quality=quality,     # "low", "medium", "high"
        output_format="png",
    )

    # Response contains base64-encoded image data
    image_data = base64.b64decode(response.data[0].b64_json)

    usage = {
        "input_tokens": response.usage.input_tokens if response.usage else None,
        "output_tokens": response.usage.output_tokens if response.usage else None,
    }

    return image_data, usage
```

### Image Evaluation Call

```python
async def evaluate_image(
    image_bytes: bytes,
    criteria: str,
    constraints: str,
    threshold: float
) -> dict:
    """Evaluate a generated image against criteria using multimodal LLM.

    Returns structured evaluation result.
    """
    client = openai.AsyncOpenAI()

    b64_image = base64.b64encode(image_bytes).decode("utf-8")

    response = await client.chat.completions.create(
        model="gpt-5.2",  # Or whatever multimodal model is available
        messages=[
            {
                "role": "system",
                "content": EVALUATOR_SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"CRITERIA:\n{criteria}\n\nCONSTRAINTS:\n{constraints}\n\nTHRESHOLD: {threshold}\n\nEvaluate the attached image.",
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{b64_image}",
                        },
                    },
                ],
            },
        ],
        response_format={"type": "json_object"},
        max_tokens=1000,
    )

    return json.loads(response.choices[0].message.content)
```

### Cost Estimation

Based on OpenAI pricing for gpt-image-1.5 (as of early 2026):

| Quality | Approximate Cost Per Image |
|---------|---------------------------|
| Low | ~$0.02 |
| Medium | ~$0.05 |
| High | ~$0.08 |

Evaluation call (multimodal LLM): ~$0.01-$0.03 per evaluation.

**Per auto-iterate session (10 iterations, high quality):**
- 10 generations: ~$0.80
- 10 evaluations: ~$0.20
- **Total: ~$1.00 per session**

The UI should show running cost estimation during auto-iterate sessions.

---

## 11. Phase Breakdown

### Phase 1: Foundation (Build First)

**Goal:** Single image generation with calibration sliders. No autonomous loop yet.

**Backend:**
- `image_lab_database.py` -- SQLAlchemy models, table creation
- `calibration_engine.py` -- Slider-to-text mapping for all 10 default dimensions
- `image_lab_service.py` -- Prompt assembly (template + criteria + calibration), OpenAI image generation call, image save to disk
- `server/routers/image_lab.py` -- REST endpoints: `POST /generate`, `GET /images/{id}`, profiles CRUD, templates CRUD

**Frontend:**
- `ImageLabPage.tsx` -- Page shell with breadcrumb, route in `main.tsx`
- `ImageCanvas.tsx` -- Image display area with empty state
- `CalibrationPanel.tsx` + `CalibrationSlider.tsx` -- EQ sliders (all 10 default dimensions)
- `PromptEditor.tsx` -- Text input for criteria
- `GenerationControls.tsx` -- Generate button, quality/size selectors
- `useImageLab.ts` -- React Query hooks for generate, profiles, templates

**What works after Phase 1:**
- User types criteria, selects quality/size, hits Generate
- Image appears in canvas
- User adjusts sliders, regenerates
- Can save/load calibration profiles
- Can create/edit prompt templates

### Phase 2: Autonomous Loop

**Goal:** Auto-iterate with live progress updates.

**Backend:**
- Image evaluation via multimodal LLM (evaluate_image function)
- Autonomous loop orchestration (async task with WebSocket updates)
- Criteria refinement logic (parse evaluator suggestions, rewrite criteria)
- Session management (start, stop, track iterations)
- WebSocket endpoint `/ws/image-lab/{session_id}`

**Frontend:**
- `IterationHistory.tsx` -- Bottom thumbnail strip with scores
- Auto-iterate button and stop button in GenerationControls
- WebSocket integration for live iteration updates
- `EvaluationPanel.tsx` -- Show evaluator feedback
- Running cost estimator display

**What works after Phase 2:**
- User hits Auto-Iterate, watches iterations appear live
- Each iteration shows thumbnail + match score
- Loop stops when threshold met or max iterations reached
- Can stop manually
- Full iteration history preserved

### Phase 3: Polish and Power Features

**Goal:** Comparison tools, batch generation, custom dimensions, session history.

**Backend:**
- Batch generation (multiple variations per call)
- Custom calibration dimensions CRUD
- Session history with search/filter
- Image export (download individual or batch as ZIP)

**Frontend:**
- `ImageComparison.tsx` -- Side-by-side comparison mode
- Batch generation UI (request N variations)
- `SessionHistory.tsx` -- Browse past sessions
- Custom dimension editor (add your own EQ sliders)
- Image download/export buttons
- Keyboard shortcuts (similar to main AutoForge app)

### Phase 4: Advanced (Future)

**Goal:** Team features, advanced workflows.

- Reference image upload (show the AI an example of what you want)
- A/B comparison voting (pick best from a set)
- Calibration profile sharing/export
- Multi-image campaigns (generate a series with consistent style)
- Budget management (set spending limits per session)
- Prompt version history (track changes to templates over time)
- Integration with AutoForge projects (generate images for a project's assets)

---

## 12. Edge Cases and Failure Modes

### API Failures

| Failure | Handling |
|---------|---------|
| OpenAI API key missing/invalid | Show clear error on page load: "OpenAI API key not configured. Add OPENAI_API_KEY to your .env file." |
| Rate limit hit during auto-iterate | Pause loop, show retry countdown, auto-resume with exponential backoff |
| Content policy rejection | Show the rejection reason, suggest prompt modifications, skip iteration in loop |
| Network timeout | Retry up to 3 times with increasing delay, then fail the iteration |
| API returns unexpected format | Log the raw response, show generic error, continue loop with next attempt |

### Image Quality Issues

| Issue | Handling |
|-------|---------|
| Evaluator always says "good enough" (match score too generous) | Allow user to lower threshold; show calibration adjustment suggestion |
| Evaluator always says "not good enough" (too strict) | After max_iterations, present best image (highest score) and suggest raising threshold |
| Loop produces images that get WORSE over iterations | Detect score regression (3 consecutive decreases), stop loop, present best-scored image |
| Generated image has wrong aspect ratio | Validate size parameter before sending; display at correct aspect ratio regardless |

### Calibration Edge Cases

| Edge Case | Handling |
|-----------|---------|
| All sliders at extreme values (+5 or -5) | Show a warning: "Extreme calibration values may produce unpredictable results" |
| Conflicting calibration (e.g., "hyper-realistic" + "stylized") | The engine concatenates modifiers; the model resolves conflicts naturally. Show a warning if opposing dimensions are both extreme. |
| Custom dimension text is empty or nonsensical | Validate dimension mapping text is non-empty and at least 10 characters |
| Profile loaded but dimensions changed since save | Ignore unknown dimension keys; set missing dimensions to 0; show info toast |

### Storage and Performance

| Concern | Handling |
|---------|---------|
| Disk space from accumulated images | Show total disk usage in settings; provide "Clean up old sessions" action (delete images older than X days) |
| Large number of sessions slowing DB queries | Index on `created_at`; paginate session list; lazy-load image metadata |
| Concurrent auto-iterate sessions | Limit to 1 active auto-iterate session at a time; queue additional requests |
| Browser tab closed during auto-iterate | Loop continues on backend; reconnecting WebSocket picks up current state |

### Security

| Concern | Handling |
|---------|---------|
| Prompt injection via criteria text | Criteria goes directly to OpenAI, which has its own content filtering. No system prompt injection risk because criteria is a separate layer. |
| API key exposure | Key stored in server-side .env, never sent to frontend. All API calls go through backend. |
| Image content moderation | OpenAI enforces its own content policy. Log rejections for the user. |
| Path traversal in image storage | All image paths are generated server-side using UUIDs. No user input in file paths. |

---

## 13. Configuration

### Environment Variables

Add to `~/.autoforge/.env`:

```bash
# Required for Image Lab
OPENAI_API_KEY=sk-...

# Optional overrides
IMAGE_LAB_MODEL=gpt-image-1.5          # Image generation model
IMAGE_LAB_EVALUATOR_MODEL=gpt-5.2      # Evaluation model (multimodal)
IMAGE_LAB_DEFAULT_QUALITY=high          # Default quality: low, medium, high
IMAGE_LAB_DEFAULT_SIZE=1024x1536        # Default size
IMAGE_LAB_MAX_ITERATIONS=10             # Max auto-iterate iterations
IMAGE_LAB_MATCH_THRESHOLD=0.85          # Default match threshold
IMAGE_LAB_STORAGE_DIR=                  # Override image storage path (default: ~/.autoforge/image-lab/)
```

### Settings UI Integration

Add an "Image Lab" section to the existing SettingsModal.tsx with:
- OpenAI API key input (masked)
- Default quality selector
- Default size selector
- Max iterations slider
- Match threshold slider
- Storage location display + disk usage

---

## 14. Success Metrics

How do you know this system is working:

1. **Calibration convergence** -- After 3-5 slider adjustments, the user says "that's what I want." If it takes 15+ adjustments, the dimension mappings need better text.

2. **Auto-iterate effectiveness** -- The autonomous loop should reach the match threshold in 5 or fewer iterations for 80% of requests. If it regularly hits max_iterations without converging, the evaluator prompt or criteria refinement logic needs tuning.

3. **Profile reusability** -- A saved calibration profile should produce consistent results across different criteria. If loading "TechCorp Brand Profile" gives wildly different quality for different subjects, the calibration dimensions are too coupled to specific content.

4. **Baseline stability** -- With all sliders at 0, two generations of the same criteria should produce images of comparable quality and style (not identical, but recognizably consistent). If vanilla outputs are erratic, the base template needs work.

5. **Cost efficiency** -- Average auto-iterate session should cost under $1.50. If costs are regularly above $3, the evaluator is being too strict or the criteria refinement is ineffective.

---

## 15. Glossary

| Term | Definition |
|------|-----------|
| **Vanilla defaults** | Generation with all calibration sliders at 0 -- no modifiers applied. The AI's unbiased baseline. |
| **Calibration profile** | A saved set of slider values that encode a human's visual preferences. Applied as external prompt modifiers. |
| **Hard constraint** | A non-negotiable requirement (ethnicity, clothing, logo) that goes in the base prompt template. Binary: present or absent. |
| **Soft calibration** | A nuanced preference (face realism, lighting mood) controlled by EQ sliders. Continuous: ranges from -5 to +5. |
| **Match threshold** | The minimum `overall_match` score (0.0-1.0) an image must achieve for the autonomous loop to consider it "good enough." |
| **Criteria** | The user's free-text description of what the specific image should show. Changes per image. |
| **Template** | A reusable prompt skeleton with variable placeholders for hard constraints. |
| **Evaluator** | A multimodal LLM that looks at a generated image and scores how well it matches the criteria. |
| **Iteration** | One cycle of generate-evaluate-refine in the autonomous loop. |
| **EQ board** | The calibration slider panel, visually modeled after an audio equalizer mixing board. |

---

## 16. References

- [OpenAI Image Generation API Guide](https://developers.openai.com/api/docs/guides/image-generation)
- [OpenAI Images API Reference](https://developers.openai.com/api/reference/resources/images/)
- [GPT Image 1.5 Prompting Guide (OpenAI Cookbook)](https://cookbook.openai.com/examples/multimodal/image-gen-1.5-prompting_guide)
- [GPT Image 1.5 Model Documentation](https://platform.openai.com/docs/models/gpt-image-1.5)
- [Idea2Img: Iterative Self-Refinement with GPT-4V for Automatic Image Design and Generation](https://idea2img.github.io/)
- [Iterative Refinement Improves Compositional Image Generation (arXiv)](https://arxiv.org/abs/2601.15286)
- [AWS Evaluator Reflect-Refine Loop Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/agentic-ai-patterns/evaluator-reflect-refine-loop-patterns.html)
- [Slider UI Design Best Practices (NN/g)](https://www.nngroup.com/articles/gui-slider-controls/)
- [Sliders, Knobs, and Matrices: Balancing Exploration and Precision (NN/g)](https://www.nngroup.com/articles/sliders-knobs/)
- AutoForge `ui/WORKSPACE_STANDARDS.md` -- UI build standards for new pages
- AutoForge `server/routers/__init__.py` -- Router registration pattern
- AutoForge `ui/src/main.tsx` -- Hash-based routing pattern
