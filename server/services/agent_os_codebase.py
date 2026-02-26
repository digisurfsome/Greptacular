"""
Agent OS Codebase Reality Engine
==================================

Analyzes an existing codebase to infer Standards, Product, and Specs.
Enables retrofitting Agent OS onto projects that already have code.
"""

import json
import logging
import re
from pathlib import Path
from typing import Any, Optional

from .agent_os_file_utils import AgentOSFileUtils

logger = logging.getLogger(__name__)

# Directories to exclude from all file system traversals
EXCLUDE_DIRS = {
    "node_modules", ".git", "venv", "__pycache__", "dist", "build",
    ".next", ".nuxt", "target", ".venv", "env",
}

# Maximum depth for file structure scanning (relative to project root)
_MAX_SCAN_DEPTH = 3

# Maximum number of source files to sample for code pattern detection
_MAX_SAMPLE_FILES = 10

# Maximum lines to read from each sampled file
_MAX_LINES_PER_FILE = 50

# Source file extensions eligible for code pattern analysis
_SOURCE_EXTENSIONS = {".py", ".ts", ".tsx", ".js", ".jsx"}

# ── Detection maps ──────────────────────────────────────────────────

_NODE_FRAMEWORK_MAP: dict[str, str] = {
    "react": "React",
    "next": "Next.js",
    "vue": "Vue",
    "nuxt": "Nuxt",
    "svelte": "Svelte",
    "@sveltejs/kit": "SvelteKit",
    "express": "Express",
    "fastify": "Fastify",
    "koa": "Koa",
    "hono": "Hono",
    "tailwindcss": "Tailwind CSS",
    "@angular/core": "Angular",
    "solid-js": "Solid",
    "astro": "Astro",
    "remix": "Remix",
    "gatsby": "Gatsby",
    "vite": "Vite",
    "webpack": "Webpack",
    "@tanstack/react-query": "TanStack Query",
    "zustand": "Zustand",
    "@reduxjs/toolkit": "Redux Toolkit",
    "redux": "Redux",
}

_PYTHON_FRAMEWORK_MAP: dict[str, str] = {
    "fastapi": "FastAPI",
    "django": "Django",
    "flask": "Flask",
    "sqlalchemy": "SQLAlchemy",
    "pydantic": "Pydantic",
    "celery": "Celery",
    "alembic": "Alembic",
    "starlette": "Starlette",
    "aiohttp": "aiohttp",
    "uvicorn": "Uvicorn",
    "gunicorn": "Gunicorn",
}

_DB_PACKAGE_MAP: dict[str, str] = {
    "pg": "PostgreSQL",
    "mysql": "MySQL",
    "mysql2": "MySQL",
    "sqlite3": "SQLite",
    "better-sqlite3": "SQLite",
    "mongodb": "MongoDB",
    "redis": "Redis",
    "prisma": "Prisma",
    "sqlalchemy": "SQLAlchemy",
    "sequelize": "Sequelize",
    "mongoose": "MongoDB",
    "typeorm": "TypeORM",
    "drizzle-orm": "Drizzle",
    "psycopg2": "PostgreSQL",
    "psycopg": "PostgreSQL",
    "asyncpg": "PostgreSQL",
    "pymongo": "MongoDB",
    "motor": "MongoDB",
    "aioredis": "Redis",
    "ioredis": "Redis",
    "knex": "SQL (Knex)",
    "peewee": "SQLite",
}

# Linter/formatter config files and the tool they represent
_LINTER_CONFIG_FILES: list[tuple[str, str]] = [
    (".eslintrc", "ESLint"),
    (".eslintrc.js", "ESLint"),
    (".eslintrc.cjs", "ESLint"),
    (".eslintrc.json", "ESLint"),
    (".eslintrc.yml", "ESLint"),
    (".eslintrc.yaml", "ESLint"),
    ("eslint.config.js", "ESLint (flat config)"),
    ("eslint.config.mjs", "ESLint (flat config)"),
    (".prettierrc", "Prettier"),
    (".prettierrc.js", "Prettier"),
    (".prettierrc.json", "Prettier"),
    (".prettierrc.yml", "Prettier"),
    ("prettier.config.js", "Prettier"),
    ("ruff.toml", "Ruff"),
    (".editorconfig", "EditorConfig"),
    ("tsconfig.json", "TypeScript"),
    ("biome.json", "Biome"),
    ("biome.jsonc", "Biome"),
    (".stylelintrc", "Stylelint"),
    (".stylelintrc.json", "Stylelint"),
]

# Test framework indicators found in dependency manifests
_TEST_FRAMEWORK_MAP: dict[str, str] = {
    "jest": "Jest",
    "@jest/core": "Jest",
    "vitest": "Vitest",
    "mocha": "Mocha",
    "jasmine": "Jasmine",
    "pytest": "pytest",
    "@playwright/test": "Playwright",
    "playwright": "Playwright",
    "cypress": "Cypress",
    "@testing-library/react": "React Testing Library",
}

# Expected standards filenames (same order used by other Agent OS services)
_STANDARDS_FILENAMES = [
    "technology-stack.md",
    "coding-conventions.md",
    "architecture-patterns.md",
    "ui-ux-standards.md",
    "quality-standards.md",
    "security-requirements.md",
]

