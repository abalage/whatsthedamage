"""Test data builder for creating realistic test data for DrilldownResponseService.

This module provides utilities for creating test data structures
that mimic real processing results.
"""
from typing import Dict, List, Any, Optional
from whatsthedamage.models.domain.dt_models import AccountResponse, AggregatedRow, DateField, ProcessingResponse, StatisticalMetadata, DisplayRawField
from datetime import datetime
import uuid

class DrilldownTestDataBuilder:
    """Builder for creating test data for DrilldownResponseService testing."""

    @staticmethod
    def create_aggregated_row(
        row_id: Optional[str] = None,
        category: str = "Grocery",
        amount: float = 100.00,
        timestamp: str = "1704067200",  # Jan 1, 2024
        is_calculated: bool = False
    ) -> AggregatedRow:
        """Create a single AggregatedRow for testing.

        Args:
            row_id: Optional row ID (UUID will be generated if None)
            category: Category name
            amount: Transaction amount
            timestamp: Unix timestamp string
            is_calculated: Whether this is a calculated row

        Returns:
            AggregatedRow instance
        """
        return AggregatedRow(
            row_id=row_id or str(uuid.uuid4()),
            category=category,
            total=DisplayRawField(display=f"{amount:.2f}", raw=amount),
            date=DateField(
                timestamp=int(timestamp),
                display=datetime.fromtimestamp(int(timestamp)).strftime('%Y-%m-%d')
            ),
            details=[],
            is_calculated=is_calculated
        )

    @staticmethod
    def create_datatables_response(
        account_number: str = "ACCT12345678",
        categories: Optional[List[str]] = None,
        months: Optional[List[str]] = None,
        currency: str = "EUR"
    ) -> AccountResponse:
        """Create a AccountResponse with realistic test data.

        Args:
            account_number: Account number
            categories: List of category names (default: Grocery, Vehicle, Utility)
            months: List of timestamp strings (default: Jan and Feb 2024)
            currency: Currency code

        Returns:
            AccountResponse instance
        """
        categories = categories or ["Grocery", "Vehicle", "Utility"]
        months = months or ["1704067200", "1706745600"]  # Jan 2024, Feb 2024

        data = []
        for i, category in enumerate(categories):
            for month in months:
                data.append(DrilldownTestDataBuilder.create_aggregated_row(
                    category=category,
                    amount=100.00 + i * 10,
                    timestamp=month
                ))

        return AccountResponse(
            data=data,
            account=account_number,
            currency=currency
        )

    @staticmethod
    def create_cached_response(
        result_id: str = "test123",
        account_number: str = "ACCT12345678",
        categories: Optional[List[str]] = None,
        months: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Create a realistic cached processing response for testing.

        Args:
            result_id: Processing result ID
            account_number: Account number
            categories: List of category names
            months: List of timestamp strings

        Returns:
            Dictionary containing cached processing response
        """
        categories = categories or ["Grocery", "Vehicle", "Utility"]
        months = months or ["1704067200", "1706745600"]  # Jan 2024, Feb 2024

        dt_response = DrilldownTestDataBuilder.create_datatables_response(
            account_number=account_number,
            categories=categories,
            months=months
        )

        return {
            'data': {
                account_number: dt_response
            },
            'statistical_metadata': StatisticalMetadata(highlights=[]),
            'result_id': result_id
        }

    @staticmethod
    def create_processing_response(
        result_id: str = "test123",
        account_number: str = "ACCT12345678",
        categories: Optional[List[str]] = None,
        months: Optional[List[str]] = None
    ) -> ProcessingResponse:
        """Create a ProcessingResponse object for testing.

        Args:
            result_id: Processing result ID
            account_number: Account number
            categories: List of category names
            months: List of timestamp strings

        Returns:
            ProcessingResponse instance
        """
        cached_data = DrilldownTestDataBuilder.create_cached_response(
            result_id=result_id,
            account_number=account_number,
            categories=categories,
            months=months
        )

        return ProcessingResponse(
            result_id=result_id,
            data={account_number: cached_data['data'][account_number]},
            metadata={},
            statistical_metadata=cached_data['statistical_metadata']
        )

    @staticmethod
    def create_id_mappings(
        result_id: str = "test123",
        account_number: str = "ACCT12345678",
        categories: Optional[List[str]] = None,
        months: Optional[List[str]] = None
    ) -> Dict[str, str]:
        """Create ID mappings for testing.

        Args:
            result_id: Processing result ID
            account_number: Account number
            categories: List of category names
            months: List of timestamp strings

        Returns:
            Dictionary containing ID mappings
        """
        categories = categories or ["Grocery", "Vehicle", "Utility"]
        months = months or ["1704067200", "1706745600"]  # Jan 2024, Feb 2024

        mappings = {
            # Account mappings
            f"account:{result_id}:account1": account_number,
            f"account_reverse:{result_id}:{account_number}": "account1",

            # Category mappings
            f"category_reverse:{result_id}:Grocery": "cat1",
            f"category_reverse:{result_id}:Vehicle": "cat2",
            f"category_reverse:{result_id}:Utility": "cat3",
            f"category:{result_id}:cat1": "Grocery",
            f"category:{result_id}:cat2": "Vehicle",
            f"category:{result_id}:cat3": "Utility",

            # Month mappings
            "month_reverse:1704067200": "month1",
            "month_reverse:1706745600": "month2",
            "month:month1": "1704067200",
            "month:month2": "1706745600"
        }

        return mappings

    @staticmethod
    def create_complete_test_setup(
        result_id: str = "test123",
        account_number: str = "ACCT12345678"
    ) -> Dict[str, Any]:
        """Create a complete test setup with all required data.

        Args:
            result_id: Processing result ID
            account_number: Account number

        Returns:
            Dictionary containing all test data components
        """
        return {
            'id_mappings': DrilldownTestDataBuilder.create_id_mappings(
                result_id=result_id,
                account_number=account_number
            ),
            'cache_data': {
                result_id: DrilldownTestDataBuilder.create_processing_response(
                    result_id=result_id,
                    account_number=account_number
                )
            },
            'formatting_results': {
                'account_id': f"{account_number[:8]}-{account_number[8:16]}",
                'highlights': {}
            }
        }