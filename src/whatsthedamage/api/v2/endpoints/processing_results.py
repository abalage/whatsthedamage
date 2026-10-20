"""Processing result endpoints.

CSV upload processing plus the user's processing result listings.
"""

import time
from datetime import datetime, UTC
from typing import Optional, cast

from flask import Blueprint, Response, current_app, jsonify, request

from whatsthedamage.api.auth_decorators import require_authentication, require_csrf
from whatsthedamage.api.helpers import (
    cleanup_files,
    get_config_file,
    handle_error,
    parse_request_params,
    save_uploaded_files,
    validate_csv_file,
    _get_processing_result_repository,
    _get_processing_service,
    _get_transaction_import_service,
    _get_transaction_repository,
)
from whatsthedamage.models.database.user import User as UserDB
from whatsthedamage.models.domain.dt_models import ProcessingResponse

processing_results_bp = Blueprint('api_v2_processing_results', __name__)


def _format_transaction_date(value: Optional[datetime]) -> str | None:
    """Format a transaction datetime as an ISO 8601 date string.

    Args:
        value: Transaction datetime; may be None.

    Returns:
        Date portion in YYYY-MM-DD format, or None.
    """
    return value.strftime('%Y-%m-%d') if value else None


@processing_results_bp.route('/processing-results', methods=['POST'])
@require_authentication
@require_csrf
def create_processing_result() -> tuple[Response, int]:
    """POST /api/v2/processing-results - Create new transaction processing result.

    Creates ProcessingResult metadata and saves individual Transaction entities.
    All Transaction entities are linked to the ProcessingResult via result_id.

    This is the primary endpoint for processing CSV transaction files.
    Requires authentication.

    Accepts multipart/form-data with:
    - csv_file (required): CSV file with bank transactions
    - config_file (optional): YAML configuration file
    - start_date (optional): Filter start date
    - end_date (optional): Filter end date
    - date_format (optional): Date format string (default from config)
    - ml_enabled (optional): Enable ML categorization (default: false)
    - category_filter (optional): Filter by specific category
    - csv_profile_id (optional): CSV profile ID to use

    Returns:
        Response with processing result metadata only (no full data structure)

    Status Codes:
        201: Successfully created processing result
        400: Bad request (missing file, invalid parameters)
        401: Not authenticated
        409: Conflict (duplicate transaction)
        422: Unprocessable entity (CSV parsing error, validation failed)
        500: Internal server error
    """
    from whatsthedamage.models.database.processing_result import (
        ProcessingResult as ProcessingResultDB
    )
    from whatsthedamage.models.repositories.unit_of_work import (
        SqlAlchemyUnitOfWork
    )

    start_time = time.time()
    user = cast(UserDB, request.user)  # type: ignore[attr-defined]

    csv_file = validate_csv_file()
    config_file = get_config_file()
    params = parse_request_params()

    csv_path, config_path = save_uploaded_files(csv_file, config_file)

    try:
        result: ProcessingResponse = _get_processing_service(
        ).process_with_details(
            csv_file_path=csv_path,
            config_file_path=config_path,
            start_date=params.start_date,
            end_date=params.end_date,
            ml_enabled=params.ml_enabled,
            category_filter=params.category_filter,
            csv_profile_id=params.csv_profile_id
        )

        # Create ProcessingResultDB with new schema (metadata only)
        metadata = result.metadata
        import_service = _get_transaction_import_service()
        start_date_val, end_date_val = (
            import_service.extract_result_date_range(metadata, params)
        )

        processing_result_db = ProcessingResultDB(
            result_id=result.result_id,
            user_id=cast(int, user.id),  # type: ignore[arg-type]
            csv_profile_id=params.csv_profile_id if params.csv_profile_id else None,
            row_count=getattr(metadata, 'row_count', None),
            processing_time=getattr(metadata, 'processing_time', None),
            ml_enabled=params.ml_enabled if params.ml_enabled else False,
            start_date=start_date_val,
            end_date=end_date_val,
            created_at=datetime.now(UTC)
        )

        # Persist the processing result and its transactions in a single
        # transaction so a failure cannot leave a partial import behind
        all_csv_rows = import_service.extract_csv_rows_from_result(result)
        with SqlAlchemyUnitOfWork(current_app.extensions['db_session_factory']) as uow:
            uow.processing_results.add(processing_result_db)
            import_service.persist_result_transactions(
                cast(int, user.id), result.result_id, all_csv_rows, uow
            )
            uow.commit()

        processing_time = time.time() - start_time

        # Build response with metadata only
        response = {
            'result_id': result.result_id,
            'user_id': user.id,
            'csv_profile_id': params.csv_profile_id,
            'row_count': getattr(metadata, 'row_count', len(all_csv_rows)),
            'processing_time': processing_time,
            'ml_enabled': params.ml_enabled if params.ml_enabled else False,
            'start_date': start_date_val.isoformat() if start_date_val else None,
            'end_date': end_date_val.isoformat() if end_date_val else None,
            'created_at': datetime.now(UTC).isoformat(),
            'transactions_count': len(all_csv_rows),
            'message': 'Processing result created successfully'
        }

        return jsonify(response), 201

    except ValueError as e:
        # Handle duplicate transaction errors
        error_message = str(e)
        if 'already exists' in error_message.lower():
            return jsonify({
                'error': error_message,
                'code': 'DUPLICATE_TRANSACTION'
            }), 409
        # CSV parsing / validation failures carry controlled messages
        return jsonify({'error': error_message}), 422
    except Exception as e:
        return handle_error(e)
    finally:
        cleanup_files(csv_path, config_path)