# Expected product filenames
_PRODUCT_FILENAMES = [
    "vision.md",
    "target-users.md",
    "use-cases.md",
    "roadmap.md",
    "constraints.md",
    "competitive-context.md",
]

# ── Prompt templates ─────────────────────────────────────────────────

_STANDARDS_INFERENCE_PROMPT = """Analyze the following codebase scan results and generate standards files.

## Technology Stack
{tech_stack_json}

## File Structure
{file_structure_json}

## Code Patterns
{code_patterns_json}

## Linter Configuration
{linter_config_json}

## Test Patterns
{test_patterns_json}

Based on the analysis above, generate content for each of the 6 standards files.
Write substantive, specific content based on what you observe in the codebase.
Do NOT be generic — reference the actual frameworks, patterns, and tools detected.

Return ONLY valid JSON with this exact structure:
{{
  "technology-stack.md": "<full markdown content>",
  "coding-conventions.md": "<full markdown content>",
  "architecture-patterns.md": "<full markdown content>",
  "ui-ux-standards.md": "<full markdown content>",
  "quality-standards.md": "<full markdown content>",
  "security-requirements.md": "<full markdown content>"
}}

For each file, write proper markdown with ## headers for each section.
Be specific to this codebase — mention the actual frameworks, languages, and tools detected.
"""

_PRODUCT_INFERENCE_PROMPT = """Analyze the following codebase information and infer the Product layer.

## README Content
{readme_content}

## Codebase Analysis
{analysis_json}

## Detected Routes/Endpoints
{routes_info}

## Detected Components
{components_info}

Based on the codebase analysis, reverse-engineer the product vision, users, and use cases.
Infer as much as possible from the code structure, README, comments, and naming patterns.

Return ONLY valid JSON with this exact structure:
{{
  "vision.md": "<full markdown content>",
  "target-users.md": "<full markdown content>",
  "use-cases.md": "<full markdown content>",
  "roadmap.md": "<full markdown content>",
  "constraints.md": "<full markdown content>",
  "competitive-context.md": "<full markdown content>"
}}

For each file, write proper markdown with ## headers.
Be specific — reference actual functionality observed in the codebase.
If something cannot be inferred, write "[Needs further discussion]" for that section.
"""

_FEATURE_INFERENCE_PROMPT = """Reverse-engineer the features implemented in this existing codebase.

## File List
{file_list}

## Detected Routes/Endpoints
{routes_info}

## Detected Components
{components_info}

## Detected Models/Schemas
{models_info}

## Technology Stack
{tech_stack_json}

## Code Structure
{file_structure_json}

For each feature you identify, provide:
- name: Clear, concise feature name
- description: 1-2 sentence description of what it does
- priority: must_have / should_have / nice_to_have (infer from code centrality)
- category: auth, ui, data, api, infrastructure, integration, etc.
- evidence: Which files/routes/components prove this feature exists

Return ONLY valid JSON array:
[
  {{
    "name": "<feature name>",
    "description": "<1-2 sentences>",
    "priority": "<must_have|should_have|nice_to_have>",
    "category": "<category>",
    "evidence": ["<file or route that proves this exists>"]
  }}
]

Order by importance (must_have first). Group related functionality into single features.
"""


# ── Helper functions ─────────────────────────────────────────────────

def _relative_depth(path: Path, base: Path) -> int:
    """Return the number of path components between base and path."""
    try:
        return len(path.relative_to(base).parts)
    except ValueError:
        return 999


def _is_excluded(path: Path) -> bool:
    """Return True if any component of path is in the exclusion set."""
    return any(part in EXCLUDE_DIRS for part in path.parts)


