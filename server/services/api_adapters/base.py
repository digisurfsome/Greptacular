"""Base API adapter interface + adapter registry."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Optional

logger = logging.getLogger(__name__)


class APIAdapter(ABC):
    """Base class for all API adapters."""

    def __init__(self, api_key: str = "", **kwargs: object) -> None:
        self.api_key = api_key

    @abstractmethod
    async def execute(self, action: str, payload: dict) -> dict:
        """Execute an action with the given payload.

        Returns a dict with at minimum:
            {"output": str, ...any additional fields}
        """
        ...

    def validate_key(self) -> bool:
        return bool(self.api_key and self.api_key.strip())


# ---------------------------------------------------------------------------
# Adapter registry — maps service_key → adapter class
# ---------------------------------------------------------------------------

_ADAPTER_REGISTRY: dict[str, type[APIAdapter]] = {}


def register_adapter(service_key: str, cls: type[APIAdapter]) -> None:
    _ADAPTER_REGISTRY[service_key] = cls


def get_adapter(service_key: str, variables: dict[str, str]) -> Optional[APIAdapter]:
    """Return an instantiated adapter for service_key, or None if not registered."""
    cls = _ADAPTER_REGISTRY.get(service_key)
    if not cls:
        return None

    # Look for an API key in variables using common key patterns
    key_patterns = [
        service_key.upper() + "_API_KEY",
        service_key.upper() + "_KEY",
        service_key.upper() + "_TOKEN",
    ]
    api_key = ""
    for pattern in key_patterns:
        if pattern in variables:
            api_key = variables[pattern]
            break

    return cls(api_key=api_key, variables=variables)
