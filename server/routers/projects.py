"""
Projects Router
===============

API endpoints for project management.
Uses project registry for path lookups instead of fixed generations/ directory.
"""

import re
import shutil
import sys
from pathlib import Path
from typing import Any, Callable

from fastapi import APIRouter, HTTPException

from ..schemas import (
    ProjectCreate,
    ProjectDetail,
    ProjectPrompts,
    ProjectPromptsUpdate,
    ProjectSettingsUpdate,
    ProjectStats,
    ProjectSummary,
)

# Lazy imports to avoid circular dependencies
# These are initialized by _init_imports() before first use.
_imports_initialized = False
_check_spec_exists: Callable[..., Any] | None = None
_scaffold_project_prompts: Callable[..., Any] | None = None
_get_project_prompts_dir: Callable[..., Any] | None = None
_count_passing_tests: Callable[..., Any] | None = None


def _init_imports():
    """Lazy import of project-level modules."""
    global _imports_initialized, _check_spec_exists
    global _scaffold_project_prompts, _get_project_prompts_dir
    global _count_passing_tests

    if _imports_initialized:
        return

    import sys
    root = Path(__file__).parent.parent.parent
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

    from progress import count_passing_tests
    from prompts import get_project_prompts_dir, scaffold_project_prompts
    from start import check_spec_exists

    _check_spec_exists = check_spec_exists
    _scaffold_project_prompts = scaffold_project_prompts
    _get_project_prompts_dir = get_project_prompts_dir
    _count_passing_tests = count_passing_tests
    _imports_initialized = True


def _get_registry_functions():
    """Get registry functions with lazy import."""
    import sys
    root = Path(__file__).parent.parent.parent
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

    from registry import (
        get_project_concurrency,
        get_project_path,
        list_registered_projects,
        register_project,
        set_project_concurrency,
        unregister_project,
        validate_project_path,
    )
    return (
        register_project,
        unregister_project,
        get_project_path,
        list_registered_projects,
        validate_project_path,
        get_project_concurrency,
        set_project_concurrency,
    )


from ..services.boilerplate_manager import (
    clone_boilerplate,
    get_boilerplate_registry,
    load_project_config,
    save_project_config,
)
from ..services.style_manager import (
    ACCENT_COMPATIBILITY,
    get_accent_styles,
    get_audience_profiles,
    get_style_guide_markdown,
    get_style_option,
    get_style_registry,
    recommend_styles,
    save_style_guide,
)
from ..services.style_modifiers import get_modifier_registry

router = APIRouter(prefix="/api/projects", tags=["projects"])


boilerplate_router = APIRouter(prefix="/api/boilerplates", tags=["boilerplates"])


@boilerplate_router.get("")
async def list_boilerplates():
    """Return the available boilerplate templates organized by category."""
    return get_boilerplate_registry()


styles_router = APIRouter(prefix="/api/styles", tags=["styles"])


@styles_router.get("")
async def list_styles(include_tokens: bool = False):
    """Return all available UI design styles.

    Args:
        include_tokens: If True, include full style_guide with color tokens,
            typography, components, and spacing data for rendering UI previews.
    """
    return get_style_registry(include_tokens=include_tokens)


@styles_router.get("/profiles")
async def get_profiles():
    """Return audience, vibe, and age group profiles for style recommendation."""
    return get_audience_profiles()


@styles_router.get("/recommend")
async def get_recommendations(
    audience: str | None = None,
    vibe: str | None = None,
    age_group: str | None = None,
):
    """Recommend UI styles based on audience, vibe, and age group."""
    return recommend_styles(audience, vibe, age_group)


@styles_router.get("/modifiers")
async def list_modifiers(include_tokens: bool = False):
    """Return all available accessibility modifiers.

    Args:
        include_tokens: If True, include full token_overrides for each modifier.
            Used by the live preview engine to apply modifier effects visually.
    """
    return get_modifier_registry(include_tokens=include_tokens)


@styles_router.get("/combinations")
async def get_style_combinations():
    """Return all pre-validated base+accent combinations."""
    combos = []
    for accent_id, compat in ACCENT_COMPATIBILITY.items():
        accent_style = get_style_option(accent_id)
        if not accent_style:
            continue
        for base_id in compat["works_as_accent_for"]:
            base_style = get_style_option(base_id)
            if not base_style:
                continue
            combos.append({
                "base_id": base_id,
                "base_name": base_style["name"],
                "accent_id": accent_id,
                "accent_name": accent_style["name"],
            })
    return combos


