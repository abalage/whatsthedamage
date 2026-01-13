"""Statistical Analysis Service for detecting outliers and applying Pareto analysis.

This service uses the Strategy Pattern to apply various statistical algorithms
to transaction data, providing highlight metadata for visualization.
"""
from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, List, Tuple
import numpy as np
from scipy import stats
from whatsthedamage.config.dt_models import CellHighlight


class StatisticalAlgorithm(ABC):
    """Abstract base class for statistical algorithms."""

    @abstractmethod
    def analyze(self, data: Dict[str, float]) -> Dict[str, str]:
        """Analyze the data and return highlight metadata.

        :param data: Dictionary with keys as identifiers and values as amounts.
        :return: Dictionary with keys as identifiers and values as highlight types (e.g., 'outlier', 'pareto').
        """
        pass


class IQROutlierDetection(StatisticalAlgorithm):
    """IQR-based outlier detection algorithm."""

    def analyze(self, data: Dict[str, float]) -> Dict[str, str]:
        highlights: Dict[str, str] = {}
        amounts = list(data.values())
        keys = list(data.keys())

        if not amounts:
            return highlights

        # Calculate Q1, Q3, IQR using scipy
        q1 = np.percentile(amounts, 25)
        q3 = np.percentile(amounts, 75)
        iqr = stats.iqr(amounts)  # Use scipy.stats.iqr
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr

        for key, amount in zip(keys, amounts):
            if amount < lower_bound or amount > upper_bound:
                highlights[key] = 'outlier'

        return highlights


class ParetoAnalysis(StatisticalAlgorithm):
    """Pareto analysis for identifying top contributors."""

    def analyze(self, data: Dict[str, float]) -> Dict[str, str]:
        highlights: Dict[str, str] = {}
        # Convert to list of (key, amount) tuples
        items = [(key, abs(amount)) for key, amount in data.items()]

        if not items:
            return highlights

        # Sort by amount descending
        items.sort(key=lambda x: x[1], reverse=True)

        total = sum(amount for _, amount in items)
        cumulative: float = 0.0
        for key, amount in items:
            cumulative += amount
            if cumulative < 0.8 * total:  # 80% rule - use < instead of <=
                highlights[key] = 'pareto'
            else:
                # Include the item that pushes us over 80%
                highlights[key] = 'pareto'
                break

        return highlights


class AnalysisDirection(Enum):
    """Direction for statistical analysis.

    COLUMNS: Analyze inner keys within each outer key (e.g., categories within months)
    ROWS: Analyze outer keys within each inner key (e.g., months within categories)
    """
    COLUMNS = "columns"
    ROWS = "rows"

class StatisticalAnalysisService:
    """Service for applying statistical algorithms to data.

    Uses Strategy Pattern for extensible algorithm selection.
    Decoupled from AppConfig - only depends on algorithm names.
    """

    def __init__(self, enabled_algorithms: List[str] | None = None):
        """Initialize statistical analysis service.

        :param enabled_algorithms: List of algorithm names to enable (e.g., ['iqr', 'pareto'])
                                   If None, all algorithms are enabled.
        """
        self.algorithms: Dict[str, StatisticalAlgorithm] = {
            'iqr': IQROutlierDetection(),
            'pareto': ParetoAnalysis(),
        }
        self.enabled_algorithms = enabled_algorithms if enabled_algorithms is not None else list(self.algorithms.keys())

    def analyze(self, data: Dict[str, float], algorithms: List[str] | None = None) -> Dict[str, str]:
        """Apply specified algorithms (or enabled algorithms) and return combined highlights.

        :param data: The flat data to analyze (keys as identifiers, values as amounts).
        :param algorithms: Optional list of algorithm names to use (overrides enabled_algorithms).
        :return: Dictionary of highlights keyed by identifiers.
        """
        algorithms_to_use = algorithms if algorithms is not None else self.enabled_algorithms
        highlights = {}
        for algo_name in algorithms_to_use:
            if algo_name in self.algorithms:
                algo_highlights = self.algorithms[algo_name].analyze(data)
                # Only add highlights for keys that don't already exist
                for key, value in algo_highlights.items():
                    if key not in highlights:
                        highlights[key] = value
        return highlights

    def _transform_data_for_analysis(
        self,
        summary: Dict[str, Dict[str, float]],
        direction: AnalysisDirection
    ) -> List[Tuple[str, Dict[str, float]]]:
        """Transform summary data based on analysis direction.

        :param summary: Nested dictionary structure Dict[outer_key, Dict[inner_key, amount]]
        :param direction: Analysis direction (COLUMNS or ROWS)
        :return: List of (key, data_dict) tuples for analysis
        """
        if direction == AnalysisDirection.COLUMNS:
            # Analyze inner keys within each outer key (e.g., categories within months)
            return [(outer_key, inner_data) for outer_key, inner_data in summary.items()]
        else:  # ROWS
            # Analyze outer keys within each inner key (e.g., months within categories)
            # Transpose the data structure
            transposed_data: Dict[str, Dict[str, float]] = {}
            for outer_key, inner_data in summary.items():
                for inner_key, amount in inner_data.items():
                    if inner_key not in transposed_data:
                        transposed_data[inner_key] = {}
                    transposed_data[inner_key][outer_key] = amount
            return [(inner_key, outer_data) for inner_key, outer_data in transposed_data.items()]

    def get_highlights(
        self,
        summary: Dict[str, Dict[str, float]],
        direction: AnalysisDirection = AnalysisDirection.COLUMNS,
        algorithms: List[str] | None = None
    ) -> List[CellHighlight]:
        """Get highlights for the summary data with flexible analysis direction.

        :param summary: Dict[outer_key, Dict[inner_key, amount]]
                      For COLUMNS: Dict[month, Dict[category, amount]]
                      For ROWS: Dict[month, Dict[category, amount]] (will be transposed)
        :param direction: Analysis direction (COLUMNS or ROWS), default COLUMNS
        :param algorithms: Optional list of algorithm names to use (overrides enabled_algorithms)
        :return: List of CellHighlight
        """
        highlights = []
        transformed_data = self._transform_data_for_analysis(summary, direction)

        for outer_key, inner_data in transformed_data:
            data_highlights = self.analyze(inner_data, algorithms)

            for inner_key, highlight_type in data_highlights.items():
                if direction == AnalysisDirection.COLUMNS:
                    # COLUMNS: row=inner_key, column=outer_key (e.g., row=category, column=month)
                    highlights.append(CellHighlight(
                        row=inner_key,
                        column=outer_key,
                        highlight_type=highlight_type
                    ))
                else:  # ROWS
                    # ROWS: row=outer_key, column=inner_key (e.g., row=month, column=category)
                    highlights.append(CellHighlight(
                        row=inner_key,
                        column=outer_key,
                        highlight_type=highlight_type
                    ))
        return highlights
