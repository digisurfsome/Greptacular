"""
hooks/base.py — Base class all hook modules must inherit from.
"""

from abc import ABC, abstractmethod
from typing import Dict, List


class HookModule(ABC):
    name: str = ""
    required_env_vars: List[str] = []
    required_input_columns: List[str] = []
    output_columns: List[str] = []

    TIER_ANGLES: Dict[str, str] = {
        "A": "",
        "B": "",
        "C": "",
        "D": "",
    }

    @abstractmethod
    def fetch_data(self, row: dict) -> dict:
        """
        Given a business row from the CSV, call the API and return
        a dict of output_columns populated with real data.
        Return empty dict {} on failure — caller handles gracefully.
        """
        raise NotImplementedError

    @abstractmethod
    def assign_tier(self, data: dict) -> str:
        """
        Given the fetched data dict, return tier: 'A', 'B', 'C', or 'D'.
        """
        raise NotImplementedError

    def check_env(self) -> List[str]:
        """Return list of missing required env vars."""
        import os
        return [v for v in self.required_env_vars if not os.getenv(v)]

    def check_input(self, row: dict) -> List[str]:
        """Return list of missing required input columns."""
        return [c for c in self.required_input_columns if c not in row or not row[c]]
