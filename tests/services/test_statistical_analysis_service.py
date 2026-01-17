"""Tests for StatisticalAnalysisService and related algorithms."""

import pytest
from whatsthedamage.services.statistical_analysis_service import (
    StatisticalAnalysisService,
    IQROutlierDetection,
    ParetoAnalysis,
    StatisticalAlgorithm,
    AnalysisDirection
)
from whatsthedamage.config.dt_models import CellHighlight
from typing import Dict

@pytest.fixture
def summary_data_with_outliers():
    """Fixture providing summary data with outliers for testing."""
    return {
        "2023-01": {
            "Grocery": 500.0,
            "Rent": 1000.0,  # Should be outlier
            "Entertainment": 100.0,
            "Utilities": 200.0,
            "Transport": 150.0,
            "Dining": 300.0,
            "Shopping": 250.0
        },
        "2023-02": {
            "Grocery": 400.0,
            "Rent": 800.0,  # Should be outlier
            "Entertainment": 50.0,
            "Utilities": 200.0,
            "Transport": 150.0,
            "Dining": 200.0,
            "Shopping": 200.0
        },
        "2023-03": {
            "Grocery": 450.0,
            "Rent": 600.0,
            "Entertainment": 60.0,
            "Utilities": 210.0,
            "Transport": 160.0,
            "Dining": 220.0,
            "Shopping": 220.0
        },
        "2023-04": {
            "Grocery": 480.0,
            "Rent": 650.0,
            "Entertainment": 70.0,
            "Utilities": 220.0,
            "Transport": 170.0,
            "Dining": 230.0,
            "Shopping": 230.0
        },
        "2023-05": {
            "Grocery": 470.0,
            "Rent": 620.0,
            "Entertainment": 65.0,
            "Utilities": 215.0,
            "Transport": 165.0,
            "Dining": 225.0,
            "Shopping": 225.0
        }
    }

class TestIQROutlierDetection:
    """Tests for IQROutlierDetection algorithm."""

    def test_empty_data_returns_empty_highlights(self):
        """Test with empty data returns empty highlights."""
        algorithm = IQROutlierDetection()
        result = algorithm.analyze({})
        assert result == {}

    def test_single_data_point_no_outliers(self):
        """Test single data point is never an outlier."""
        algorithm = IQROutlierDetection()
        data = {"item1": 100.0}
        result = algorithm.analyze(data)
        assert result == {}

    def test_normal_distribution_no_outliers(self):
        """Test normal distribution with no outliers."""
        algorithm = IQROutlierDetection()
        # Data: 10, 20, 30, 40, 50, 60, 70, 80, 90
        data = {f"item{i}": float(10 * (i + 1)) for i in range(9)}
        result = algorithm.analyze(data)
        assert result == {}

    def test_data_with_lower_outlier(self):
        """Test data with lower outlier detection."""
        algorithm = IQROutlierDetection()
        # Data with one very low value: -100, 10, 20, 30, 40, 50, 60, 70, 80, 90
        data = {"outlier": -100.0, "item1": 10.0, "item2": 20.0, "item3": 30.0,
                "item4": 40.0, "item5": 50.0, "item6": 60.0, "item7": 70.0,
                "item8": 80.0, "item9": 90.0}
        result = algorithm.analyze(data)
        assert "outlier" in result
        assert result["outlier"] == "outlier"

    def test_data_with_upper_outlier(self):
        """Test data with upper outlier detection."""
        algorithm = IQROutlierDetection()
        # Data with one very high value: 10, 20, 30, 40, 50, 60, 70, 80, 90, 1000
        data = {"item1": 10.0, "item2": 20.0, "item3": 30.0, "item4": 40.0,
                "item5": 50.0, "item6": 60.0, "item7": 70.0, "item8": 80.0,
                "item9": 90.0, "outlier": 1000.0}
        result = algorithm.analyze(data)
        assert "outlier" in result
        assert result["outlier"] == "outlier"

    def test_multiple_outliers(self):
        """Test data with multiple outliers."""
        algorithm = IQROutlierDetection()
        # Data with multiple outliers: -100, 10, 20, 30, 40, 50, 60, 70, 80, 90, 1000
        data = {"low_outlier": -100.0, "item1": 10.0, "item2": 20.0, "item3": 30.0,
                "item4": 40.0, "item5": 50.0, "item6": 60.0, "item7": 70.0,
                "item8": 80.0, "item9": 90.0, "high_outlier": 1000.0}
        result = algorithm.analyze(data)
        assert "low_outlier" in result
        assert "high_outlier" in result
        assert result["low_outlier"] == "outlier"
        assert result["high_outlier"] == "outlier"

