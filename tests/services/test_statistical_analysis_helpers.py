"""Tests for helper methods extracted from StatisticalAnalysisService."""

import pytest
from whatsthedamage.services.statistical_analysis_service import StatisticalAnalysisService

from whatsthedamage.services.statistical_analysis_service import AnalysisDirection
from whatsthedamage.models.domain.statistical_algorithms import (
    IQROutlierDetection,
    ParetoAnalysis
)
from whatsthedamage.models.domain.dt_models import AggregatedRow, DisplayRawField, DateField
from whatsthedamage.models.domain.account import Account
import uuid

@pytest.fixture
def sample_dt_response():
    """Create a sample Account for testing helper methods."""
    row_id_grocery="f178193c-faef-4d1e-86a5-61347d30a0d7"
    regular_rows = [
        AggregatedRow(
            row_id=row_id_grocery,
            category_id="grocery",
            total=DisplayRawField(display="100.00", raw=100.0),
            date=DateField(display="January 2023", timestamp=1672531200),
            details=[],
            is_calculated=False
        ),
        AggregatedRow(
            row_id=str(uuid.uuid4()),
            category_id="home_maintenance",
            total=DisplayRawField(display="500.00", raw=500.0),
            date=DateField(display="January 2023", timestamp=1672531200),
            details=[],
            is_calculated=False
        ),
        AggregatedRow(
            row_id=str(uuid.uuid4()),
            category_id="utility",
            total=DisplayRawField(display="200.00", raw=200.0),
            date=DateField(display="February 2023", timestamp=1677657600),
            details=[],
            is_calculated=False
        )
    ]

    calculated_rows = [
        AggregatedRow(
            row_id=str(uuid.uuid4()),
            category_id="balance",
            total=DisplayRawField(display="600.00", raw=600.0),
            date=DateField(display="January 2023", timestamp=1672531200),
            details=[],
            is_calculated=True
        ),
        AggregatedRow(
            row_id=str(uuid.uuid4()),
            category_id="total_spendings",
            total=DisplayRawField(display="800.00", raw=800.0),
            date=DateField(display="Total", timestamp=0),
            details=[],
            is_calculated=True
        )
    ]

    all_rows = regular_rows + calculated_rows

    return Account(
        data=all_rows,
        id="12345678",
        currency="EUR"
    )

@pytest.fixture
def dt_response_with_outliers():
    """Create a Account with data that will produce outliers."""
    row_id_outlier="f178193c-faef-4d1e-86a5-61347d30a0d7"
    regular_rows = [
        AggregatedRow(
            row_id=row_id_outlier,
            category_id="grocery",
            total=DisplayRawField(display="-100.00", raw=-100.0),
            date=DateField(display="January 2023", timestamp=1672531200),
            details=[],
            is_calculated=False
        ),
        AggregatedRow(
            row_id=str(uuid.uuid4()),
            category_id="home_maintenance",
            total=DisplayRawField(display="-200.00", raw=-200.0),
            date=DateField(display="January 2023", timestamp=1672531200),
            details=[],
            is_calculated=False
        ),
        AggregatedRow(
            row_id=str(uuid.uuid4()),
            category_id="utility",
            total=DisplayRawField(display="-100000.00", raw=-100000.0),
            date=DateField(display="January 2023", timestamp=1672531200),
            details=[],
            is_calculated=False
        )
    ]

    calculated_rows = [
        AggregatedRow(
            row_id=str(uuid.uuid4()),
            category_id="balance",
            total=DisplayRawField(display="-300.00", raw=-300.0),
            date=DateField(display="January 2023", timestamp=1672531200),
            details=[],
            is_calculated=True
        )
    ]

    all_rows = regular_rows + calculated_rows

    return Account(
        data=all_rows,
        id="12345678",
        currency="EUR"
    )

