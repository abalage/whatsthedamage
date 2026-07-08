from typing import Optional, Dict, List, Union, Tuple, TYPE_CHECKING
from whatsthedamage.config.config import AppContext, EnricherPatternSets
from whatsthedamage.models.domain.dt_models import DateField
from whatsthedamage.models.domain.csv_row import CsvRow
from whatsthedamage.models.domain.row_enrichment import RowEnrichment
from whatsthedamage.models.domain.row_enrichment_ml import RowEnrichmentML
from whatsthedamage.models.domain.row_filter import RowFilter
from whatsthedamage.models.domain.dt_response_builder import AccountResponseBuilder
from whatsthedamage.utils.date_converter import DateConverter
from whatsthedamage.utils.logging import get_logger

if TYPE_CHECKING:
    from whatsthedamage.services.text_correction_service import TextCorrectionService
    from whatsthedamage.models.domain.account import Account

logger = get_logger(__name__)

"""
RowsProcessor processes rows of CSV data. It filters, enriches, categorizes, and summarizes the rows.
"""


class RowsProcessor:
    def __init__(self, context: AppContext) -> None:
        """
        Initializes the RowsProcessor with the application context.

        Args:
            context (AppContext): The application context containing configuration and arguments.
        """
        self.context = context
        self._date_attribute_format: str = context.config.csv.date_attribute_format
        self._cfg_pattern_sets: EnricherPatternSets = context.config.enricher_pattern_sets
        self._start_date: Optional[str] = context.args.start_date
        self._start_date_epoch: float = 0
        self._end_date: Optional[str] = context.args.end_date
        self._end_date_epoch: float = 0
        self._verbose: bool = context.args.verbose
        self._category_id: str = context.args.category_id  # This is the attribute name to categorize by (e.g., 'category_id', 'type')
        self._filter: Optional[str] = context.args.filter  # This is now a category_id filter
        self._training_data: bool = context.args.training_data
        self._ml: bool = context.args.ml
        # Lazy import to avoid circular dependency
        from whatsthedamage.services.text_correction_service import TextCorrectionService
        self._text_correction_service = TextCorrectionService(context.config.text_cleaning)

        # Convert start and end dates to epoch if provided
        if self._start_date:
            formatted_start_date = DateConverter.convert_date_format(
                self._start_date, self._date_attribute_format
            )
            self._start_date_epoch = DateConverter.convert_to_epoch(
                formatted_start_date, self._date_attribute_format
            )
        if self._end_date:
            formatted_end_date = DateConverter.convert_date_format(
                self._end_date, self._date_attribute_format
            )
            self._end_date_epoch = DateConverter.convert_to_epoch(
                formatted_end_date, self._date_attribute_format
            )

    def _clean_rows(self, rows: List[CsvRow]) -> List[CsvRow]:
        """
        Clean text fields in rows before processing.

        Args:
            rows (List[CsvRow]): List of CsvRow objects to clean.

        Returns:
            List[CsvRow]: List of cleaned CsvRow objects.
        """
        logger.debug(f"Cleaning {len(rows)} rows")
        for row in rows:
            # Directly modify the partner attribute (partner field is mandatory)
            row.partner = self._text_correction_service.clean_partner_field(row.partner)
        logger.info(f"Cleaned {len(rows)} rows successfully")
        return rows

    def process_rows(self, rows: List[CsvRow]) -> Dict[str, "Account"]:
        """
        Processes a list of CsvRow objects and returns per-account Account structures.

        Groups rows by account first, then processes each account independently.
        Each account gets its own Balance and Total Spendings calculations.
        Uses a builder pattern for transparent, step-by-step construction of the response.
        Uses filtering that provides DateField objects with accurate timestamps.

        Args:
            rows (List[CsvRow]): List of CsvRow objects (potentially from multiple accounts).

        Returns:
            Dict[str, Account]: Mapping of account_id → Account.
        """
        # Local import to avoid circular dependency
        from whatsthedamage.view.row_printer import print_categorized_rows, print_training_data
        logger.info(f"Starting processing of {len(rows)} rows")
        # Apply text cleaning
        rows = self._clean_rows(rows)

        # Group rows by account first
        row_filter = RowFilter(rows, self.context)
        rows_by_account = row_filter.filter_by_account()

        responses_by_account: Dict[str, "Account"] = {}

        # Process each account independently
        for account_id, account_rows in rows_by_account.items():
            # Filter rows by date or month for this account
            filtered_sets = self._filter_rows(account_rows)

            # Initialize the builder with all necessary fields
            # Format account ID by adding dashes every 8 digits
            formatted_account_id = '-'.join(
                account_id[i:i+8] for i in range(0, len(account_id), 8)
            )
            
            builder = AccountResponseBuilder(
                date_format=self._date_attribute_format,
                id=account_id,
                name="",  # Will be empty for now, can be set later
                formatted_id=formatted_account_id,
                currency=account_rows[0].currency if account_rows else ""
            )

            # Process each month/date range for this account
            for month_field, set_rows in filtered_sets:
                # Enrich and categorize rows
                categorized_rows = self._enrich_and_categorize_rows(set_rows)
                categorized_rows = self._apply_filter(categorized_rows)

                # Calculate category totals inline
                category_totals = {}
                for category_id, category_rows in categorized_rows.items():
                    total = sum(float(getattr(row, 'amount', 0)) for row in category_rows)
                    category_totals[category_id] = total

                # Add each category to the builder with DateField
                for category_id, category_rows in categorized_rows.items():
                    builder.add_category_data(
                        category_id=category_id,
                        rows=category_rows,
                        total_amount=category_totals[category_id],
                        date_field=month_field
                    )

            # Build and store the final response for this account
            account_response = builder.build()
            responses_by_account[account_id] = account_response

        # Print verbose/training_data output if flags are set
        if self._verbose:
            print_categorized_rows(responses_by_account)
        elif self._training_data:
            print_training_data(responses_by_account)

        logger.info(f"Completed processing {len(responses_by_account)} accounts")
        return responses_by_account


    def _filter_rows(self, rows: List[CsvRow]) -> List[Tuple[DateField, List[CsvRow]]]:
        """
        Filters rows by date or month.

        Returns DateField objects with proper timestamps instead of string keys.
        For date ranges, creates a DateField with the start date.

        Args:
            rows (List[CsvRow]): List of CsvRow objects to be filtered.

        Returns:
            List[Tuple[DateField, List[CsvRow]]]: A list of tuples with DateField and filtered rows.
        """
        row_filter = RowFilter(rows, self.context)
        if self._start_date_epoch > 0 and self._end_date_epoch > 0:
            # For date range filtering, forward the tuples returned by RowFilter
            return row_filter.filter_by_date(self._start_date_epoch, self._end_date_epoch)
        return list(row_filter.filter_by_month())

    def _enrich_and_categorize_rows(self, rows: List[CsvRow]) -> Dict[str, List[CsvRow]]:
        """
        Enriches and categorizes rows by the specified attribute.

        Args:
            rows (List[CsvRow]): List of CsvRow objects to be enriched and categorized.

        Returns:
            Dict[str, List[CsvRow]]: A dictionary of categorized rows.

        Raises:
            ValueError: If the category attribute is not set.
        """
        if not self._category_id:
            raise ValueError("Category attribute is not set")
        enricher: Union[RowEnrichmentML, RowEnrichment]
        if self._ml:
            enricher = RowEnrichmentML(rows, self.context.config.ml_config.ml_confidence_threshold)
        else:
            enricher = RowEnrichment(rows, self._cfg_pattern_sets)
        return enricher.categorize_by_attribute(self._category_id)

    def _apply_filter(self, rows_dict: Dict[str, List[CsvRow]]) -> Dict[str, List[CsvRow]]:
        """
        Applies the filter to the categorized rows.
        The filter is a category_id that we want to include exclusively.

        Args:
            rows_dict (Dict[str, List[CsvRow]]): A dictionary of categorized rows by category_id.

        Returns:
            Dict[str, List[CsvRow]]: A dictionary of filtered rows (only the matching category_id).
        """
        if self._filter:
            return {k: v for k, v in rows_dict.items() if k == self._filter}
        return rows_dict
