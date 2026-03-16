"""
First-run setup wizard — auto-detects the user's environment and
personalizes their brain file. Takes 30 seconds, no technical knowledge needed.
"""

import os
import platform
import shutil
import subprocess
from pathlib import Path

DATA_DIR = Path.home() / ".vibehelper"
BRAIN_FILE = DATA_DIR / "my_brain.md"
CONFIG_FILE = DATA_DIR / "config.json"


def detect_os() -> dict:
    """Detect OS and shell."""
    info = {
        "os": platform.system(),
        "os_version": platform.version(),
        "machine": platform.machine(),
    }
    if info["os"] == "Windows":
        info["shell"] = "Command Prompt (cmd.exe)"
        info["home"] = os.environ.get("USERPROFILE", str(Path.home()))
    elif info["os"] == "Darwin":
        info["shell"] = "zsh" if os.path.exists("/bin/zsh") else "bash"
        info["home"] = str(Path.home())
    else:
        info["shell"] = os.environ.get("SHELL", "bash").split("/")[-1]
        info["home"] = str(Path.home())
    return info


def detect_tools() -> dict:
    """Check which dev tools are installed."""
    tools = {}
    checks = {
        "git": ["git", "--version"],
        "node": ["node", "--version"],
        "npm": ["npm", "--version"],
        "python": ["python", "--version"] if platform.system() == "Windows" else ["python3", "--version"],
        "pip": ["pip", "--version"] if platform.system() == "Windows" else ["pip3", "--version"],
        "claude": ["claude", "--version"],
        "code": ["code", "--version"],
    }
    for name, cmd in checks.items():
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                ver = (result.stdout.strip() or result.stderr.strip()).split("\n")[0]
                tools[name] = ver
        except Exception:
            pass
    return tools


def find_projects() -> list[dict]:
    """Look for common project directories."""
    projects = []
    home = Path.home()

    # Common places people put projects
    search_dirs = [
        home / "Projects",
        home / "projects",
        home / "GitHub",
        home / "Documents" / "GitHub",
        home / "repos",
        home / "code",
        home / "Code",
        home / "dev",
        home / "Dev",
        home / "Desktop",
    ]

    for search_dir in search_dirs:
        if not search_dir.exists():
            continue
        try:
            for item in search_dir.iterdir():
                if item.is_dir() and (item / ".git").exists():
                    projects.append({
                        "name": item.name,
                        "path": str(item),
                        "has_package_json": (item / "package.json").exists(),
                        "has_requirements": (item / "requirements.txt").exists(),
                    })
        except PermissionError:
            continue

    return projects[:20]  # Cap at 20


def personalize_brain(brain_path: Path, env_info: dict, tools: dict, projects: list):
    """Update the brain file with detected environment info."""
    text = brain_path.read_text(encoding="utf-8")

    # Replace OS info
    text = text.replace(
        "- OS: (auto-detected on first run)",
        f"- OS: {env_info['os']} {env_info.get('os_version', '')}"
    )
    text = text.replace(
        "- Shell: (auto-detected)",
        f"- Shell: {env_info['shell']}"
    )

    # Add detected tools
    tool_lines = "\n".join(f"- {name}: {ver}" for name, ver in tools.items())
    text = text.replace(
        "## My Projects\n",
        f"## My Tools (auto-detected)\n\n{tool_lines}\n\n## My Projects\n"
    )

    # Add detected projects
    if projects:
        project_lines = "\n".join(
            f"- {p['name']}: `{p['path']}`"
            + (" (Node.js)" if p['has_package_json'] else "")
            + (" (Python)" if p['has_requirements'] else "")
            for p in projects
        )
        text = text.replace(
            "<!-- Add your projects manually too: -->",
            f"<!-- Auto-detected projects: -->\n{project_lines}\n<!-- Add more manually: -->"
        )

    brain_path.write_text(text, encoding="utf-8")


def run_setup():
    """Run the first-time setup wizard."""
    print()
    print("=" * 55)
    print("  Welcome to VibeHelper!")
    print("  Your AI coding sidekick.")
    print("=" * 55)
    print()
    print("  Let me learn about your machine real quick...")
    print()

    # Detect environment
    env_info = detect_os()
    print(f"  OS: {env_info['os']}")
    print(f"  Shell: {env_info['shell']}")

    tools = detect_tools()
    if tools:
        print(f"  Tools found: {', '.join(tools.keys())}")
    else:
        print("  No dev tools detected yet — that's fine!")

    projects = find_projects()
    if projects:
        print(f"  Projects found: {len(projects)}")
        for p in projects[:5]:
            print(f"    - {p['name']} ({p['path']})")
        if len(projects) > 5:
            print(f"    ... and {len(projects) - 5} more")

    # Create data directory and brain file
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    if not BRAIN_FILE.exists():
        # Copy default brain
        default_brain = Path(__file__).parent / "brain_default.md"
        if default_brain.exists():
            shutil.copy2(default_brain, BRAIN_FILE)
        else:
            BRAIN_FILE.write_text("# My Brain\n\nEdit this file to teach VibeHelper about you.\n", encoding="utf-8")

    # Personalize it
    personalize_brain(BRAIN_FILE, env_info, tools, projects)

    print()
    print(f"  Brain file created: {BRAIN_FILE}")
    print("  (Edit it anytime to teach me more)")
    print()

    # API key check
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("  ─── One more thing ───")
        print()
        print("  I need an Anthropic API key to work.")
        print("  Get one at: https://console.anthropic.com")
        print("  (Costs ~2-5 cents per help session)")
        print()

        key = input("  Paste your API key here (or press Enter to skip): ").strip()
        if key:
            # Save to config
            import json
            config = {"api_key": key}
            CONFIG_FILE.write_text(json.dumps(config, indent=2), encoding="utf-8")
            print("  Saved! You won't need to enter it again.")
        else:
            print("  No worries — set ANTHROPIC_API_KEY env var later.")

    print()
    print("=" * 55)
    print("  Setup complete! Run `vibehelper` to start.")
    print("  Then press Ctrl+Shift+X whenever you need help.")
    print("=" * 55)
    print()

    return True


if __name__ == "__main__":
    run_setup()
