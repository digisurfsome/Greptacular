# Phase 3: Enhanced Mechanism Analysis + Verification Agents

> 6 dimensions, N-way close calls, Caveat Appendix, and verifier agents.

**Priority**: HIGH — mechanism analysis is the brain of the pipeline.
**Depends on**: Phase 1 (Orchestration), Phase 2 (Refinement feeds into mechanism context).

---

## Overview

This phase upgrades the mechanism analysis from 4 dimensions to 6, adds N-way close
call handling (3+ alternatives within 15%), adds the Caveat Appendix output, and
implements the Stage N.5 Verifier pattern for quality checking.

---

## 3.1 Enhanced Mechanism Analysis (6 Dimensions)

### Modify: `server/services/agent_os_mechanism.py`

**Current state**: 4 scoring dimensions (complexity, standards_match, scalability,
maintainability) with flat 0-1 weights.

**Target state**: 6 scoring dimensions from the addendum, configurable weights,
N-way close call detection, Caveat Appendix generation.

#### Changes to `AgentOSMechanism`

**Replace scoring constants**:

```python
# OLD (remove)
SCORING_CRITERIA = ["complexity", "standards_match", "scalability", "maintainability"]

# NEW
DEFAULT_SCORING_DIMENSIONS = {
    "implementation_speed": 0.20,
    "maintainability": 0.20,
    "user_experience": 0.20,
    "security": 0.15,
    "cost": 0.10,
    "brand_alignment": 0.15,
}
```

**New/modified methods**:

```python
def get_analysis_prompt(self, decision_point: str, options: list, context: str) -> str:
    """Enhanced prompt requesting 6-dimension scoring.

    Now includes:
    - Score on all 6 dimensions (0-100 scale, not 0-1)
    - Key differentiator explanation
    - Why scores differ (narrative)
    - Risk if wrong (LOW/MEDIUM/HIGH + explanation)
    - Switch cost estimate (days + files affected)
    """
    ...

def process_analysis(self, analysis_json: dict, ...) -> dict:
    """Enhanced analysis processing.

    New fields in output:
    - gap_category: "clear_winner" | "close_call" | "very_close" | "needs_human"
    - risk_if_wrong: "LOW" | "MEDIUM" | "HIGH"
    - switch_cost: {"days": int, "files": list[str], "dependencies": list[str]}
    - key_differentiator: str
    - why_scores_differ: str
    - caveat_entry: dict (if close call, pre-formatted for Caveat Appendix)
    """
    ...

def detect_n_way_close_calls(self, analysis: dict) -> dict:
    """Detect when 3+ options are within 15% of each other.

    Returns:
    {
        "is_n_way": true,
        "options_in_range": 3,
        "top_options": [
            {"name": "Option A", "score": 78.5},
            {"name": "Option B", "score": 72.1},
            {"name": "Option C", "score": 71.8}
        ],
        "max_gap": 6.7,
        "recommendation": "spec_top_2_preserve_3rd"
    }
    """
    ...

def generate_caveat_entry(self, analysis: dict) -> dict:
    """Generate a Caveat Appendix entry for a close call.

    Entry format (from addendum):
    {
        "mechanism_id": "UI-003",
        "name": "Project Timeline Visualization",
        "selected": {"name": "React Flow", "score": 78.5},
        "alternative": {"name": "CSS Grid + Canvas", "score": 72.1},
        "score_gap": 6.4,
        "switch_trigger": "If React Flow bundle size impacts mobile load times...",
        "switch_cost": "HIGH — 5-7 day refactor",
        "files_affected": ["TimelineView.tsx", "ProjectCard.tsx"],
        "dependencies_affected": ["None"],
        "worktree_recommended": true  # gap < 10% AND cost >= medium AND user-facing
    }

    For N-way (3+): includes additional_alternatives list.
    """
    ...

def generate_caveat_appendix(self) -> str:
    """Generate full Caveat Appendix markdown from all close calls."""
    ...
```

**Updated Developer's Choice weights** (now operates on 6 dimensions):

