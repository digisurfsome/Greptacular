"""Unit tests for server/services/prd_ingestion.py — [ROBOT] functions only, no LLM calls."""


from server.services.prd_ingestion import (
    normalize_prd_steps,
    save_prd_upload,
    validate_prd_content,
)


class TestValidatePRDContent:
    def test_validate_prd_too_short(self):
        assert validate_prd_content("short") is False
        assert validate_prd_content("") is False
        assert validate_prd_content("   ") is False

    def test_validate_prd_valid(self):
        content = "# My PRD\n\n" + "This is a detailed PRD with sufficient content. " * 10
        assert validate_prd_content(content) is True

    def test_validate_prd_binary(self):
        content = "\x00\x01\x02" * 100
        assert validate_prd_content(content) is False


class TestNormalizePRDSteps:
    def test_normalize_prd_steps(self):
        raw = [
            {
                "order": 1,
                "title": "Step 1",
                "description": "First step",
                "prompt": "Do the first thing",
                "expectedOutput": "Result 1",
                "notes": "Note 1",
                "model": "sonnet",
            },
            {
                "order": 2,
                "title": "Step 2",
                "prompt": "Do the second thing",
            },
        ]
        normalized = normalize_prd_steps(raw)
        assert len(normalized) == 2

        # First step has all fields
        assert normalized[0]["order"] == 1
        assert normalized[0]["title"] == "Step 1"
        assert normalized[0]["prompt"] == "Do the first thing"
        assert normalized[0]["expectedOutput"] == "Result 1"

        # Second step has defaults
        assert normalized[1]["order"] == 2
        assert normalized[1]["title"] == "Step 2"
        assert normalized[1]["expectedOutput"] == ""
        assert "id" in normalized[1]

    def test_normalize_prd_steps_with_expected_output_variant(self):
        """Test that 'expected_output' (snake_case) is handled as well."""
        raw = [
            {
                "order": 1,
                "title": "Step 1",
                "prompt": "Do something",
                "expected_output": "Some result",
            },
        ]
        normalized = normalize_prd_steps(raw)
        assert normalized[0]["expectedOutput"] == "Some result"


class TestSavePRDUpload:
    def test_save_prd_upload(self, tmp_path, monkeypatch):
        # Redirect the uploads dir to tmp
        monkeypatch.setattr(
            "server.services.prd_ingestion._prd_uploads_dir",
            lambda: tmp_path / "prd_uploads",
        )

        content = "# Test PRD\n\nThis is a test PRD document with enough content for validation."
        prd = save_prd_upload("test_prd.md", content)

        assert prd.prd_id.startswith("prd_")
        assert prd.filename == "test_prd.md"
        assert prd.source == "upload"

        # Verify file was saved
        saved_file = tmp_path / "prd_uploads" / f"{prd.prd_id}.md"
        assert saved_file.exists()
        assert saved_file.read_text(encoding="utf-8") == content

        # Verify metadata was saved
        meta_file = tmp_path / "prd_uploads" / f"{prd.prd_id}.meta.json"
        assert meta_file.exists()
