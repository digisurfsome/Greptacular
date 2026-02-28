"""
Boilerplate Template Manager
=============================

Manages boilerplate templates for the project creation flow.
Provides a registry of available starter templates organized by category
(web, mobile, web+mobile, scratch), along with functions to clone
boilerplate repositories and persist project configuration.
"""

import asyncio
import json
import logging
import shutil
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)


# =============================================================================
# Boilerplate Registry
# =============================================================================

# Each category contains a label for display and a list of template options.
# Options marked available=False are shown in the UI but cannot be selected.
BOILERPLATE_REGISTRY: dict[str, dict] = {
    "web": {
        "label": "Web Application",
        "options": [
            {
                "id": "web-supabase-stripe",
                "name": "SaaS Starter (Supabase + Stripe)",
                "description": "Full-stack SaaS with auth, payments, credits, admin panel, email",
                "tech_summary": "React 18 + TypeScript + Vite + Supabase + Stripe + Vercel",
                "repo_url": "https://github.com/digisurfsome/Gen-Ai",
                "available": True,
                "pre_built": [
                    "Authentication (email/password + OAuth)",
                    "Stripe subscriptions and one-time payments",
                    "Credit system with atomic operations",
                    "Admin dashboard (11 tabs)",
                    "User profiles and settings",
                    "Email system via Resend",
                    "Dark/light theme",
                    "49 shadcn/ui components",
                ],
            },
        ],
    },
    "mobile": {
        "label": "Mobile Application",
        "options": [
            {
                "id": "mobile-flutter-firebase",
                "name": "Flutter Starter (Firebase)",
                "description": "Full-featured Flutter app with Firebase auth, Firestore, subscriptions, analytics, and 30+ components",
                "tech_summary": "Flutter + Dart + Firebase (Auth, Firestore, Storage, Functions, Messaging, Remote Config) + Riverpod + RevenueCat + Mixpanel + Sentry + GoRouter + Freezed",
                "repo_url": "https://github.com/digisurfsome/apparence-kit-firebase",
                "available": True,
                "pre_built": [
                    "Authentication (email/password, Google, phone, anonymous)",
                    "Account linking (anonymous to authenticated)",
                    "Phone auth with OTP verification",
                    "RevenueCat subscription paywall with trial toggle",
                    "Feature comparison table (free vs premium)",
                    "Multi-step onboarding with progress tracking",
                    "Push notifications (Firebase + local scheduling)",
                    "Riverpod state management with code generation",
                    "GoRouter navigation with auth guards",
                    "Firestore database with offline persistence",
                    "Firebase Storage uploads with progress streaming",
                    "Cloud Functions integration (configurable region)",
                    "Firebase Remote Config for feature flags",
                    "Mixpanel analytics with route tracking",
                    "Facebook App Events with ATT handling",
                    "Sentry error reporting (production only)",
                    "Light/dark theme with persistence",
                    "Material 3 custom color and text system",
                    "Responsive layout system (4 breakpoints)",
                    "Slang i18n with code-generated translations",
                    "In-app review and rating prompts",
                    "Feature request voting system (feedback module)",
                    "User profile with avatar upload and compression",
                    "Settings page with account deletion",
                    "App update notification bottom sheet",
                    "Toast/snackbar system (success, error, alert)",
                    "Skeleton loading screens",
                    "Fade and slide animation utilities",
                    "Bottom navigation with tab-based routing",
                    "Freezed immutable models with JSON serialization",
                    "Dual environment system (dev + prod)",
                    "Permission handling (notifications, ATT, storage)",
                    "Secure token storage (FlutterSecureStorage)",
                    "Dio HTTP client with error handling",
                    "30+ reusable UI components",
                    "7 complete screens (auth, home, onboarding, paywall, notifications, feedback, settings)",
                    "GitHub Actions CI (analyze + test + build_runner)",
                    "Dependabot for dependency updates",
                    "Full test infrastructure with fake implementations",
                    "Social sign-in buttons (Google, Apple, Facebook, Microsoft, Twitter)",
                    "Password recovery flow",
                    "Google Mobile Ads infrastructure (ready to enable)",
                    "Deep linking support via GoRouter",
                    "404 error page",
                    "Notification permission onboarding step",
                    "iOS App Tracking Transparency consent flow",
                ],
            },
        ],
    },
    "web_mobile": {
        "label": "Web + Mobile",
        "options": [],
    },
    "scratch": {
        "label": "From Scratch",
        "options": [
            {
                "id": "scratch",
                "name": "No Boilerplate",
                "description": "Full control over tech stack and architecture",
                "tech_summary": "You decide during spec creation",
                "repo_url": None,
                "available": True,
                "pre_built": [],
            },
        ],
    },
}


# =============================================================================
# Registry Lookup
# =============================================================================


def get_boilerplate_registry() -> list[dict]:
    """
    Return the boilerplate registry as a JSON-serializable list of categories.

    Each entry contains the category key, display label, and the list of
    template options within that category.

    Returns:
        List of dicts, each with keys: category, label, options.
    """
    result: list[dict] = []
    for category_key, category_data in BOILERPLATE_REGISTRY.items():
        result.append({
            "category": category_key,
            "label": category_data["label"],
            "options": category_data["options"],
        })
    return result


def get_boilerplate_option(option_id: str) -> dict | None:
    """
    Find and return a specific boilerplate option by its unique ID.

    Searches across all categories in the registry.

    Args:
        option_id: The unique identifier of the boilerplate option
                   (e.g., "web-supabase-stripe", "scratch").

    Returns:
        The option dict if found, or None if no option matches the given ID.
    """
    for category_data in BOILERPLATE_REGISTRY.values():
        options: list[dict] = category_data["options"]
        for option in options:
            if option["id"] == option_id:
                return option
    return None