```python
def apply_developers_choice(self, options: list[dict]) -> list[dict]:
    """Apply weighted biases using 6 dimensions.

    Weight sources (in priority order):
    1. config.yml scoring_dimensions (user-customized)
    2. DEFAULT_SCORING_DIMENSIONS (factory defaults)

    Biases (from config.yml developers_choice):
    - bias_toward_standards -> boosts brand_alignment
    - bias_toward_simplicity -> boosts implementation_speed
    - bias_toward_adoption -> boosts maintainability
    - bias_toward_docs -> boosts user_experience
    """
    ...
```

**Three Interaction Modes** (from addendum):

```python
def get_interaction_mode(self, total_mechanisms: int, close_calls: int) -> str:
    """Determine user interaction mode.

    Returns:
    - "full_control": User reviews every mechanism
    - "developers_choice": One-click accept all
    - "review_exceptions": Auto-select clear winners, present close calls only

    Default: "review_exceptions"
    """
    ...

def accept_all_developers_choice(self) -> list[dict]:
    """One-click accept all recommendations. Return summary of decisions."""
    ...
```

---

## 3.2 Verification Agents (Stage N.5 Pattern)

### File: `server/services/agent_os_verify.py` (NEW)

**Class**: `AgentOSVerifier`

A generic verifier that can be configured per stage. Uses Sonnet at temperature 0.

```python
class AgentOSVerifier:
    """Stage N.5 verification agent.

    Runs a second AI (Sonnet) to review a worker's output against the input
    and quality criteria. If verification fails, feeds issues back to worker
    for correction.
    """

    def __init__(self, orchestrator: AgentOSOrchestrator, config: dict):
        self.orchestrator = orchestrator
        self.config = config
        self.verification_results: dict[str, dict] = {}

    async def verify(
        self,
        stage_name: str,
        original_input: str,
        stage_output: dict,
        verification_criteria: list[str],
    ) -> dict:
        """Run verification on a stage's output.

        Returns:
        {
            "verdict": "pass" | "fail",
            "issues_found": int,
            "issues_critical": int,
            "issues_minor": int,
            "verification_results": [
                {
                    "check": "item_completeness",
                    "status": "pass" | "minor_issue" | "critical_issue",
                    "detail": str,
                    "fix": str (optional)
                }
            ],
            "missing_from_output": [],
            "fabricated_content": [],
            "misclassified_items": []
        }
        """
        prompt = self._build_verification_prompt(
            stage_name, original_input, stage_output, verification_criteria
        )
        result = await self.orchestrator.execute(
            prompt=prompt,
            model="sonnet",  # Always Sonnet for verifiers
            stage_name=f"{stage_name}_verify"
        )
        return self._process_verification(stage_name, result)

    async def verify_and_retry(
        self,
        stage_name: str,
        original_input: str,
        stage_output: dict,
        verification_criteria: list[str],
        worker_prompt_fn,      # Callable that generates the worker prompt
        worker_process_fn,     # Callable that processes worker output
    ) -> tuple[dict, dict]:
        """Verify, and if failed, re-run worker with corrections.

        Returns (final_output, verification_report).
        """
        report = await self.verify(stage_name, original_input, stage_output, verification_criteria)

        if report["verdict"] == "fail" and self.config.get("max_retries", 1) > 0:
            # Build correction prompt
            correction_context = self._format_issues_for_worker(report)
            corrected_prompt = worker_prompt_fn() + f"\n\nCORRECTION RUN. Fix these issues:\n{correction_context}"

            corrected_result = await self.orchestrator.execute(
                prompt=corrected_prompt,
                model="sonnet",
                stage_name=f"{stage_name}_correction"
            )
            corrected_output = worker_process_fn(corrected_result)

            # Re-verify (but don't retry again)
            final_report = await self.verify(
                stage_name, original_input, corrected_output, verification_criteria
            )
            return corrected_output, final_report

        return stage_output, report
```

### Stage-Specific Verification Criteria

