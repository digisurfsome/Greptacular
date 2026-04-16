"""
Adapter Registry — Auto-Discovery for API Adapters
=====================================================

Imports all adapter modules to trigger their register_adapter() calls.
Uses the existing register_adapter/get_adapter from base.py — does NOT
recreate them.
"""

import logging

# Re-export from base for convenience
from .base import get_adapter, register_adapter  # noqa: F401

logger = logging.getLogger(__name__)


def discover_adapters() -> list[str]:
    """Import all adapter modules to register them. Returns list of registered service keys."""
    from .base import _ADAPTER_REGISTRY

    modules = [
        "google_sheets",
        "slack",
        "airtable",
        "generic_rest",
    ]

    for mod_name in modules:
        try:
            __import__(f"server.services.api_adapters.{mod_name}", fromlist=[mod_name])
        except ImportError as e:
            logger.warning("Adapter module %s not available: %s", mod_name, e)
        except Exception as e:
            logger.warning("Failed to load adapter module %s: %s", mod_name, e)

    return list(_ADAPTER_REGISTRY.keys())


# Auto-discover on import
_registered = discover_adapters()
if _registered:
    logger.info("Registered API adapters: %s", _registered)
