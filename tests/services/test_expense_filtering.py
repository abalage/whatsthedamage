"""Tests for expense filtering in StatisticalAnalysisService."""

import pytest
from whatsthedamage.services.statistical_analysis_service import StatisticalAnalysisService, AnalysisDirection
from whatsthedamage.config.dt_models import DataTablesResponse, AggregatedRow, DateField, DisplayRawField

@pytest.fixture
def sample_data_with_mixed_values():
    """Fixture providing sample data with both positive and negative values."""
    return [
        AggregatedRow(
            category="Grocery",
            total=DisplayRawField(display="-264100.00", raw="-264100.00"),
            date=DateField(display="January 2024", timestamp=1672531200),
            details=[],
            is_calculated=False
        ),
        AggregatedRow(
            category="Maintenance",
            total=DisplayRawField(display="-140588.00", raw="-140588.00"),
            date=DateField(display="January 2024", timestamp=1672531200),
            details=[],
            is_calculated=False
        ),
        AggregatedRow(
            category="Interest",
            total=DisplayRawField(display="9.00", raw="9.00"),
            date=DateField(display="January 2024", timestamp=1672531200),
            details=[],
            is_calculated=False
        ),
        AggregatedRow(
            category="Refund",
            total=DisplayRawField(display="2416.00", raw="2416.00"),
            date=DateField(display="January 2024", timestamp=1672531200),
            details=[],
            is_calculated=False
        ),
        AggregatedRow(
            category="Health",
            total=DisplayRawField(display="-25795.00", raw="-25795.00"),
            date=DateField(display="January 2024", timestamp=1672531200),
            details=[],
            is_calculated=False
        ),
        AggregatedRow(
            category="Vehicle",
            total=DisplayRawField(display="-58542.00", raw="-58542.00"),
            date=DateField(display="January 2024", timestamp=1672531200),
            details=[],
            is_calculated=False
        ),
    ]

@pytest.fixture
def sample_data_all_expenses():
    """Fixture providing sample data with only expense values."""
    return [
        AggregatedRow(
            category="Grocery",
            total=DisplayRawField(display="-264100.00", raw="-264100.00"),
            date=DateField(display="January 2024", timestamp=1672531200),
            details=[],
            is_calculated=False
        ),
        AggregatedRow(
            category="Maintenance",
            total=DisplayRawField(display="-140588.00", raw="-140588.00"),
            date=DateField(display="January 2024", timestamp=1672531200),
            details=[],
            is_calculated=False
        ),
        AggregatedRow(
            category="Health",
            total=DisplayRawField(display="-25795.00", raw="-25795.00"),
            date=DateField(display="January 2024", timestamp=1672531200),
            details=[],
            is_calculated=False
        ),
    ]

@pytest.fixture
def sample_data_all_income():
    """Fixture providing sample data with only income values."""
    return [
        AggregatedRow(
            category="Interest",
            total=DisplayRawField(display="9.00", raw="9.00"),
            date=DateField(display="January 2024", timestamp=1672531200),
            details=[],
            is_calculated=False
        ),
        AggregatedRow(
            category="Refund",
            total=DisplayRawField(display="2416.00", raw="2416.00"),
            date=DateField(display="January 2024", timestamp=1672531200),
            details=[],
            is_calculated=False
        ),
    ]

