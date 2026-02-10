"""Statistical algorithms for transaction data analysis.

This module contains the Strategy Pattern implementation for various
statistical analysis algorithms used to identify patterns in transaction data.
"""
from abc import ABC, abstractmethod
from typing import Dict
import numpy as np
from scipy import stats

class StatisticalAlgorithm(ABC):
    """Abstract base class for statistical algorithms."""

    def __init__(self) -> None:
        """Initialize algorithm."""
        pass

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
        """Detect outliers using Interquartile Range method.

        Args:
            data: Dictionary with keys as identifiers and values as amounts

        Returns:
            Dictionary with keys as identifiers and values as 'outlier' for detected outliers
        """
        highlights: Dict[str, str] = {}
        amounts = list(data.values())
        keys = list(data.keys())

        # Validate dataset size and warn/return early for small datasets
        if not amounts or len(amounts) < 4:
            print("Warning: Not enough data. IQR outlier detection requires at least 4 data points for meaningful results.")
            return highlights

        # Warn for very small datasets
        if 4 <= len(amounts) <= 10:
            print("Warning: Small dataset size (4-10 points). IQR may not be representative.")

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
        """Identify top contributors using Pareto 80/20 rule.

        Args:
            data: Dictionary with keys as identifiers and values as amounts

        Returns:
            Dictionary with keys as identifiers and values as 'pareto' for top contributors
        """
        highlights: Dict[str, str] = {}
        # Convert to list of (key, amount) tuples
        items = [(key, abs(amount)) for key, amount in data.items()]

        if not items:
            return highlights

        # Check for zero total using original values (before abs)
        if sum(data.values()) == 0:
            print("Warning: Not enough data. Pareto principle won't apply.")
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
