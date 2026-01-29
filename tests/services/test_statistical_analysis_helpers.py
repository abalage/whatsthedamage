"""Tests for helper methods extracted from StatisticalAnalysisService."""

import pytest
from whatsthedamage.services.statistical_analysis_service import StatisticalAnalysisService
from whatsthedamage.services.exclusion_service import ExclusionService
from whatsthedamage.config.dt_models import DataTablesResponse, AggregatedRow, DisplayRawField, DateField

@pytest.fixture
def sample_dt_response():
    """Create a sample DataTablesResponse for testing helper methods."""
    regular_rows = [
        AggregatedRow(
            category="Grocery",
            total=DisplayRawField(display="100.00", raw=100.0),
            date=DateField(display="January 2023", timestamp=1672531200),
            details=[],
            is_calculated=False
        ),
        AggregatedRow(
            category="Rent",
            total=DisplayRawField(display="500.00", raw=500.0),
            date=DateField(display="January 2023", timestamp=1672531200),
            details=[],
            is_calculated=False
        ),
        AggregatedRow(
            category="Utilities",
            total=DisplayRawField(display="200.00", raw=200.0),
            date=DateField(display="February 2023", timestamp=1677657600),
            details=[],
            is_calculated=False
        )
    ]

    calculated_rows = [
        AggregatedRow(
            category="Balance",
            total=DisplayRawField(display="600.00", raw=600.0),
            date=DateField(display="January 2023", timestamp=1672531200),
            details=[],
            is_calculated=True
        ),
        AggregatedRow(
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
        from whatsthedamage.services.statistical_analysis_service import AnalysisDirection
        from whatsthedamage.services.statistical_analysis_service import IQROutlierDetection

        service = StatisticalAnalysisService()
        algo = IQROutlierDetection(direction=AnalysisDirection.ROWS)

        # When use_default_directions is True, should use algorithm's direction
        result = service._get_algorithm_direction(algo, AnalysisDirection.COLUMNS, True)
        assert result == AnalysisDirection.ROWS

    def test_get_algorithm_direction_without_default(self):
        """Test _get_algorithm_direction uses parameter when default not requested."""
        from whatsthedamage.services.statistical_analysis_service import AnalysisDirection
        from whatsthedamage.services.statistical_analysis_service import IQROutlierDetection

        service = StatisticalAnalysisService()
        algo = IQROutlierDetection(direction=AnalysisDirection.ROWS)

        # When use_default_directions is False, should use parameter direction
        result = service._get_algorithm_direction(algo, AnalysisDirection.COLUMNS, False)
        assert result == AnalysisDirection.COLUMNS

    def test_build_highlight_columns_direction(self):
        """Test _build_highlight for COLUMNS direction."""
        from whatsthedamage.services.statistical_analysis_service import AnalysisDirection

        service = StatisticalAnalysisService()
        highlight = service._build_highlight(
            AnalysisDirection.COLUMNS,
            "January 2023",
            "Grocery",
            "outlier"
        )

        assert highlight.row == "Grocery"
        assert highlight.column == "January 2023"
        assert highlight.highlight_type == "outlier"

    def test_build_highlight_rows_direction(self):
        """Test _build_highlight for ROWS direction."""
        from whatsthedamage.services.statistical_analysis_service import AnalysisDirection

        service = StatisticalAnalysisService()
        highlight = service._build_highlight(
            AnalysisDirection.ROWS,
            "January 2023",
            "Grocery",
            "pareto"
        )

        assert highlight.row == "January 2023"
        assert highlight.column == "Grocery"
        assert highlight.highlight_type == "pareto"

    def test_create_highlight_for_algorithm(self):
        """Test _create_highlight_for_algorithm processes algorithm results correctly."""
        from whatsthedamage.services.statistical_analysis_service import AnalysisDirection, IQROutlierDetection

        service = StatisticalAnalysisService()
        algo = IQROutlierDetection()

        # Create test data with more data points for proper IQR calculation
        # Data: 100, 150, 160, 170, 180, 190, 200, 250, 300, 1000 (outlier)
        test_data = {
            "January 2023": {
                "Grocery": 100.0,
                "Rent": 1000.0,  # This should be an outlier
                "Utilities": 150.0,
                "Transport": 160.0,
                "Entertainment": 170.0,
                "Dining": 180.0,
                "Shopping": 190.0,
                "Health": 200.0,
                "Education": 250.0,
                "Other": 300.0
            }
        }

        transformed_data = service._transform_data_for_analysis(test_data, AnalysisDirection.COLUMNS)
        highlights = service._create_highlight_for_algorithm(
            algo,
            AnalysisDirection.COLUMNS,
            transformed_data
        )

        # Should have at least one highlight for Rent
        assert len(highlights) > 0
        highlight_dict = {(h.row, h.column): h.highlight_type for h in highlights}
        assert ("Rent", "January 2023") in highlight_dict
        assert highlight_dict[("Rent", "January 2023")] == "outlier"
