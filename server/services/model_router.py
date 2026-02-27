"""
Model Router Service
====================

Provides intelligent auto-routing of AI models based on step characteristics.
Used by the YT Strategy Lab to select the optimal model tier (Opus/Sonnet/Haiku)
for each step in a strategy workflow.

Also provides default role system prompts for common agent personas.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Model Constants
# ---------------------------------------------------------------------------

MODEL_OPUS = "claude-opus-4-6"
MODEL_SONNET = "claude-sonnet-4-6"
MODEL_HAIKU = "claude-haiku-4-5"

# Keywords that indicate a step needs Opus (complex reasoning, creative work)
OPUS_KEYWORDS = frozenset({"strategy", "create", "write", "analyze", "design", "brand"})

# Keywords that indicate a step can use Haiku (simple data gathering)
HAIKU_KEYWORDS = frozenset({"list", "find", "search", "gather", "collect", "navigate"})


def select_model(step_title: str) -> str:
    """Pick the optimal model based on step title keywords.

    Args:
        step_title: The title of the strategy step.

    Returns:
        Model identifier string (e.g. "claude-opus-4-6").
    """
    title_lower = step_title.lower()

    if any(kw in title_lower for kw in OPUS_KEYWORDS):
        return MODEL_OPUS

    if any(kw in title_lower for kw in HAIKU_KEYWORDS):
        return MODEL_HAIKU

    return MODEL_SONNET


def get_model_label(model_id: str) -> str:
    """Return a human-readable label for a model ID."""
    labels = {
        MODEL_OPUS: "Opus 4.6 (Heavy thinking)",
        MODEL_SONNET: "Sonnet 4.6 (Balanced)",
        MODEL_HAIKU: "Haiku 4.5 (Fast & light)",
    }
    return labels.get(model_id, model_id)


# ---------------------------------------------------------------------------
# Default Role System Prompts
# ---------------------------------------------------------------------------

DEFAULT_ROLES: dict[str, str] = {
    "researcher": (
        "You are a meticulous research analyst. Your job is to gather comprehensive data, "
        "identify patterns, and document everything thoroughly. Be exhaustive in your search. "
        "Don't stop at surface-level information - dig deeper. Organize findings in clear "
        "categories with supporting evidence."
    ),
    "marketer": (
        "You are a direct response marketing expert. Everything you create should drive action. "
        "Use proven frameworks: AIDA, PAS, urgency, scarcity, social proof. Write copy that "
        "converts. Think about the customer's pain points and desires. Every headline should "
        "stop the scroll. Every CTA should be clear and compelling."
    ),
    "designer": (
        "You are a brand-focused creative director. Maintain strict adherence to brand guidelines. "
        "Every visual element should be consistent - colors, typography, spacing, tone. Create "
        "assets that look like they came from a premium agency. Quality over quantity."
    ),
    "analyst": (
        "You are a strategic business analyst. Extract patterns, identify opportunities, and "
        "think about scalability. When looking at data, don't just report what you see - interpret "
        "what it means for the business. Create frameworks and systems, not just lists."
    ),
    "outreach_specialist": (
        "You are a professional business development representative. Your messages should be "
        "personalized, warm but professional, and value-first. Don't be pushy. Lead with what "
        "you can do for them, not what you're selling. Research each prospect before reaching out."
    ),
    "full_stack_operator": (
        "You are a versatile agency operator who can handle any task. You adapt your approach "
        "based on what's needed - research, creative, analytical, or outreach. You think about "
        "the full pipeline: how does this step feed into the next one? What context will the "
        "next step need from your output?"
    ),
}

# Mapping from role key to display label
ROLE_LABELS: dict[str, str] = {
    "researcher": "Researcher",
    "marketer": "Marketer",
    "designer": "Designer",
    "analyst": "Analyst",
    "outreach_specialist": "Outreach Specialist",
    "full_stack_operator": "Full-Stack Operator",
}


def get_role_system_prompt(role_key: str) -> str:
    """Return the system prompt for a built-in role, or empty string if not found."""
    return DEFAULT_ROLES.get(role_key, "")


def list_default_roles() -> list[dict[str, str]]:
    """Return all default roles as a list of {key, label, system_prompt} dicts."""
    return [
        {"key": k, "label": ROLE_LABELS[k], "system_prompt": v}
        for k, v in DEFAULT_ROLES.items()
    ]
