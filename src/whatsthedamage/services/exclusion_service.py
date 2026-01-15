"""Exclusion Service for managing category exclusions in statistical analysis.

This service handles the configuration and application of category exclusions
for statistical algorithms. It supports both default exclusions (from configuration)
and user-defined exclusions (session-based).
"""
import json
from typing import Dict, List, Optional, Any
from pathlib import Path

class ExclusionService:
    """Service for managing category exclusions in statistical analysis.

    Supports algorithm-specific exclusions and user customizations.
    """

    DEFAULT_EXCLUSIONS_PATH = "config/exclusions.json"

    def __init__(self, exclusions_path: Optional[str] = None):
        """Initialize the exclusion service.

        Args:
            exclusions_path: Path to JSON configuration file. If None, uses default path.
        """
        self.exclusions_path = exclusions_path or self.DEFAULT_EXCLUSIONS_PATH
        self.default_exclusions = self._load_default_exclusions()
        self.user_exclusions: Dict[str, List[str]] = {}

    def _load_default_exclusions(self) -> Dict[str, List[str]]:
        """Load default exclusions from JSON configuration file.

        Returns:
            Dictionary mapping algorithm names to lists of excluded categories.
            Returns empty dict if file doesn't exist or is invalid.
        """
        try:
            config_path = Path(self.exclusions_path)
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Ensure we have the expected structure
                    if isinstance(data, dict):
                        return self._normalize_exclusions(data)
        except (json.JSONDecodeError, IOError, OSError):
            pass
        return {}

    def _normalize_exclusions(self, raw_data: Dict[str, Any]) -> Dict[str, List[str]]:
        """Normalize raw exclusion data to ensure proper structure.

        Args:
            raw_data: Raw data from JSON file

        Returns:
            Normalized dictionary with algorithm-specific exclusion lists
        """
        normalized = {}

        # Handle 'default' key
        if 'default' in raw_data and isinstance(raw_data['default'], list):
            normalized['default'] = [str(item) for item in raw_data['default']]

        # Handle algorithm-specific keys
        for algo in ['iqr', 'pareto']:
            if algo in raw_data and isinstance(raw_data[algo], list):
                normalized[algo] = [str(item) for item in raw_data[algo]]

        return normalized

    def get_exclusions(self, algorithm: str | None = None) -> List[str]:
        """Get exclusions for specific algorithm or all algorithms.

        Args:
            algorithm: Optional algorithm name ('iqr', 'pareto'). If None, returns all exclusions.

        Returns:
            List of excluded category names
        """
        if algorithm:
            # Get algorithm-specific exclusions
            algo_exclusions = self.default_exclusions.get(algorithm, [])
            user_algo_exclusions = self.user_exclusions.get(algorithm, [])
            return list(set(algo_exclusions + user_algo_exclusions))

        # Get all exclusions (union of all algorithm exclusions)
        all_exclusions = []
        for excl_list in self.default_exclusions.values():
            all_exclusions.extend(excl_list)
        for excl_list in self.user_exclusions.values():
            all_exclusions.extend(excl_list)
        return list(set(all_exclusions))

    def set_user_exclusions(self, algorithm: str, exclusions: List[str]) -> None:
        """Set user-defined exclusions for a specific algorithm.

        Args:
            algorithm: Algorithm name ('iqr', 'pareto', or 'default')
            exclusions: List of category names to exclude
        """
        if not isinstance(exclusions, list):
            raise ValueError("Exclusions must be a list of strings")

        # Normalize to strings
        normalized_exclusions = [str(excl) for excl in exclusions]
        self.user_exclusions[algorithm] = normalized_exclusions

    def clear_user_exclusions(self, algorithm: Optional[str] = None) -> None:
        """Clear user-defined exclusions.

        Args:
            algorithm: Optional algorithm name. If None, clears all user exclusions.
        """
        if algorithm:
            self.user_exclusions.pop(algorithm, None)
        else:
            self.user_exclusions.clear()

    def is_excluded(self, category: str, algorithm: str | None = None) -> bool:
        """Check if a category is excluded.

        Args:
            category: Category name to check
            algorithm: Optional algorithm name for algorithm-specific check

        Returns:
            True if category is excluded, False otherwise
        """
        if not category:
            return False

        exclusions = self.get_exclusions(algorithm)
        return str(category) in exclusions

    def get_exclusion_config(self) -> Dict[str, Any]:
        """Get the current exclusion configuration for frontend display.

        Returns:
            Dictionary containing both default and user exclusions
        """
        return {
            'default': self.default_exclusions,
            'user': self.user_exclusions
        }
