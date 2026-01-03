"""Response Builder Service for standardized response generation.

This service centralizes all response building logic across web and API endpoints,
eliminating duplication and ensuring consistent metadata, error handling, and
response structure.

Architecture Patterns:
- Builder Pattern: Complex response objects built step-by-step
- Facade Pattern: Simplifies complex response building logic
- Template Method: Common structure, variant implementations
- DRY Principle: Single implementation for response building
"""
from typing import Dict, Any, Optional, List, Union, TYPE_CHECKING

if TYPE_CHECKING:
    from flask import Response
from whatsthedamage.models.api_models import (
    DetailedResponse,
    DetailedMetadata,
    ErrorResponse,
    ProcessingRequest
)
from whatsthedamage.services.data_formatting_service import DataFormattingService


class ResponseBuilderService:
    """Service for building standardized API and web responses.

    This service consolidates response building logic that was previously
    scattered across v1/v2 API endpoints, routes_helpers, and error handlers.
    """

    def __init__(self, formatting_service: Optional[DataFormattingService] = None) -> None:
        """Initialize the response builder service.

        Args:
            formatting_service: Optional DataFormattingService instance (injected via DI)
        """
        self._formatting_service = formatting_service or DataFormattingService()

    def build_api_detailed_response(
        self,
        datatables_response: Any,
        metadata: Dict[str, Any],
        params: ProcessingRequest,
        processing_time: float
    ) -> DetailedResponse:
        """Build standardized API detailed response.

        Args:
            datatables_response: Dict[str, DataTablesResponse] mapping account to response objects
            metadata: Processing metadata (row_count, etc.)
            params: Request parameters
            processing_time: Total processing time in seconds

        Returns:
            DetailedResponse: Pydantic model for v2 API response with array of account responses

        Example:
            >>> response = service.build_api_detailed_response(
            ...     datatables_response={'12345': dt_response1, '67890': dt_response2},
            ...     metadata={'row_count': 150},
            ...     params=ProcessingRequest(ml_enabled=True),
            ...     processing_time=1.2
            ... )
        """
        # Convert dict to array, sorted by account ID
        aggregated_rows = []
        for account_id in sorted(datatables_response.keys()):
            dt_response = datatables_response[account_id]
            # Add all aggregated rows from this account
            aggregated_rows.extend(dt_response.data)

        return DetailedResponse(
            data=aggregated_rows,  # List[AggregatedRow] from all accounts
            metadata=DetailedMetadata(
                row_count=metadata['row_count'],
                processing_time=processing_time,
                ml_enabled=params.ml_enabled,
                date_range=self._build_date_range(params)
            )
        )

    def build_html_response(
        self,
        template: str,
        headers: Optional[List[str]] = None,
        rows: Optional[List[List[Dict[str, Union[str, float, None]]]]] = None,
        **kwargs: Any
    ) -> "Response":
        """Build HTML response with proper headers.

        Args:
            template: Template name (e.g., 'result.html', 'v2_results.html')
            headers: Table headers (for v1 templates)
            rows: Table rows with display/order/details metadata (for v1 templates)
            \\**kwargs: Additional template context variables (e.g., dt_responses for v2)

        Returns:
            Flask Response object with rendered HTML

        Example:
            >>> # For v1 template
            >>> response = service.build_html_response(
            ...     template='result.html',
            ...     headers=['Categories', 'January', 'February'],
            ...     rows=[[{'display': 'Grocery', 'order': None}]]
            ... )
            >>> # For v2 template with multi-account
            >>> response = service.build_html_response(
            ...     template='v2_results.html',
            ...     dt_responses=dt_responses_dict
            ... )
        """
        from flask import make_response, render_template

        template_context = {**kwargs}
        if headers is not None:
            template_context['headers'] = headers
        if rows is not None:
            template_context['rows'] = rows

        return make_response(
            render_template(template, **template_context)
        )

    def build_error_response(
        self,
        error: Exception,
        default_code: int = 500,
        default_message: str = "Internal server error",
        context: Optional[Dict[str, Any]] = None
    ) -> tuple["Response", int]:
        """Build standardized error response.

        Centralizes error response building logic that was duplicated in
        api/helpers.py::handle_error() and api/error_handlers.py.

        Args:
            error: The exception to handle
            default_code: Default status code if exception type not recognized
            default_message: Default error message
            context: Optional additional context

        Returns:
            tuple: (jsonified error response, status code)

        Example:
            >>> response, code = service.build_error_response(
            ...     ValueError("Invalid date format"),
            ...     default_code=422,
            ...     default_message="Validation error"
            ... )
        """
        from flask import jsonify
        from werkzeug.exceptions import BadRequest
        from pydantic import ValidationError as PydanticValidationError
        from whatsthedamage.utils.validation import ValidationError

        # Determine status code and message based on exception type
        if isinstance(error, BadRequest):
            field_value = context.get("field", "unknown") if context else "unknown"
            error_response = ErrorResponse(
                code=400,
                message=str(error),
                details={"field": str(field_value)}
            )
            status_code = 400

        elif isinstance(error, PydanticValidationError):
            validation_errors = [str(err) for err in error.errors()]
            error_response = ErrorResponse(
                code=400,
                message="Invalid request parameters",
                details={"errors": validation_errors}
            )
            status_code = 400

        elif isinstance(error, ValidationError):
            error_response = ErrorResponse(
                code=400,
                message=error.result.error_message or "Validation failed",
                details=error.result.details or {}
            )
            status_code = 400

        elif isinstance(error, FileNotFoundError):
            error_response = ErrorResponse(
                code=400,
                message="File not found",
                details={"error": str(error)}
            )
            status_code = 400

        elif isinstance(error, ValueError):
            error_response = ErrorResponse(
                code=422,
                message="Processing error",
                details={"error": str(error)}
            )
            status_code = 422

        else:
            # Generic exception handling
            error_response = ErrorResponse(
                code=default_code,
                message=default_message,
                details={"error": str(error), "type": type(error).__name__}
            )
            status_code = default_code

        return jsonify(error_response.model_dump()), status_code


    # Private helper methods

    def _build_date_range(self, params: ProcessingRequest) -> Optional[Dict[str, str]]:
        """Build date range dictionary from parameters.

        Args:
            params: Processing request parameters

        Returns:
            Dict with start/end dates or None if no dates specified
        """
        if not params.start_date and not params.end_date:
            return None

        date_range = {}
        if params.start_date:
            date_range['start'] = params.start_date
        if params.end_date:
            date_range['end'] = params.end_date

        return date_range
