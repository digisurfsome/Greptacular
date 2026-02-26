"""
Agent OS Mechanism Analysis
============================

Evaluates competing technical approaches for features.
Scores options against criteria and applies Developer's Choice
tiebreaker for close decisions.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Optional

logger = logging.getLogger(__name__)


def _escape_braces(text: str) -> str:
    """Escape curly braces in user content so .format() doesn't choke."""
    return text.replace("{", "{{").replace("}", "}}")

# Scoring criteria
SCORING_CRITERIA = ["complexity", "standards_match", "scalability", "maintainability"]

# ── Prompt template ──────────────────────────────────────────────────

MECHANISM_ANALYSIS_PROMPT = """Evaluate the following technical options for this decision point.

## Decision Point
{decision_point}

## Options to Evaluate
{options_list}

## Context
{context}

## Standards
{standards_summary}

Score each option on these criteria (0.0 to 1.0):
- complexity: How simple is this to implement? (1.0 = very simple)
- standards_match: How well does it match the project's standards? (1.0 = perfect match)
- scalability: How well does it scale? (1.0 = highly scalable)
- maintainability: How easy is it to maintain long-term? (1.0 = very maintainable)

Return ONLY valid JSON:
{{
  "options": [
    {{
      "name": "<option name>",
      "scores": {{
        "complexity": <0.0-1.0>,
        "standards_match": <0.0-1.0>,
        "scalability": <0.0-1.0>,
        "maintainability": <0.0-1.0>
      }},
      "overall_score": <weighted average>,
      "pros": ["<pro 1>", "<pro 2>"],
      "cons": ["<con 1>", "<con 2>"]
    }}
  ],
  "reasoning": "<brief explanation of scoring>"
}}
"""