class TestParetoAnalysis:
    """Tests for ParetoAnalysis algorithm."""

    def test_empty_data_returns_empty_highlights(self):
        """Test with empty data returns empty highlights."""
        algorithm = ParetoAnalysis()
        result = algorithm.analyze({})
        assert result == {}

    def test_single_item_is_pareto(self):
        """Test single item is always in pareto."""
        algorithm = ParetoAnalysis()
        data = {"item1": 100.0}
        result = algorithm.analyze(data)
        assert result == {"item1": "pareto"}

    def test_two_items_both_pareto(self):
        """Test two items where both contribute to 80%."""
        algorithm = ParetoAnalysis()
        data = {"item1": 60.0, "item2": 40.0}  # 60 + 40 = 100, 80% = 80
        result = algorithm.analyze(data)
        assert "item1" in result
        assert "item2" in result
        assert result["item1"] == "pareto"
        assert result["item2"] == "pareto"

    def test_pareto_80_20_rule(self):
        """Test 80/20 rule - top contributors get pareto highlight."""
        algorithm = ParetoAnalysis()
        # Data: 50, 30, 10, 5, 3, 2 (total = 100, 80% = 80)
        # Pareto should include: 50, 30 (cumulative: 50 + 30 = 80)
        data = {"item1": 50.0, "item2": 30.0, "item3": 10.0, "item4": 5.0, "item5": 3.0, "item6": 2.0}
        result = algorithm.analyze(data)
        assert "item1" in result
        assert "item2" in result
        assert "item3" not in result  # 50 + 30 + 10 = 90 > 80, so item3 not included
        assert result["item1"] == "pareto"
        assert result["item2"] == "pareto"

    def test_negative_values_handled_correctly(self):
        """Test pareto analysis with negative values (absolute values used)."""
        algorithm = ParetoAnalysis()
        # Data with negative values: -50, -30, -10, -5, -3, -2 (absolute: 50, 30, 10, 5, 3, 2)
        data = {"item1": -50.0, "item2": -30.0, "item3": -10.0, "item4": -5.0, "item5": -3.0, "item6": -2.0}
        result = algorithm.analyze(data)
        assert "item1" in result
        assert "item2" in result
        assert result["item1"] == "pareto"
        assert result["item2"] == "pareto"

    def test_mixed_positive_negative_values(self):
        """Test pareto analysis with mixed positive and negative values."""
        algorithm = ParetoAnalysis()
        # Mixed values: 100, -50, 30, -20, 10, -5
        # Absolute values: 100, 50, 30, 20, 10, 5 (total = 215, 80% = 172)
        # Pareto: 100, -50, 30 (cumulative: 100 + 50 + 30 = 180 > 172)
        data = {"item1": 100.0, "item2": -50.0, "item3": 30.0, "item4": -20.0, "item5": 10.0, "item6": -5.0}
        result = algorithm.analyze(data)
        assert "item1" in result
        assert "item2" in result
        assert "item3" in result
        assert result["item1"] == "pareto"
        assert result["item2"] == "pareto"
        assert result["item3"] == "pareto"

