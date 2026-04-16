"""
Execution Nodes Package
========================

Registry for execution node types. Each node registers itself at import time.
"""

import logging
from typing import Optional

from .base_node import BaseExecutionNode, ExecutionResult

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Node registry — maps node_type string to node class
# ---------------------------------------------------------------------------

NODE_REGISTRY: dict[str, type[BaseExecutionNode]] = {}


def register_node(node_type: str, cls: type[BaseExecutionNode]) -> None:
    """Register a node class for a given node type string."""
    NODE_REGISTRY[node_type] = cls


def get_node(node_type: str) -> Optional[BaseExecutionNode]:
    """Get an instantiated node for the given type, or None if not registered."""
    cls = NODE_REGISTRY.get(node_type)
    return cls() if cls else None


def list_node_types() -> list[str]:
    """List all registered node type strings."""
    return list(NODE_REGISTRY.keys())


# Auto-import node modules to trigger registration
# Lazy imports to avoid errors if optional deps (Playwright) are missing
def _register_all() -> None:
    """Import all node modules to trigger their register_node() calls."""
    _node_modules = [
        ("web_scraper", "web_scraper"),
        ("browser_automator", "browser_automator"),
        ("api_executor", "api_executor"),
        ("deployment_executor", "deployment_executor"),
        ("notification_sender", "notification_sender"),
    ]
    for node_name, mod_name in _node_modules:
        try:
            __import__(f"{__name__}.{mod_name}", fromlist=[mod_name])
        except ImportError as e:
            logger.warning("Failed to import %s node: %s", node_name, e)


_register_all()