class AgentOSMechanism:
    """Evaluates competing technical approaches and applies Developer's Choice tiebreaker."""

    def __init__(self, config: dict[str, Any], standards_summary: str = ""):
        self.config = config  # mechanism_analysis + developers_choice sections
        self.standards_summary = standards_summary
        self._analyses: list[dict[str, Any]] = []
        self._decisions: list[dict[str, Any]] = []

    # ── Prompt generation ────────────────────────────────────────────

    def get_analysis_prompt(self, decision_point: str, options: list[str], context: str) -> str:
        """Return a prompt for Claude to analyze competing technical options."""
        options_list = "\n".join(f"- {opt}" for opt in options)
        return MECHANISM_ANALYSIS_PROMPT.format(
            decision_point=_escape_braces(decision_point),
            options_list=_escape_braces(options_list),
            context=_escape_braces(context),
            standards_summary=_escape_braces(self.standards_summary or "(No standards defined)"),
        )

    # ── Processing Claude responses ──────────────────────────────────

    def process_analysis(self, analysis_json: dict[str, Any], feature_id: Optional[int] = None) -> dict[str, Any]:
        """Process Claude's analysis output. Apply Developer's Choice if scores are close."""
        raw_options = analysis_json.get("options", [])
        reasoning = analysis_json.get("reasoning", "")

        # Normalize options
        options: list[dict[str, Any]] = []
        for opt in raw_options:
            scores = opt.get("scores", {})
            # Clamp scores to 0.0-1.0
            clamped_scores: dict[str, float] = {}
            for criterion in SCORING_CRITERIA:
                val = float(scores.get(criterion, 0.5))
                clamped_scores[criterion] = max(0.0, min(1.0, val))

            overall = float(opt.get("overall_score", 0.0))
            if overall == 0.0:
                # Calculate if not provided
                overall = sum(clamped_scores.values()) / len(clamped_scores) if clamped_scores else 0.0

            options.append({
                "name": opt.get("name", "Unknown"),
                "scores": clamped_scores,
                "overall_score": max(0.0, min(1.0, overall)),
                "pros": opt.get("pros", []),
                "cons": opt.get("cons", []),
            })

        # Sort by overall score descending
        options.sort(key=lambda o: o["overall_score"], reverse=True)

        # Apply Developer's Choice if top two are close
        if len(options) >= 2:
            gap = abs(options[0]["overall_score"] - options[1]["overall_score"])
            gap_threshold = self.config.get("mechanism_analysis", {}).get("present_alternatives_gap", 15) / 100.0
            if gap <= gap_threshold:
                options = self.apply_developers_choice(options)

        # Determine recommendation
        recommended = options[0]["name"] if options else "None"
        confidence = options[0].get("overall_score", 0.0) if options else 0.0

        # Check thresholds
        auto_threshold = self.config.get("mechanism_analysis", {}).get("auto_select_threshold", 85) / 100.0
        auto_selected = confidence >= auto_threshold

        analysis: dict[str, Any] = {
            "decision_point": "",  # Set by caller
            "feature_id": feature_id,
            "options": options,
            "recommended": recommended,
            "confidence": confidence,
            "auto_selected": auto_selected,
            "reasoning": reasoning,
            "timestamp": datetime.now(tz=timezone.utc).isoformat(),
        }

        self._analyses.append(analysis)
        logger.info("Analysis complete: recommended=%s confidence=%.2f auto=%s", recommended, confidence, auto_selected)
        return analysis

    # ── Developer's Choice ───────────────────────────────────────────

    def apply_developers_choice(self, options: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Apply Developer's Choice weighted biases to option scores."""
        dc_config = self.config.get("developers_choice", {})
        if not dc_config.get("enabled", True):
            return options

        bias_standards = dc_config.get("bias_toward_standards", 0.3)
        bias_simplicity = dc_config.get("bias_toward_simplicity", 0.2)
        bias_adoption = dc_config.get("bias_toward_adoption", 0.2)
        bias_docs = dc_config.get("bias_toward_docs", 0.1)
        raw_weight = max(0.0, 1.0 - bias_standards - bias_simplicity - bias_adoption - bias_docs)

        for option in options:
            scores = option.get("scores", {})
            adjusted = (
                scores.get("standards_match", 0.5) * bias_standards
                + scores.get("complexity", 0.5) * bias_simplicity  # Higher complexity score = simpler
                + scores.get("maintainability", 0.5) * bias_adoption  # Proxy for adoption
                + scores.get("maintainability", 0.5) * bias_docs  # Proxy for docs quality
                + option.get("overall_score", 0.5) * raw_weight
            )
            option["adjusted_score"] = adjusted

        return sorted(options, key=lambda o: o.get("adjusted_score", 0), reverse=True)

    # ── Threshold checks ─────────────────────────────────────────────

    def should_auto_select(self, analysis: dict[str, Any]) -> bool:
        """Return True if the top option exceeds auto_select_threshold."""
        threshold = self.config.get("mechanism_analysis", {}).get("auto_select_threshold", 85) / 100.0
        return bool(analysis.get("confidence", 0.0) >= threshold)

    def should_present_alternatives(self, analysis: dict[str, Any]) -> bool:
        """Return True if top two options are within the alternatives gap threshold."""
        options = analysis.get("options", [])
        if len(options) < 2:
            return False
        gap_threshold = self.config.get("mechanism_analysis", {}).get("present_alternatives_gap", 15) / 100.0
        gap = abs(options[0].get("overall_score", 0) - options[1].get("overall_score", 0))
        return bool(gap <= gap_threshold)

    def needs_human_input(self, analysis: dict[str, Any]) -> bool:
        """Return True if all options score below min_viable_score."""
        min_score = self.config.get("mechanism_analysis", {}).get("min_viable_score", 60) / 100.0
        options = analysis.get("options", [])
        if not options:
            return True
        return all(o.get("overall_score", 0) < min_score for o in options)

    # ── Decision recording ───────────────────────────────────────────

    def record_decision(self, analysis: dict[str, Any], chosen_option: str, reason: str = "") -> dict[str, Any]:
        """Record the final decision. Returns a decision dict for decisions.log."""
        decision: dict[str, Any] = {
            "decision_point": analysis.get("decision_point", ""),
            "feature_id": analysis.get("feature_id"),
            "chosen": chosen_option,
            "confidence": analysis.get("confidence", 0.0),
            "auto_selected": analysis.get("auto_selected", False),
            "reason": reason or analysis.get("reasoning", ""),
            "alternatives": [o["name"] for o in analysis.get("options", []) if o["name"] != chosen_option],
            "timestamp": datetime.now(tz=timezone.utc).isoformat(),
        }
        self._decisions.append(decision)
        logger.info("Recorded decision: %s -> %s", decision["decision_point"], chosen_option)
        return decision

    def get_decision_log_entry(self, decision: dict[str, Any]) -> str:
        """Format a decision as a markdown entry for decisions.log."""
        lines = [
            f"## [{decision['timestamp']}] {decision['decision_point']}",
            "",
            f"**Chosen:** {decision['chosen']}",
            f"**Confidence:** {decision['confidence']:.0%}",
            f"**Auto-selected:** {'Yes' if decision['auto_selected'] else 'No'}",
        ]

        if decision.get("feature_id") is not None:
            lines.append(f"**Feature:** #{decision['feature_id']}")

        if decision.get("reason"):
            lines.append(f"**Reason:** {decision['reason']}")

        if decision.get("alternatives"):
            lines.append(f"**Alternatives considered:** {', '.join(decision['alternatives'])}")

        lines.append("")
        return "\n".join(lines)

    # ── Accessors ────────────────────────────────────────────────────

    def get_all_analyses(self) -> list[dict[str, Any]]:
        """Return all analyses performed."""
        return list(self._analyses)

    def get_all_decisions(self) -> list[dict[str, Any]]:
        """Return all recorded decisions."""
        return list(self._decisions)
