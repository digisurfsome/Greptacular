"""
Agent OS Session Manager
=========================

Manages interactive Agent OS PRD creation sessions.
Each project has at most one active session.
Orchestrates the Stage 1-8 workflow over WebSocket, dispatching
to Phase 1-4 services at each stage.
"""

import logging
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, AsyncGenerator, Optional

import yaml

from .agent_os_features import AgentOSFeatures
from .agent_os_file_utils import AgentOSFileUtils
from .agent_os_handoff import AgentOSHandoff
from .agent_os_intake import AgentOSIntake
from .agent_os_mechanism import AgentOSMechanism
from .agent_os_product import AgentOSProduct
from .agent_os_specs import AgentOSSpecs
from .agent_os_standards import AgentOSStandards

logger = logging.getLogger(__name__)


class AgentOSSession:
    """
    Manages one interactive Agent OS PRD creation session for a project.

    Stages:
    0. Intake Dock (handled by UI + REST, not this session)
    1. Intake — classify input, extract entities
    2. Standards Check — verify/create standards
    3. Product Discovery — adaptive question flow
    4. Feature Extraction — derive features from product
    5. Gap Analysis — cross-layer gap detection
    6. Spec Generation — generate spec per feature
    7. Database Population — populate features.db
    8. Handoff — assemble and verify handoff package
    """

    STAGES = [
        "intake",
        "standards",
        "product_discovery",
        "feature_extraction",
        "gap_analysis",
        "spec_generation",
        "database_population",
        "handoff",
    ]

    def __init__(self, project_name: str, project_dir: Path):
        self.project_name = project_name
        self.project_dir = project_dir
        self.created_at = datetime.now(tz=timezone.utc)
        self.current_stage: str = "intake"
        self.current_stage_index: int = 0
        self.messages: list[dict[str, Any]] = []

        # Initialize Phase 1 services (always needed)
        self.file_utils = AgentOSFileUtils(project_dir)
        self.file_utils.ensure_agent_os_dirs()
        self.standards = AgentOSStandards(project_dir, self.file_utils)
        self.intake = AgentOSIntake()

        # Load config
        self._config = self._load_config()

        # Phase 2-4 services — created as needed during the workflow
        self.product: Optional[AgentOSProduct] = None
        self.features: Optional[AgentOSFeatures] = None
        self.mechanism: Optional[AgentOSMechanism] = None
        self.specs: Optional[AgentOSSpecs] = None
        self.handoff: Optional[AgentOSHandoff] = None

        self.complete: bool = False

        # Track whether the user has been shown the first question in questionnaire stages
        self._standards_question_shown: bool = False
        self._product_question_shown: bool = False

    def _load_config(self) -> dict[str, Any]:
        """Load agent_os config from .agent/settings/config.yml."""
        config_path = self.project_dir / ".agent" / "settings" / "config.yml"
        if config_path.is_file():
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    raw = yaml.safe_load(f) or {}
                return raw.get("agent_os", {})
            except Exception as e:
                logger.warning("Failed to load Agent OS config: %s", e)
        return {}

    # ── Message processing ──────────────────────────────────────────

    async def process_message(self, message: str) -> AsyncGenerator[dict[str, Any], None]:
        """Route user input to the current stage handler. Yields response events."""
        # Record the incoming message
        self.messages.append({
            "role": "user",
            "content": message,
            "stage": self.current_stage,
            "timestamp": datetime.now(tz=timezone.utc).isoformat(),
        })

        handler = getattr(self, f"_handle_{self.current_stage}", None)
        if handler is None:
            yield {"type": "error", "message": f"Unknown stage: {self.current_stage}"}
            return

        async for event in handler(message):
            # Record assistant messages
            if event.get("type") == "message":
                self.messages.append({
                    "role": "assistant",
                    "content": event.get("content", ""),
                    "stage": self.current_stage,
                    "timestamp": datetime.now(tz=timezone.utc).isoformat(),
                })
            yield event

    # ── Stage handlers ──────────────────────────────────────────────

    async def _handle_intake(self, message: str) -> AsyncGenerator[dict[str, Any], None]:
        """Stage 1: Accumulate input, classify, extract entities."""
        if message == "__approve__":
            # User approves entities and moves on
            self.advance_stage()
            yield {"type": "stage_change", "stage": self.current_stage, "index": self.current_stage_index, "total": len(self.STAGES)}
            return

        self.intake.add_input(message)

        # Extract entities from accumulated raw input (local, no LLM)
        self.intake.extract_from_raw_input()

        # Return classification and extraction prompts for the caller to process
        yield {
            "type": "message",
            "content": "Processing your input...",
        }

        # Run entity gap detection
        gaps = self.intake.detect_gaps()
        entities = self.intake.get_entities()

        blocking = [g for g in gaps if g["severity"] == "blocking"]

        if entities and not blocking:
            yield {
                "type": "message",
                "content": "I've captured your initial input. Moving to standards check.",
            }
            yield {"type": "progress", "stage": "intake", "entities": entities, "gaps": gaps}
            self.advance_stage()
            yield {"type": "stage_change", "stage": self.current_stage, "index": self.current_stage_index, "total": len(self.STAGES)}
        else:
            yield {
                "type": "message",
                "content": "Tell me more about what you want to build. I need at least a description of the product or the problem it solves.",
            }
            yield {"type": "progress", "stage": "intake", "entities": entities, "gaps": gaps}

    async def _handle_standards(self, message: str) -> AsyncGenerator[dict[str, Any], None]:
        """Stage 2: Check/create standards via questionnaire."""
        if message == "__approve__":
            self.advance_stage()
            yield {"type": "stage_change", "stage": self.current_stage, "index": self.current_stage_index, "total": len(self.STAGES)}
            return

        # If standards already exist, skip
        if self.file_utils.standards_exist() and not self.standards._answers:
            summary = self.standards.get_standards_summary()
            yield {"type": "message", "content": f"Found existing standards.\n\n{summary}"}
            self.advance_stage()
            yield {"type": "stage_change", "stage": self.current_stage, "index": self.current_stage_index, "total": len(self.STAGES)}
            return

        # On first entry, show the first question without consuming the message as an answer
        if not self._standards_question_shown:
            self._standards_question_shown = True
            next_q = self.standards.get_next_question()
            if next_q:
                yield {"type": "question", "question": next_q}
                yield {"type": "progress", "stage": "standards", **self.standards.get_progress()}
            else:
                # No questions to ask — generate files and advance
                self.standards.generate_standards_files()
                yield {"type": "message", "content": "Standards files generated."}
                self.advance_stage()
                yield {"type": "stage_change", "stage": self.current_stage, "index": self.current_stage_index, "total": len(self.STAGES)}
            return

        # Process the answer to the previously shown question
        next_q = self.standards.get_next_question()
        if message and next_q:
            self.standards.process_answer(next_q["id"], message)

        # Get the next question
        next_q = self.standards.get_next_question()
        if next_q:
            yield {"type": "question", "question": next_q}
            yield {"type": "progress", "stage": "standards", **self.standards.get_progress()}
        else:
            # All questions answered — generate files
            self.standards.generate_standards_files()
            yield {"type": "message", "content": "Standards files generated."}
            self.advance_stage()
            yield {"type": "stage_change", "stage": self.current_stage, "index": self.current_stage_index, "total": len(self.STAGES)}

    async def _handle_product_discovery(self, message: str) -> AsyncGenerator[dict[str, Any], None]:
        """Stage 3: Adaptive product question flow."""
        if self.product is None:
            self.product = AgentOSProduct(
                self.project_dir, self.file_utils, self.intake.get_entities()
            )
            self.product.auto_fill_from_entities()

        if message == "__approve__":
            self.product.generate_product_docs()
            yield {"type": "message", "content": "Product documents generated."}
            self.advance_stage()
            yield {"type": "stage_change", "stage": self.current_stage, "index": self.current_stage_index, "total": len(self.STAGES)}
            return

        # On first entry, show the first question without consuming the message as an answer
        if not self._product_question_shown:
            self._product_question_shown = True
            next_q = self.product.get_next_question()
            if next_q:
                yield {"type": "question", "question": next_q}
                yield {"type": "progress", "stage": "product_discovery", **self.product.get_progress()}
            else:
                self.product.generate_product_docs()
                yield {"type": "message", "content": "All product questions answered. Documents generated."}
                self.advance_stage()
                yield {"type": "stage_change", "stage": self.current_stage, "index": self.current_stage_index, "total": len(self.STAGES)}
            return

        # Process the answer to the previously shown question
        next_q = self.product.get_next_question()
        if message and next_q:
            self.product.process_answer(next_q["id"], message)

        next_q = self.product.get_next_question()
        if next_q:
            yield {"type": "question", "question": next_q}
            yield {"type": "progress", "stage": "product_discovery", **self.product.get_progress()}
        else:
            self.product.generate_product_docs()
            yield {"type": "message", "content": "All product questions answered. Documents generated."}
            self.advance_stage()
            yield {"type": "stage_change", "stage": self.current_stage, "index": self.current_stage_index, "total": len(self.STAGES)}

    async def _handle_feature_extraction(self, message: str) -> AsyncGenerator[dict[str, Any], None]:
        """Stage 4: Extract features from product context."""
        if self.features is None:
            self.features = AgentOSFeatures(
                self.project_dir, self.file_utils,
                self.intake.get_entities(), self._config,
            )

        if message == "__approve__":
            self.advance_stage()
            yield {"type": "stage_change", "stage": self.current_stage, "index": self.current_stage_index, "total": len(self.STAGES)}
            return

        # Feature extraction prompt is available for Claude-powered extraction
        prompt = self.features.get_feature_extraction_prompt()
        feature_list = self.features.get_feature_list()

        yield {
            "type": "features",
            "features": feature_list,
            "extraction_prompt": prompt,
        }
        yield {
            "type": "message",
            "content": f"Extracted {len(feature_list)} features. Review and approve to continue.",
        }

    async def _handle_gap_analysis(self, message: str) -> AsyncGenerator[dict[str, Any], None]:
        """Stage 5: Cross-layer gap detection."""
        if self.features is None:
            yield {"type": "error", "message": "Features not initialized"}
            return

        if message == "__approve__":
            self.advance_stage()
            yield {"type": "stage_change", "stage": self.current_stage, "index": self.current_stage_index, "total": len(self.STAGES)}
            return

        prompt = self.features.get_gap_analysis_prompt()
        gaps = self.features.get_all_gaps()

        yield {"type": "gaps", "gaps": gaps, "analysis_prompt": prompt}
        yield {
            "type": "message",
            "content": f"Gap analysis found {len(gaps)} items. Review and approve to continue.",
        }

    async def _handle_spec_generation(self, message: str) -> AsyncGenerator[dict[str, Any], None]:
        """Stage 6: Generate specs per feature."""
        if self.features is None:
            yield {"type": "error", "message": "Features not initialized"}
            return

        if self.mechanism is None:
            self.mechanism = AgentOSMechanism(
                self._config,
                self.standards.get_standards_summary(),
            )

        if self.specs is None:
            product_summary = self.product.get_product_summary() if self.product else ""
            self.specs = AgentOSSpecs(
                self.project_dir, self.file_utils,
                self.features, self.mechanism,
                self.standards.get_standards_summary(),
                product_summary,
            )

        if message == "__approve__":
            self.advance_stage()
            yield {"type": "stage_change", "stage": self.current_stage, "index": self.current_stage_index, "total": len(self.STAGES)}
            return

        # Provide spec generation prompts for each feature
        feature_list = self.features.get_feature_list()
        for feature in feature_list:
            yield {
                "type": "spec_preview",
                "feature_id": feature["id"],
                "feature_name": feature["name"],
                "generation_prompt": self.specs.get_spec_generation_prompt(feature),
            }

        yield {
            "type": "message",
            "content": f"Spec generation ready for {len(feature_list)} features.",
        }

    async def _handle_database_population(self, message: str) -> AsyncGenerator[dict[str, Any], None]:
        """Stage 7: Populate features.db from specs."""
        if self.features is None or self.specs is None:
            yield {"type": "error", "message": "Features or specs not initialized"}
            return

        if self.handoff is None:
            self.handoff = AgentOSHandoff(
                self.project_dir, self.file_utils,
                self.features, self.specs, self.mechanism,
            )

        if message == "__approve__":
            self.advance_stage()
            yield {"type": "stage_change", "stage": self.current_stage, "index": self.current_stage_index, "total": len(self.STAGES)}
            return

        # Populate features.db
        try:
            count = self.handoff.populate_features_db()
            graph = self.handoff.generate_dependency_graph()
            build_order = self.handoff.calculate_build_order()
            yield {
                "type": "message",
                "content": f"Populated features.db with {count} features. Dependency graph: {graph['edges']} edges, valid={graph['valid']}.",
            }
            yield {
                "type": "progress",
                "stage": "database_population",
                "feature_count": count,
                "graph": graph,
                "build_order": build_order,
            }
        except Exception as e:
            yield {"type": "error", "message": f"Database population failed: {e}"}

    async def _handle_handoff(self, message: str) -> AsyncGenerator[dict[str, Any], None]:
        """Stage 8: Assemble and verify handoff package."""
        if self.handoff is None:
            yield {"type": "error", "message": "Handoff not initialized"}
            return

        # Generate scope boundary and context primer
        try:
            self.handoff.generate_scope_boundary()
            self.handoff.generate_context_primer()
        except Exception as e:
            logger.warning("Handoff generation warning: %s", e)

        status = self.handoff.assemble_handoff_package()

        if status["ready"]:
            self.complete = True
            yield {"type": "handoff_ready", "status": status}
            yield {
                "type": "complete",
                "handoff": status,
                "build_plan": self.handoff.get_build_plan_summary(),
            }
        else:
            yield {
                "type": "message",
                "content": f"Handoff not ready. Missing: {', '.join(status['missing'])}",
            }
            yield {"type": "handoff_ready", "status": status}

    # ── Stage navigation ────────────────────────────────────────────

    def advance_stage(self) -> str:
        """Move to the next stage. Returns the new stage name."""
        if self.current_stage_index < len(self.STAGES) - 1:
            self.current_stage_index += 1
            self.current_stage = self.STAGES[self.current_stage_index]
        return self.current_stage

    def get_stage(self) -> str:
        return self.current_stage

    def get_progress(self) -> dict[str, Any]:
        return {
            "current_stage": self.current_stage,
            "stage_index": self.current_stage_index,
            "total_stages": len(self.STAGES),
        }

    def is_complete(self) -> bool:
        return self.complete

    def get_messages(self) -> list[dict[str, Any]]:
        return list(self.messages)


# ── Session registry (thread-safe, follows spec_chat_session.py) ────

_sessions: dict[str, AgentOSSession] = {}
_sessions_lock = threading.Lock()


def get_session(project_name: str) -> Optional[AgentOSSession]:
    with _sessions_lock:
        return _sessions.get(project_name)


def create_session(project_name: str, project_dir: Path) -> AgentOSSession:
    with _sessions_lock:
        _sessions.pop(project_name, None)
        session = AgentOSSession(project_name, project_dir)
        _sessions[project_name] = session
    return session


async def remove_session(project_name: str) -> None:
    with _sessions_lock:
        _sessions.pop(project_name, None)


def list_sessions() -> list[str]:
    with _sessions_lock:
        return list(_sessions.keys())


async def cleanup_all_agent_os_sessions() -> None:
    """Close all active sessions. Called on server shutdown."""
    with _sessions_lock:
        _sessions.clear()
