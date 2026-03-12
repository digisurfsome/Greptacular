"""Unit tests for server/services/sheet_blueprint.py — all [ROBOT] functions, no LLM calls."""

import asyncio

from server.models.tool_factory import IngestionSource, StepType
from server.services.sheet_blueprint import (
    assemble_blueprint,
    classify_step,
    compute_input_source,
    detect_apis,
    detect_prior_references,
    extract_user_variables,
    filter_and_validate,
    generate_blueprint,
)


def _step(title: str, prompt: str, **kwargs) -> dict:
    """Helper to create a step dict."""
    return {
        "id": kwargs.get("id", "s1"),
        "order": kwargs.get("order", 1),
        "title": title,
        "description": kwargs.get("description", ""),
        "prompt": prompt,
        "expectedOutput": kwargs.get("expectedOutput", "output"),
        "notes": kwargs.get("notes", ""),
        "model": kwargs.get("model", "sonnet"),
    }


class TestClassifyStep:
    def test_classify_step_action(self):
        step = _step("Upload to Meta", "upload the campaign to facebook ads")
        assert classify_step(step) == StepType.ACTION

    def test_classify_step_manual(self):
        step = _step("Review Results", "review and approve the final output")
        assert classify_step(step) == StepType.MANUAL

    def test_classify_step_generation(self):
        step = _step("Generate Ad Copy", "generate 40 ad copy variations")
        assert classify_step(step) == StepType.GENERATION

    def test_classify_step_default_research(self):
        step = _step("Analyze Competitors", "analyze the top competitors in the space")
        assert classify_step(step) == StepType.RESEARCH


class TestDetectAPIs:
    def test_detect_apis_meta(self):
        steps = [_step("Ad Setup", "set up facebook ads campaign")]
        apis = detect_apis(steps)
        assert len(apis) == 1
        assert apis[0].service_key == "meta_marketing"

    def test_detect_apis_multiple(self):
        steps = [
            _step("Research", "use gpt to analyze and then set up facebook ads"),
            _step("Track", "integrate with stripe for payment processing"),
        ]
        apis = detect_apis(steps)
        keys = {a.service_key for a in apis}
        assert "openai" in keys
        assert "meta_marketing" in keys
        assert "stripe" in keys

    def test_detect_apis_none(self):
        steps = [_step("Think", "brainstorm ideas for the project")]
        apis = detect_apis(steps)
        assert len(apis) == 0


class TestExtractVariables:
    def test_extract_variables(self):
        steps = [
            _step("Research", "Research {niche} trends and {budget} allocation"),
        ]
        variables = extract_user_variables(steps)
        assert "niche" in variables
        assert "budget" in variables

    def test_extract_variables_skips_system(self):
        steps = [
            _step("Step", "Use {previousOutput} and {niche} for {row_number}"),
        ]
        variables = extract_user_variables(steps)
        assert "niche" in variables
        assert "previousOutput" not in variables
        assert "row_number" not in variables


class TestComputeInputSource:
    def test_compute_input_source_first(self):
        step = _step("First", "do something")
        result = compute_input_source(1, step, [step])
        assert result == "user_input"

    def test_compute_input_source_chain(self):
        step = _step("Third", "continue the work")
        result = compute_input_source(3, step, [_step("A", "a"), _step("B", "b"), step])
        assert result == "row_2"

    def test_compute_input_source_multi(self):
        step = _step("Merge", "combine results from step 1 and step 3")
        result = compute_input_source(4, step, [
            _step("A", "a"), _step("B", "b"), _step("C", "c"), step
        ])
        assert result == "row_1+row_3"


class TestDetectPriorReferences:
    def test_detect_step_references(self):
        refs = detect_prior_references("take output from step 2 and step 4", 5)
        assert refs == [2, 4]

    def test_detect_previous(self):
        refs = detect_prior_references("use the previous step's output", 3)
        assert refs == [2]

    def test_no_references(self):
        refs = detect_prior_references("do something new", 2)
        assert refs == []


class TestFilterAndValidate:
    def test_filter_and_validate(self):
        steps = [
            _step("Good Step", "has a prompt"),
            {"title": "", "prompt": "no title"},
            {"title": "No Prompt", "prompt": ""},
            _step("Another Good", "also has a prompt"),
        ]
        valid = filter_and_validate(steps)
        assert len(valid) == 2
        assert valid[0]["title"] == "Good Step"
        assert valid[1]["title"] == "Another Good"


class TestAssembleBlueprint:
    def test_assemble_blueprint(self):
        steps = [
            _step("Research", "research {niche} market", order=1, id="s1"),
            _step("Generate", "generate ad copy", order=2, id="s2"),
        ]
        bp = assemble_blueprint(
            project_name="Test Tool",
            project_description="A test tool",
            source_video_id="vid123",
            source_video_title="Test Video",
            source_video_channel="TestChannel",
            source_project_id="proj_1",
            steps=steps,
            converted_prompts=["converted prompt 1", "converted prompt 2"],
            detected_api_list=[],
            user_variables=["niche"],
        )
        assert bp.tool_name == "Test Tool"
        assert len(bp.chain_config) == 2
        assert bp.chain_config[0].input_source == "user_input"
        assert bp.chain_config[1].input_source == "row_1"
        assert bp.chain_config[0].output_destination == "row_1_output"
        assert bp.chain_config[1].output_destination == "row_2_output"
        assert bp.user_input_variables == ["niche"]
        assert bp.ingestion_source == IngestionSource.YOUTUBE


class TestGenerateBlueprint:
    def test_generate_blueprint_skip_conversion(self):
        """Test full pipeline with skip_prompt_conversion=True (no LLM)."""
        steps = [
            _step("Research ICP", "Research the ideal customer profile for {niche}", order=1, id="s1"),
            _step("Generate Ads", "Generate facebook ads based on ICP", order=2, id="s2"),
            _step("Review", "Review and approve the ads", order=3, id="s3"),
        ]
        bp = asyncio.get_event_loop().run_until_complete(
            generate_blueprint(
                project_name="Meta Ads Pipeline",
                project_description="Generate and deploy Meta ads",
                steps=steps,
                source_video_id="vid123",
                skip_prompt_conversion=True,
            )
        )
        assert bp.tool_name == "Meta Ads Pipeline"
        assert len(bp.chain_config) == 3

        # Check classifications
        assert bp.chain_config[0].step_type == StepType.RESEARCH
        assert bp.chain_config[1].step_type == StepType.GENERATION
        assert bp.chain_config[2].step_type == StepType.MANUAL
        assert bp.chain_config[2].is_gate is True  # MANUAL steps are gates

        # Check API detection
        api_keys = {a.service_key for a in bp.detected_apis}
        assert "meta_marketing" in api_keys

        # Check variables
        assert "niche" in bp.user_input_variables
