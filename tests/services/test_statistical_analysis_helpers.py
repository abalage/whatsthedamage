"""Tests for helper methods extracted from StatisticalAnalysisService."""

import pytest
from whatsthedamage.services.statistical_analysis_service import StatisticalAnalysisService
from whatsthedamage.services.exclusion_service import ExclusionService
from whatsthedamage.models.statistical_algorithms import (
    AnalysisDirection,
    IQROutlierDetection,
    ParetoAnalysis
)
from whatsthedamage.config.dt_models import DataTablesResponse, AggregatedRow, DisplayRawField, DateField
import uuid

@pytest.fixture
def sample_dt_response():
    """Create a sample DataTablesResponse for testing helper methods."""
    row_id_grocery="f178193c-faef-4d1e-86a5-61347d30a0d7"
    regular_rows = [
        AggregatedRow(
            row_id=row_id_grocery,
            category="Grocery",
            total=DisplayRawField(display="100.00", raw=100.0),
            date=DateField(display="January 2023", timestamp=1672531200),
            details=[],
            is_calculated=False
        ),
        AggregatedRow(
            row_id=str(uuid.uuid4()),
            category="Rent",
            total=DisplayRawField(display="500.00", raw=500.0),
            date=DateField(display="January 2023", timestamp=1672531200),
            details=[],
            is_calculated=False
        ),
        AggregatedRow(
            row_id=str(uuid.uuid4()),
            category="Utilities",
            total=DisplayRawField(display="200.00", raw=200.0),
            date=DateField(display="February 2023", timestamp=1677657600),
            details=[],
            is_calculated=False
        )
    ]

    calculated_rows = [
        AggregatedRow(
            row_id=str(uuid.uuid4()),
            category="Balance",
            total=DisplayRawField(display="600.00", raw=600.0),
            date=DateField(display="January 2023", timestamp=1672531200),
            details=[],
            is_calculated=True
        ),
        AggregatedRow(
            row_id=str(uuid.uuid4()),
            category="Total",
            total=DisplayRawField(display="800.00", raw=800.0),
            date=DateField(display="Total", timestamp=0),
            details=[],
            is_calculated=True
        )
    ]

    all_rows = regular_rows + calculated_rows

    return DataTablesResponse(
        data=all_rows,
        account="12345678",
        currency="EUR"
    )