```python
VERIFICATION_CRITERIA = {
    "transcription": [
        "Every distinct idea from the original appears in the output",
        "original_quote fields actually exist in the input (not fabricated)",
        "Content accurately represents what the user said",
        "No detail was lost in reformatting",
        "Item type classifications are correct",
    ],
    "mechanism": [
        "Recommended approaches are consistent with project constraints",
        "Score percentages are justified by the pros/cons listed",
        "No approach contradicts a user-stated requirement",
        "Dependencies between mechanisms are correct",
        "Score gaps match the gap_category classification",
    ],
    "prd": [
        "Every item from intake through specs appears in the PRD (zero orphans)",
        "Provenance tags are correct (USER items actually came from user)",
        "Mechanism recommendations match mechanism analysis output",
        "The PRD is internally consistent (no section contradicts another)",
        "All sections have substantive content (not just headers)",
        "Acceptance criteria are testable and specific",
    ],
}
```

### Session Integration

Verification runs automatically after each enabled stage:

```python
async def _maybe_verify(self, stage_name: str, original_input: str, output: dict) -> dict:
    """Run verification if enabled for this stage."""
    if not self.config["agent_os"]["verification"]["enabled"]:
        return output

    if stage_name not in VERIFICATION_CRITERIA:
        return output

    output, report = await self.verifier.verify_and_retry(
        stage_name=stage_name,
        original_input=original_input,
        stage_output=output,
        verification_criteria=VERIFICATION_CRITERIA[stage_name],
        worker_prompt_fn=lambda: getattr(self, f'_get_{stage_name}_prompt')(),
        worker_process_fn=lambda r: getattr(self, f'_process_{stage_name}')(r),
    )

    yield {
        "type": "verification",
        "stage": stage_name,
        "verdict": report["verdict"],
        "issues": report["issues_found"],
        "critical": report["issues_critical"],
    }

    if report["verdict"] == "fail" and self.config["agent_os"]["verification"]["fail_on_critical"]:
        yield {"type": "error", "message": f"Verification failed for {stage_name}: {report['issues_critical']} critical issues"}

    return output
```

### Cost Impact (from addendum)

| Verifier | Est. Tokens | Est. Cost |
|----------|-------------|-----------|
| Transcription (1.5) | 8K-12K | ~$0.15 |
| Mechanism (6.5) | 12K-18K | ~$0.22 |
| PRD (7.5) | 20K-30K | ~$0.35 |
| **Total** | **40K-60K** | **~$0.72** |

~30% more tokens per pipeline run. Toggleable via `verification.enabled: false`.

---

## 3.3 Caveat Appendix Router Endpoints

### Modify: `server/routers/agent_os.py`

```python
@router.get("/mechanism/{project_name}/caveat-appendix")
async def get_caveat_appendix(project_name: str):
    """Get the Caveat Appendix (all close-call alternatives)."""
    ...

@router.get("/mechanism/{project_name}/interaction-mode")
async def get_mechanism_interaction_mode(project_name: str):
    """Get recommended interaction mode (full_control/developers_choice/review_exceptions)."""
    ...

@router.post("/mechanism/{project_name}/accept-all")
async def accept_all_developers_choice(project_name: str):
    """One-click accept all Developer's Choice recommendations."""
    ...
```

---

## Phase 3 Deliverables

| # | Deliverable | File |
|---|-------------|------|
| 1 | Enhanced mechanism (6 dims, N-way, caveat) | `server/services/agent_os_mechanism.py` (modify) |
| 2 | Generic verifier framework | `server/services/agent_os_verify.py` |
| 3 | Verification integration in session | `server/services/agent_os_session.py` (modify) |
| 4 | Caveat appendix endpoints | `server/routers/agent_os.py` (modify) |
| 5 | Tests | `test_agent_os_verify.py`, update `test_agent_os_mechanism.py` |

**Estimated complexity**: High. Mechanism rewrite is the most logic-dense change.
Verifier framework is medium but needs careful prompt engineering.
