from typing import List, Dict, Callable, Optional
from whatsthedamage.models.csv_row import CsvRow
from whatsthedamage.config.dt_models import DisplayRawField, DateField, DetailRow, AggregatedRow, DataTablesResponse
from whatsthedamage.utils.date_converter import DateConverter


# Type alias for row calculator callables
# Calculators receive the builder instance and return a list of AggregatedRow objects.
# They are invoked sequentially after all category data has been added, and can access
# previously calculated rows from earlier calculators.
RowCalculator = Callable[["DataTablesResponseBuilder"], List[AggregatedRow]]


class DataTablesResponseBuilder:
    """
    Builds DataTablesResponse in a transparent, step-by-step manner.
    
    This builder encapsulates the logic for converting CSV rows into DataTables-compatible
    structures, providing a clear API for incrementally building the response.
    """

    def __init__(self, currency: str, date_format: str, calculators: Optional[List[RowCalculator]] = None) -> None:
        """
        Initializes the DataTablesResponseBuilder.

        Args:
            currency (str): The currency code to use for formatting amounts.
            date_format (str): The date format string for parsing dates.
            calculators (Optional[List[RowCalculator]]): List of calculator functions that generate
                additional aggregated rows. Each calculator receives the builder instance and returns
                a list of AggregatedRow objects. Calculators are invoked sequentially during build()
                after all category data has been added. Later calculators can access rows created by
                earlier calculators. Defaults to [create_balance_rows, create_total_spendings].
        """
        from whatsthedamage.models.dt_calculators import create_balance_rows, create_total_spendings

        self._currency = currency
        self._date_format = date_format
        self._aggregated_rows: List[AggregatedRow] = []
        self._month_totals: Dict[int, tuple[DateField, float]] = {}
        self._calculators = calculators if calculators is not None else [create_balance_rows, create_total_spendings]

    def add_category_data(
        self,
        category: str,
        rows: List[CsvRow],
        total_amount: float,
        month_field: DateField
    ) -> None:
        """
        Adds data for a single category/month combination.

        Args:
            category (str): Category name (e.g., 'Groceries', 'Entertainment').
            rows (List[CsvRow]): Raw CSV rows for this category/month.
            total_amount (float): Aggregated total amount for this category/month.
            month_field (DateField): DateField with proper timestamp from actual data.
        """
        details = self._build_detail_rows(rows)
        aggregated_row = self.build_aggregated_row(
            category, total_amount, details, month_field
        )
        self._aggregated_rows.append(aggregated_row)

        # Track month totals for Balance calculation
        month_timestamp = month_field.timestamp
        if month_timestamp in self._month_totals:
            # Add to existing month total
            existing_field, existing_total = self._month_totals[month_timestamp]
            self._month_totals[month_timestamp] = (existing_field, existing_total + total_amount)
        else:
            # Initialize new month total
            self._month_totals[month_timestamp] = (month_field, total_amount)

    def build(self) -> DataTablesResponse:
        """
        Returns the final DataTablesResponse.

        Invokes all calculators sequentially after category data has been added.
        Each calculator can access the builder's internal state and previously
        calculated rows. Any exceptions raised by calculators will propagate to the caller.

        Returns:
            DataTablesResponse: The complete DataTables-compatible response object.
        """
        # Invoke calculators sequentially, allowing each to access prior rows
        for calculator in self._calculators:
            calculated_rows = calculator(self)
            self._aggregated_rows.extend(calculated_rows)

        return DataTablesResponse(data=self._aggregated_rows)

    def _build_detail_rows(self, rows: List[CsvRow]) -> List[DetailRow]:
        """
        Converts CsvRow objects to DetailRow objects.

        Args:
            rows (List[CsvRow]): List of CSV rows to convert.

        Returns:
            List[DetailRow]: List of detail rows for DataTables.
        """
        details = []
        for row in rows:
            date_str = getattr(row, 'date', None)
            date_display = date_str if date_str else ""
            date_timestamp = (
                DateConverter.convert_to_epoch(date_str, self._date_format)
                if date_str else 0
            )
            date_field = DateField(display=date_display, timestamp=date_timestamp)

            amount_value = getattr(row, 'amount', 0.0)
            row_currency = getattr(row, 'currency', self._currency)
            amount_display = (
                f"{row_currency} {amount_value:,.2f}" if row_currency
                else f"{amount_value:,.2f}"
            )
            amount_field = DisplayRawField(display=amount_display, raw=amount_value)

            merchant = getattr(row, 'partner', getattr(row, 'merchant', ""))
            details.append(
                DetailRow(date=date_field, amount=amount_field, merchant=merchant)
            )
        return details

    def build_aggregated_row(
        self,
        category: str,
        total_amount: float,
        details: List[DetailRow],
        month_field: DateField
    ) -> AggregatedRow:
        """
        Creates a single AggregatedRow with proper formatting.

        This public helper method is available for custom calculators to create
        properly formatted AggregatedRow objects without duplicating formatting logic.

        Args:
            category (str): Category name.
            total_amount (float): Total amount for this category/month.
            details (List[DetailRow]): List of detail rows.
            month_field (DateField): DateField with timestamp from actual data.

        Returns:
            AggregatedRow: The aggregated row for DataTables.
        """
        # Format total amount
        total_display = (
            f"{self._currency} {total_amount:,.2f}" if self._currency
            else f"{total_amount:,.2f}"
        )
        total_field = DisplayRawField(display=total_display, raw=total_amount)

        return AggregatedRow(
            category=category,
            total=total_field,
            month=month_field,
            details=details
        )




