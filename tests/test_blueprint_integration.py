"""Integration tests for the blueprint pipeline — [ROBOT], no LLM calls."""

import asyncio

from server.models.tool_factory import IngestionSource, StepType
from server.services.sheet_blueprint import generate_blueprint
from server.services.tool_registry import ToolRegistryService


def _mock_steps() -> list[dict]:
    """5 mock YTStrategyStep objects simulating a Meta Ads pipeline."""
    return [
        {
            "id": "s1",
            "order": 1,
            "title": "Research Ideal Customer Profile",
            "description": "Analyze target audience",
            "prompt": "Research the ideal customer profile for {niche}. Identify demographics, pain points, and buying triggers.",
            "expectedOutput": "ICP document with 3-5 customer segments",
            "notes": "",
            "model": "sonnet",
        },
        {
            "id": "s2",
            "order": 2,
            "title": "Generate Ad Copy Variations",
            "description": "Create ad copy",
            "prompt": "Generate 40 ad copy variations targeting the ICP from the previous step. Use {niche} terminology.",
            "expectedOutput": "40 ad copy variations in a table format",
            "notes": "Focus on hooks",
            "model": "sonnet",
        },
        {
            "id": "s3",
            "order": 3,
            "title": "Design Ad Creatives",
            "description": "Create visual assets",
            "prompt": "Design 10 ad creative concepts using canva for {niche} facebook ads campaign",
            "expectedOutput": "10 ad creative mockups",
            "notes": "",
            "model": "opus",
        },
        {
            "id": "s4",
            "order": 4,
            "title": "Review and Approve",
            "description": "Human review gate",
            "prompt": "Review all ad copy and creatives. Approve the top 10 combinations.",
            "expectedOutput": "Approved ad set list",
            "notes": "",
            "model": "sonnet",
        },
        {
            "id": "s5",
            "order": 5,
            "title": "Upload to Meta Ads",
            "description": "Deploy campaigns",
            "prompt": "Upload the approved ads to facebook ads manager. Set {budget} daily budget targeting {target_audience}.",
            "expectedOutput": "Campaign IDs and status report",
            "notes": "",
            "model": "sonnet",
        },
    ]


class TestFullPipelineMockSteps:
    def test_full_pipeline_mock_steps(self):
        """5 mock YTStrategyStep objects → SheetBlueprint with correct chain wiring."""
        steps = _mock_steps()
        bp = asyncio.get_event_loop().run_until_complete(
            generate_blueprint(
                project_name="Meta Ads Pipeline",
                project_description="Full Meta ads setup from research to deployment",
                steps=steps,
                source_video_id="abc123",
                source_video_title="How to Set Up Meta Ads",
                source_video_channel="Marketing Pro",
                source_project_id="proj_meta",
                skip_prompt_conversion=True,
            )
        )

        # 5 steps → 5 chain rows
        assert len(bp.chain_config) == 5

        # Chain wiring
        assert bp.chain_config[0].input_source == "user_input"
        assert bp.chain_config[1].input_source == "row_1"
        assert bp.chain_config[4].input_source == "row_4"

        # Step classifications
        assert bp.chain_config[0].step_type == StepType.RESEARCH
        assert bp.chain_config[1].step_type == StepType.GENERATION
        assert bp.chain_config[2].step_type == StepType.GENERATION  # "design" is a generation signal
        assert bp.chain_config[3].step_type == StepType.MANUAL  # "review and approve"
        assert bp.chain_config[4].step_type == StepType.ACTION  # "upload to"

        # Gate detection
        assert bp.chain_config[3].is_gate is True  # MANUAL = gate
        assert bp.chain_config[0].is_gate is False

        # API detection
        api_keys = {a.service_key for a in bp.detected_apis}
        assert "meta_marketing" in api_keys  # "facebook ads" detected
        assert "canva" in api_keys  # "canva" detected

        # Variable extraction
        assert "niche" in bp.user_input_variables
        assert "budget" in bp.user_input_variables
        assert "target_audience" in bp.user_input_variables

        # Model normalization
        assert bp.chain_config[2].model_recommendation == "opus"
        assert bp.chain_config[0].model_recommendation == "sonnet"


class TestRegistryEndpointCRUD:
    def test_registry_crud(self, tmp_path):
        """Create → list → get → archive cycle."""
        loop = asyncio.get_event_loop()
        registry = ToolRegistryService(registry_path=tmp_path / "test.json")

        steps = _mock_steps()
        bp = loop.run_until_complete(
            generate_blueprint(
                project_name="Test",
                project_description="Test tool",
                steps=steps,
                skip_prompt_conversion=True,
            )
        )

        # Create
        tool = loop.run_until_complete(registry.create_tool(bp))
        assert tool.tool_id.startswith("tool_")

        # List
        tools = loop.run_until_complete(registry.list_tools())
        assert len(tools) == 1

        # Get
        found = loop.run_until_complete(registry.get_tool(tool.tool_id))
        assert found is not None
        assert found.blueprint.tool_name == "Test"

        # Archive
        archived = loop.run_until_complete(registry.archive_tool(tool.tool_id))
        assert archived.status.value == "archived"

        # Verify archived tools show up correctly
        active = loop.run_until_complete(registry.list_tools(status=ToolStatus.DRAFT))
        assert len(active) == 0


class TestBlueprintFromPRD:
    def test_blueprint_from_prd_steps(self):
        """Mock PRD content → normalized steps → blueprint (no actual Claude call)."""
        # Simulate what extract_steps_from_prd would return after Claude processes
        prd_steps = [
            {
                "order": 1,
                "title": "Define Requirements",
                "description": "Gather project requirements",
                "prompt": "Analyze the PRD and extract key requirements for {product_name}",
                "expectedOutput": "Requirements document",
                "notes": "",
                "model": "sonnet",
            },
            {
                "order": 2,
                "title": "Generate Implementation Plan",
                "description": "Create a plan",
                "prompt": "Generate a detailed implementation plan based on the requirements",
                "expectedOutput": "Implementation plan with timelines",
                "notes": "",
                "model": "sonnet",
            },
            {
                "order": 3,
                "title": "Review Plan",
                "description": "Human approval",
                "prompt": "Review and approve the implementation plan",
                "expectedOutput": "Approved plan",
                "notes": "",
                "model": "sonnet",
            },
        ]

        from server.services.prd_ingestion import normalize_prd_steps
        normalized = normalize_prd_steps(prd_steps)

        bp = asyncio.get_event_loop().run_until_complete(
            generate_blueprint(
                project_name="PRD Project",
                project_description="From PRD",
                steps=normalized,
                ingestion_source=IngestionSource.PRD_UPLOAD,
                source_prd_id="prd_test123",
                skip_prompt_conversion=True,
            )
        )

        assert bp.ingestion_source == IngestionSource.PRD_UPLOAD
        assert bp.source_prd_id == "prd_test123"
        assert len(bp.chain_config) == 3
        assert "product_name" in bp.user_input_variables


# Need this import for the status filter test
from server.models.tool_factory import ToolStatus