# =============================================================================
# Clone Operations
# =============================================================================


async def clone_boilerplate(option_id: str, target_dir: Path) -> dict:
    """
    Clone a boilerplate repository into the target directory.

    Performs a shallow clone of the template repo, removes the original
    .git history, and initializes a fresh git repository so the user
    starts with a clean commit history.

    Args:
        option_id: The unique identifier of the boilerplate option to clone.
        target_dir: Destination directory for the cloned template.
                    Must not already exist (git clone creates it).

    Returns:
        Dict with clone metadata:
        - status: "success"
        - option_id: The boilerplate option ID
        - option_name: Human-readable name of the template
        - target_dir: String path of the target directory
        - cloned_at: ISO 8601 timestamp of when the clone completed

    Raises:
        ValueError: If option_id is not found, the option has no repo_url,
                    or the option is not marked as available.
        RuntimeError: If the git clone or git init subprocess fails.
    """
    option = get_boilerplate_option(option_id)
    if option is None:
        raise ValueError(f"Unknown boilerplate option: {option_id}")

    repo_url = option.get("repo_url")
    if not repo_url:
        raise ValueError(f"Boilerplate option '{option_id}' has no repository URL")

    if not option.get("available", False):
        raise ValueError(f"Boilerplate option '{option_id}' is not currently available")

    # Clone the repository
    logger.info("Cloning boilerplate '%s' from %s into %s", option_id, repo_url, target_dir)
    clone_proc = await asyncio.create_subprocess_exec(
        "git", "clone", repo_url, str(target_dir),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    clone_stdout, clone_stderr = await clone_proc.communicate()

    if clone_proc.returncode != 0:
        error_msg = clone_stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"git clone failed (exit {clone_proc.returncode}): {error_msg}")

    # Remove the original .git directory so the user starts fresh
    git_dir = target_dir / ".git"
    if git_dir.exists():
        shutil.rmtree(git_dir)
        logger.debug("Removed original .git directory from %s", target_dir)

    # Initialize a new git repository
    init_proc = await asyncio.create_subprocess_exec(
        "git", "init",
        cwd=str(target_dir),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    init_stdout, init_stderr = await init_proc.communicate()

    if init_proc.returncode != 0:
        error_msg = init_stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"git init failed (exit {init_proc.returncode}): {error_msg}")

    logger.info("Successfully cloned boilerplate '%s' into %s", option_id, target_dir)

    return {
        "status": "success",
        "option_id": option_id,
        "option_name": option["name"],
        "target_dir": str(target_dir),
        "cloned_at": datetime.now(timezone.utc).isoformat(),
    }


# =============================================================================
# Project Configuration Persistence
# =============================================================================


def save_project_config(
    project_dir: Path,
    option_id: str,
    style_id: str | None = None,
    modifier_ids: list[str] | None = None,
    custom_colors: dict[str, str] | None = None,
    accent_style: str | None = None,
    palette_id: str | None = None,
) -> None:
    """
    Write a project_config.json file recording the boilerplate and style choices.

    The file is stored at ``{project_dir}/.autoforge/project_config.json`` and
    captures which boilerplate template was used to create the project, along
    with an optional UI style identifier and accessibility/style modifier IDs.

    Args:
        project_dir: Root directory of the project.
        option_id: The boilerplate option ID that was selected (e.g., "scratch").
        style_id: Optional style/theme identifier chosen during project creation.
        modifier_ids: Optional list of style modifier IDs (e.g., accessibility options).
                      Saved as ``style_modifiers`` in the config for prompt injection.
        custom_colors: Optional dict of color role overrides (e.g., {"primary": "#FF0000"}).
        accent_style: Optional accent style ID for interactive element overrides.
        palette_id: Optional preset palette ID from the palette strip.

    Raises:
        OSError: If the configuration file cannot be written.
    """
    option = get_boilerplate_option(option_id)

    config: dict = {
        "project_type": option_id,
        "boilerplate": {
            "option_id": option_id,
            "option_name": option["name"] if option else option_id,
            "tech_summary": option["tech_summary"] if option else None,
        },
        "style": style_id,
        "accent_style": accent_style,
        "style_modifiers": modifier_ids if modifier_ids else [],
        "custom_colors": custom_colors if custom_colors else {},
        "palette_id": palette_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    config_dir = project_dir / ".autoforge"
    config_dir.mkdir(parents=True, exist_ok=True)

    config_path = config_dir / "project_config.json"
    try:
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)
        logger.info("Saved project config to %s", config_path)
    except OSError as e:
        logger.error("Failed to save project config to %s: %s", config_path, e)
        raise


def load_project_config(project_dir: Path) -> dict | None:
    """
    Read the project_config.json file if it exists.

    Args:
        project_dir: Root directory of the project.

    Returns:
        The parsed configuration dict, or None if the file does not exist
        or cannot be parsed.
    """
    config_path = project_dir / ".autoforge" / "project_config.json"

    if not config_path.exists():
        return None

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, dict):
            logger.warning("Invalid project config format in %s: expected dict, got %s", config_path, type(data).__name__)
            return None

        return data
    except json.JSONDecodeError as e:
        logger.warning("Failed to parse project config at %s: %s", config_path, e)
        return None
    except OSError as e:
        logger.warning("Failed to read project config at %s: %s", config_path, e)
        return None