# ============================================================================
# Description-based style recommendation helpers
# ============================================================================


def _extract_audience(description: str) -> str | None:
    """Extract audience signal from app description using keyword matching."""
    keywords: dict[str, list[str]] = {
        "health_50plus": [
            "health", "medical", "diabetes", "diabetic", "elderly", "senior", "blood pressure",
            "medication", "prescription", "wellness", "fitness tracker", "heart rate",
            "glucose", "sugar", "glycemic", "nutrition label", "barcode",
        ],
        "young_edgy": [
            "gen z", "tiktok", "social", "meme", "trend", "viral", "influencer",
            "streetwear", "sneaker", "music", "playlist", "festival",
        ],
        "premium_luxury": [
            "luxury", "premium", "exclusive", "boutique", "high-end", "concierge",
            "wealth", "investment", "portfolio", "vip", "membership",
        ],
        "friendly_approachable": [
            "kids", "family", "community", "recipe", "cooking", "pet",
            "garden", "hobby", "craft", "local", "neighborhood", "volunteer",
        ],
        "finance_dashboard": [
            "finance", "banking", "budget", "expense", "invoice", "accounting",
            "crypto", "stock", "trading", "analytics", "dashboard", "report",
        ],
        "gaming_entertainment": [
            "game", "gaming", "quiz", "trivia", "stream", "entertainment",
            "comic", "anime", "esport", "score", "leaderboard",
        ],
    }

    best_match = None
    best_score = 0
    for audience_key, words in keywords.items():
        score = sum(1 for w in words if w in description)
        if score > best_score:
            best_score = score
            best_match = audience_key

    return best_match if best_score > 0 else None


def _extract_vibe(description: str) -> str | None:
    """Extract vibe signal from app description."""
    keywords: dict[str, list[str]] = {
        "trustworthy": [
            "trust", "secure", "reliable", "professional", "accurate", "verified",
            "certified", "medical", "legal", "compliance", "safe",
        ],
        "fun": [
            "fun", "playful", "exciting", "party", "celebrate", "game", "social",
            "colorful", "creative", "silly", "casual",
        ],
        "modern": [
            "modern", "sleek", "cutting-edge", "innovative", "smart", "ai",
            "machine learning", "tech", "startup", "saas", "platform",
        ],
        "nostalgic": [
            "retro", "vintage", "classic", "throwback", "old school", "traditional",
            "heritage", "antique", "nostalgic",
        ],
        "edgy": [
            "edgy", "bold", "disruptive", "underground", "rebel", "punk",
            "dark", "gritty", "raw", "intense",
        ],
        "warm": [
            "warm", "cozy", "comfort", "home", "family", "gentle", "caring",
            "nurturing", "organic", "natural", "handmade",
        ],
    }

    best_match = None
    best_score = 0
    for vibe_key, words in keywords.items():
        score = sum(1 for w in words if w in description)
        if score > best_score:
            best_score = score
            best_match = vibe_key

    return best_match if best_score > 0 else None


def _extract_age_group(description: str) -> str | None:
    """Extract age group signal from app description."""
    young_keywords = [
        "teen", "student", "young", "gen z", "millennial", "college", "campus",
        "youth", "kid", "child",
    ]
    middle_keywords = [
        "professional", "adult", "working", "parent", "business", "enterprise",
        "corporate", "office",
    ]
    older_keywords = [
        "senior", "elderly", "retired", "aging", "50+", "60+", "70+", "older",
        "grandparent", "accessible", "low vision", "diabetic", "diabetes",
        "blood pressure", "medication",
    ]

    young_score = sum(1 for w in young_keywords if w in description)
    middle_score = sum(1 for w in middle_keywords if w in description)
    older_score = sum(1 for w in older_keywords if w in description)

    if older_score > young_score and older_score > middle_score:
        return "50plus"
    if young_score > middle_score:
        return "under_30"
    if middle_score > 0:
        return "30_50"

    return None


@styles_router.post("/recommend-from-description")
async def recommend_from_description(body: dict):
    """
    Accept a brief app description and return style recommendations.

    Uses keyword matching to map the description to audience/vibe/age signals,
    then feeds those into the existing recommendation engine.
    """
    description = body.get("description", "").lower()
    if not description or len(description) < 10:
        raise HTTPException(status_code=400, detail="Please provide at least a brief description (10+ characters)")

    audience = _extract_audience(description)
    vibe = _extract_vibe(description)
    age_group = _extract_age_group(description)

    recommendations = recommend_styles(audience, vibe, age_group)

    return {
        "detected_signals": {
            "audience": audience,
            "vibe": vibe,
            "age_group": age_group,
        },
        "recommendations": recommendations[:5],  # Top 5
    }


