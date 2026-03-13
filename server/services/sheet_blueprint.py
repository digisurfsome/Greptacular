"""Blueprint Engine — transforms YTStrategyStep[] → SheetBlueprint.

Pipeline:
  [1] filter_and_validate()       [ROBOT]
  [2] classify_step()             [ROBOT]
  [3] detect_apis()               [ROBOT]
  [4] research_api_pricing()      [AGENT] — Sonnet + WebSearch researches pricing
  [5] extract_user_variables()    [ROBOT]
  [6] compute_input_source()      [ROBOT]
  [6.5] early_report              [ROBOT+AGENT] — consulting report emitted via SSE
  [7] convert_prompts()           [AGENT] — Claude Sonnet rewrites prompts
  [8] assemble_blueprint()        [ROBOT]
"""

from __future__ import annotations

import logging
import re
import uuid
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from ..services.api_research import BlueprintAPIResearch

from ..models.tool_factory import (
    ChainConfigRow,
    DetectedAPI,
    IngestionSource,
    SheetBlueprint,
    StepType,
    ThemeConfig,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# [ROBOT] Step Classification Signals
# ---------------------------------------------------------------------------

ACTION_SIGNALS = [
    "upload", "send", "deploy", "publish", "post to", "push to",
    "submit", "create campaign", "launch", "import to", "export to",
    "sync", "connect to", "integrate with", "call api", "webhook",
]

MANUAL_SIGNALS = [
    "review", "approve", "select", "decide", "choose", "manually",
    "hand-pick", "curate", "evaluate", "compare and pick", "sign off",
]

GENERATION_SIGNALS = [
    "generate", "create", "write", "build", "design", "draft",
    "compose", "produce", "make", "craft", "develop", "format",
]


# ---------------------------------------------------------------------------
# [ROBOT] API Detection Patterns (13 services)
# ---------------------------------------------------------------------------

API_PATTERNS: dict[str, dict] = {
    "openai": {
        "patterns": ["gpt", "openai", "chatgpt", "dall-e", "whisper"],
        "service_name": "OpenAI",
        "signup_url": "https://platform.openai.com/api-keys",
        "env_vars": ["OPENAI_API_KEY"],
    },
    "anthropic": {
        "patterns": ["claude", "anthropic"],
        "service_name": "Anthropic (Claude)",
        "signup_url": "https://console.anthropic.com/",
        "env_vars": ["ANTHROPIC_API_KEY"],
    },
    "meta_marketing": {
        "patterns": ["facebook ads", "meta ads", "instagram ads", "meta campaign", "meta marketing"],
        "service_name": "Meta Marketing API",
        "signup_url": "https://developers.facebook.com/",
        "env_vars": ["META_APP_ID", "META_APP_SECRET", "META_ACCESS_TOKEN"],
    },
    "google_ads": {
        "patterns": ["google ads", "adwords", "ppc campaign"],
        "service_name": "Google Ads",
        "signup_url": "https://ads.google.com/",
        "env_vars": ["GOOGLE_ADS_CLIENT_ID", "GOOGLE_ADS_CLIENT_SECRET"],
    },
    "phantombuster": {
        "patterns": ["phantombuster", "phantom"],
        "service_name": "PhantomBuster",
        "signup_url": "https://phantombuster.com/",
        "env_vars": ["PHANTOMBUSTER_API_KEY"],
    },
    "apollo": {
        "patterns": ["apollo.io", "apollo", "lead enrichment"],
        "service_name": "Apollo.io",
        "signup_url": "https://app.apollo.io/",
        "env_vars": ["APOLLO_API_KEY"],
    },
    "instantly": {
        "patterns": ["instantly", "cold email", "email warmup"],
        "service_name": "Instantly",
        "signup_url": "https://instantly.ai/",
        "env_vars": ["INSTANTLY_API_KEY"],
    },
    "canva": {
        "patterns": ["canva", "design template"],
        "service_name": "Canva",
        "signup_url": "https://www.canva.com/developers/",
        "env_vars": ["CANVA_API_KEY"],
    },
    "airtable": {
        "patterns": ["airtable", "airtable base"],
        "service_name": "Airtable",
        "signup_url": "https://airtable.com/developers",
        "env_vars": ["AIRTABLE_API_KEY", "AIRTABLE_BASE_ID"],
    },
    "zapier": {
        "patterns": ["zapier", "zap", "automation webhook"],
        "service_name": "Zapier",
        "signup_url": "https://zapier.com/developer",
        "env_vars": ["ZAPIER_WEBHOOK_URL"],
    },
    "stripe": {
        "patterns": ["stripe", "payment processing", "checkout"],
        "service_name": "Stripe",
        "signup_url": "https://dashboard.stripe.com/apikeys",
        "env_vars": ["STRIPE_API_KEY", "STRIPE_WEBHOOK_SECRET"],
    },
    "twilio": {
        "patterns": ["twilio", "sms api", "whatsapp api"],
        "service_name": "Twilio",
        "signup_url": "https://www.twilio.com/console",
        "env_vars": ["TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN"],
    },
    "sendgrid": {
        "patterns": ["sendgrid", "transactional email"],
        "service_name": "SendGrid",
        "signup_url": "https://app.sendgrid.com/settings/api_keys",
        "env_vars": ["SENDGRID_API_KEY"],
    },
}

# System variables to exclude from user variable extraction
_SYSTEM_VARIABLES = {"previousOutput", "row_number", "total_steps"}


# ---------------------------------------------------------------------------
# [ROBOT] Pipeline Functions
# ---------------------------------------------------------------------------

def filter_and_validate(steps: list[dict]) -> list[dict]:
    """[ROBOT] Remove steps with empty title/description or prompt. Returns valid steps.

    Falls back to 'description' if 'title' is missing (video processor may omit title).
    """
    valid = []
    for step in steps:
        title = (step.get("title") or step.get("description") or "").strip()
        prompt = (step.get("prompt") or "").strip()
        if title and prompt:
            # Backfill title from description if missing so downstream sees it
            if not (step.get("title") or "").strip() and title:
                step["title"] = title[:120]  # Cap at reasonable length
            valid.append(step)
        else:
            logger.debug("Filtered out step (empty title+desc/prompt): %s", step.get("title", "<no title>"))
    return valid


def classify_step(step: dict) -> StepType:
    """[ROBOT] Classify a step by keyword matching.

    Priority: ACTION > MANUAL > GENERATION > RESEARCH (default).
    """
    text = f"{step.get('title', '')} {step.get('prompt', '')} {step.get('description', '')}".lower()

    for signal in ACTION_SIGNALS:
        if signal in text:
            return StepType.ACTION

    for signal in MANUAL_SIGNALS:
        if signal in text:
            return StepType.MANUAL

    for signal in GENERATION_SIGNALS:
        if signal in text:
            return StepType.GENERATION

    return StepType.RESEARCH


def detect_apis(steps: list[dict]) -> list[DetectedAPI]:
    """[ROBOT] Scan all step prompts and detect required external APIs."""
    detected: dict[str, DetectedAPI] = {}
    for step in steps:
        text = f"{step.get('title', '')} {step.get('prompt', '')} {step.get('expectedOutput', '')}".lower()
        for service_key, config in API_PATTERNS.items():
            if service_key in detected:
                continue
            for pattern in config["patterns"]:
                if pattern in text:
                    detected[service_key] = DetectedAPI(
                        service_name=config["service_name"],
                        service_key=service_key,
                        detection_pattern=pattern,
                        signup_url=config["signup_url"],
                        required_env_vars=config["env_vars"],
                    )
                    break
    return list(detected.values())


def extract_user_variables(steps: list[dict]) -> list[str]:
    """[ROBOT] Find all {variable} placeholders across all step prompts."""
    variables: set[str] = set()
    pattern = re.compile(r"\{(\w+)\}")

    for step in steps:
        prompt = step.get("prompt", "")
        for match in pattern.finditer(prompt):
            var_name = match.group(1)
            if var_name not in _SYSTEM_VARIABLES:
                variables.add(var_name)

    return sorted(variables)


def detect_prior_references(prompt: str, row_number: int) -> list[int]:
    """[ROBOT] Find references to prior steps in prompt text.

    Looks for patterns like 'step 3', 'row 2', 'previous step', etc.
    """
    refs: set[int] = set()
    lower = prompt.lower()

    # Match "step N" or "row N"
    for m in re.finditer(r"(?:step|row)\s+(\d+)", lower):
        ref = int(m.group(1))
        if 1 <= ref < row_number:
            refs.add(ref)

    # "previous" / "prior" → row_number - 1
    if row_number > 1 and any(w in lower for w in ("previous", "prior", "last step", "preceding")):
        refs.add(row_number - 1)

    return sorted(refs)


def compute_input_source(row_number: int, step: dict, all_steps: list[dict]) -> str:
    """[ROBOT] Compute input_source for a chain row."""
    if row_number == 1:
        return "user_input"

    references = detect_prior_references(step.get("prompt", ""), row_number)
    if len(references) > 1:
        return "+".join(f"row_{r}" for r in references)

    return f"row_{row_number - 1}"


def _normalize_model(model_str: str) -> str:
    """[ROBOT] Normalize model string to short form."""
    lower = model_str.lower()
    if "opus" in lower:
        return "opus"
    if "haiku" in lower:
        return "haiku"
    return "sonnet"


# ---------------------------------------------------------------------------
# [AGENT] Prompt Conversion (Claude Sonnet)
# ---------------------------------------------------------------------------

PROMPT_CONVERSION_SYSTEM = (
    "You are a prompt conversion specialist. You convert video-extracted prompts "
    "into structured chain-executable prompts. Return ONLY the converted prompt, "
    "no explanation, no markdown fences."
)


async def convert_single_prompt(
    original_prompt: str,
    step_number: int,
    total_steps: int,
    tool_name: str,
    expected_output: str,
) -> str:
    """[AGENT] Convert a video-style prompt to a chain-executable prompt.

    Uses Claude Haiku for speed (~3x faster than Sonnet, ~4x cheaper).
    This is a straightforward rewrite task — Haiku handles it well.
    Includes retry logic (max 2 retries) and output validation.
    """
    from ..services.yt_processor import YTProcessor

    user_message = (
        f'Given this video-extracted step prompt:\n'
        f'"{original_prompt}"\n\n'
        f'Context: This is Step {step_number} of {total_steps} in a "{tool_name}" workflow.\n'
        f'Expected output: {expected_output}\n\n'
        f'Convert it to a structured chain prompt that:\n'
        f'1. Is self-contained (doesn\'t reference "the video" or "what we just did")\n'
        f'2. Uses {{{{previousOutput}}}} to reference the prior step\'s result\n'
        f'3. Uses {{{{variable_name}}}} for user-configurable inputs\n'
        f'4. Specifies the expected output format clearly\n'
        f'5. Is under 500 words\n\n'
        f'Return ONLY the converted prompt, no explanation.'
    )

    # Sonnet for prompt conversion — cheap (67 hrs/day capacity) and reliable.
    # Haiku was timing out due to CLI startup overhead; Sonnet is fast enough
    # and this step is too important to risk [UNCONVERTED] fallbacks.
    prompt_model = "claude-sonnet-4-6"
    processor = YTProcessor(model=prompt_model)
    max_retries = 2

    for attempt in range(max_retries + 1):
        try:
            result = await processor._call_via_sdk(
                PROMPT_CONVERSION_SYSTEM,
                user_message if attempt == 0 else f"{user_message}\n\nPlease provide the converted prompt.",
                prompt_model,
                timeout=120,  # 60s was too tight — CLI startup overhead + Sonnet response
            )

            if not result or not result.strip():
                if attempt < max_retries:
                    continue
                return f"[UNCONVERTED] {original_prompt}"

            # Truncate if too long (>500 words ~ 3000 chars)
            if len(result.split()) > 500:
                words = result.split()[:500]
                result = " ".join(words) + "\n\n[Output format: " + expected_output + "]"

            return result.strip()

        except Exception as e:
            logger.warning("Prompt conversion attempt %d failed: %s", attempt + 1, e)
            if attempt >= max_retries:
                return f"[UNCONVERTED] {original_prompt}"

    return f"[UNCONVERTED] {original_prompt}"


async def convert_prompts(
    steps: list[dict],
    tool_name: str,
    on_progress: Optional[callable] = None,
) -> list[str]:
    """[AGENT] Batch wrapper — calls convert_single_prompt for each step."""
    converted = []
    total = len(steps)

    for i, step in enumerate(steps):
        if on_progress:
            on_progress(f"Converting prompt {i + 1}/{total}...")

        result = await convert_single_prompt(
            original_prompt=step.get("prompt", ""),
            step_number=i + 1,
            total_steps=total,
            tool_name=tool_name,
            expected_output=step.get("expectedOutput", ""),
        )
        converted.append(result)

    return converted


# ---------------------------------------------------------------------------
# [ROBOT] Blueprint Assembly
# ---------------------------------------------------------------------------

def assemble_blueprint(
    project_name: str,
    project_description: str,
    source_video_id: str,
    source_video_title: str,
    source_video_channel: str,
    source_project_id: str,
    steps: list[dict],
    converted_prompts: list[str],
    detected_api_list: list[DetectedAPI],
    user_variables: list[str],
    theme: Optional[ThemeConfig] = None,
    ingestion_source: IngestionSource = IngestionSource.YOUTUBE,
    source_prd_id: Optional[str] = None,
) -> SheetBlueprint:
    """[ROBOT] Combine all computed fields into final SheetBlueprint."""
    chain_rows: list[ChainConfigRow] = []

    for i, step in enumerate(steps):
        row_number = i + 1
        step_type = classify_step(step)
        input_source = compute_input_source(row_number, step, steps)

        # Build per-row API requirements
        step_text = f"{step.get('title', '')} {step.get('prompt', '')} {step.get('expectedOutput', '')}".lower()
        row_apis: list[str] = []
        for service_key, config in API_PATTERNS.items():
            for pattern in config["patterns"]:
                if pattern in step_text:
                    row_apis.append(service_key)
                    break

        title = (step.get("title", "") or "")[:60].strip()
        if not title:
            title = f"Step {row_number}"

        row = ChainConfigRow(
            row_number=row_number,
            step_type=step_type,
            title=title,
            prompt_template=converted_prompts[i] if i < len(converted_prompts) else step.get("prompt", ""),
            expected_output=step.get("expectedOutput", ""),
            input_source=input_source,
            output_destination=f"row_{row_number}_output",
            model_recommendation=_normalize_model(step.get("model", "sonnet")),
            apis_required=row_apis,
            is_gate=(step_type == StepType.MANUAL),
            max_retries=1,
            timeout_seconds=120,
            notes=step.get("notes", ""),
            original_step_id=step.get("id", str(uuid.uuid4().hex[:8])),
            original_step_order=step.get("order", row_number),
        )
        chain_rows.append(row)

    return SheetBlueprint(
        blueprint_id=f"bp_{uuid.uuid4().hex[:12]}",
        tool_name=project_name,
        tool_description=project_description,
        source_video_id=source_video_id,
        source_video_title=source_video_title,
        source_video_channel=source_video_channel,
        source_project_id=source_project_id,
        chain_config=chain_rows,
        detected_apis=detected_api_list,
        user_input_variables=user_variables,
        theme=theme,
        ingestion_source=ingestion_source,
        source_prd_id=source_prd_id,
    )


# ---------------------------------------------------------------------------
# [ROBOT + AGENT] Consulting Report (emitted before slow prompt conversion)
# ---------------------------------------------------------------------------

def _build_consulting_metrics(
    steps: list[dict],
    detected_apis: list[DetectedAPI],
    user_variables: list[str],
    api_research: "BlueprintAPIResearch | None",
) -> dict:
    """[ROBOT] Compute data-driven metrics for the consulting report. Zero tokens."""
    # Count step types
    type_counts: dict[str, int] = {"manual": 0, "generation": 0, "action": 0, "research": 0}
    model_counts: dict[str, int] = {"opus": 0, "sonnet": 0, "haiku": 0}
    for step in steps:
        stype = classify_step(step).value
        type_counts[stype] = type_counts.get(stype, 0) + 1
        model = _normalize_model(step.get("model", "sonnet"))
        model_counts[model] = model_counts.get(model, 0) + 1

    # Aggregate red flags from API research
    red_flags: list[str] = []
    if api_research:
        for r in api_research.results:
            red_flags.extend(r.red_flags)

    # Complexity score (1-10)
    score = 1
    score += min(len(steps), 3)  # more steps = harder (up to +3)
    score += min(type_counts.get("action", 0), 2)  # API actions add complexity (+2 max)
    score += min(type_counts.get("manual", 0), 2)  # manual gates add friction (+2 max)
    score += 1 if len(detected_apis) >= 3 else 0  # 3+ APIs = complex
    score += 1 if len(red_flags) >= 2 else 0  # multiple red flags
    score = min(score, 10)

    # Verdict
    if score <= 3:
        verdict = "Simple — straightforward to automate"
    elif score <= 5:
        verdict = "Moderate — some setup work needed"
    elif score <= 7:
        verdict = "Complex — expect significant configuration"
    else:
        verdict = "Very complex — consider simplifying first"

    return {
        "total_steps": len(steps),
        "manual_steps": type_counts.get("manual", 0),
        "automated_steps": len(steps) - type_counts.get("manual", 0),
        "step_types": type_counts,
        "model_breakdown": model_counts,
        "api_count": len(detected_apis),
        "api_names": [a.service_name for a in detected_apis],
        "red_flags": red_flags,
        "user_variables": user_variables,
        "complexity_score": score,
        "verdict": verdict,
        "estimated_monthly_cost": api_research.total_estimated_monthly_cost if api_research else "Unknown",
    }


async def _ai_consulting_assessment(
    project_name: str,
    metrics: dict,
    steps: list[dict],
) -> str:
    """[AGENT] Ask Sonnet for a consulting-style assessment of the plan."""
    from ..services.yt_processor import YTProcessor

    step_summary = "\n".join(
        f"  {i+1}. [{classify_step(s).value.upper()}] {s.get('title', 'Untitled')}"
        for i, s in enumerate(steps)
    )

    prompt = f"""You are a senior consultant evaluating a strategy extracted from a YouTube video.

MISSION CONTEXT: This tool exists to simplify the ideas in videos into the most automated,
least-friction, easiest-to-template strategy that can run on autopilot. The user wants to know:
Can I template this? Can I run it regularly with minimal effort? How close to autopilot can this get?

Plan: "{project_name}"
Steps: {metrics['total_steps']} total ({metrics['automated_steps']} automated, {metrics['manual_steps']} require human input)
APIs needed: {', '.join(metrics['api_names']) or 'None'}
Red flags from API research: {'; '.join(metrics['red_flags']) or 'None'}
Complexity: {metrics['complexity_score']}/10
Estimated monthly API cost: {metrics['estimated_monthly_cost']}
Variables user must provide: {', '.join(metrics['user_variables']) or 'None'}

Step breakdown:
{step_summary}

Write a 2-3 paragraph consulting assessment covering:
1. **Autopilot potential**: How close can this get to running on autopilot? What parts can be fully templated and reused? What still needs human touch each time?
2. **Simplification opportunities**: Where can steps be combined, removed, or automated further? What's the minimum viable version that still delivers the core value?
3. **Implementation path**: What's the fastest way to get this running as a repeatable template? Flag any friction points or gotchas.

VALUE FRAMEWORK: Content generation, copy creation, and framework building via AI are HIGH-value automation — they save real hours. Don't dismiss workflows just because they don't call external APIs. A templated strategy that generates tailored content on demand IS automation. Rate ideas on how repeatable and low-friction they can become, not on engineering complexity.

Be direct. No fluff. Plain language — the reader is NOT a coder."""

    system = "You are a direct, no-nonsense automation strategist. You evaluate how close a plan can get to autopilot — templatable, repeatable, minimal friction. Short paragraphs, plain language."

    processor = YTProcessor(model="claude-sonnet-4-6")
    try:
        result = await processor._call_via_sdk(system, prompt, "claude-sonnet-4-6", timeout=60)
        return result.strip()
    except Exception as e:
        logger.warning("AI consulting assessment failed: %s", e)
        return f"Could not generate AI assessment: {e}"


# ---------------------------------------------------------------------------
# Main Entry Point
# ---------------------------------------------------------------------------

async def generate_blueprint(
    project_name: str,
    project_description: str,
    steps: list[dict],
    source_video_id: str = "",
    source_video_title: str = "",
    source_video_channel: str = "",
    source_project_id: str = "",
    theme: Optional[ThemeConfig] = None,
    skip_prompt_conversion: bool = False,
    on_progress: Optional[callable] = None,
    ingestion_source: IngestionSource = IngestionSource.YOUTUBE,
    source_prd_id: Optional[str] = None,
) -> SheetBlueprint:
    """Generate a complete SheetBlueprint from extracted steps.

    Orchestrates the full pipeline:
    filter → classify → detect APIs → research pricing → extract vars →
    convert prompts → assemble.
    """
    if on_progress:
        on_progress("Filtering and validating steps...")

    valid_steps = filter_and_validate(steps)
    if not valid_steps:
        raise ValueError("No valid steps found after filtering")

    if on_progress:
        on_progress(f"Validated {len(valid_steps)} steps")

    # [ROBOT] steps — all zero tokens, instant
    if on_progress:
        on_progress("Classifying step types...")
    # Classification happens inside assemble, but we can report detection here
    detected_api_list = detect_apis(valid_steps)
    if on_progress:
        on_progress(f"Detected {len(detected_api_list)} API{'s' if len(detected_api_list) != 1 else ''}")

    # [AGENT] API pricing research — Sonnet + WebSearch with static DB fallback.
    # Runs after detection so we know which APIs to research. Errors are non-fatal;
    # if the entire research step fails, api_research stays None on the blueprint.
    api_research_result = None
    if detected_api_list:
        try:
            from .api_research import research_api_pricing

            if on_progress:
                on_progress(f"Researching pricing for {len(detected_api_list)} APIs...")
            api_research_result = await research_api_pricing(
                detected_apis=detected_api_list,
                progress_callback=on_progress,
            )
            if on_progress:
                on_progress(
                    f"API research complete ({api_research_result.research_duration_seconds:.1f}s)"
                )
        except Exception as e:
            logger.warning("API pricing research failed (non-fatal): %s", e)
            if on_progress:
                on_progress("API pricing research failed — continuing without it")

    user_variables = extract_user_variables(valid_steps)
    if on_progress:
        on_progress(f"Found {len(user_variables)} variable{'s' if len(user_variables) != 1 else ''}")

    # [AGENT + ROBOT] Consulting report — emitted before slow prompt conversion
    if on_progress:
        on_progress("Building consulting report...")

    consulting_metrics = _build_consulting_metrics(
        valid_steps, detected_api_list, user_variables, api_research_result,
    )

    # AI consulting assessment (Sonnet, ~15-30s)
    if on_progress:
        on_progress("Getting AI consulting assessment...")
    ai_assessment = await _ai_consulting_assessment(
        project_name, consulting_metrics, valid_steps,
    )

    # Emit early report as structured event (frontend catches this)
    if on_progress:
        on_progress({
            "type": "early_report",
            "data": {
                "metrics": consulting_metrics,
                "assessment": ai_assessment,
                "api_research": api_research_result.model_dump() if api_research_result else None,
            },
        })

    # [AGENT] prompt conversion via Haiku (or skip for testing)
    if skip_prompt_conversion:
        converted_prompts = [s.get("prompt", "") for s in valid_steps]
        if on_progress:
            on_progress("Skipped prompt conversion (test mode)")
    else:
        if on_progress:
            on_progress(f"Converting {len(valid_steps)} prompts via Sonnet...")
        converted_prompts = await convert_prompts(valid_steps, project_name, on_progress)

    if on_progress:
        on_progress("Assembling final blueprint...")

    # [ROBOT] final assembly
    blueprint = assemble_blueprint(
        project_name=project_name,
        project_description=project_description,
        source_video_id=source_video_id,
        source_video_title=source_video_title,
        source_video_channel=source_video_channel,
        source_project_id=source_project_id,
        steps=valid_steps,
        converted_prompts=converted_prompts,
        detected_api_list=detected_api_list,
        user_variables=user_variables,
        theme=theme,
        ingestion_source=ingestion_source,
        source_prd_id=source_prd_id,
    )

    # Attach API research results to the blueprint (if research succeeded)
    if api_research_result is not None:
        blueprint.api_research = api_research_result

    if on_progress:
        on_progress(f"Blueprint complete: {len(blueprint.chain_config)} chain rows")

    return blueprint