class TestStatisticalAnalysisService:
    """Tests for StatisticalAnalysisService integration."""

    def test_init_with_all_algorithms_enabled(self):
        """Test initialization with all algorithms enabled by default."""
        service = StatisticalAnalysisService()
        assert len(service.enabled_algorithms) == 2
        assert "iqr" in service.enabled_algorithms
        assert "pareto" in service.enabled_algorithms

    def test_init_with_specific_algorithms(self):
        """Test initialization with specific algorithms."""
        service = StatisticalAnalysisService(enabled_algorithms=["iqr"])
        assert len(service.enabled_algorithms) == 1
        assert "iqr" in service.enabled_algorithms
        assert "pareto" not in service.enabled_algorithms

    def test_init_with_empty_algorithms_list(self):
        """Test initialization with empty algorithms list."""
        service = StatisticalAnalysisService(enabled_algorithms=[])
        # When empty list is provided, it should result in empty algorithms
        assert len(service.enabled_algorithms) == 0
        assert service.analyze({}) == {}

    def test_analyze_with_both_algorithms(self):
        """Test analyze with both algorithms enabled."""
        service = StatisticalAnalysisService(enabled_algorithms=["iqr", "pareto"])
        # Data with both outlier and pareto characteristics
        # Need more data points for IQR to work properly
        data = {
            "outlier": 1000.0,  # Should be outlier
            "item1": 10.0,
            "item2": 20.0,
            "item3": 30.0,
            "item4": 40.0,
            "item5": 50.0,
            "item6": 60.0,
            "item7": 70.0,
            "item8": 80.0,
            "item9": 90.0
        }
        result = service.analyze(data)
        assert "outlier" in result
        assert result["outlier"] == "outlier"
        # Pareto should also work
        assert len(result) >= 1  # At least the outlier

    def test_analyze_with_only_iqr(self):
        """Test analyze with only IQR algorithm."""
        service = StatisticalAnalysisService(enabled_algorithms=["iqr"])
        # Need more data points for IQR to work properly
        data = {
            "outlier": 1000.0,
            "item1": 10.0,
            "item2": 20.0,
            "item3": 30.0,
            "item4": 40.0,
            "item5": 50.0,
            "item6": 60.0,
            "item7": 70.0,
            "item8": 80.0,
            "item9": 90.0
        }
        result = service.analyze(data)
        assert "outlier" in result
        assert result["outlier"] == "outlier"
        assert len(result) == 1  # Only the outlier

    def test_analyze_with_only_pareto(self):
        """Test analyze with only Pareto algorithm."""
        service = StatisticalAnalysisService(enabled_algorithms=["pareto"])
        # Use data where pareto1 will be included in Pareto analysis
        data = {
            "item1": 60.0,    # Should be pareto
            "item2": 40.0,    # Should be pareto
            "item3": 10.0     # Should not be pareto
        }
        result = service.analyze(data)
        assert "item1" in result
        assert "item2" in result
        assert result["item1"] == "pareto"
        assert result["item2"] == "pareto"
        assert "item3" not in result

    def test_analyze_with_invalid_algorithm_name(self):
        """Test analyze with invalid algorithm name (should be ignored)."""
        service = StatisticalAnalysisService(enabled_algorithms=["iqr", "invalid_algo"])
        data = {"item1": 10.0, "item2": 20.0}
        result = service.analyze(data)
        assert result == {}  # No highlights from valid algorithms

    def test_get_highlights_with_summary_data(self):
        """Test get_highlights method with summary data structure (COLUMNS direction)."""
        service = StatisticalAnalysisService(enabled_algorithms=["iqr", "pareto"])

        # Create test summary data with more data points for proper IQR calculation
        summary = {
            "2023-01": {
                "Grocery": 500.0,
                "Rent": 1000.0,  # Should be outlier
                "Entertainment": 100.0,
                "Utilities": 200.0,
                "Transport": 150.0
            },
            "2023-02": {
                "Grocery": 400.0,
                "Utilities": 200.0,
                "Entertainment": 50.0,
                "Transport": 150.0
            }
        }

        highlights = service.get_highlights(summary, AnalysisDirection.COLUMNS)

        # Should have highlights for various categories
        assert len(highlights) > 0
        assert all(isinstance(h, CellHighlight) for h in highlights)

        # Check that we have highlights for the right categories and months
        highlight_dict = {(h.row, h.column): h.highlight_type for h in highlights}

        # Should have Rent as outlier in Jan 2023
        assert ("Rent", "2023-01") in highlight_dict
        # The type might be either "outlier" or "pareto" depending on which algorithm catches it first
        assert highlight_dict[("Rent", "2023-01")] in ["outlier", "pareto"]

    def test_get_highlights_with_rows_direction(self):
        """Test get_highlights method with ROWS direction (months within categories)."""
        service = StatisticalAnalysisService(enabled_algorithms=["iqr", "pareto"])

        # Create test summary data
        summary = {
            "2023-01": {
                "Grocery": 500.0,
                "Rent": 1000.0,
                "Entertainment": 100.0,
                "Utilities": 200.0,
                "Transport": 150.0
            },
            "2023-02": {
                "Grocery": 400.0,
                "Utilities": 200.0,
                "Entertainment": 50.0,
                "Transport": 150.0
            },
            "2023-03": {
                "Grocery": 1500.0,  # Should be outlier for Grocery category
                "Utilities": 250.0,
                "Entertainment": 75.0
            }
        }

        highlights = service.get_highlights(summary, AnalysisDirection.ROWS)

        # Should have highlights for various months within categories
        assert len(highlights) > 0
        assert all(isinstance(h, CellHighlight) for h in highlights)

        # Check that we have highlights for the right months and categories
        highlight_dict = {(h.row, h.column): h.highlight_type for h in highlights}

        # Should have 2023-03 as outlier for Grocery category
        # For ROWS direction: row=category, column=month
        assert ("Grocery", "2023-03") in highlight_dict
        assert highlight_dict[("Grocery", "2023-03")] in ["outlier", "pareto"]


    def test_get_highlights_with_runtime_algorithm_selection(self, summary_data_with_outliers):
        """Test get_highlights with runtime algorithm selection."""
        service = StatisticalAnalysisService(enabled_algorithms=["iqr", "pareto"])

        # Test with only IQR algorithm (explicitly use COLUMNS to override IQR's default)
        highlights_iqr = service.get_highlights(summary_data_with_outliers, AnalysisDirection.COLUMNS, algorithms=["iqr"])
        assert len(highlights_iqr) > 0

        # Test with only Pareto algorithm (explicitly use COLUMNS to match Pareto's default)
        highlights_pareto = service.get_highlights(summary_data_with_outliers, AnalysisDirection.COLUMNS, algorithms=["pareto"])
        assert len(highlights_pareto) > 0

        # Test with both algorithms
        highlights_both = service.get_highlights(summary_data_with_outliers, AnalysisDirection.COLUMNS, algorithms=["iqr", "pareto"])
        assert len(highlights_both) > 0

    def test_analyze_with_runtime_algorithm_selection(self):
        """Test analyze method with runtime algorithm selection."""
        service = StatisticalAnalysisService(enabled_algorithms=["iqr"])

        data = {
            "outlier": 1000.0,
            "item1": 10.0,
            "item2": 20.0,
            "item3": 30.0,
            "item4": 40.0,
            "item5": 50.0,
            "item6": 60.0,
            "item7": 70.0,
            "item8": 80.0,
            "item9": 90.0
        }

        # Test with default algorithms (should use enabled_algorithms)
        result_default = service.analyze(data)
        assert "outlier" in result_default

        # Test with runtime algorithm selection (override enabled_algorithms)
        result_pareto = service.analyze(data, algorithms=["pareto"])
        assert len(result_pareto) > 0

        # Test with empty algorithm list
        result_empty = service.analyze(data, algorithms=[])
        assert result_empty == {}

    def test_data_transformation_for_columns_direction(self):
        """Test data transformation for COLUMNS direction."""
        service = StatisticalAnalysisService()

        summary = {
            "month1": {"cat1": 100.0, "cat2": 200.0},
            "month2": {"cat1": 150.0, "cat3": 300.0}
        }

        transformed = service._transform_data_for_analysis(summary, AnalysisDirection.COLUMNS)
        assert len(transformed) == 2
        assert ("month1", {"cat1": 100.0, "cat2": 200.0}) in transformed
        assert ("month2", {"cat1": 150.0, "cat3": 300.0}) in transformed

    def test_data_transformation_for_rows_direction(self):
        """Test data transformation for ROWS direction."""
        service = StatisticalAnalysisService()

        summary = {
            "month1": {"cat1": 100.0, "cat2": 200.0},
            "month2": {"cat1": 150.0, "cat3": 300.0}
        }

        transformed = service._transform_data_for_analysis(summary, AnalysisDirection.ROWS)
        assert len(transformed) == 3
        assert ("cat1", {"month1": 100.0, "month2": 150.0}) in transformed
        assert ("cat2", {"month1": 200.0}) in transformed
        assert ("cat3", {"month2": 300.0}) in transformed

    def test_get_highlights_with_empty_summary(self):
        """Test get_highlights with empty summary."""
        service = StatisticalAnalysisService()
        highlights = service.get_highlights({})
        assert highlights == []

    def test_get_highlights_with_no_highlights(self):
        """Test get_highlights when no highlights are detected."""
        service = StatisticalAnalysisService(enabled_algorithms=["iqr"])
        summary = {
            "2023-01": {
                "Grocery": 100.0,
                "Entertainment": 100.0,
                "Utilities": 100.0
            }
        }
        highlights = service.get_highlights(summary)
        assert highlights == []

class TestStatisticalAlgorithmIntegration:
    """Integration tests for statistical algorithms."""

    def test_algorithm_strategy_pattern(self):
        """Test that algorithms follow the strategy pattern correctly."""
        # Create a mock algorithm
        class MockAlgorithm(StatisticalAlgorithm):
            def analyze(self, data: Dict[str, float]) -> Dict[str, str]:
                return {"mock_item": "mock_highlight"}

        # Test that it can be used with the service
        service = StatisticalAnalysisService(enabled_algorithms=[])
        service.algorithms["mock"] = MockAlgorithm()

        # Enable the mock algorithm
        service.enabled_algorithms = ["mock"]
        data = {"mock_item": 100.0, "other": 50.0}
        result = service.analyze(data)

        assert "mock_item" in result
        assert result["mock_item"] == "mock_highlight"
