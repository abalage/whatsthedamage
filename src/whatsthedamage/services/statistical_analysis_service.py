"""Statistical Analysis Service for detecting outliers and applying Pareto analysis.

This service uses the Strategy Pattern to apply various statistical algorithms
to transaction data, providing highlight metadata for visualization.
"""
from abc import ABC, abstractmethod
from typing import Dict, List
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
            if cumulative <= 0.8 * total:  # 80% rule
                highlights[key] = 'pareto'
            else:
                break

        return highlights


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
        self.enabled_algorithms = enabled_algorithms or list(self.algorithms.keys())

    def analyze(self, data: Dict[str, float]) -> Dict[str, str]:
        """Apply enabled algorithms and return combined highlights.

        :param data: The flat data to analyze (keys as identifiers, values as amounts).
        :return: Dictionary of highlights keyed by identifiers.
        """
        highlights = {}
        for algo_name in self.enabled_algorithms:
            if algo_name in self.algorithms:
                algo_highlights = self.algorithms[algo_name].analyze(data)
                highlights.update(algo_highlights)
        return highlights

    def get_highlights(self, summary: Dict[str, Dict[str, float]]) -> List[CellHighlight]:
        """Get highlights for the summary data.

        :param summary: Dict[month, Dict[category, amount]]
        :return: List of CellHighlight
        """
        highlights = []
        for month, categories in summary.items():
            category_highlights = self.analyze(categories)
            for category, highlight_type in category_highlights.items():
                highlights.append(CellHighlight(
                    row=category,
                    column=month,
                    highlight_type=highlight_type
                ))
        return highlights