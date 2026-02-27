# PRD: Intelligent Model Routing & Role Attachments

## Overview
Each step in a strategy can be assigned a specific AI model and a role that shapes the agent's behavior. The system intelligently routes tasks to the right model tier based on complexity, and roles provide domain-specific system prompts.

## Model Routing

### Available Models (via AutoForge Subscription)
| Model | Best For | Cost Tier |
|-------|----------|-----------|
| Opus 4.6 | Complex reasoning, strategy creation, ad copy, competitive analysis | High |
| Sonnet 4.6 | Medium tasks, form filling, structured data extraction, navigation | Medium |
| Haiku 4.5 | Simple tasks, data gathering, copy/paste, basic research, OCR | Low |

### Per-Step Model Selection
In the strategy builder, each step has a model dropdown:
```
┌─────────────────────────────────────────┐
│ Step 3: Competitive Research            │
│ Model: [Sonnet 4.6 ▾]                  │
│        ├─ Opus 4.6 (Heavy thinking)     │
│        ├─ Sonnet 4.6 (Balanced) ✓       │
│        ├─ Haiku 4.5 (Fast & light)      │
│        └─ Auto (let system decide)      │
└─────────────────────────────────────────┘
```

### Auto-Routing Logic
When set to "Auto", the system picks the model based on step characteristics:
```python
def select_model(step: YTStrategyStep) -> str:
    # Opus: strategy creation, writing, analysis, complex reasoning
    if any(kw in step.title.lower() for kw in ['strategy', 'create', 'write', 'analyze', 'design', 'brand']):
        return 'opus-4-6'

    # Haiku: simple data gathering, navigation, copy/paste
    if any(kw in step.title.lower() for kw in ['list', 'find', 'search', 'gather', 'collect', 'navigate']):
        return 'haiku-4-5'

    # Sonnet: default for everything else
    return 'sonnet-4-6'
```

### Subscription-Based Access
- Models accessed through AutoForge's existing subscription piping
- No raw API keys needed for the agent execution
- The 200K context window models work for all strategy steps
- 1M context only needed if we're feeding entire codebases (not this use case)

## Role Attachments

### Concept
Roles are system prompts that shape HOW the agent approaches a step. They come from the existing Role Library (`/#/roles`) in AutoForge.

### Default Roles for Strategy Lab

**Researcher**
```
You are a meticulous research analyst. Your job is to gather comprehensive data,
identify patterns, and document everything thoroughly. Be exhaustive in your search.
Don't stop at surface-level information - dig deeper. Organize findings in clear
categories with supporting evidence.
```

**Marketer**
```
You are a direct response marketing expert. Everything you create should drive action.
Use proven frameworks: AIDA, PAS, urgency, scarcity, social proof. Write copy that
converts. Think about the customer's pain points and desires. Every headline should
stop the scroll. Every CTA should be clear and compelling.
```

**Designer**
```
You are a brand-focused creative director. Maintain strict adherence to brand guidelines.
Every visual element should be consistent - colors, typography, spacing, tone. Create
assets that look like they came from a premium agency. Quality over quantity.
```

**Analyst**
```
You are a strategic business analyst. Extract patterns, identify opportunities, and
think about scalability. When looking at data, don't just report what you see - interpret
what it means for the business. Create frameworks and systems, not just lists.
```

**Outreach Specialist**
```
You are a professional business development representative. Your messages should be
personalized, warm but professional, and value-first. Don't be pushy. Lead with what
you can do for them, not what you're selling. Research each prospect before reaching out.
```

**Full-Stack Operator**
```
You are a versatile agency operator who can handle any task. You adapt your approach
based on what's needed - research, creative, analytical, or outreach. You think about
the full pipeline: how does this step feed into the next one? What context will the
next step need from your output?
```

### Per-Step Role Assignment
```
┌─────────────────────────────────────────┐
│ Step 2: Competitive Research            │
│ Model: [Sonnet 4.6 ▾]                  │
│ Role:  [Researcher ▾]                  │
│        ├─ Researcher ✓                  │
│        ├─ Marketer                      │
│        ├─ Designer                      │
│        ├─ Analyst                       │
│        ├─ Outreach Specialist           │
│        ├─ Full-Stack Operator           │
│        ├─ Custom (from Role Library)... │
│        └─ None (no role)                │
└─────────────────────────────────────────┘
```

### Custom Roles
Users can create custom roles in the Role Library and they appear in the step role dropdown. This is already built in AutoForge at `/#/roles`.

### Role + Model Combination
The execution engine combines the role system prompt with the step prompt:
```python
def build_step_message(step, role, previous_outputs):
    system_prompt = role.system_prompt if role else ""

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"""
{step.prompt}

## Context from Previous Steps
{format_previous_outputs(previous_outputs)}

## Brand Guidelines
{project.brand_guide if project.brand_guide else "None set"}

## Expected Output
{step.expectedOutput}
"""}
    ]
```

## Settings Panel Integration
Global defaults configurable in Settings:
- Default model for new steps
- Default role for new steps
- Cost tracking / budget limits per project
- Auto-routing enabled/disabled

## SaaS Considerations
For the future SaaS version:
- Free tier: Haiku only, 3 steps per project
- Pro tier: All models, unlimited steps, auto-routing
- Enterprise: Custom roles, team sharing, priority execution

## Success Criteria
- Users can set model + role per step
- Auto-routing picks sensible defaults
- Role system prompts measurably improve output quality
- No API key management needed (subscription-based)
- Custom roles from Role Library appear in dropdown
- Cost tracking shows estimated/actual spend per project