class AgentOSCodebaseAnalyzer:
    """Analyzes an existing codebase to infer Standards, Product, and Specs."""

    def __init__(self, project_dir: Path, file_utils: AgentOSFileUtils):
        self.project_dir = project_dir
        self.file_utils = file_utils
        self._analysis: dict[str, Any] = {}

    # ── Master scan ──────────────────────────────────────────────────

    def scan_codebase(self) -> dict[str, Any]:
        """Run all detection methods and return comprehensive analysis.

        Calls detect_tech_stack, detect_file_structure, detect_code_patterns,
        detect_linter_config, and detect_test_patterns. Stores the combined
        results in self._analysis for use by prompt generators.
        """
        logger.info("Starting codebase scan for: %s", self.project_dir)

        tech_stack = self.detect_tech_stack()
        file_structure = self.detect_file_structure()
        code_patterns = self.detect_code_patterns()
        linter_config = self.detect_linter_config()
        test_patterns = self.detect_test_patterns()

        self._analysis = {
            "tech_stack": tech_stack,
            "file_structure": file_structure,
            "code_patterns": code_patterns,
            "linter_config": linter_config,
            "test_patterns": test_patterns,
            "project_dir": str(self.project_dir),
        }

        logger.info(
            "Codebase scan complete: %d languages, %d frameworks, %d files",
            len(tech_stack.get("languages", [])),
            len(tech_stack.get("frameworks", [])),
            file_structure.get("file_count", 0),
        )
        return dict(self._analysis)

    # ── Technology stack detection ───────────────────────────────────

    def detect_tech_stack(self) -> dict[str, Any]:
        """Detect languages, frameworks, databases, and tools from manifest files.

        Scans package.json, requirements.txt, pyproject.toml, Cargo.toml,
        go.mod, Gemfile, and pom.xml to build a comprehensive technology
        inventory.
        """
        languages: list[str] = []
        frameworks: list[str] = []
        databases: list[str] = []
        tools: list[str] = []

        # ── Node.js / JavaScript / TypeScript ────────────────────────
        pkg_json_path = self.project_dir / "package.json"
        if pkg_json_path.is_file():
            try:
                pkg = json.loads(pkg_json_path.read_text(encoding="utf-8"))
                deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}

                # Language detection
                if "typescript" in deps or (self.project_dir / "tsconfig.json").is_file():
                    if "TypeScript" not in languages:
                        languages.append("TypeScript")
                    if "JavaScript" not in languages:
                        languages.append("JavaScript")
                else:
                    if "JavaScript" not in languages:
                        languages.append("JavaScript")

                # Framework detection
                for pkg_name, framework_name in _NODE_FRAMEWORK_MAP.items():
                    if pkg_name in deps and framework_name not in frameworks:
                        frameworks.append(framework_name)

                # Database detection
                for pkg_name, db_name in _DB_PACKAGE_MAP.items():
                    if pkg_name in deps and db_name not in databases:
                        databases.append(db_name)

                # Tool detection from devDependencies
                if "eslint" in deps or any(k.startswith("eslint") for k in deps):
                    if "ESLint" not in tools:
                        tools.append("ESLint")
                if "prettier" in deps:
                    if "Prettier" not in tools:
                        tools.append("Prettier")
                if "jest" in deps or "@jest/core" in deps:
                    if "Jest" not in tools:
                        tools.append("Jest")
                if "vitest" in deps:
                    if "Vitest" not in tools:
                        tools.append("Vitest")
                if "playwright" in deps or "@playwright/test" in deps:
                    if "Playwright" not in tools:
                        tools.append("Playwright")

            except (json.JSONDecodeError, OSError) as e:
                logger.warning("Failed to parse package.json: %s", e)

        # ── Python (requirements.txt) ────────────────────────────────
        req_txt_path = self.project_dir / "requirements.txt"
        if req_txt_path.is_file():
            try:
                content = req_txt_path.read_text(encoding="utf-8").lower()
                if "Python" not in languages:
                    languages.append("Python")

                for pkg_name, framework_name in _PYTHON_FRAMEWORK_MAP.items():
                    if pkg_name in content and framework_name not in frameworks:
                        frameworks.append(framework_name)

                for pkg_name, db_name in _DB_PACKAGE_MAP.items():
                    if pkg_name in content and db_name not in databases:
                        databases.append(db_name)

                if "ruff" in content and "Ruff" not in tools:
                    tools.append("Ruff")
                if "mypy" in content and "mypy" not in tools:
                    tools.append("mypy")
                if "pytest" in content and "pytest" not in tools:
                    tools.append("pytest")

            except OSError as e:
                logger.warning("Failed to read requirements.txt: %s", e)

        # ── Python (pyproject.toml) ──────────────────────────────────
        pyproject_path = self.project_dir / "pyproject.toml"
        if pyproject_path.is_file():
            try:
                content = pyproject_path.read_text(encoding="utf-8").lower()
                if "Python" not in languages:
                    languages.append("Python")

                for pkg_name, framework_name in _PYTHON_FRAMEWORK_MAP.items():
                    if pkg_name in content and framework_name not in frameworks:
                        frameworks.append(framework_name)

                for pkg_name, db_name in _DB_PACKAGE_MAP.items():
                    if pkg_name in content and db_name not in databases:
                        databases.append(db_name)

                if "ruff" in content and "Ruff" not in tools:
                    tools.append("Ruff")
                if "mypy" in content and "mypy" not in tools:
                    tools.append("mypy")

            except OSError as e:
                logger.warning("Failed to read pyproject.toml: %s", e)

        # ── Rust ─────────────────────────────────────────────────────
        if (self.project_dir / "Cargo.toml").is_file():
            if "Rust" not in languages:
                languages.append("Rust")

        # ── Go ───────────────────────────────────────────────────────
        if (self.project_dir / "go.mod").is_file():
            if "Go" not in languages:
                languages.append("Go")

        # ── Ruby ─────────────────────────────────────────────────────
        if (self.project_dir / "Gemfile").is_file():
            if "Ruby" not in languages:
                languages.append("Ruby")

        # ── Java ─────────────────────────────────────────────────────
        if (self.project_dir / "pom.xml").is_file():
            if "Java" not in languages:
                languages.append("Java")

        # ── Docker ───────────────────────────────────────────────────
        has_docker = (
            (self.project_dir / "Dockerfile").is_file()
            or (self.project_dir / "docker-compose.yml").is_file()
            or (self.project_dir / "docker-compose.yaml").is_file()
        )
        if has_docker and "Docker" not in tools:
            tools.append("Docker")

        result: dict[str, Any] = {
            "languages": languages,
            "frameworks": frameworks,
            "databases": databases,
            "tools": tools,
        }
        logger.debug("Detected tech stack: %s", result)
        return result

    # ── File structure detection ─────────────────────────────────────

    def detect_file_structure(self) -> dict[str, Any]:
        """Analyze directory layout to detect organization patterns.

        Uses Path.rglob() but limits depth to 3 levels and excludes common
        non-source directories. Classifies the structure as by-type,
        by-feature, or flat based on directory naming conventions.
        """
        file_count = 0
        key_directories: list[str] = []
        depth_1_dirs: set[str] = set()
        depth_2_dirs: set[str] = set()

        try:
            for path in self.project_dir.rglob("*"):
                if _is_excluded(path):
                    continue

                depth = _relative_depth(path, self.project_dir)
                if depth > _MAX_SCAN_DEPTH:
                    continue

                if path.is_file():
                    file_count += 1
                elif path.is_dir():
                    # Skip hidden directories at any level
                    if path.name.startswith("."):
                        continue

                    if depth == 1:
                        depth_1_dirs.add(path.name)
                        key_directories.append(path.name)
                    elif depth == 2:
                        depth_2_dirs.add(path.name)

        except OSError as e:
            logger.warning("Error scanning file structure: %s", e)

        # Classify organization pattern
        pattern = self._classify_structure_pattern(depth_1_dirs, depth_2_dirs)

        result: dict[str, Any] = {
            "pattern": pattern,
            "key_directories": sorted(key_directories),
            "file_count": file_count,
        }
        logger.debug("Detected file structure: pattern=%s, files=%d", pattern, file_count)
        return result

    def _classify_structure_pattern(self, depth_1: set[str], depth_2: set[str]) -> str:
        """Classify directory layout as by-type, by-feature, or flat.

        Compares how many directory names match structural (by-type) indicators
        versus domain-specific (by-feature) indicators.
        """
        by_type_indicators = {
            "components", "hooks", "utils", "helpers", "services", "models",
            "views", "controllers", "middleware", "routes", "schemas",
            "types", "styles", "assets", "lib",
        }
        by_feature_indicators = {
            "auth", "dashboard", "settings", "profile", "admin", "users",
            "products", "orders", "payments", "notifications", "chat",
            "search", "analytics",
        }

        all_dirs = depth_1 | depth_2
        type_matches = len(all_dirs & by_type_indicators)
        feature_matches = len(all_dirs & by_feature_indicators)

        if type_matches == 0 and feature_matches == 0:
            return "flat"
        if type_matches > feature_matches:
            return "by-type"
        if feature_matches > type_matches:
            return "by-feature"

        # Equal counts — heuristic: src/ is more common in by-type projects
        if "src" in depth_1:
            return "by-type"
        return "flat"

    # ── Code pattern detection ───────────────────────────────────────

    def detect_code_patterns(self) -> dict[str, Any]:
        """Detect naming conventions, component style, indentation, and import style.

        Collects up to 10 source files sorted by size (largest first), reads
        the first 50 lines of each, and uses regex to determine the dominant
        patterns in the codebase.
        """
        source_files = self._collect_source_files()
        if not source_files:
            return {
                "naming_convention": "unknown",
                "component_style": "unknown",
                "indentation": "unknown",
                "import_style": "unknown",
                "files_sampled": 0,
            }

        # Counters for each pattern category
        snake_count = 0
        camel_count = 0
        pascal_count = 0

        functional_count = 0
        class_count = 0

        spaces_2_count = 0
        spaces_4_count = 0
        tab_count = 0

        es_module_count = 0
        commonjs_count = 0
        python_import_count = 0

        # Compiled regex patterns for naming convention detection
        snake_re = re.compile(r"[a-z]+_[a-z]+")
        camel_re = re.compile(r"[a-z]+[A-Z][a-z]+")
        pascal_re = re.compile(r"[A-Z][a-z]+[A-Z]")

        for file_path in source_files:
            try:
                text = file_path.read_text(encoding="utf-8", errors="replace")
                lines = text.splitlines()[:_MAX_LINES_PER_FILE]
            except OSError:
                continue

            for line in lines:
                stripped = line.rstrip()
                if not stripped:
                    continue

                # Naming convention counts
                snake_count += len(snake_re.findall(stripped))
                camel_count += len(camel_re.findall(stripped))
                pascal_count += len(pascal_re.findall(stripped))

                # Component style detection (React-specific)
                if "function " in stripped and ("props" in stripped.lower() or "Props" in stripped):
                    functional_count += 1
                if stripped.lstrip().startswith("const ") and ("React.FC" in stripped or ": FC" in stripped):
                    functional_count += 1
                if "class " in stripped and ("extends Component" in stripped or "extends React.Component" in stripped):
                    class_count += 1

                # Indentation analysis (only for indented lines)
                if line[0:1].isspace():
                    leading = line[: len(line) - len(line.lstrip())]
                    if "\t" in leading:
                        tab_count += 1
                    elif leading.startswith("    "):
                        spaces_4_count += 1
                    elif leading.startswith("  "):
                        spaces_2_count += 1

                # Import style detection
                trimmed = stripped.lstrip()
                if trimmed.startswith("import ") and " from " in trimmed:
                    es_module_count += 1
                elif trimmed.startswith("export "):
                    es_module_count += 1
                elif "require(" in trimmed:
                    commonjs_count += 1
                elif trimmed.startswith("from ") and " import " in trimmed:
                    python_import_count += 1
                elif trimmed.startswith("import ") and " from " not in trimmed and "(" not in trimmed:
                    python_import_count += 1

        # Determine winners by majority vote
        naming_counts = {
            "snake_case": snake_count,
            "camelCase": camel_count,
            "PascalCase": pascal_count,
        }
        if any(naming_counts.values()):
            naming_convention = max(naming_counts, key=naming_counts.get)  # type: ignore[arg-type]
        else:
            naming_convention = "unknown"

        if functional_count + class_count == 0:
            component_style = "none"
        elif functional_count > class_count:
            component_style = "functional"
        elif class_count > functional_count:
            component_style = "class"
        else:
            component_style = "mixed"

        indent_counts = {
            "2 spaces": spaces_2_count,
            "4 spaces": spaces_4_count,
            "tabs": tab_count,
        }
        if any(indent_counts.values()):
            indentation = max(indent_counts, key=indent_counts.get)  # type: ignore[arg-type]
        else:
            indentation = "unknown"

        import_counts = {
            "ES modules": es_module_count,
            "CommonJS": commonjs_count,
            "Python": python_import_count,
        }
        if any(import_counts.values()):
            import_style = max(import_counts, key=import_counts.get)  # type: ignore[arg-type]
        else:
            import_style = "unknown"

        result: dict[str, Any] = {
            "naming_convention": naming_convention,
            "component_style": component_style,
            "indentation": indentation,
            "import_style": import_style,
            "files_sampled": len(source_files),
        }
        logger.debug("Detected code patterns: %s", result)
        return result

    def _collect_source_files(self) -> list[Path]:
        """Collect up to _MAX_SAMPLE_FILES source files sorted by size (largest first).

        Only considers files with extensions in _SOURCE_EXTENSIONS, excludes
        files inside excluded directories, and limits depth to _MAX_SCAN_DEPTH.
        """
        candidates: list[tuple[int, Path]] = []

        try:
            for path in self.project_dir.rglob("*"):
                if not path.is_file():
                    continue
                if _is_excluded(path):
                    continue
                if _relative_depth(path, self.project_dir) > _MAX_SCAN_DEPTH:
                    continue
                if path.suffix not in _SOURCE_EXTENSIONS:
                    continue

                try:
                    size = path.stat().st_size
                except OSError:
                    continue
                candidates.append((size, path))

        except OSError as e:
            logger.warning("Error collecting source files: %s", e)

        # Sort by file size descending, take the largest files first
        candidates.sort(key=lambda t: t[0], reverse=True)
        return [path for _, path in candidates[:_MAX_SAMPLE_FILES]]

    # ── Linter configuration detection ───────────────────────────────

    def detect_linter_config(self) -> dict[str, Any]:
        """Detect linter, formatter, and type-checker configuration files.

        Looks for well-known config filenames in the project root and also
        checks pyproject.toml for embedded tool configuration sections.
        """
        detected: list[dict[str, str]] = []

        for filename, tool_name in _LINTER_CONFIG_FILES:
            if (self.project_dir / filename).is_file():
                detected.append({"file": filename, "tool": tool_name})

        # Check pyproject.toml for embedded tool sections
        pyproject_path = self.project_dir / "pyproject.toml"
        if pyproject_path.is_file():
            try:
                content = pyproject_path.read_text(encoding="utf-8")
                if "[tool.ruff]" in content:
                    has_ruff = any(d["tool"].startswith("Ruff") for d in detected)
                    if not has_ruff:
                        detected.append({"file": "pyproject.toml [tool.ruff]", "tool": "Ruff"})
                if "[tool.mypy]" in content:
                    detected.append({"file": "pyproject.toml [tool.mypy]", "tool": "mypy"})
                if "[tool.black]" in content:
                    detected.append({"file": "pyproject.toml [tool.black]", "tool": "Black"})
                if "[tool.isort]" in content:
                    detected.append({"file": "pyproject.toml [tool.isort]", "tool": "isort"})
            except OSError as e:
                logger.warning("Failed to read pyproject.toml for linter config: %s", e)

        result: dict[str, Any] = {
            "configs": detected,
            "count": len(detected),
        }
        logger.debug("Detected %d linter/formatter configs", len(detected))
        return result

    # ── Test pattern detection ───────────────────────────────────────

    def detect_test_patterns(self) -> dict[str, Any]:
        """Detect test frameworks, file naming patterns, and coverage configuration.

        Scans for files matching common test patterns (*.test.*, *.spec.*,
        test_*), checks dependency manifests for test framework packages,
        and looks for coverage tool configuration.
        """
        test_files: list[str] = []
        framework: Optional[str] = None
        test_pattern: Optional[str] = None
        has_coverage = False

        # Scan for test files
        try:
            for path in self.project_dir.rglob("*"):
                if not path.is_file():
                    continue
                if _is_excluded(path):
                    continue
                # Allow test files one level deeper than normal scan depth
                if _relative_depth(path, self.project_dir) > _MAX_SCAN_DEPTH + 1:
                    continue

                name = path.name
                if ".test." in name or ".spec." in name:
                    try:
                        test_files.append(str(path.relative_to(self.project_dir)))
                    except ValueError:
                        test_files.append(name)
                    if test_pattern is None:
                        test_pattern = ".test./.spec. (co-located)"
                elif name.startswith("test_") and name.endswith(".py"):
                    try:
                        test_files.append(str(path.relative_to(self.project_dir)))
                    except ValueError:
                        test_files.append(name)
                    if test_pattern is None:
                        test_pattern = "test_*.py (Python convention)"

        except OSError as e:
            logger.warning("Error scanning for test files: %s", e)

        # Detect test framework from package.json
        pkg_json_path = self.project_dir / "package.json"
        if pkg_json_path.is_file():
            try:
                pkg = json.loads(pkg_json_path.read_text(encoding="utf-8"))
                deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}

                for pkg_name, fw_name in _TEST_FRAMEWORK_MAP.items():
                    if pkg_name in deps:
                        framework = fw_name
                        break

                # Coverage tool detection
                coverage_packages = {"c8", "istanbul", "nyc", "@vitest/coverage-v8", "@vitest/coverage-istanbul"}
                if coverage_packages & set(deps.keys()):
                    has_coverage = True

            except (json.JSONDecodeError, OSError):
                pass

        # Detect test framework from Python manifests
        if framework is None:
            for manifest in ["requirements.txt", "pyproject.toml"]:
                manifest_path = self.project_dir / manifest
                if manifest_path.is_file():
                    try:
                        content = manifest_path.read_text(encoding="utf-8").lower()
                        for pkg_name, fw_name in _TEST_FRAMEWORK_MAP.items():
                            if pkg_name in content:
                                framework = fw_name
                                break
                        if "coverage" in content or "pytest-cov" in content:
                            has_coverage = True
                    except OSError:
                        pass
                if framework:
                    break

        # Check for dedicated test directories
        for test_dir_name in ["tests", "test", "__tests__", "spec", "specs"]:
            if (self.project_dir / test_dir_name).is_dir():
                if test_pattern is None:
                    test_pattern = f"{test_dir_name}/ directory"
                break

        result: dict[str, Any] = {
            "framework": framework or "unknown",
            "pattern": test_pattern or "unknown",
            "coverage": has_coverage,
            "test_file_count": len(test_files),
        }
        logger.debug("Detected test patterns: %s", result)
        return result

    # ── Standards inference ──────────────────────────────────────────

    def get_standards_inference_prompt(self) -> str:
        """Return a prompt for Claude to generate standards files from scan results.

        Includes all detection results formatted as JSON. Asks Claude to return
        JSON with content for each of the 6 standards files.
        """
        analysis = self._ensure_analysis()

        return _STANDARDS_INFERENCE_PROMPT.format(
            tech_stack_json=json.dumps(analysis.get("tech_stack", {}), indent=2),
            file_structure_json=json.dumps(analysis.get("file_structure", {}), indent=2),
            code_patterns_json=json.dumps(analysis.get("code_patterns", {}), indent=2),
            linter_config_json=json.dumps(analysis.get("linter_config", {}), indent=2),
            test_patterns_json=json.dumps(analysis.get("test_patterns", {}), indent=2),
        )

    def process_standards_inference(self, standards_json: dict[str, str]) -> list[Path]:
        """Write Claude's generated standards to files via file_utils.

        Args:
            standards_json: Dict mapping standard filename to markdown content.

        Returns:
            List of paths that were successfully written.
        """
        written: list[Path] = []
        for filename in _STANDARDS_FILENAMES:
            content = standards_json.get(filename)
            if content and isinstance(content, str) and content.strip():
                path = self.file_utils.write_standards_file(filename, content)
                written.append(path)
                logger.debug("Wrote inferred standards file: %s", filename)
            else:
                logger.warning("No content provided for standards file: %s", filename)

        logger.info("Wrote %d inferred standards files", len(written))
        return written

    # ── Product inference ────────────────────────────────────────────

    def get_product_inference_prompt(self) -> str:
        """Return a prompt for Claude to infer Product layer from codebase.

        Reads README files and includes codebase analysis, detected routes,
        and detected components to help Claude reverse-engineer product
        vision, target users, and use cases.
        """
        analysis = self._ensure_analysis()

        readme_content = self._read_readme()
        routes_info = self._detect_routes()
        components_info = self._detect_components()

        return _PRODUCT_INFERENCE_PROMPT.format(
            readme_content=readme_content or "(No README found)",
            analysis_json=json.dumps(analysis, indent=2, default=str),
            routes_info=routes_info or "(No routes detected)",
            components_info=components_info or "(No components detected)",
        )

    def process_product_inference(self, product_json: dict[str, str]) -> list[Path]:
        """Write Claude's inferred product documents via file_utils.

        Args:
            product_json: Dict mapping product filename to markdown content.

        Returns:
            List of paths that were successfully written.
        """
        written: list[Path] = []
        for filename in _PRODUCT_FILENAMES:
            content = product_json.get(filename)
            if content and isinstance(content, str) and content.strip():
                path = self.file_utils.write_product_file(filename, content)
                written.append(path)
                logger.debug("Wrote inferred product file: %s", filename)
            else:
                logger.warning("No content provided for product file: %s", filename)

        logger.info("Wrote %d inferred product files", len(written))
        return written

    # ── Feature inference ────────────────────────────────────────────

    def get_feature_inference_prompt(self) -> str:
        """Return a prompt for Claude to reverse-engineer features from the codebase.

        Includes file list, detected routes, components, and models so Claude
        can identify what features have already been implemented.
        """
        analysis = self._ensure_analysis()

        file_list = self._build_file_list()
        routes_info = self._detect_routes()
        components_info = self._detect_components()
        models_info = self._detect_models()

        return _FEATURE_INFERENCE_PROMPT.format(
            file_list=file_list or "(No source files found)",
            routes_info=routes_info or "(No routes detected)",
            components_info=components_info or "(No components detected)",
            models_info=models_info or "(No models detected)",
            tech_stack_json=json.dumps(analysis.get("tech_stack", {}), indent=2),
            file_structure_json=json.dumps(analysis.get("file_structure", {}), indent=2),
        )

    def process_feature_inference(self, features_json: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Create feature records from Claude's reverse-engineered feature list.

        All features are marked with passes: "passing" since they already
        exist in the codebase.

        Args:
            features_json: List of feature dicts from Claude's inference.

        Returns:
            List of processed feature dicts with IDs and passing status.
        """
        processed: list[dict[str, Any]] = []
        feature_id = 1

        for raw in features_json:
            feature: dict[str, Any] = {
                "id": feature_id,
                "name": raw.get("name", "Unnamed Feature"),
                "description": raw.get("description", ""),
                "priority": raw.get("priority", "should_have"),
                "category": raw.get("category", "general"),
                "passes": "passing",
                "evidence": raw.get("evidence", []),
                "source": "codebase_inference",
            }
            processed.append(feature)
            feature_id += 1

        logger.info("Processed %d inferred features (all marked as passing)", len(processed))
        return processed

    # ── Analysis summary ─────────────────────────────────────────────

    def get_analysis_summary(self) -> str:
        """Return a human-readable summary of what was detected in the codebase."""
        if not self._analysis:
            return "No codebase analysis has been performed yet. Run scan_codebase() first."

        tech = self._analysis.get("tech_stack", {})
        structure = self._analysis.get("file_structure", {})
        patterns = self._analysis.get("code_patterns", {})
        linter = self._analysis.get("linter_config", {})
        tests = self._analysis.get("test_patterns", {})

        lines: list[str] = [
            "Codebase Analysis Summary",
            "=" * 25,
            "",
        ]

        # Technology stack
        languages = tech.get("languages", [])
        frameworks = tech.get("frameworks", [])
        databases = tech.get("databases", [])
        tools = tech.get("tools", [])

        lines.append("Technology Stack:")
        lines.append(f"  Languages: {', '.join(languages) if languages else 'None detected'}")
        lines.append(f"  Frameworks: {', '.join(frameworks) if frameworks else 'None detected'}")
        lines.append(f"  Databases: {', '.join(databases) if databases else 'None detected'}")
        lines.append(f"  Tools: {', '.join(tools) if tools else 'None detected'}")
        lines.append("")

        # File structure
        lines.append("File Structure:")
        lines.append(f"  Pattern: {structure.get('pattern', 'unknown')}")
        lines.append(f"  Total files: {structure.get('file_count', 0)}")
        key_dirs = structure.get("key_directories", [])
        if key_dirs:
            lines.append(f"  Key directories: {', '.join(key_dirs[:10])}")
            if len(key_dirs) > 10:
                lines.append(f"    ... and {len(key_dirs) - 10} more")
        lines.append("")

        # Code patterns
        lines.append("Code Patterns:")
        lines.append(f"  Naming: {patterns.get('naming_convention', 'unknown')}")
        lines.append(f"  Component style: {patterns.get('component_style', 'unknown')}")
        lines.append(f"  Indentation: {patterns.get('indentation', 'unknown')}")
        lines.append(f"  Import style: {patterns.get('import_style', 'unknown')}")
        lines.append(f"  Files sampled: {patterns.get('files_sampled', 0)}")
        lines.append("")

        # Linter configuration
        configs = linter.get("configs", [])
        lines.append("Linter/Formatter Configuration:")
        if configs:
            for cfg in configs:
                lines.append(f"  - {cfg.get('tool', 'unknown')} ({cfg.get('file', '')})")
        else:
            lines.append("  None detected")
        lines.append("")

        # Test patterns
        lines.append("Testing:")
        lines.append(f"  Framework: {tests.get('framework', 'unknown')}")
        lines.append(f"  Pattern: {tests.get('pattern', 'unknown')}")
        lines.append(f"  Coverage: {'Yes' if tests.get('coverage') else 'No'}")
        lines.append(f"  Test files: {tests.get('test_file_count', 0)}")

        return "\n".join(lines)

    # ── Private helpers ──────────────────────────────────────────────

    def _ensure_analysis(self) -> dict[str, Any]:
        """Return cached analysis or run scan_codebase() if not yet performed."""
        if not self._analysis:
            self.scan_codebase()
        return self._analysis

    def _read_readme(self) -> Optional[str]:
        """Read the project README, trying common filenames. Truncates long files."""
        for name in ["README.md", "README.rst", "README.txt", "README", "readme.md"]:
            path = self.project_dir / name
            if path.is_file():
                try:
                    content = path.read_text(encoding="utf-8", errors="replace")
                    # Truncate very long READMEs to keep prompts manageable
                    if len(content) > 5000:
                        content = content[:5000] + "\n\n[... truncated ...]"
                    return content
                except OSError:
                    continue
        return None

    def _detect_routes(self) -> str:
        """Scan source files for HTTP route/endpoint definitions."""
        route_patterns = [
            re.compile(r'@app\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)'),
            re.compile(r'router\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)'),
            re.compile(r'app\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)'),
            re.compile(r"path\s*\(\s*[\"']([^\"']+)"),
        ]

        route_lines: list[str] = []
        seen: set[str] = set()

        for file_path in self._collect_source_files():
            try:
                content = file_path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue

            for pattern in route_patterns:
                for match in pattern.finditer(content):
                    groups = match.groups()
                    if len(groups) == 2:
                        line = f"  {groups[0].upper()} {groups[1]}"
                    elif len(groups) == 1:
                        line = f"  {groups[0]}"
                    else:
                        continue
                    if line not in seen:
                        seen.add(line)
                        route_lines.append(line)

        if route_lines:
            return "Detected routes/endpoints:\n" + "\n".join(route_lines[:50])
        return ""

    def _detect_components(self) -> str:
        """Scan for React/Vue/Svelte component files."""
        components: list[str] = []

        try:
            for path in self.project_dir.rglob("*"):
                if not path.is_file():
                    continue
                if _is_excluded(path):
                    continue
                if _relative_depth(path, self.project_dir) > _MAX_SCAN_DEPTH:
                    continue

                name = path.name
                is_component = False

                # React components: PascalCase .tsx/.jsx files
                if path.suffix in {".tsx", ".jsx"} and name[0].isupper():
                    is_component = True
                # Vue single-file components
                elif path.suffix == ".vue":
                    is_component = True
                # Svelte components
                elif path.suffix == ".svelte":
                    is_component = True

                if is_component:
                    try:
                        components.append(str(path.relative_to(self.project_dir)))
                    except ValueError:
                        components.append(name)

        except OSError as e:
            logger.warning("Error detecting components: %s", e)

        if components:
            display = components[:30]
            result = "Detected components:\n" + "\n".join(f"  - {c}" for c in display)
            if len(components) > 30:
                result += f"\n  ... and {len(components) - 30} more"
            return result
        return ""

    def _detect_models(self) -> str:
        """Scan source files for data model/schema definitions."""
        model_patterns = [
            re.compile(r"class\s+(\w+)\(.*(?:Base|Model|Schema|db\.Model)"),
            re.compile(r"(?:model|schema)\s+(\w+)\s*\{"),
            re.compile(r"const\s+(\w+Schema)\s*="),
            re.compile(r"interface\s+(\w+)\s*\{"),
        ]

        model_lines: list[str] = []
        seen: set[str] = set()

        for file_path in self._collect_source_files():
            try:
                content = file_path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue

            for pattern in model_patterns:
                for match in pattern.finditer(content):
                    model_name = match.group(1)
                    try:
                        rel = str(file_path.relative_to(self.project_dir))
                    except ValueError:
                        rel = file_path.name
                    line = f"  - {model_name} ({rel})"
                    if line not in seen:
                        seen.add(line)
                        model_lines.append(line)

        if model_lines:
            return "Detected models/schemas:\n" + "\n".join(model_lines[:30])
        return ""

    def _build_file_list(self) -> str:
        """Build a concise list of source files for prompt inclusion."""
        all_extensions = _SOURCE_EXTENSIONS | {".html", ".css", ".scss", ".vue", ".svelte"}
        files: list[str] = []

        try:
            for path in self.project_dir.rglob("*"):
                if not path.is_file():
                    continue
                if _is_excluded(path):
                    continue
                if _relative_depth(path, self.project_dir) > _MAX_SCAN_DEPTH:
                    continue
                if path.suffix in all_extensions:
                    try:
                        files.append(str(path.relative_to(self.project_dir)))
                    except ValueError:
                        files.append(path.name)
        except OSError as e:
            logger.warning("Error building file list: %s", e)

        if files:
            display = sorted(files)[:50]
            result = "\n".join(f"  - {f}" for f in display)
            if len(files) > 50:
                result += f"\n  ... and {len(files) - 50} more files"
            return result
        return ""
