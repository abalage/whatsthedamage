"""Processing service for CSV transaction processing.

This service layer orchestrates the business logic for processing bank transaction
CSV files. It provides a clean interface for Controllers (CLI, Web, API) to use,
isolating them from file I/O and configuration details.

The service accepts file-like objects only. Controllers are responsible for opening files.
"""
from typing import Dict, BinaryIO, TextIO, Union
import time
import tempfile
import os
from whatsthedamage.config.config import AppArgs, AppContext, load_config
from whatsthedamage.models.csv_processor import CSVProcessor
from whatsthedamage.config.dt_models import DataTablesResponse


FileObject = Union[BinaryIO, TextIO]


class ProcessingService:
    """Service for processing CSV transaction files.
    
    This service orchestrates CSV reading, transaction processing, and categorization
    by delegating to CSVProcessor. It handles the adaptation of file-like objects to
    temporary files and provides metadata about processing.
    """
    
    def __init__(self) -> None:
        """Initialize the processing service."""
        pass
    
    def process_summary(
        self,
        csv_file: FileObject,
        config_file: FileObject | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        ml_enabled: bool = False,
        category_filter: str | None = None,
        language: str = 'en'
    ) -> Dict:
        """Process CSV file and return summary totals.
        
        This method processes a CSV file and returns aggregated summary data
        grouped by category and month. Used by v1 API and CLI.
        
        Args:
            csv_file: File-like object containing CSV data
            config_file: Optional YAML config file-like object
            start_date: Filter transactions from this date (YYYY-MM-DD)
            end_date: Filter transactions to this date (YYYY-MM-DD)
            ml_enabled: Use ML-based categorization instead of regex
            category_filter: Filter results to specific category
            language: Output language for month names ('en' or 'hu')
            
        Returns:
            dict: Contains 'data' (summary totals), 'metadata' (processing info)
        """
        start_time = time.time()
        
        # Save file-like objects to temporary files
        csv_path = self._save_temp_file(csv_file, suffix='.csv')
        config_path = self._save_temp_file(config_file, suffix='.yml') if config_file else None
        
        try:
            # Build arguments for CSVProcessor
            args = self._build_args(
                filename=csv_path,
                config=config_path,
                start_date=start_date,
                end_date=end_date,
                ml_enabled=ml_enabled,
                category_filter=category_filter,
                language=language,
                verbose=False
            )
            
            # Load config and create context
            config = load_config(config_path)
            context = AppContext(config, args)
            
            # Process using existing CSVProcessor
            processor = CSVProcessor(context)
            rows = processor._read_csv_file()
            summary_data = processor.processor.process_rows(rows)
            
            # Build response with metadata
            processing_time = time.time() - start_time
            
            return {
                "data": summary_data,
                "metadata": {
                    "processing_time": round(processing_time, 2),
                    "row_count": len(rows),
                    "ml_enabled": ml_enabled,
                    "filters_applied": {
                        "start_date": start_date,
                        "end_date": end_date,
                        "category": category_filter
                    }
                }
            }
        finally:
            # Clean up temporary files
            self._cleanup_temp_file(csv_path)
            if config_path:
                self._cleanup_temp_file(config_path)
    
    def process_with_details(
        self,
        csv_file: FileObject,
        config_file: FileObject | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        ml_enabled: bool = False,
        category_filter: str | None = None,
        language: str = 'en'
    ) -> Dict:
        """Process CSV file and return detailed transaction data.
        
        This method processes a CSV file and returns detailed transaction-level
        data with aggregation by category and month. Used by v2 API.
        
        Args:
            csv_file: File-like object containing CSV data
            config_file: Optional YAML config file-like object
            start_date: Filter transactions from this date (YYYY-MM-DD)
            end_date: Filter transactions to this date (YYYY-MM-DD)
            ml_enabled: Use ML-based categorization instead of regex
            category_filter: Filter results to specific category
            language: Output language for month names ('en' or 'hu')
            
        Returns:
            dict: Contains 'data' (DataTablesResponse), 'metadata' (processing info)
        """
        start_time = time.time()
        
        # Save file-like objects to temporary files
        csv_path = self._save_temp_file(csv_file, suffix='.csv')
        config_path = self._save_temp_file(config_file, suffix='.yml') if config_file else None
        
        try:
            # Build arguments for CSVProcessor
            args = self._build_args(
                filename=csv_path,
                config=config_path,
                start_date=start_date,
                end_date=end_date,
                ml_enabled=ml_enabled,
                category_filter=category_filter,
                language=language,
                verbose=True  # Always verbose for detailed view
            )
            
            # Load config and create context
            config = load_config(config_path)
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
        finally:
            # Clean up temporary files
            self._cleanup_temp_file(csv_path)
            if config_path:
                self._cleanup_temp_file(config_path)
    
    def _save_temp_file(self, file_obj: FileObject, suffix: str) -> str:
        """Save file-like object to a temporary file.
        
        Args:
            file_obj: File-like object to save
            suffix: File suffix (e.g., '.csv', '.yml')
            
        Returns:
            str: Path to the temporary file
        """
        file_obj.seek(0)  # Reset to beginning
        content = file_obj.read()
        if isinstance(content, bytes):
            content = content.decode('utf-8')
        
        # Ensure content is string
        content_str = str(content)
        
        # Create temporary file
        fd, path = tempfile.mkstemp(suffix=suffix, text=True)
        try:
            with os.fdopen(fd, 'w') as tmp:
                tmp.write(content_str)
        except:
            os.close(fd)
            raise
        
        return path
    
    def _cleanup_temp_file(self, path: str) -> None:
        """Delete temporary file.
        
        Args:
            path: Path to temporary file
        """
        try:
            if os.path.exists(path):
                os.unlink(path)
        except OSError:
            pass  # Ignore cleanup errors
    
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