class TestExpenseFiltering:
    """Tests for expense filtering functionality."""

    def test_filter_expenses_only_enabled_by_default(self):
        """Test that filter_expenses_only is enabled by default."""
        service = StatisticalAnalysisService()
        assert service.filter_expenses_only is True

    def test_filter_expenses_only_can_be_disabled(self):
        """Test that filter_expenses_only can be disabled."""
        service = StatisticalAnalysisService(filter_expenses_only=False)
        assert service.filter_expenses_only is False

    def test_filter_expenses_only_removes_positive_values(self, sample_data_with_mixed_values):
        """Test that _filter_expenses_only removes positive values when enabled."""
        dt_response = DataTablesResponse(
            data=sample_data_with_mixed_values,
            account="Test Account",
            currency="USD"
        )
        service = StatisticalAnalysisService(filter_expenses_only=True)
        filtered_response = service._filter_expenses_only(dt_response)

        # Should only have negative values
        assert len(filtered_response.data) == 4  # Grocery, Maintenance, Health, Vehicle
        categories = [row.category for row in filtered_response.data]
        assert "Grocery" in categories
        assert "Maintenance" in categories
        assert "Health" in categories
        assert "Vehicle" in categories
        assert "Interest" not in categories
        assert "Refund" not in categories

    def test_filter_expenses_only_removes_zero_values(self):
        """Test that _filter_expenses_only removes zero values."""
        data = [
            AggregatedRow(
                category="Grocery",
                total=DisplayRawField(display="-100.00", raw="-100.00"),
                date=DateField(display="January 2024", timestamp=1672531200),
                details=[],
                is_calculated=False
            ),
            AggregatedRow(
                category="Interest",
                total=DisplayRawField(display="0.00", raw="0.00"),
                date=DateField(display="January 2024", timestamp=1672531200),
                details=[],
                is_calculated=False
            ),
        ]
        dt_response = DataTablesResponse(
            data=data,
            account="Test Account",
            currency="USD"
        )
        service = StatisticalAnalysisService(filter_expenses_only=True)
        filtered_response = service._filter_expenses_only(dt_response)

        # Should only have negative values (zero is not negative)
        assert len(filtered_response.data) == 1
        assert filtered_response.data[0].category == "Grocery"

    def test_filter_expenses_only_disabled_keeps_all_values(self, sample_data_with_mixed_values):
        """Test that _filter_expenses_only keeps all values when disabled."""
        dt_response = DataTablesResponse(
            data=sample_data_with_mixed_values,
            account="Test Account",
            currency="USD"
        )
        service = StatisticalAnalysisService(filter_expenses_only=False)
        filtered_response = service._filter_expenses_only(dt_response)

        # Should have all values
        assert len(filtered_response.data) == 6
        categories = [row.category for row in filtered_response.data]
        assert "Grocery" in categories
        assert "Maintenance" in categories
        assert "Interest" in categories
        assert "Refund" in categories
        assert "Health" in categories
        assert "Vehicle" in categories

    def test_filter_expenses_only_with_all_expenses(self, sample_data_all_expenses):
        """Test that _filter_expenses_only keeps all values when all are expenses."""
        dt_response = DataTablesResponse(
            data=sample_data_all_expenses,
            account="Test Account",
            currency="USD"
        )
        service = StatisticalAnalysisService(filter_expenses_only=True)
        filtered_response = service._filter_expenses_only(dt_response)

        # Should have all values since they're all expenses
        assert len(filtered_response.data) == 3
        categories = [row.category for row in filtered_response.data]
        assert "Grocery" in categories
        assert "Maintenance" in categories
        assert "Health" in categories

    def test_filter_expenses_only_with_all_income(self, sample_data_all_income):
        """Test that _filter_expenses_only removes all values when all are income."""
        dt_response = DataTablesResponse(
            data=sample_data_all_income,
            account="Test Account",
            currency="USD"
        )
        service = StatisticalAnalysisService(filter_expenses_only=True)
        filtered_response = service._filter_expenses_only(dt_response)

        # Should have no values since they're all income
        assert len(filtered_response.data) == 0

    def test_compute_statistical_metadata_with_expense_filtering(self, sample_data_with_mixed_values):
        """Test that compute_statistical_metadata applies expense filtering by default."""
        dt_response = DataTablesResponse(
            data=sample_data_with_mixed_values,
            account="Test Account",
            currency="USD"
        )
        datatables_responses = {"test_table": dt_response}

        service = StatisticalAnalysisService(enabled_algorithms=["pareto"], filter_expenses_only=True)
        metadata = service.compute_statistical_metadata(datatables_responses)

        # Should only analyze expense categories
        # With the test data, the top expenses by absolute value are:
        # Grocery (-264100), Maintenance (-140588), Vehicle (-58542), Health (-25795)
        # Total = 489,025, 80% = 391,220
        # Pareto should include: Grocery, Maintenance (264100 + 140588 = 404,688 > 391,220)
        assert len(metadata.highlights) > 0
        highlight_categories = {h.row for h in metadata.highlights if h.highlight_type == "pareto"}
        assert "Grocery" in highlight_categories
        assert "Maintenance" in highlight_categories
        # Income categories should not be in highlights
        assert not any(h.row in ["Interest", "Refund"] for h in metadata.highlights if h.highlight_type == "pareto")

    def test_compute_statistical_metadata_without_expense_filtering(self, sample_data_with_mixed_values):
        """Test that compute_statistical_metadata can skip expense filtering."""
        dt_response = DataTablesResponse(
            data=sample_data_with_mixed_values,
            account="Test Account",
            currency="USD"
        )
        datatables_responses = {"test_table": dt_response}

        service = StatisticalAnalysisService(enabled_algorithms=["pareto"], filter_expenses_only=False)
        metadata = service.compute_statistical_metadata(datatables_responses)

        # Should analyze all categories (both expenses and income)
        assert len(metadata.highlights) > 0
        highlight_categories = {h.row for h in metadata.highlights if h.highlight_type == "pareto"}
        # With all values included, the absolute values are:
        # Grocery (264100), Maintenance (140588), Vehicle (58542), Health (25795), Interest (9), Refund (2416)
        # Total = 489,025 + 2425 = 491,450, 80% = 393,160
        # Pareto should include: Grocery, Maintenance (264100 + 140588 = 404,688 > 393,160)
        assert "Grocery" in highlight_categories
        assert "Maintenance" in highlight_categories
        # Vehicle is not included because Grocery + Maintenance already exceed 80%

    def test_compute_statistical_metadata_with_expense_filtering_custom_params(self, sample_data_with_mixed_values):
        """Test that compute_statistical_metadata works with custom parameters."""
        dt_response = DataTablesResponse(
            data=sample_data_with_mixed_values,
            account="Test Account",
            currency="USD"
        )
        datatables_responses = {"test_table": dt_response}

        service = StatisticalAnalysisService(enabled_algorithms=["pareto"], filter_expenses_only=True)
        metadata = service.compute_statistical_metadata(
            datatables_responses=datatables_responses,
            algorithms=["pareto"],
            direction=AnalysisDirection.COLUMNS
        )

        # Should only analyze expense categories
        highlight_categories = {h.row for h in metadata.highlights if h.highlight_type == "pareto"}
        assert "Grocery" in highlight_categories
        assert "Maintenance" in highlight_categories
        # Income categories should not be in highlights
        assert not any(h.row in ["Interest", "Refund"] for h in metadata.highlights if h.highlight_type == "pareto")

    def test_compute_statistical_metadata_without_expense_filtering_custom_params(self, sample_data_with_mixed_values):
        """Test that compute_statistical_metadata works with custom parameters and no filtering."""
        dt_response = DataTablesResponse(
            data=sample_data_with_mixed_values,
            account="Test Account",
            currency="USD"
        )
        datatables_responses = {"test_table": dt_response}

        service = StatisticalAnalysisService(enabled_algorithms=["pareto"], filter_expenses_only=False)
        metadata = service.compute_statistical_metadata(
            datatables_responses=datatables_responses,
            algorithms=["pareto"],
            direction=AnalysisDirection.COLUMNS
        )

        # Should analyze all categories (both expenses and income)
        highlight_categories = {h.row for h in metadata.highlights if h.highlight_type == "pareto"}
        # With all values included, the absolute values are:
        # Grocery (264100), Maintenance (140588), Vehicle (58542), Health (25795), Interest (9), Refund (2416)
        # Total = 489,025 + 2425 = 491,450, 80% = 393,160
        # Pareto should include: Grocery, Maintenance (264100 + 140588 = 404,688 > 393,160)
        assert "Grocery" in highlight_categories
        assert "Maintenance" in highlight_categories
        # Vehicle is not included because Grocery + Maintenance already exceed 80%