class TestHelperMethods:
    """Tests for extracted helper methods."""

    def test_build_month_to_rows_map(self, sample_dt_response):
        """Test _build_month_to_rows_map creates correct mapping."""
        service = StatisticalAnalysisService()
        month_map = service._build_month_to_rows_map(sample_dt_response)

        # Should have entries for January 2023 and February 2023
        assert "January 2023" in month_map
        assert "February 2023" in month_map

        # January should have 3 rows (Grocery, Rent, Balance)
        assert len(month_map["January 2023"]) == 3
        categories = [row.category_id for row in month_map["January 2023"]]
        assert "grocery" in categories
        assert "home_maintenance" in categories
        assert "balance" in categories

        # February should have 1 row (Utilities)
        assert len(month_map["February 2023"]) == 1
        assert month_map["February 2023"][0].category_id == "utility"

    def test_is_cell_excluded_calculated_row(self, sample_dt_response):
        """Test _is_cell_excluded identifies calculated rows."""
        service = StatisticalAnalysisService()
        # Balance row is calculated
        result = service._is_cell_excluded("January 2023", "balance", sample_dt_response)
        assert result is True

    def test_is_cell_excluded_regular_row(self, sample_dt_response):
        """Test _is_cell_excluded identifies regular rows as not excluded."""
        service = StatisticalAnalysisService()
        # Grocery row is not calculated
        result = service._is_cell_excluded("January 2023", "grocery", sample_dt_response)
        assert result is False

    def test_is_cell_excluded_with_exclusion_service(self, sample_dt_response):
        """Test _is_cell_excluded with exclusion service."""
        service = StatisticalAnalysisService()
        service.set_user_exclusions("default", ["home_maintenance"])
        # Rent is in exclusion list
        result = service._is_cell_excluded("January 2023", "home_maintenance", sample_dt_response)
        assert result is True

        # Grocery is not excluded
        result = service._is_cell_excluded("January 2023", "grocery", sample_dt_response)
        assert result is False

    def test_is_cell_excluded_nonexistent_month(self, sample_dt_response):
        """Test _is_cell_excluded with non-existent month."""
        service = StatisticalAnalysisService()
        result = service._is_cell_excluded("March 2023", "grocery", sample_dt_response)
        assert result is False

    def test_direction_handling_simplification(self):
        """Test that direction handling is simplified after removing _get_algorithm_direction."""
        service = StatisticalAnalysisService()

        # Since algorithms no longer have preferred directions, direction is used directly
        # The _get_algorithm_direction method has been removed as it was just a wrapper
        # Test that the service still works correctly with direction parameters
        from whatsthedamage.models.domain.dt_models import SummaryData

        summary = SummaryData(
            summary={
                "2023-01": {
                    "grocery": 500.0,
                    "home_maintenance": 1000.0,
                    "entertainment_and_leisure": 100.0,
                    "utility": 200.0,
                    "transportation": 150.0
                }
            },
            currency="USD",
            account_id="test"
        )

        # Test that both COLUMNS and ROWS directions work
        highlights_columns = service.get_highlights(summary, AnalysisDirection.COLUMNS)
        highlights_rows = service.get_highlights(summary, AnalysisDirection.ROWS)

        # Both should work without errors
        assert isinstance(highlights_columns, list)
        assert isinstance(highlights_rows, list)

    def test_build_highlight_columns_direction(self):
        """Test _build_highlight for COLUMNS direction."""
        service = StatisticalAnalysisService()
        highlight = service._build_highlight(
            "f178193c-faef-4d1e-86a5-61347d30a0d7",
            "outlier"
        )

        assert highlight.row_id == "f178193c-faef-4d1e-86a5-61347d30a0d7"
        assert highlight.highlight_types == ["outlier"]

    def test_build_highlight_rows_direction(self):
        """Test _build_highlight for ROWS direction."""
        service = StatisticalAnalysisService()
        highlight = service._build_highlight(
            "f178193c-faef-4d1e-86a5-61347d30a0d7",
            "pareto"
        )

        assert highlight.row_id == "f178193c-faef-4d1e-86a5-61347d30a0d7"
        assert highlight.highlight_types == ["pareto"]

    def test_create_highlight_for_algorithm_columns_direction(self, dt_response_with_outliers):
        """Test _create_highlight_for_algorithm with COLUMNS direction."""
        service = StatisticalAnalysisService()
        algo = IQROutlierDetection()

        # Create transformed data for COLUMNS direction with actual outliers
        # Format: List[Tuple[month, Dict[category, amount]]]
        # Using negative values (expenses) that will create outliers: -100, -200, -300, -100000
        # All categories together will create an outlier
        transformed_data = [
            ("January 2023", {"grocery": -100.0, "home_maintenance": -200.0, "utility": -100000.0, "balance": -300.0}),
        ]

        # Call the method
        highlights = service._create_highlight_for_algorithm(
            algo,
            AnalysisDirection.COLUMNS,
            transformed_data,
            dt_response_with_outliers
        )

        # Should find highlights for outliers
        assert len(highlights) > 0
        # Check that highlight type is correct
        for highlight in highlights:
            assert highlight.highlight_types[0] == "outlier"

    def test_create_highlight_for_algorithm_rows_direction(self, sample_dt_response):
        """Test _create_highlight_for_algorithm with ROWS direction."""
        service = StatisticalAnalysisService()
        algo = ParetoAnalysis()

        # Create transformed data for ROWS direction
        # Format: List[Tuple[category, Dict[month, amount]]]
        transformed_data = [
            ("grocery", {"January 2023": 100.0}),
            ("home_maintenance", {"January 2023": 500.0}),
            ("utility", {"February 2023": 200.0}),
            ("balance", {"January 2023": 600.0})
        ]

        # Call the method
        highlights = service._create_highlight_for_algorithm(
            algo,
            AnalysisDirection.ROWS,
            transformed_data,
            sample_dt_response
        )

        # Should find highlights for pareto items
        assert len(highlights) > 0
        # Check that highlights reference the correct row IDs
        highlight_row_ids = [h.row_id for h in highlights]
        # The grocery row should be in the highlights (it's a pareto item)
        grocery_row_id = "f178193c-faef-4d1e-86a5-61347d30a0d7"
        assert grocery_row_id in highlight_row_ids
        # Check that highlight type is correct
        for highlight in highlights:
            assert highlight.highlight_types[0] == "pareto"

    def test_create_highlight_for_algorithm_empty_data(self, sample_dt_response):
        """Test _create_highlight_for_algorithm with empty transformed data."""
        service = StatisticalAnalysisService()
        algo = IQROutlierDetection()

        # Empty transformed data
        transformed_data = []

        # Call the method
        highlights = service._create_highlight_for_algorithm(
            algo,
            AnalysisDirection.COLUMNS,
            transformed_data,
            sample_dt_response
        )

        # Should return empty list
        assert len(highlights) == 0

    def test_create_highlight_for_algorithm_no_matches(self, sample_dt_response):
        """Test _create_highlight_for_algorithm when no rows match the data."""
        service = StatisticalAnalysisService()
        algo = IQROutlierDetection()

        # Create transformed data with non-existent months/categories
        transformed_data = [
            ("March 2023", {"Unknown": 1000.0}),
            ("April 2023", {"Another": 2000.0})
        ]

        # Call the method
        highlights = service._create_highlight_for_algorithm(
            algo,
            AnalysisDirection.COLUMNS,
            transformed_data,
            sample_dt_response
        )

        # Should return empty list since no rows match
        assert len(highlights) == 0