@styles_router.post("/extract-from-screenshot")
async def extract_from_screenshot(body: dict):
    """Accept a base64 image and return extracted style analysis.

    The image is sent to a vision-capable LLM which identifies the UI
    design style and extracts design tokens using the Idea Code methodology.
    """
    image_data = body.get("image")
    if not image_data:
        raise HTTPException(status_code=400, detail="No image provided")

    from ..services.style_extractor import extract_style_from_image
    try:
        result = await extract_style_from_image(image_data)
        return result
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))


@styles_router.get("/{style_id}")
async def get_style(style_id: str):
    """Return full details for a specific style including the complete style guide."""
    style = get_style_option(style_id)
    if not style:
        raise HTTPException(status_code=404, detail=f"Style '{style_id}' not found")
    return style


@styles_router.get("/{style_id}/guide")
async def get_style_guide(style_id: str):
    """Return the generated Markdown style guide for a given style."""
    guide = get_style_guide_markdown(style_id)
    if not guide:
        raise HTTPException(status_code=404, detail=f"Style '{style_id}' not found")
    return {"style_id": style_id, "markdown": guide}


@styles_router.get("/{style_id}/accent-compatibility")
async def get_accent_compatibility(style_id: str):
    """Return styles that work as accents for the given base style."""
    style = get_style_option(style_id)
    if not style:
        raise HTTPException(status_code=404, detail=f"Style '{style_id}' not found")
    return get_accent_styles(style_id)


def validate_project_name(name: str) -> str:
    """Validate and sanitize project name to prevent path traversal."""
    if not re.match(r'^[a-zA-Z0-9_-]{1,50}$', name):
        raise HTTPException(
            status_code=400,
            detail="Invalid project name. Use only letters, numbers, hyphens, and underscores (1-50 chars)."
        )
    return name


def get_project_stats(project_dir: Path) -> ProjectStats:
    """Get statistics for a project."""
    _init_imports()
    assert _count_passing_tests is not None  # guaranteed by _init_imports()
    passing, in_progress, total = _count_passing_tests(project_dir)
    percentage = (passing / total * 100) if total > 0 else 0.0
    return ProjectStats(
        passing=passing,
        in_progress=in_progress,
        total=total,
        percentage=round(percentage, 1)
    )


@router.get("", response_model=list[ProjectSummary])
async def list_projects():
    """List all registered projects."""
    _init_imports()
    assert _check_spec_exists is not None  # guaranteed by _init_imports()
    (_, _, _, list_registered_projects, validate_project_path,
     get_project_concurrency, _) = _get_registry_functions()

    projects = list_registered_projects()
    result = []

    for name, info in projects.items():
        project_dir = Path(info["path"])

        # Skip if path no longer exists
        is_valid, _ = validate_project_path(project_dir)
        if not is_valid:
            continue

        has_spec = _check_spec_exists(project_dir)
        stats = get_project_stats(project_dir)

        # Load boilerplate/style info from project config
        project_config = load_project_config(project_dir)
        bp_id = None
        st_id = None
        if project_config:
            bp_info = project_config.get("boilerplate")
            bp_id = bp_info.get("option_id") if isinstance(bp_info, dict) else None
            st_id = project_config.get("style")

        result.append(ProjectSummary(
            name=name,
            path=info["path"],
            has_spec=has_spec,
            stats=stats,
            default_concurrency=info.get("default_concurrency", 3),
            boilerplate_id=bp_id,
            style_id=st_id,
        ))

    return result


