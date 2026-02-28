#!/usr/bin/env python3
"""
DunkStack Coding Agent
======================

Spawns a Claude SDK session that operates under the .agent/ file-based protocol.
The agent reads system_prompt.md for its operating instructions, communicates
through .agent/comms/ files (walkie-talkie), and tracks all state in the
.agent/ file system.

Usage:
    python dunkstack_agent.py --project-dir /path/to/project
    python dunkstack_agent.py --project-dir my-app --model claude-opus-4-6
    python dunkstack_agent.py --project-dir my-app --billing-mode subscription
"""

import argparse
import asyncio
import io
import json
import shutil
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient
from claude_agent_sdk.types import HookMatcher

from registry import get_effective_sdk_env, get_project_path
from security import bash_security_hook

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace", line_buffering=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="DunkStack Coding Agent")
    parser.add_argument("--project-dir", required=True, help="Project directory or registered name")
    parser.add_argument("--model", default="claude-sonnet-4-6", help="Claude model to use")
    parser.add_argument("--billing-mode", choices=["subscription", "api"], default="subscription",
                        help="Billing mode: subscription (free, 200K) or api (paid, 1M)")
    return parser.parse_args()


def resolve_project_dir(project_dir_arg: str) -> Path:
    """Resolve project directory from path or registered name."""
    path = Path(project_dir_arg)
    if path.is_absolute() and path.exists():
        return path

    # Try registry lookup
    registered = get_project_path(project_dir_arg)
    if registered and registered.exists():
        return registered

    # Try as relative path
    if path.exists():
        return path.resolve()

    print(f"Error: Project directory not found: {project_dir_arg}")
    sys.exit(1)


def load_system_prompt(project_dir: Path) -> str:
    """Load the .agent/system_prompt.md file as the agent's operating instructions."""
    prompt_path = project_dir / ".agent" / "system_prompt.md"
    if prompt_path.exists():
        return prompt_path.read_text(encoding="utf-8")

    # Fall back to the template
    template_path = Path(__file__).parent / "server" / "templates" / "agent-os" / "universal" / "system_prompt.md"
    if template_path.exists():
        return template_path.read_text(encoding="utf-8")

    # Minimal fallback
    return (
        "You operate in file-based mode. Read .agent/index.md first, then "
        ".agent/working_memory.md for state, then .agent/comms/from_human.md for tasks. "
        "Write all substantive output to files, not chat. Keep chat responses to 1-2 sentences."
    )


def ensure_agent_dir(project_dir: Path) -> None:
    """Ensure .agent/ directory structure and templates exist."""
    agent_dir = project_dir / ".agent"
    for subdir in ["comms", "knowledge", "output", "progress", "settings"]:
        (agent_dir / subdir).mkdir(parents=True, exist_ok=True)

    # Copy universal templates if they don't exist
    sys.path.insert(0, str(Path(__file__).parent / "server"))
    try:
        from services.agent_os_file_utils import copy_universal_templates
        copy_universal_templates(agent_dir)
    except ImportError:
        pass  # Templates may already be in place


