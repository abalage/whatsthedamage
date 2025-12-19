"""Processing service for CSV transaction processing.

This service layer orchestrates the business logic for processing bank transaction
CSV files. It provides a clean interface for Controllers (CLI, Web, API) to use,
isolating them from file I/O and configuration details.

Controllers are responsible for saving uploaded files to disk and passing file paths.
"""
from typing import Dict, Any, Optional
import time
from whatsthedamage.config.config import AppArgs, AppContext
from whatsthedamage.models.csv_processor import CSVProcessor
from whatsthedamage.services.configuration_service import ConfigurationService


class ProcessingService:
    """Service for processing CSV transaction files.
    
    This service orchestrates CSV reading, transaction processing, and categorization
    by delegating to CSVProcessor. It provides metadata about processing.
    
    Controllers must save uploaded files to disk and pass file paths to this service.
    """

    def __init__(self, configuration_service: Optional[ConfigurationService] = None) -> None:
        """Initialize the processing service.
        
        Args:
            configuration_service: Service for loading configuration (optional, created if None)
        """
        self._config_service = configuration_service or ConfigurationService()
    
    def process_summary(
        self,
        csv_file_path: str,
        config_file_path: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        ml_enabled: bool = False,
        category_filter: str | None = None,
        language: str = 'en'
    ) -> Dict[str, Any]:
        """Process CSV file and return summary totals.
        
        This method processes a CSV file and returns aggregated summary data
        grouped by category and month. Used by v1 API and CLI.
        
        Args:
            csv_file_path: Path to CSV file on disk
            config_file_path: Optional path to YAML config file
            start_date: Filter transactions from this date (YYYY-MM-DD)
            end_date: Filter transactions to this date (YYYY-MM-DD)
            ml_enabled: Use ML-based categorization instead of regex
            category_filter: Filter results to specific category
            language: Output language for month names ('en' or 'hu')
            
        Returns:
            dict: Contains 'data' (summary totals), 'metadata' (processing info)
        """
        start_time = time.time()
        
        # Build arguments for CSVProcessor
        args = self._build_args(
            filename=csv_file_path,
            config=config_file_path,
            start_date=start_date,
            end_date=end_date,
            ml_enabled=ml_enabled,
            category_filter=category_filter,
            language=language,
            verbose=False
        )
        
        # Load config using ConfigurationService
        config_result = self._config_service.load_config(config_file_path)
        config = config_result.config
        if config is None:
            raise ValueError(f"Failed to load configuration: {config_result.validation_result.error_message}")
        
        context = AppContext(config, args)

        # Process using existing CSVProcessor
        processor = CSVProcessor(context)
        rows = processor._read_csv_file()
        summary_data_by_month = processor.processor.process_rows(rows)

        # Flatten summary data: aggregate across all months
        # summary_data_by_month is Dict[str, Dict[str, float]] (month -> category -> amount)
        # We need Dict[str, float] (category -> total_amount)
        flattened_data: Dict[str, float] = {}
        for month_name, categories in summary_data_by_month.items():
            for category, amount in categories.items():
                if category in flattened_data:
                    flattened_data[category] += amount
                else:
                    flattened_data[category] = amount

        # Build response with metadata
        processing_time = time.time() - start_time

        return {
            "data": flattened_data,
            "monthly_data": summary_data_by_month,
            "metadata": {
                "processing_time": round(processing_time, 2),
                "row_count": len(rows),
                "ml_enabled": ml_enabled,
                "filters_applied": {
                    "start_date": start_date,
                    "end_date": end_date,
                    "category": category_filter
                }
            },
            "processor": processor
        }

    def process_with_details(
        self,
        csv_file_path: str,
        config_file_path: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        ml_enabled: bool = False,
        category_filter: str | None = None,
        language: str = 'en'
    ) -> Dict[str, Any]:
        """Process CSV file and return detailed transaction data.

        This method processes a CSV file and returns detailed transaction-level
        data with aggregation by category and month. Used by v2 API.

        Args:
            csv_file_path: Path to CSV file on disk
            config_file_path: Optional path to YAML config file
            start_date: Filter transactions from this date (YYYY-MM-DD)
            end_date: Filter transactions to this date (YYYY-MM-DD)
            ml_enabled: Use ML-based categorization instead of regex
            category_filter: Filter results to specific category
            language: Output language for month names ('en' or 'hu')

        Returns:
            dict: Contains 'data' (DataTablesResponse), 'metadata' (processing info)
        """
        start_time = time.time()

        # Build arguments for CSVProcessor
        args = self._build_args(
            filename=csv_file_path,
            config=config_file_path,
            start_date=start_date,
            end_date=end_date,
            ml_enabled=ml_enabled,
            category_filter=category_filter,
            language=language,
            verbose=True  # Always verbose for detailed view
        )

        # Load config using ConfigurationService
        config_result = self._config_service.load_config(config_file_path)
        config = config_result.config
        if config is None:
            raise ValueError(f"Failed to load configuration: {config_result.validation_result.error_message}")
        
        context = AppContext(config, args)

        # Process using existing CSVProcessor
        processor = CSVProcessor(context)
        datatables_response = processor.process_v2()

        # Build response with metadata
        processing_time = time.time() - start_time

        return {
            "data": datatables_response,
            "metadata": {
                "processing_time": round(processing_time, 2),
                "row_count": len(processor._read_csv_file()),
                "ml_enabled": ml_enabled,
                "filters_applied": {
                    "start_date": start_date,
                    "end_date": end_date,
                    "category": category_filter
                }
            }
        }

    def _build_args(
        self,
        filename: str,
        config: str | None,
        start_date: str | None = None,
        end_date: str | None = None,
        ml_enabled: bool = False,
        category_filter: str | None = None,
        language: str = 'en',
        verbose: bool = False
    ) -> AppArgs:
        """Build AppArgs from service parameters.

        Args:
            filename: Path to CSV file
            config: Path to config file
            start_date: Start date filter
            end_date: End date filter
            ml_enabled: ML categorization flag
            category_filter: Category filter
            language: Language code
            verbose: Verbose output flag

        Returns:
            AppArgs: Application arguments dictionary
        """
        return AppArgs(
            filename=filename,
            config=config or '',
            start_date=start_date,
            end_date=end_date,
            category='category',  # Default categorization attribute
            filter=category_filter,
            output=None,
            output_format='json',
            verbose=verbose,
            nowrap=False,
            no_currency_format=False,
            training_data=False,
            lang=language,
            ml=ml_enabled
        )