@router.post("", response_model=ProjectSummary)
async def create_project(project: ProjectCreate):
    """Create a new project at the specified path."""
    _init_imports()
    assert _scaffold_project_prompts is not None  # guaranteed by _init_imports()
    (register_project, _, get_project_path, list_registered_projects,
     _, _, _) = _get_registry_functions()

    name = validate_project_name(project.name)
    project_path = Path(project.path).resolve()

    # Check if project name already registered
    existing = get_project_path(name)
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Project '{name}' already exists at {existing}"
        )

    # Check if path already registered under a different name
    all_projects = list_registered_projects()
    for existing_name, info in all_projects.items():
        existing_path = Path(info["path"]).resolve()
        # Case-insensitive comparison on Windows
        if sys.platform == "win32":
            paths_match = str(existing_path).lower() == str(project_path).lower()
        else:
            paths_match = existing_path == project_path

        if paths_match:
            raise HTTPException(
                status_code=409,
                detail=f"Path '{project_path}' is already registered as project '{existing_name}'"
            )

    # Security: Check if path is in a blocked location
    from .filesystem import is_path_blocked
    if is_path_blocked(project_path):
        raise HTTPException(
            status_code=403,
            detail="Cannot create project in system or sensitive directory"
        )

    boilerplate_id = project.boilerplate_id
    style_id = project.style_id
    needs_clone = boilerplate_id and boilerplate_id != "scratch"

    # For boilerplate clone: target dir must NOT exist (git clone creates it)
    # For scratch/no boilerplate: create the dir if needed
    if needs_clone:
        if project_path.exists():
            # Directory exists - check if empty (ok) or non-empty (error)
            if any(project_path.iterdir()):
                raise HTTPException(
                    status_code=400,
                    detail="Directory must be empty for boilerplate clone"
                )
            # Remove empty dir so git clone can create it
            project_path.rmdir()

        # Clone the boilerplate repo
        try:
            await clone_boilerplate(boilerplate_id, project_path)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except RuntimeError as e:
            raise HTTPException(status_code=500, detail=str(e))
    else:
        # Standard flow: create directory if needed
        if project_path.exists():
            if not project_path.is_dir():
                raise HTTPException(
                    status_code=400,
                    detail="Path exists but is not a directory"
                )
        else:
            try:
                project_path.mkdir(parents=True, exist_ok=True)
            except OSError as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to create directory: {e}"
                )

    # Scaffold prompts
    _scaffold_project_prompts(project_path)

    # Save project config (boilerplate + style choices + modifiers + custom colors + accent + palette)
    custom_colors = project.custom_colors or None
    accent_style = project.accent_style
    palette_id = project.palette_id
    if boilerplate_id:
        save_project_config(
            project_path,
            boilerplate_id,
            style_id,
            modifier_ids=project.modifier_ids or None,
            custom_colors=custom_colors if custom_colors else None,
            accent_style=accent_style,
            palette_id=palette_id,
        )

    # Save style guide if a style was selected (with custom color overrides and optional accent)
    if style_id:
        save_style_guide(project_path, style_id, custom_colors=custom_colors, accent_id=accent_style)

    # Register in registry
    try:
        register_project(name, project_path)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to register project: {e}"
        )

    return ProjectSummary(
        name=name,
        path=project_path.as_posix(),
        has_spec=False,  # Just created, no spec yet
        stats=ProjectStats(passing=0, total=0, percentage=0.0),
        default_concurrency=3,
        boilerplate_id=boilerplate_id,
        style_id=style_id,
    )


@router.get("/{name}", response_model=ProjectDetail)
async def get_project(name: str):
    """Get detailed information about a project."""
    _init_imports()
    assert _check_spec_exists is not None  # guaranteed by _init_imports()
    assert _get_project_prompts_dir is not None  # guaranteed by _init_imports()
    (_, _, get_project_path, _, _, get_project_concurrency, _) = _get_registry_functions()

    name = validate_project_name(name)
    project_dir = get_project_path(name)

    if not project_dir:
        raise HTTPException(status_code=404, detail=f"Project '{name}' not found in registry")

    if not project_dir.exists():
        raise HTTPException(status_code=404, detail=f"Project directory no longer exists: {project_dir}")

    has_spec = _check_spec_exists(project_dir)
    stats = get_project_stats(project_dir)
    prompts_dir = _get_project_prompts_dir(project_dir)

    project_config = load_project_config(project_dir)
    bp_id = None
    st_id = None
    if project_config:
        bp_info = project_config.get("boilerplate")
        bp_id = bp_info.get("option_id") if isinstance(bp_info, dict) else None
        st_id = project_config.get("style")

    return ProjectDetail(
        name=name,
        path=project_dir.as_posix(),
        has_spec=has_spec,
        stats=stats,
        prompts_dir=str(prompts_dir),
        default_concurrency=get_project_concurrency(name),
        boilerplate_id=bp_id,
        style_id=st_id,
    )