@pytest.fixture
def dt_response_with_outliers():
    """Create a DataTablesResponse with data that will produce outliers."""
    row_id_outlier="f178193c-faef-4d1e-86a5-61347d30a0d7"
    regular_rows = [
        AggregatedRow(
            row_id=row_id_outlier,
            category="Grocery",
            total=DisplayRawField(display="-100.00", raw=-100.0),
            date=DateField(display="January 2023", timestamp=1672531200),
            details=[],
            is_calculated=False
        ),
        AggregatedRow(
            row_id=str(uuid.uuid4()),
            category="Rent",
            total=DisplayRawField(display="-200.00", raw=-200.0),
            date=DateField(display="January 2023", timestamp=1672531200),
            details=[],
            is_calculated=False
        ),
        AggregatedRow(
            row_id=str(uuid.uuid4()),
            category="Utilities",
            total=DisplayRawField(display="-100000.00", raw=-100000.0),
            date=DateField(display="January 2023", timestamp=1672531200),
            details=[],
            is_calculated=False
        )
    ]

    calculated_rows = [
        AggregatedRow(
            row_id=str(uuid.uuid4()),
            category="Balance",
            total=DisplayRawField(display="-300.00", raw=-300.0),
            date=DateField(display="January 2023", timestamp=1672531200),
            details=[],
            is_calculated=True
        )
    ]

    all_rows = regular_rows + calculated_rows

    return DataTablesResponse(
        data=all_rows,
        account="12345678",
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
        categories = [row.category for row in month_map["January 2023"]]
        assert "Grocery" in categories
        assert "Rent" in categories
        assert "Balance" in categories

        # February should have 1 row (Utilities)
        assert len(month_map["February 2023"]) == 1
        assert month_map["February 2023"][0].category == "Utilities"

    def test_is_cell_excluded_calculated_row(self, sample_dt_response):
        """Test _is_cell_excluded identifies calculated rows."""
        service = StatisticalAnalysisService()
        # Balance row is calculated
        result = service._is_cell_excluded("January 2023", "Balance", sample_dt_response)
        assert result is True

    def test_is_cell_excluded_regular_row(self, sample_dt_response):
        """Test _is_cell_excluded identifies regular rows as not excluded."""
        service = StatisticalAnalysisService()
        # Grocery row is not calculated
        result = service._is_cell_excluded("January 2023", "Grocery", sample_dt_response)
        assert result is False

    def test_is_cell_excluded_with_exclusion_service(self, sample_dt_response):
        """Test _is_cell_excluded with exclusion service."""
        exclusion_service = ExclusionService()
        exclusion_service.set_user_exclusions("default", ["Rent"])

        service = StatisticalAnalysisService(exclusion_service=exclusion_service)
        # Rent is in exclusion list
        result = service._is_cell_excluded("January 2023", "Rent", sample_dt_response)
        assert result is True

        # Grocery is not excluded
        result = service._is_cell_excluded("January 2023", "Grocery", sample_dt_response)
        assert result is False

    def test_is_cell_excluded_nonexistent_month(self, sample_dt_response):
        """Test _is_cell_excluded with non-existent month."""
        service = StatisticalAnalysisService()
        result = service._is_cell_excluded("March 2023", "Grocery", sample_dt_response)
        assert result is False

    def test_get_algorithm_direction_with_default(self):
        """Test _get_algorithm_direction uses algorithm's default when requested."""
        service = StatisticalAnalysisService()
        algo = IQROutlierDetection(direction=AnalysisDirection.ROWS)

        # When use_default_directions is True, should use algorithm's direction
        result = service._get_algorithm_direction(algo, AnalysisDirection.COLUMNS, True)
        assert result == AnalysisDirection.ROWS

    def test_get_algorithm_direction_without_default(self):
        """Test _get_algorithm_direction uses parameter when default not requested."""
        service = StatisticalAnalysisService()
        algo = IQROutlierDetection(direction=AnalysisDirection.ROWS)

        # When use_default_directions is False, should use parameter direction
        result = service._get_algorithm_direction(algo, AnalysisDirection.COLUMNS, False)
        assert result == AnalysisDirection.COLUMNS

    def test_build_highlight_columns_direction(self):
        """Test _build_highlight for COLUMNS direction."""
        service = StatisticalAnalysisService()
        highlight = service._build_highlight(
            "f178193c-faef-4d1e-86a5-61347d30a0d7",
            "outlier"
        )

        assert highlight.row_id == "f178193c-faef-4d1e-86a5-61347d30a0d7"
        assert highlight.highlight_type == "outlier"

    def test_build_highlight_rows_direction(self):
        """Test _build_highlight for ROWS direction."""
        service = StatisticalAnalysisService()
        highlight = service._build_highlight(
            "f178193c-faef-4d1e-86a5-61347d30a0d7",
            "pareto"
        )

        assert highlight.row_id == "f178193c-faef-4d1e-86a5-61347d30a0d7"
        assert highlight.highlight_type == "pareto"

    def test_create_highlight_for_algorithm_columns_direction(self, dt_response_with_outliers):
        """Test _create_highlight_for_algorithm with COLUMNS direction."""
        service = StatisticalAnalysisService()
        algo = IQROutlierDetection(direction=AnalysisDirection.COLUMNS)

        # Create transformed data for COLUMNS direction with actual outliers
        # Format: List[Tuple[month, Dict[category, amount]]]
        # Using negative values (expenses) that will create outliers: -100, -200, -300, -100000
        # All categories together will create an outlier
        transformed_data = [
            ("January 2023", {"Grocery": -100.0, "Rent": -200.0, "Utilities": -100000.0, "Balance": -300.0}),
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
            assert highlight.highlight_type == "outlier"

    def test_create_highlight_for_algorithm_rows_direction(self, sample_dt_response):
        """Test _create_highlight_for_algorithm with ROWS direction."""
        service = StatisticalAnalysisService()
        algo = ParetoAnalysis(direction=AnalysisDirection.ROWS)

        # Create transformed data for ROWS direction
        # Format: List[Tuple[category, Dict[month, amount]]]
        transformed_data = [
            ("Grocery", {"January 2023": 100.0}),
            ("Rent", {"January 2023": 500.0}),
            ("Utilities", {"February 2023": 200.0}),
            ("Balance", {"January 2023": 600.0})
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
            assert highlight.highlight_type == "pareto"

    def test_create_highlight_for_algorithm_empty_data(self, sample_dt_response):
        """Test _create_highlight_for_algorithm with empty transformed data."""
        service = StatisticalAnalysisService()
        algo = IQROutlierDetection(direction=AnalysisDirection.COLUMNS)

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
        algo = IQROutlierDetection(direction=AnalysisDirection.COLUMNS)

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
