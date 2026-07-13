from typing import List, Dict, Callable, Optional, Any, TYPE_CHECKING
from whatsthedamage.models.domain.csv_row import CsvRow
from whatsthedamage.models.common.display_fields import DisplayRawField, DateField
from whatsthedamage.models.domain.dt_models import AggregatedRow, DetailRow
from whatsthedamage.utils.date_converter import DateConverter
import uuid

if TYPE_CHECKING:
    from whatsthedamage.models.domain.account import Account

# Type alias for row calculator callables
# Calculators receive the builder instance and return a list of AggregatedRow objects.
# They are invoked sequentially after all category data has been added, and can access
# previously calculated rows from earlier calculators.
RowCalculator = Callable[["AccountResponseBuilder"], List[AggregatedRow]]


class AccountResponseBuilder:
    """
    Builds Account in a transparent, step-by-step manner.

    This builder encapsulates the logic for converting CSV rows into account-compatible
    structures, providing a clear API for incrementally building the response.

    Note: This builder now creates Account models (unified) instead of AccountResponse.
    The 'account' parameter has been renamed to 'id' to match the new Account model.
    """

    def __init__(
        self,
        date_format: str,
        calculators: Optional[List[RowCalculator]] = None,
        id: str = "",
        name: str = "",
        formatted_id: str = "",
        currency: str = "",
        metadata: Optional[Any] = None,
        result_id: str = "",
        statistical_metadata: Optional[Any] = None
    ) -> None:
        """
        Initializes the AccountResponseBuilder.

        Args:
            date_format (str): The date format string for parsing dates.
            calculators (Optional[List[RowCalculator]]): List of calculator functions that generate
                additional aggregated rows. Each calculator receives the builder instance and returns
                a list of AggregatedRow objects. Calculators are invoked sequentially during build()
                after all category data has been added. Later calculators can access rows created by
                earlier calculators. Defaults to [create_balance_rows, create_total_spendings].
            id (str): Account identifier (raw account number). Replaces the old 'account' parameter.
            name (str): Account display name.
            formatted_id (str): Formatted account ID for display.
            currency (str): Currency code.
            metadata (Optional[Any]): Optional detailed metadata.
            result_id (str): Processing result identifier.
            statistical_metadata (Optional[Any]): Optional statistical metadata.
        """
        from whatsthedamage.models.domain.dt_calculators import create_balance_rows, create_total_spendings, create_cost_of_living_rows

        self._date_format = date_format
        self._aggregated_rows: List[AggregatedRow] = []
        self._month_totals: Dict[int, tuple[DateField, float]] = {}
        self._calculators = calculators if calculators is not None else [create_balance_rows, create_total_spendings, create_cost_of_living_rows]
        self._id = id
        self._name = name
        self._formatted_id = formatted_id
        self._currency = currency
        self._metadata = metadata
        self._result_id = result_id
        self._statistical_metadata = statistical_metadata

    def add_category_data(
        self,
        category_id: str,
        rows: List[CsvRow],
        total_amount: float,
        date_field: DateField
    ) -> None:
        """
        Adds data for a single category/month combination.

        Args:
            category_id (str): Category ID (e.g., 'grocery', 'clothes').
            rows (List[CsvRow]): Raw CSV rows for this category/month.
            total_amount (float): Aggregated total amount for this category/month.
            date_field (DateField): DateField with proper timestamp from actual data.
        """
        details = self._build_detail_rows(rows)
        aggregated_row = self.build_aggregated_row(
            category_id, total_amount, details, date_field
        )
        self._aggregated_rows.append(aggregated_row)

        # Track month totals for Balance calculation
        month_timestamp = date_field.timestamp
        if month_timestamp in self._month_totals:
            # Add to existing month total
            existing_field, existing_total = self._month_totals[month_timestamp]
            self._month_totals[month_timestamp] = (existing_field, existing_total + total_amount)
        else:
            # Initialize new month total
            self._month_totals[month_timestamp] = (date_field, total_amount)

    def build(self) -> "Account":
        """
        Returns the final Account.

        Invokes all calculators sequentially after category data has been added.
        Each calculator can access the builder's internal state and previously
        calculated rows. Any exceptions raised by calculators will propagate to the caller.

        Returns:
            Account: The complete account-compatible response object.
        """
        # Invoke calculators sequentially, allowing each to access prior rows
        for calculator in self._calculators:
            calculated_rows = calculator(self)
            self._aggregated_rows.extend(calculated_rows)

        # Import Account here to avoid circular imports
        from whatsthedamage.models.domain.account import Account

        return Account(
            id=self._id,
            name=self._name,
            formatted_id=self._formatted_id,
            data=self._aggregated_rows,
            currency=self._currency,
            result_id=self._result_id,
            metadata=self._metadata
        )

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
            row_currency = getattr(row, 'currency', '')
            amount_display = f"{amount_value:,.2f}"
            amount_field = DisplayRawField(display=amount_display, raw=amount_value)

            merchant = getattr(row, 'partner', getattr(row, 'merchant', ""))
            account = getattr(row, 'account', '')
            transaction_type = getattr(row, 'type', '')
            confidence = getattr(row, 'confidence', None)
            notice = getattr(row, 'notice', '')

            details.append(
                DetailRow(
                    row_id=str(uuid.uuid4()),
                    date=date_field,
                    amount=amount_field,
                    merchant=merchant,
                    currency=row_currency,
                    account=account,
                    type=transaction_type,
                    confidence=confidence,
                    notice=notice
                )
            )
        return details

    def build_aggregated_row(
        self,
        category_id: str,
        total_amount: float,
        details: List[DetailRow],
        date_field: DateField,
        is_calculated: bool = False
    ) -> AggregatedRow:
        """
        Creates a single AggregatedRow with proper formatting.

        This public helper method is available for custom calculators to create
        properly formatted AggregatedRow objects without duplicating formatting logic.

        Args:
            category_id (str): Category ID (e.g., 'grocery', 'balance').
            total_amount (float): Total amount for this category/month.
            details (List[DetailRow]): List of detail rows.
            date_field (DateField): DateField with timestamp from actual data.
            is_calculated (bool): Whether this row represents calculated data.

        Returns:
            AggregatedRow: The aggregated row for DataTables.
        """
        # Format total amount without currency
        total_display = f"{total_amount:,.2f}"
        total_field = DisplayRawField(display=total_display, raw=total_amount)

        return AggregatedRow(
            row_id=str(uuid.uuid4()),
            category_id=category_id,
            total=total_field,
            date=date_field,
            details=details,
            is_calculated=is_calculated
        )