@router.delete("/{name}")
async def delete_project(name: str, delete_files: bool = False):
    """
    Delete a project from the registry.

    Args:
        name: Project name to delete
        delete_files: If True, also delete the project directory and files
    """
    _init_imports()
    (_, unregister_project, get_project_path, _, _, _, _) = _get_registry_functions()

    name = validate_project_name(name)
    project_dir = get_project_path(name)

    if not project_dir:
        raise HTTPException(status_code=404, detail=f"Project '{name}' not found")

    # Check if agent is running
    from autoforge_paths import has_agent_running
    if has_agent_running(project_dir):
        raise HTTPException(
            status_code=409,
            detail="Cannot delete project while agent is running. Stop the agent first."
        )

    # Optionally delete files
    if delete_files and project_dir.exists():
        try:
            shutil.rmtree(project_dir)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to delete project files: {e}")

    # Unregister from registry
    unregister_project(name)

    return {
        "success": True,
        "message": f"Project '{name}' deleted" + (" (files removed)" if delete_files else " (files preserved)")
    }


@router.get("/{name}/prompts", response_model=ProjectPrompts)
async def get_project_prompts(name: str):
    """Get the content of project prompt files."""
    _init_imports()
    assert _get_project_prompts_dir is not None  # guaranteed by _init_imports()
    (_, _, get_project_path, _, _, _, _) = _get_registry_functions()

    name = validate_project_name(name)
    project_dir = get_project_path(name)

    if not project_dir:
        raise HTTPException(status_code=404, detail=f"Project '{name}' not found")

    if not project_dir.exists():
        raise HTTPException(status_code=404, detail="Project directory not found")

    prompts_dir: Path = _get_project_prompts_dir(project_dir)

    def read_file(filename: str) -> str:
        filepath = prompts_dir / filename
        if filepath.exists():
            try:
                return filepath.read_text(encoding="utf-8")
            except Exception:
                return ""
        return ""

    return ProjectPrompts(
        app_spec=read_file("app_spec.txt"),
        initializer_prompt=read_file("initializer_prompt.md"),
        coding_prompt=read_file("coding_prompt.md"),
    )


@router.put("/{name}/prompts")
async def update_project_prompts(name: str, prompts: ProjectPromptsUpdate):
    """Update project prompt files."""
    _init_imports()
    assert _get_project_prompts_dir is not None  # guaranteed by _init_imports()
    (_, _, get_project_path, _, _, _, _) = _get_registry_functions()

    name = validate_project_name(name)
    project_dir = get_project_path(name)

    if not project_dir:
        raise HTTPException(status_code=404, detail=f"Project '{name}' not found")

    if not project_dir.exists():
        raise HTTPException(status_code=404, detail="Project directory not found")

    prompts_dir = _get_project_prompts_dir(project_dir)
    prompts_dir.mkdir(parents=True, exist_ok=True)

    def write_file(filename: str, content: str | None):
        if content is not None:
            filepath = prompts_dir / filename
            filepath.write_text(content, encoding="utf-8")

    write_file("app_spec.txt", prompts.app_spec)
    write_file("initializer_prompt.md", prompts.initializer_prompt)
    write_file("coding_prompt.md", prompts.coding_prompt)

    return {"success": True, "message": "Prompts updated"}


@router.get("/{name}/stats", response_model=ProjectStats)
async def get_project_stats_endpoint(name: str):
    """Get current progress statistics for a project."""
    _init_imports()
    (_, _, get_project_path, _, _, _, _) = _get_registry_functions()

    name = validate_project_name(name)
    project_dir = get_project_path(name)

    if not project_dir:
        raise HTTPException(status_code=404, detail=f"Project '{name}' not found")

    if not project_dir.exists():
        raise HTTPException(status_code=404, detail="Project directory not found")

    return get_project_stats(project_dir)