@processing_results_bp.route('/processing-results', methods=['GET'])
@require_authentication
def list_processing_results() -> tuple[Response, int]:
    """GET /api/v2/processing-results - List all processing results for authenticated user.

    Requires authentication. Returns a paginated list of the user's processing results.

    Query Parameters:
        limit (optional): Maximum number of results to return (default: 100)
        offset (optional): Pagination offset (default: 0)

    Returns:
        List of processing results with metadata

    Status Codes:
        200: Successfully retrieved processing results
        401: Not authenticated
        500: Internal server error
    """
    user = cast(UserDB, request.user)  # type: ignore[attr-defined]

    processing_result_repo = _get_processing_result_repository()

    # Get pagination parameters
    limit = int(request.args.get('limit', 100))
    offset = int(request.args.get('offset', 0))

    # Get results for user
    results = processing_result_repo.find_by_user_id(
        cast(int, user.id), limit=limit, offset=offset  # type: ignore[arg-type]
    )

    # Get the actual transaction date range for each result
    transaction_repo = _get_transaction_repository()
    date_ranges = transaction_repo.get_date_ranges_by_result_ids(
        cast(int, user.id), [result.result_id for result in results]
    )

    # Build response with new format
    results_list = []
    for result in results:
        date_range = date_ranges.get(cast(str, result.result_id))
        results_list.append({
            'id': result.result_id,  # Now using result_id
            'csv_profile_id': result.csv_profile_id,
            'row_count': result.row_count,
            'processing_time': result.processing_time,
            'ml_enabled': result.ml_enabled,
            'start_date': result.start_date.isoformat() if result.start_date else None,
            'end_date': result.end_date.isoformat() if result.end_date else None,
            'transaction_start_date': (
                _format_transaction_date(date_range[0]) if date_range else None
            ),
            'transaction_end_date': (
                _format_transaction_date(date_range[1]) if date_range else None
            ),
            'created_at': result.created_at.isoformat() if result.created_at else None,
            # updated_at removed as per requirement
        })

    return jsonify(results_list), 200


@processing_results_bp.route('/processing-results/<result_id>', methods=['GET'])
@require_authentication
def get_processing_result_by_id(result_id: str) -> tuple[Response, int]:
    """GET /api/v2/processing-results/<result_id> - Get a specific processing result metadata.

    Returns metadata only. Transaction data should be fetched via /transactions endpoint.

    Requires authentication. Returns the processing result if it belongs to the authenticated user.

    Args:
        result_id: UUID of the processing result to retrieve

    Returns:
        Metadata only (no transaction data)

    Status Codes:
        200: Successfully retrieved processing result
        401: Not authenticated
        403: Forbidden (result belongs to another user)
        404: Processing result not found
        500: Internal server error
    """
    user = cast(UserDB, request.user)  # type: ignore[attr-defined]

    processing_result_repo = _get_processing_result_repository()

    # Find result by user and result_id
    processing_result = processing_result_repo.find_by_user_and_result_id(
        cast(int, user.id), result_id  # type: ignore[arg-type]
    )

    if not processing_result:
        return jsonify({'error': 'Result not found or does not belong to you'}), 404

    # Get the actual transaction date range for the result
    transaction_repo = _get_transaction_repository()
    date_ranges = transaction_repo.get_date_ranges_by_result_ids(
        cast(int, user.id),  # type: ignore[arg-type]
        [cast(str, processing_result.result_id)]  # type: ignore[list-item]
    )
    date_range = date_ranges.get(cast(str, processing_result.result_id))

    # Return metadata only
    return jsonify({
        'result_id': processing_result.result_id,
        'user_id': processing_result.user_id,
        'csv_profile_id': processing_result.csv_profile_id,
        'row_count': processing_result.row_count,
        'processing_time': processing_result.processing_time,
        'ml_enabled': processing_result.ml_enabled,
        'start_date': processing_result.start_date.isoformat() if processing_result.start_date else None,
        'end_date': processing_result.end_date.isoformat() if processing_result.end_date else None,
        'transaction_start_date': (
            _format_transaction_date(date_range[0]) if date_range else None
        ),
        'transaction_end_date': (
            _format_transaction_date(date_range[1]) if date_range else None
        ),
        'created_at': processing_result.created_at.isoformat() if processing_result.created_at else None,
        # Provide link to fetch transactions for this result
        'transactions_url': f'/api/v2/transactions?result_id={processing_result.result_id}'
    }), 200