def create_dunkstack_client(
    project_dir: Path,
    model: str,
    billing_mode: str,
) -> ClaudeSDKClient:
    """Create a Claude SDK client configured for DunkStack file-based operation."""

    system_prompt = load_system_prompt(project_dir)

    # Billing: subscription = free (200K), api = paid (1M)
    force_subscription = billing_mode == "subscription"
    sdk_env = get_effective_sdk_env(force_subscription=force_subscription)

    if force_subscription:
        print("   Billing: Subscription (200K context, free)")
    else:
        print("   Billing: API key (1M context, paid)")

    # Security settings - sandbox + project-scoped filesystem
    security_settings = {
        "sandbox": {"enabled": True, "autoAllowBashIfSandboxed": True},
        "permissions": {
            "defaultMode": "acceptEdits",
            "allow": [
                "Read(./**)", "Write(./**)", "Edit(./**)",
                "Glob(./**)", "Grep(./**)",
                "Bash(*)",
                "WebFetch(*)", "WebSearch(*)",
            ],
        },
    }

    # Write settings file
    settings_dir = project_dir / ".claude"
    settings_dir.mkdir(parents=True, exist_ok=True)
    settings_file = settings_dir / "settings.json"
    with open(settings_file, "w") as f:
        json.dump(security_settings, f, indent=2)

    # Use system Claude CLI
    system_cli = shutil.which("claude")
    if system_cli:
        print(f"   CLI: {system_cli}")

    # Max turns based on billing
    max_turns = 150 if billing_mode == "subscription" else 200

    # Bash security hook with project context
    async def bash_hook_with_context(input_data, tool_use_id=None, context=None):
        if context is None:
            context = {}
        context["project_dir"] = str(project_dir.resolve())
        return await bash_security_hook(input_data, tool_use_id, context)

    # Detect alternative APIs for beta flag
    base_url = sdk_env.get("ANTHROPIC_BASE_URL", "")
    is_vertex = sdk_env.get("CLAUDE_CODE_USE_VERTEX") == "1"
    is_alternative_api = bool(base_url) or is_vertex
    use_1m = billing_mode == "api" and not is_alternative_api

    return ClaudeSDKClient(
        options=ClaudeAgentOptions(
            model=model,
            cli_path=system_cli,
            system_prompt=system_prompt,
            setting_sources=["project"],
            max_buffer_size=10 * 1024 * 1024,
            allowed_tools=[
                "Read", "Write", "Edit", "Glob", "Grep",
                "Bash", "WebFetch", "WebSearch",
            ],
            hooks={
                "PreToolUse": [
                    HookMatcher(matcher="Bash", hooks=[bash_hook_with_context]),
                ],
            },
            max_turns=max_turns,
            cwd=str(project_dir.resolve()),
            settings=str(settings_file.resolve()),
            env=sdk_env,
            betas=["context-1m-2025-08-07"] if use_1m else [],
        )
    )


INITIAL_PROMPT = """\
You are starting a new DunkStack session. Follow your operating protocol:

1. Read .agent/index.md (your file map)
2. Read .agent/working_memory.md (your current state)
3. If .agent/bridge.md exists and has content beyond the template, read it and incorporate context
4. Read .agent/comms/from_human.md for any task assignments or messages
5. Read .agent/comms/control.md for your mode signal (idle/continue/autopilot)

If from_human.md contains a task, begin working on it immediately.
If no task is assigned yet, write a status message to .agent/comms/to_human.md saying you're ready.

Remember: ALL substantive output goes to files. Chat responses are 1-2 sentences max.
"""


async def run_session(client: ClaudeSDKClient, project_dir: Path) -> None:
    """Run a single DunkStack agent session."""
    print("\n" + "=" * 60)
    print("DunkStack Agent Session Starting")
    print(f"Project: {project_dir}")
    print("=" * 60 + "\n")

    try:
        await client.query(INITIAL_PROMPT)

        turn_count = 0
        async for msg in client.receive_response():
            msg_type = type(msg).__name__

            if msg_type == "AssistantMessage" and hasattr(msg, "content"):
                turn_count += 1
                for block in msg.content:
                    block_type = type(block).__name__
                    if block_type == "TextBlock" and hasattr(block, "text"):
                        print(block.text, end="", flush=True)
                    elif block_type == "ToolUseBlock" and hasattr(block, "name"):
                        print(f"\n[Tool: {block.name}]", flush=True)

            elif msg_type == "UserMessage" and hasattr(msg, "content"):
                for block in msg.content:
                    block_type = type(block).__name__
                    if block_type == "ToolResultBlock":
                        is_error = getattr(block, "is_error", False)
                        if is_error:
                            result_content = getattr(block, "content", "")
                            error_str = str(result_content)[:500]
                            print(f"   [Error] {error_str}", flush=True)
                        else:
                            print("   [Done]", flush=True)

        print(f"\n\nSession complete. {turn_count} turns.")

    except Exception as e:
        print(f"\nSession error: {e}")
        raise


async def main():
    args = parse_args()
    project_dir = resolve_project_dir(args.project_dir)

    print("DunkStack Agent")
    print(f"   Project: {project_dir}")
    print(f"   Model: {args.model}")

    # Ensure .agent/ directory and templates
    ensure_agent_dir(project_dir)

    # Create client
    client = create_dunkstack_client(project_dir, args.model, args.billing_mode)

    # Run session
    await run_session(client, project_dir)


if __name__ == "__main__":
    asyncio.run(main())
