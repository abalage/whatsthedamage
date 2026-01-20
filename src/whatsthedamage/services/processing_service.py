"""Processing service for CSV transaction processing.

This service layer orchestrates the business logic for processing bank transaction
CSV files. It provides a clean interface for Controllers (CLI, Web, API) to use,
isolating them from file I/O and configuration details.

Controllers are responsible for saving uploaded files to disk and passing file paths.
"""
from typing import Dict, Any, Optional
import time
import uuid
from whatsthedamage.config.config import AppArgs, AppContext
from whatsthedamage.models.csv_processor import CSVProcessor
from whatsthedamage.services.configuration_service import ConfigurationService, ConfigLoadResult
from whatsthedamage.services.statistical_analysis_service import StatisticalAnalysisService
from whatsthedamage.config.dt_models import StatisticalMetadata


class ProcessingService:
    """Service for processing CSV transaction files.

    This service orchestrates CSV reading, transaction processing, and categorization
    by delegating to CSVProcessor. It provides metadata about processing.

    Controllers must save uploaded files to disk and pass file paths to this service.
    """

    def __init__(
        self,
        configuration_service: Optional[ConfigurationService] = None,
        statistical_analysis_service: Optional[StatisticalAnalysisService] = None
    ) -> None:
        """Initialize the processing service.

        Args:
            configuration_service: Service for loading configuration (optional, created if None)
            statistical_analysis_service: Service for statistical analysis (optional, for Web/API only)

        Note:
            Caching is intentionally NOT a dependency here. Caching is a cross-cutting concern
            that should be handled at the controller/infrastructure layer, not in business logic.
        """
        self._config_service = configuration_service or ConfigurationService()
        self._statistical_analysis_service = statistical_analysis_service

    def process_with_details(
        self,
        csv_file_path: str,
        config_file_path: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        ml_enabled: bool = False,
        category_filter: str | None = None,
        language: str = 'en',
        verbose: bool = False,
        training_data: bool = False
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
            verbose: Print verbose categorized output to stdout
            training_data: Print training data JSON to stderr

        Returns:
            dict: Contains 'data' (Dict[str, DataTablesResponse]), 'metadata' (processing info)
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
            verbose=verbose,
            training_data=training_data
        )

        # Load config using ConfigurationService
        config_result: ConfigLoadResult = self._config_service.load_config(config_file_path)
        config = config_result.config
        if config is None:
            raise ValueError(f"Failed to load configuration: {config_result.validation_result.error_message}")

        context = AppContext(config, args)

        # Process using existing CSVProcessor
        processor = CSVProcessor(context)
        datatables_responses = processor.process_v2()

        # Compute statistical metadata
        statistical_metadata = self._compute_statistical_metadata(datatables_responses)

        # Attach statistical metadata to each DataTablesResponse for easy access by consumers
        # Check if datatables_responses is a dict (not a mock in tests)
        if isinstance(datatables_responses, dict):
            for account_id, dt_response in datatables_responses.items():
                dt_response.statistical_metadata = statistical_metadata

        # Build response with metadata
        processing_time = time.time() - start_time

        # Get row count from cached rows to avoid re-reading CSV
        row_count = len(processor._rows)

        # Generate result_id for caching purposes (controller will handle actual caching)
        result_id = str(uuid.uuid4())

        return {
            "data": datatables_responses,
            "metadata": {
                "processing_time": round(processing_time, 2),
                "row_count": row_count,
                "ml_enabled": ml_enabled,
                "filters_applied": {
                    "start_date": start_date,
                    "end_date": end_date,
                    "category": category_filter
                }
            },
            "result_id": result_id,
            "statistical_metadata": statistical_metadata
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
        verbose: bool = False,
        training_data: bool = False
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
            training_data=training_data,
            lang=language,
            ml=ml_enabled
        )

    def _compute_statistical_metadata(self, datatables_responses: Dict[str, Any]) -> StatisticalMetadata:
        """Compute statistical metadata including highlights for the given responses.

        Args:
            datatables_responses: Dictionary of table responses

        Returns:
            StatisticalMetadata with highlights
        """
        if self._statistical_analysis_service:
            # Web/API usage - delegate to StatisticalAnalysisService
            return self._statistical_analysis_service.compute_statistical_metadata(datatables_responses)
        # CLI usage - return empty metadata
        return StatisticalMetadata(highlights=[])