@router.post("/{name}/reset")
async def reset_project(name: str, full_reset: bool = False):
    """
    Reset a project to its initial state.

    Args:
        name: Project name to reset
        full_reset: If True, also delete prompts/ directory (triggers setup wizard)

    Returns:
        Dictionary with list of deleted files and reset type
    """
    _init_imports()
    (_, _, get_project_path, _, _, _, _) = _get_registry_functions()

    name = validate_project_name(name)
    project_dir = get_project_path(name)

    if not project_dir:
        raise HTTPException(status_code=404, detail=f"Project '{name}' not found")

    if not project_dir.exists():
        raise HTTPException(status_code=404, detail="Project directory not found")

    # Check if agent is running
    from autoforge_paths import has_agent_running
    if has_agent_running(project_dir):
        raise HTTPException(
            status_code=409,
            detail="Cannot reset project while agent is running. Stop the agent first."
        )

    # Dispose of database engines to release file locks (required on Windows)
    # Import here to avoid circular imports
    from api.database import dispose_engine as dispose_features_engine
    from server.services.assistant_database import dispose_engine as dispose_assistant_engine

    dispose_features_engine(project_dir)
    dispose_assistant_engine(project_dir)

    deleted_files: list[str] = []

    from autoforge_paths import (
        get_assistant_db_path,
        get_claude_assistant_settings_path,
        get_claude_settings_path,
        get_features_db_path,
    )

    # Build list of files to delete using path helpers (finds files at current location)
    # Plus explicit old-location fallbacks for backward compatibility
    db_path = get_features_db_path(project_dir)
    asst_path = get_assistant_db_path(project_dir)
    reset_files: list[Path] = [
        db_path,
        db_path.with_suffix(".db-wal"),
        db_path.with_suffix(".db-shm"),
        asst_path,
        asst_path.with_suffix(".db-wal"),
        asst_path.with_suffix(".db-shm"),
        get_claude_settings_path(project_dir),
        get_claude_assistant_settings_path(project_dir),
        # Also clean old root-level locations if they exist
        project_dir / "features.db",
        project_dir / "features.db-wal",
        project_dir / "features.db-shm",
        project_dir / "assistant.db",
        project_dir / "assistant.db-wal",
        project_dir / "assistant.db-shm",
        project_dir / ".claude_settings.json",
        project_dir / ".claude_assistant_settings.json",
    ]

    for file_path in reset_files:
        if file_path.exists():
            try:
                relative = file_path.relative_to(project_dir)
                file_path.unlink()
                deleted_files.append(str(relative))
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to delete {file_path.name}: {e}")

    # Full reset: also delete prompts directory
    if full_reset:
        from autoforge_paths import get_prompts_dir
        # Delete prompts from both possible locations
        for prompts_dir in [get_prompts_dir(project_dir), project_dir / "prompts"]:
            if prompts_dir.exists():
                try:
                    relative = prompts_dir.relative_to(project_dir)
                    shutil.rmtree(prompts_dir)
                    deleted_files.append(f"{relative}/")
                except Exception as e:
                    raise HTTPException(status_code=500, detail=f"Failed to delete prompts: {e}")

    return {
        "success": True,
        "reset_type": "full" if full_reset else "quick",
        "deleted_files": deleted_files,
        "message": f"Project '{name}' has been reset" + (" (full reset)" if full_reset else " (quick reset)")
    }


@router.patch("/{name}/settings", response_model=ProjectDetail)
async def update_project_settings(name: str, settings: ProjectSettingsUpdate):
    """Update project-level settings (concurrency, etc.)."""
    _init_imports()
    assert _check_spec_exists is not None  # guaranteed by _init_imports()
    assert _get_project_prompts_dir is not None  # guaranteed by _init_imports()
    (_, _, get_project_path, _, _, get_project_concurrency,
     set_project_concurrency) = _get_registry_functions()

    name = validate_project_name(name)
    project_dir = get_project_path(name)

    if not project_dir:
        raise HTTPException(status_code=404, detail=f"Project '{name}' not found")

    if not project_dir.exists():
        raise HTTPException(status_code=404, detail="Project directory not found")

    # Update concurrency if provided
    if settings.default_concurrency is not None:
        success = set_project_concurrency(name, settings.default_concurrency)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update concurrency")

    # Return updated project details
    has_spec = _check_spec_exists(project_dir)
    stats = get_project_stats(project_dir)
    prompts_dir = _get_project_prompts_dir(project_dir)

    project_config = load_project_config(project_dir)
    settings_bp_id = None
    settings_st_id = None
    if project_config:
        bp_info = project_config.get("boilerplate")
        settings_bp_id = bp_info.get("option_id") if isinstance(bp_info, dict) else None
        settings_st_id = project_config.get("style")

    return ProjectDetail(
        name=name,
        path=project_dir.as_posix(),
        has_spec=has_spec,
        stats=stats,
        prompts_dir=str(prompts_dir),
        default_concurrency=get_project_concurrency(name),
        boilerplate_id=settings_bp_id,
        style_id=settings_st_id,
    )
