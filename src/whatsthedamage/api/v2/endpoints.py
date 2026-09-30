"""API v2 endpoints - Detailed transaction processing.

This module provides REST API endpoints for processing CSV transaction files
with detailed transaction-level data for DataTables rendering.
"""
from __future__ import annotations

from flask import Blueprint, jsonify, Response, request, current_app
from werkzeug.exceptions import BadRequest
import time
from datetime import datetime, UTC
from typing import TYPE_CHECKING, Any, Optional, cast

from whatsthedamage.models.domain.dt_models import ProcessingResponse
from whatsthedamage.models.api.responses import RecalculateApiResponse
from whatsthedamage.utils.date_converter import DateConverter
from whatsthedamage.models.database.user import User as UserDB
from whatsthedamage.models.database.transaction import Transaction as TransactionDB
from whatsthedamage.api.helpers import (
    validate_csv_file,
    get_config_file,
    parse_request_params,
    save_uploaded_files,
    cleanup_files,
    handle_error,
    _get_response_formatting_service,
    _get_processing_service,
    _get_statistical_service,
    _get_processing_result_repository,
    _get_transaction_repository,
    _get_correction_repository,
    _get_deduplication_service,
)
from whatsthedamage.api.auth_decorators import require_authentication, require_csrf

if TYPE_CHECKING:
    from whatsthedamage.models.repositories.unit_of_work import SqlAlchemyUnitOfWork


# Create Blueprint
v2_bp = Blueprint('api_v2', __name__, url_prefix='/api/v2')


# Removed old drilldown endpoints - replaced by /transactions/aggregate
# Old endpoints:
# - /processing-results/<result_id>/accounts/<account_id>/categories/<category_id>/months
# - /processing-results/<result_id>/accounts/<account_id>/months/<month_id>/categories
# - /processing-results/<result_id>/accounts/<account_id>/categories/<category_id>/months/<month_id>/transactions

@v2_bp.route('/categories', methods=['GET'])
def get_categories() -> tuple[Response, int]:
    """Get all available category definitions.

    Returns the assignable (non-calculated) CategoryDefinition objects that
    the frontend can use for translating category IDs to display names
    client-side and for offering category choices. Calculated categories
    (Balance, Cost of Living, Total Spendings) are excluded because they
    are computed aggregates and cannot be assigned to transactions.

    This endpoint provides the canonical source of category definitions,
    allowing the frontend to map category_id values to localized display names.

    Returns:
        List of CategoryDefinition objects with id, default_name, and patterns.

    Status Codes:
        200: Successfully retrieved categories
    """
    from whatsthedamage.config.config import get_assignable_categories
    return jsonify([
        cat.model_dump(exclude={'calculated'}) for cat in get_assignable_categories()
    ]), 200

@v2_bp.route('/categories/cost-of-living', methods=['GET'])
def get_cost_of_living_categories() -> tuple[Response, int]:
    """Get cost of living category definitions.

    Returns:
        List of CategoryDefinition objects for categories counted in cost of living calculations.

    Status Codes:
        200: Successfully retrieved list of categories
    """
    from whatsthedamage.config.config import AVAILABLE_CATEGORIES, COST_OF_LIVING_CATEGORY_IDS
    return jsonify([
        cat.model_dump(exclude={'calculated'})
        for cat in AVAILABLE_CATEGORIES
        if cat.id in COST_OF_LIVING_CATEGORY_IDS
    ]), 200


# CSV Profile endpoints

from whatsthedamage.services.csv_profile_service import CsvProfileService

_csv_profile_service = CsvProfileService()


def _get_csv_profile_service() -> CsvProfileService:
    """Get CSV profile service instance."""
    return _csv_profile_service


@v2_bp.route('/csv-profiles', methods=['GET'])
def get_csv_profiles() -> tuple[Response, int]:
    """GET /api/v2/csv-profiles - List all profiles.

    Returns a list of all available CSV profiles with their metadata.

    Returns:
        List of CSV profile objects with id, name, description, version, and csv_config.

    Status Codes:
        200: Successfully retrieved CSV profiles
        500: Failed to retrieve CSV profiles
    """
    try:
        profiles = _get_csv_profile_service().get_all_profiles()
        return jsonify([p.model_dump() for p in profiles]), 200
    except Exception as e:
        return jsonify({"error": "Failed to retrieve CSV profiles"}), 500


@v2_bp.route('/csv-profiles/<profile_id>', methods=['GET'])
def get_csv_profile(profile_id: str) -> tuple[Response, int]:
    """GET /api/v2/csv-profiles/<id> - Get specific profile.

    Returns the details of a specific CSV profile by its ID.

    Args:
        profile_id: The unique identifier of the CSV profile to retrieve.

    Returns:
        CSV profile object with all configuration details.

    Status Codes:
        200: Successfully retrieved CSV profile
        404: CSV profile not found
    """
    profile = _get_csv_profile_service().get_profile_by_id(profile_id)
    if not profile:
        return jsonify({"error": f"CSV profile not found: {profile_id}"}), 404
    return jsonify(profile.model_dump()), 200


@v2_bp.route('/openapi.json', methods=['GET'])
def get_openapi_spec() -> tuple[Response, int]:
    """GET /api/v2/openapi.json - Get OpenAPI specification.

    Returns the complete OpenAPI 3.0.3 specification for this API.
    This can be used with OpenAPI-compatible tools for documentation
    generation, client code generation, or testing.

    Returns:
        OpenAPI 3.0.3 specification as JSON

    Status Codes:
        200: Successfully returned OpenAPI specification
    """
    from whatsthedamage.api.v2.schema import get_openapi_schema
    return jsonify(get_openapi_schema()), 200


# Transaction endpoints - RESTful design for authenticated users only


def _parse_result_date(value: Any) -> Optional[datetime]:
    """Parse a date filter string into a datetime for persistence.

    Args:
        value: Date value (string or datetime); may be None.

    Returns:
        Parsed datetime, or None when the value is missing or unparseable.
    """
    if isinstance(value, datetime) or not value:
        return value
    try:
        return DateConverter.parse_to_datetime_utc(value)
    except ValueError:
        pass
    try:
        from dateutil import parser as dateutil_parser
        return dateutil_parser.parse(str(value))
    except (ValueError, OverflowError):
        return None


def _format_transaction_date(value: Optional[datetime]) -> Optional[str]:
    """Format a transaction datetime as an ISO 8601 date string.

    Args:
        value: Transaction datetime; may be None.

    Returns:
        Date portion in YYYY-MM-DD format, or None.
    """
    return value.strftime('%Y-%m-%d') if value else None


def _extract_result_date_range(
    metadata: Any,
    params: Any
) -> tuple[Optional[datetime], Optional[datetime]]:
    """Resolve the processing result date range.

    Prefers dates reported in the processing metadata, falling back to the
    request parameters. Values are parsed into datetimes for persistence
    in the processing result's DateTime columns.

    Args:
        metadata: Processing metadata from the processing response.
        params: Validated request parameters.

    Returns:
        Tuple of (start_date, end_date), either may be None.
    """
    start_date_val = None
    end_date_val = None
    date_range = getattr(metadata, 'date_range', None)
    if date_range:
        start_date_val = getattr(date_range, 'start', None)
        end_date_val = getattr(date_range, 'end', None)
    if start_date_val is None:
        start_date_val = params.start_date or None
    if end_date_val is None:
        end_date_val = params.end_date or None
    return _parse_result_date(start_date_val), _parse_result_date(end_date_val)


def _extract_csv_rows_from_result(result: ProcessingResponse) -> list[Any]:
    """Collect the individual CSV rows of a processing response.

    Args:
        result: Complete processing response with per-account data.

    Returns:
        List of CsvRow objects, one per transaction detail.
    """
    from whatsthedamage.models.domain.csv_row import CsvRow

    all_csv_rows: list[Any] = []
    for account in result.data.values():
        if hasattr(account, 'data') and account.data:
            for agg_row in account.data:
                if hasattr(agg_row, 'details') and agg_row.details:
                    for detail in agg_row.details:
                        csv_row_dict: dict[str, str] = {
                            'date': datetime.fromtimestamp(
                                detail.date.timestamp, tz=UTC
                            ).strftime('%Y-%m-%d'),
                            'type': detail.type or '',
                            'partner': detail.merchant or '',
                            'amount': str(detail.amount.raw),
                            'currency': detail.currency or '',
                            'category_id': detail.category_id or '',
                            'account': detail.account or '',
                            'notice': detail.notice or '',
                            'confidence': (
                                str(detail.confidence)
                                if detail.confidence is not None
                                else ''
                            )
                        }
                        all_csv_rows.append(CsvRow(csv_row_dict,
                            {'date': 'date', 'type': 'type', 'partner': 'partner',
                             'amount': 'amount', 'currency': 'currency',
                             'category_id': 'category_id', 'account': 'account',
                             'notice': 'notice'}))
    return all_csv_rows


def _persist_result_transactions(
    user_id: int,
    result_id: str,
    csv_rows: list[Any],
    uow: 'SqlAlchemyUnitOfWork'
) -> None:
    """Persist transaction entities, skipping deduplication duplicates.

    Runs inside the given unit of work without committing; rows already
    present in the database and rows repeated within the batch are
    skipped.

    Args:
        user_id: User identifier owning the transactions.
        result_id: Processing result the transactions belong to.
        csv_rows: CSV rows to persist.
        uow: Unit of work providing the transaction repository and
            controlling commit/rollback.
    """
    dedup_service = _get_deduplication_service()

    dedup_hashes = [
        dedup_service.generate_dedup_hash_from_row(csv_row) for csv_row in csv_rows
    ]
    existing_hashes = uow.transactions.find_existing_dedup_hashes(dedup_hashes)

    new_transactions: list[TransactionDB] = []
    batch_hashes: set[str] = set()
    for csv_row, dedup_hash in zip(csv_rows, dedup_hashes):
        if dedup_hash in existing_hashes or dedup_hash in batch_hashes:
            continue
        batch_hashes.add(dedup_hash)
        new_transactions.append(TransactionDB(
            user_id=user_id,
            result_id=result_id,
            date=DateConverter.parse_to_datetime_utc(csv_row.date),
            transaction_type=csv_row.type,
            original_partner=csv_row.partner,
            amount=float(csv_row.amount),
            currency=csv_row.currency,
            account=csv_row.account or 'unknown',
            deduplication_hash=dedup_hash,
            category_id=getattr(csv_row, 'category_id', None),
            partner=None,
            notice=getattr(csv_row, 'notice', None),
            confidence=getattr(csv_row, 'confidence', None),
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC)
        ))

    uow.transactions.add_all(new_transactions)


@v2_bp.route('/processing-results', methods=['POST'])
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
    from whatsthedamage.models.database.processing_result import ProcessingResult as ProcessingResultDB
    from whatsthedamage.api.helpers import _get_processing_result_repository

    start_time = time.time()
    user = cast(UserDB, request.user)  # type: ignore[attr-defined]

    csv_file = validate_csv_file()
    config_file = get_config_file()
    params = parse_request_params()

    csv_path, config_path = save_uploaded_files(csv_file, config_file)

    try:
        result: ProcessingResponse = _get_processing_service().process_with_details(
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
        start_date_val, end_date_val = _extract_result_date_range(metadata, params)

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
        from whatsthedamage.models.repositories.unit_of_work import SqlAlchemyUnitOfWork

        all_csv_rows = _extract_csv_rows_from_result(result)
        with SqlAlchemyUnitOfWork(current_app.extensions['db_session_factory']) as uow:
            uow.processing_results.add(processing_result_db)
            _persist_result_transactions(
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
        raise
    except Exception as e:
        return handle_error(e)
    finally:
        cleanup_files(csv_path, config_path)


@v2_bp.route('/processing-results', methods=['GET'])
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
        date_range = date_ranges.get(result.result_id)
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


@v2_bp.route('/processing-results/<result_id>', methods=['GET'])
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
        cast(int, user.id), [processing_result.result_id]  # type: ignore[arg-type]
    )
    date_range = date_ranges.get(processing_result.result_id)

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


# Transaction CRUD endpoints - Direct Transaction entity operations
# These endpoints work with individual Transaction entities, not ProcessingResults

@v2_bp.route('/transactions', methods=['GET'])
@require_authentication
def list_transaction_entities() -> tuple[Response, int]:
    """GET /api/v2/transactions - List all Transaction entities for authenticated user.

    Returns a paginated list of individual Transaction entities (not ProcessingResults).
    Supports comprehensive filtering and sorting.

    Query Parameters:
        limit (int): Maximum number of transactions to return (default: 100).
        offset (int): Pagination offset (default: 0).
        start_date (str): Filter by start date (YYYY-MM-DD format).
        end_date (str): Filter by end date (YYYY-MM-DD format).
        category_id (str): Filter by category ID.
        account (str): Filter by account.
        partner (str): Filter by partner name (searches original_partner and partner).
        transaction_type (str): Filter by transaction type (debit/credit).
        month (str): Filter by month (YYYY-MM format).
        min_amount (float): Minimum amount filter.
        max_amount (float): Maximum amount filter.
        result_id (str): Filter by processing result.
        sort_by (str): Field to sort by (date, amount, partner, account, category).
        sort_order (str): Sort order (asc/desc, default: desc).

    Returns:
        List of Transaction entities with pagination metadata.

    Status Codes:
        200: Successfully retrieved transactions.
        401: Not authenticated.
        400: Invalid query parameters.
        500: Internal server error.
    """
    user = cast(UserDB, request.user)  # type: ignore[attr-defined]

    try:
        # Parse query parameters
        limit = int(request.args.get('limit', 100))
        offset = int(request.args.get('offset', 0))
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        category_id = request.args.get('category_id')
        account = request.args.get('account')
        partner = request.args.get('partner')
        transaction_type = request.args.get('transaction_type')
        month = request.args.get('month')
        result_id = request.args.get('result_id')  # NEW: Filter by processing result

        # Parse amount filters
        min_amount: Optional[float] = None
        max_amount: Optional[float] = None
        if request.args.get('min_amount'):
            min_amount = float(request.args.get('min_amount'))
        if request.args.get('max_amount'):
            max_amount = float(request.args.get('max_amount'))

        # Parse sorting parameters
        sort_by = request.args.get('sort_by', 'date')
        sort_order = request.args.get('sort_order', 'desc')

        # Validate sort parameters
        valid_sort_fields = ['date', 'amount', 'partner', 'account', 'category']
        if sort_by not in valid_sort_fields:
            sort_by = 'date'
        if sort_order not in ['asc', 'desc']:
            sort_order = 'desc'

        # Get transactions with filters (including result_id)
        transaction_repo = _get_transaction_repository()
        transactions, total_count = transaction_repo.find_by_user_with_filters(
            user_id=cast(int, user.id),  # type: ignore[arg-type]
            start_date=start_date,
            end_date=end_date,
            category_id=category_id,
            account=account,
            partner=partner,
            transaction_type=transaction_type,
            month=month,
            min_amount=min_amount,
            max_amount=max_amount,
            result_id=result_id,  # NEW: Filter by processing result
            limit=limit,
            offset=offset,
            sort_by=sort_by,
            sort_order=sort_order
        )

        # Build response
        response_data = {
            'transactions': [
                {
                    'id': t.id,
                    'user_id': t.user_id,
                    'result_id': t.result_id,  # NEW: Include result_id in response
                    'date': t.date.isoformat() if t.date else None,
                    'transaction_type': t.transaction_type,
                    'original_partner': t.original_partner,
                    'amount': t.amount,
                    'currency': t.currency,
                    'account': t.account or 'unknown',
                    'deduplication_hash': t.deduplication_hash,
                    'category_id': t.category_id,
                    'partner': t.partner,
                    'notice': t.notice,
                    'confidence': t.confidence,
                    'created_at': t.created_at.isoformat() if t.created_at else None,
                    'updated_at': t.updated_at.isoformat() if t.updated_at else None
                }
                for t in transactions
            ],
            'total_count': total_count,
            'limit': limit,
            'offset': offset
        }

        return jsonify(response_data), 200

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@v2_bp.route('/transactions/aggregate', methods=['GET'])
@require_authentication
def aggregate_transactions() -> tuple[Response, int]:
    """GET /api/v2/transactions/aggregate - Get aggregated transaction data.

    Supports grouping by category, month, account for drilldown views.
    Replaces the old /processing-results drilldown endpoints.

    Query Parameters:
        result_id: Filter by processing result
        account: Filter by account
        category_id: Filter by category
        month: Filter by month
        group_by: How to group results (category, month, account, category_month)
        algorithms: Comma-separated algorithm names (default: iqr,pareto)
        direction: Analysis direction ('columns' default or 'rows')

    Returns:
        Aggregated transaction data with groups and highlights

    Status Codes:
        200: Successfully retrieved aggregated data
        400: Invalid parameters
        401: Not authenticated
        500: Internal server error
    """
    user = cast(UserDB, request.user)  # type: ignore[attr-defined]

    try:
        result_id = request.args.get('result_id')
        account = request.args.get('account')
        category_id = request.args.get('category_id')
        month = request.args.get('month')
        group_by = request.args.get('group_by')  # 'category', 'month', 'account', 'category_month'

        if not group_by:
            return jsonify({'error': 'group_by parameter is required'}), 400

        # Get transactions with filters
        transaction_repo = _get_transaction_repository()
        transactions, total_count = transaction_repo.find_by_user_with_filters(
            user_id=cast(int, user.id),  # type: ignore[arg-type]
            result_id=result_id,
            account=account,
            category_id=category_id,
            month=month,
            limit=10000,  # Get many for aggregation
            offset=0
        )

        # Group transactions
        groups: dict[str, list[TransactionDB]] = {}
        if group_by == 'month':
            groups = _group_transactions_by_month(transactions)
        elif group_by == 'category':
            groups = _group_transactions_by_category(transactions)
        elif group_by == 'account':
            groups = _group_transactions_by_account(transactions)
        elif group_by == 'category_month':
            groups = _group_transactions_by_category_and_month(transactions)
        else:
            return jsonify({'error': f'Invalid group_by value: {group_by}'}), 400

        # Calculate highlights over the full analysis scope (the parent
        # month x category matrix for user/result/account), then map them
        # onto this view's groups so drilldowns stay consistent with the
        # Categories matrix view
        algorithms_param = request.args.get('algorithms')
        algorithms = (
            [a.strip() for a in algorithms_param.split(',') if a.strip()]
            if algorithms_param else None
        )
        direction = request.args.get('direction') or 'columns'
        if direction not in ('columns', 'rows'):
            return jsonify(
                {'error': "direction must be 'columns' or 'rows'"}
            ), 400

        highlights = _compute_group_highlights(
            user_id=cast(int, user.id),  # type: ignore[arg-type]
            result_id=result_id,
            account=account,
            algorithms=algorithms,
            direction=direction,
            groups=groups
        )

        # Serialize TransactionDB objects to dictionaries for JSON response
        serialized_groups: dict[str, list[dict[str, Any]]] = {}
        for group_key, txns in groups.items():
            serialized_groups[group_key] = [_transaction_to_dict(t) for t in txns]

        return jsonify({
            'result_id': result_id,
            'account': account,
            'category_id': category_id,
            'month': month,
            'group_by': group_by,
            'groups': serialized_groups,
            'highlights': highlights,
            'total_count': total_count
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


def _group_transactions_by_month(transactions: list[TransactionDB]) -> dict[str, list[TransactionDB]]:
    """Group transactions by month."""
    groups: dict[str, list[TransactionDB]] = {}
    for t in transactions:
        # Extract month from date (YYYY-MM format)
        month_key = t.date.strftime('%Y-%m') if t.date else 'unknown'
        if month_key not in groups:
            groups[month_key] = []
        groups[month_key].append(t)
    return groups


def _group_transactions_by_category(transactions: list[TransactionDB]) -> dict[str, list[TransactionDB]]:
    """Group transactions by category."""
    groups: dict[str, list[TransactionDB]] = {}
    for t in transactions:
        cat = t.category_id or 'uncategorized'
        if cat not in groups:
            groups[cat] = []
        groups[cat].append(t)
    return groups


def _group_transactions_by_account(transactions: list[TransactionDB]) -> dict[str, list[TransactionDB]]:
    """Group transactions by account."""
    groups: dict[str, list[TransactionDB]] = {}
    for t in transactions:
        acc = t.account or 'unknown'
        if acc not in groups:
            groups[acc] = []
        groups[acc].append(t)
    return groups


def _group_transactions_by_category_and_month(transactions: list[TransactionDB]) -> dict[str, list[TransactionDB]]:
    """Group transactions by category and month."""
    groups: dict[str, list[TransactionDB]] = {}
    for t in transactions:
        cat = t.category_id or 'uncategorized'
        month_key = t.date.strftime('%Y-%m') if t.date else 'unknown'
        key = f"{cat}_{month_key}"
        if key not in groups:
            groups[key] = []
        groups[key].append(t)
    return groups


def _compute_group_highlights(
    user_id: int,
    result_id: Optional[str],
    account: Optional[str],
    algorithms: Optional[list[str]],
    direction: str,
    groups: dict[str, list[TransactionDB]]
) -> dict[str, list[str]]:
    """Compute statistical highlights mapped onto grouped transactions.

    Highlights are computed over the full month x category matrix for
    user/result/account (the parent matrix view's scope), then each group
    receives the union of the highlight types of the matrix cells its
    transactions cover. This keeps drilldown views consistent with the
    Categories matrix view.

    Args:
        user_id: User identifier
        result_id: Optional processing result filter
        account: Optional account filter
        algorithms: Optional algorithm names (None = enabled algorithms)
        direction: Analysis direction ('columns' or 'rows')
        groups: Transactions grouped by the view's grouping dimension

    Returns:
        Dictionary mapping group keys to highlight types
    """
    transaction_repo = _get_transaction_repository()
    scope_transactions = transaction_repo.find_all_by_user(
        user_id=user_id,
        result_id=result_id,
        account=account
    )
    statistical_service = _get_statistical_service()
    cell_highlights = (
        statistical_service.compute_highlights_from_transactions(
            scope_transactions,
            algorithms=algorithms,
            direction=direction
        )
    )

    highlights: dict[str, list[str]] = {}
    for group_key, txns in groups.items():
        group_types: list[str] = []
        for t in txns:
            month = t.date.strftime('%Y-%m') if t.date else 'unknown'
            cell_id = (
                f"{t.account or 'unknown'}|{month}"
                f"|{t.category_id or 'uncategorized'}"
            )
            for highlight_type in cell_highlights.get(cell_id, []):
                if highlight_type not in group_types:
                    group_types.append(highlight_type)
        highlights[group_key] = group_types

    return highlights


def _transaction_to_dict(t: TransactionDB) -> dict[str, Any]:
    """Convert TransactionDB object to serializable dictionary.

    This is needed because SQLAlchemy ORM objects cannot be directly JSON serialized.
    The output format matches the TransactionListItem type expected by the frontend.
    """
    result: dict[str, Any] = {
        'id': t.id,
        'user_id': t.user_id,
        'result_id': t.result_id,
        'date': t.date.isoformat() if t.date else None,
        'transaction_type': t.transaction_type,
        'original_partner': t.original_partner,
        'amount': t.amount,
        'currency': t.currency,
        'account': t.account or 'unknown',
        'deduplication_hash': t.deduplication_hash,
        'category_id': t.category_id,
        'partner': t.partner,
        'notice': t.notice,
        'confidence': t.confidence,
        'created_at': t.created_at.isoformat() if t.created_at else None,
        'updated_at': t.updated_at.isoformat() if t.updated_at else None,
    }
    return result


@v2_bp.route('/recalculate-statistics', methods=['POST'])
@require_authentication
@require_csrf
def recalculate_statistics() -> tuple[Response, int]:
    """POST /api/v2/recalculate-statistics - Recalculate statistical highlights.

    Computes statistical highlights from persisted Transaction entities for
    the authenticated user, optionally scoped to a processing result.

    Request Body (JSON):
        result_id (str, optional): Processing result to scope to.
            Omitted = all of the user's transactions.
        algorithms (list[str], optional): Algorithm names to apply
            (default: all enabled algorithms, e.g. ['iqr', 'pareto']).
        direction (str, optional): Analysis direction
            ('columns' default or 'rows').

    Returns:
        Highlights keyed by cell ID '{account}|{month}|{category}', the
        coordinates of the Categories matrix view.

    Status Codes:
        200: Successfully recalculated highlights.
        400: Bad request (invalid algorithms or direction).
        401: Not authenticated.
        500: Internal server error.
    """
    user = cast(UserDB, request.user)  # type: ignore[attr-defined]

    try:
        data = request.get_json(silent=True) or {}

        result_id = data.get('result_id')
        algorithms = data.get('algorithms')
        direction = data.get('direction') or 'columns'

        if algorithms is not None and not isinstance(algorithms, list):
            raise BadRequest('algorithms must be a list')
        if direction not in ('columns', 'rows'):
            raise BadRequest("direction must be 'columns' or 'rows'")

        transaction_repo = _get_transaction_repository()
        transactions = transaction_repo.find_all_by_user(
            user_id=cast(int, user.id),  # type: ignore[arg-type]
            result_id=result_id
        )

        statistical_service = _get_statistical_service()
        highlights = statistical_service.compute_highlights_from_transactions(
            transactions,
            algorithms=algorithms,
            direction=direction
        )
        applied_algorithms = (
            algorithms if algorithms is not None
            else list(statistical_service.enabled_algorithms)
        )

        response = RecalculateApiResponse(
            result_id=result_id,
            highlights=highlights,
            algorithms=applied_algorithms,
            direction=direction
        )

        return jsonify(response.model_dump()), 200

    except Exception as e:
        return handle_error(e)


@v2_bp.route('/transactions/<int:transaction_id>', methods=['GET'])
@require_authentication
def get_transaction_entity(transaction_id: int) -> tuple[Response, int]:
    """GET /api/v2/transactions/<transaction_id> - Get a specific Transaction entity by ID.

    Returns the individual Transaction entity if it belongs to the authenticated user.

    Args:
        transaction_id: Transaction identifier.

    Returns:
        Transaction entity data.

    Status Codes:
        200: Successfully retrieved transaction.
        401: Not authenticated.
        403: Forbidden (transaction belongs to another user).
        404: Transaction not found.
        500: Internal server error.
    """
    user = cast(UserDB, request.user)  # type: ignore[attr-defined]

    try:
        transaction_repo = _get_transaction_repository()
        transaction = transaction_repo.find_by_id(transaction_id)

        if not transaction:
            return jsonify({'error': 'Transaction not found'}), 404

        # Verify ownership
        if transaction.user_id != cast(int, user.id):  # type: ignore[arg-type]
            return jsonify({'error': 'Transaction does not belong to you'}), 403

        response_data = {
            'id': transaction.id,
            'user_id': transaction.user_id,
            'date': transaction.date.isoformat() if transaction.date else None,
            'transaction_type': transaction.transaction_type,
            'original_partner': transaction.original_partner,
            'amount': transaction.amount,
            'currency': transaction.currency,
            'account': transaction.account or 'unknown',
            'deduplication_hash': transaction.deduplication_hash,
            'category_id': transaction.category_id,
            'partner': transaction.partner,
            'notice': transaction.notice,
            'confidence': transaction.confidence,
            'created_at': transaction.created_at.isoformat() if transaction.created_at else None,
            'updated_at': transaction.updated_at.isoformat() if transaction.updated_at else None
        }

        return jsonify(response_data), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@v2_bp.route('/transactions', methods=['POST'])
@require_authentication
@require_csrf
def create_transaction_entity() -> tuple[Response, int]:
    """POST /api/v2/transactions - Create a single Transaction entity.

    Creates a new individual Transaction entity for the authenticated user.
    Requires authentication and CSRF protection.

    Request Body (JSON):
        date (str, required): Transaction date (YYYY-MM-DD format).
        transaction_type (str, required): Transaction type (debit/credit).
        original_partner (str, required): Original partner name from CSV.
        amount (float, required): Transaction amount.
        currency (str, required): Currency code.
        account (str, required): Account identifier.
        category_id (str, optional): Assigned category identifier.
        partner (str, optional): Corrected partner name.
        notice (str, optional): Transaction notice/comment.
        confidence (float, optional): Categorization confidence score.

    Returns:
        Created Transaction entity data.

    Status Codes:
        201: Successfully created transaction.
        400: Bad request (missing required fields, invalid data).
        401: Not authenticated.
        409: Conflict (duplicate transaction).
        500: Internal server error.
    """
    user = cast(UserDB, request.user)  # type: ignore[attr-defined]

    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        # Validate required fields
        required_fields = ['date', 'transaction_type', 'original_partner',
                          'amount', 'currency', 'account']
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            return jsonify({
                'error': f"Missing required fields: {', '.join(missing_fields)}"
            }), 400

        # Generate deduplication hash
        dedup_service = _get_deduplication_service()
        from whatsthedamage.models.domain.csv_row import CsvRow

        csv_row = CsvRow({
            'date': data['date'],
            'type': data['transaction_type'],
            'partner': data['original_partner'],
            'amount': str(data['amount']),
            'currency': data['currency'],
            'account': data['account'],
            'category_id': data.get('category_id', ''),
            'notice': data.get('notice', '')
        }, {
            'date': 'date',
            'type': 'type',
            'partner': 'partner',
            'amount': 'amount',
            'currency': 'currency',
            'account': 'account',
            'category_id': 'category_id',
            'notice': 'notice'
        })

        dedup_hash = dedup_service.generate_dedup_hash_from_row(csv_row)

        # Check for duplicate
        transaction_repo = _get_transaction_repository()
        existing = transaction_repo.find_by_user_and_dedup_hash(
            cast(int, user.id), dedup_hash  # type: ignore[arg-type]
        )
        if existing:
            return jsonify({
                'error': 'Transaction with same deduplication hash already exists',
                'code': 'DUPLICATE_TRANSACTION'
            }), 409

        # Create new transaction
        transaction = TransactionDB(
            user_id=cast(int, user.id),  # type: ignore[arg-type]
            date=DateConverter.parse_to_datetime_utc(data['date']),
            transaction_type=data['transaction_type'],
            original_partner=data['original_partner'],
            amount=data['amount'],
            currency=data['currency'],
            account=data['account'] or 'unknown',
            deduplication_hash=dedup_hash,
            category_id=data.get('category_id'),
            partner=data.get('partner'),
            notice=data.get('notice'),
            confidence=data.get('confidence')
        )

        saved_transaction = transaction_repo.create(transaction)

        # Auto-create correction if partner, category_id, or notice were provided
        # This ensures future uploads with the same partner get the same corrections
        correction_repo = _get_correction_repository()
        from whatsthedamage.models.database.correction import Correction as CorrectionDB

        # Check if correction already exists
        existing_correction = correction_repo.find_by_user_and_original_partner(
            cast(int, user.id), data['original_partner']  # type: ignore[arg-type]
        )

        # Only create/update correction if user provided corrected values
        has_corrections = (
            data.get('partner') or
            data.get('category_id') or
            data.get('notice')
        )

        if has_corrections:
            if existing_correction:
                # Update existing correction
                correction_update_data: dict[str, Any] = {}
                if data.get('partner'):
                    correction_update_data['corrected_partner'] = data['partner']
                if data.get('category_id'):
                    correction_update_data['corrected_category_id'] = data['category_id']
                if data.get('notice'):
                    correction_update_data['corrected_notice'] = data['notice']
                correction_repo.update(existing_correction.id, **correction_update_data)
            else:
                # Create new correction
                correction = CorrectionDB(
                    user_id=cast(int, user.id),  # type: ignore[arg-type]
                    original_partner=data['original_partner'],
                    corrected_partner=data.get('partner'),
                    corrected_category_id=data.get('category_id'),
                    corrected_notice=data.get('notice')
                )
                correction_repo.create(correction)

        response_data = {
            'id': saved_transaction.id,
            'user_id': saved_transaction.user_id,
            'date': saved_transaction.date.isoformat() if saved_transaction.date else None,
            'transaction_type': saved_transaction.transaction_type,
            'original_partner': saved_transaction.original_partner,
            'amount': saved_transaction.amount,
            'currency': saved_transaction.currency,
            'account': saved_transaction.account or 'unknown',
            'deduplication_hash': saved_transaction.deduplication_hash,
            'category_id': saved_transaction.category_id,
            'partner': saved_transaction.partner,
            'notice': saved_transaction.notice,
            'confidence': saved_transaction.confidence,
            'created_at': saved_transaction.created_at.isoformat() if saved_transaction.created_at else None,
            'updated_at': saved_transaction.updated_at.isoformat() if saved_transaction.updated_at else None
        }

        return jsonify(response_data), 201

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def _validate_update_transaction_data(
    data: Any | None
) -> tuple[dict[str, Any], Response, int] | tuple[None, Response, int]:
    """Validate and extract update data from request.

    Args:
        data: JSON data from request.

    Returns:
        Tuple of (update_data, error_response, status_code).
        If valid, update_data contains the fields to update.
        If invalid, error_response and status_code are set.
    """
    if not data:
        return None, jsonify({'error': 'No data provided'}), 400

    update_data: dict[str, Any] = {}
    valid_fields = {'category_id', 'partner', 'notice', 'confidence'}

    for field in valid_fields:
        if field in data:
            update_data[field] = data[field]

    if not update_data:
        return None, jsonify({'error': 'No valid fields to update'}), 400

    return update_data, None, 200


def _handle_correction_update(
    user: UserDB,
    transaction: TransactionDB,
    data: dict[str, Any]
) -> None:
    """Handle creation or update of correction for transaction.

    Args:
        user: Authenticated user.
        transaction: Transaction being updated.
        data: Request data containing update fields.
    """
    correction_repo = _get_correction_repository()
    from whatsthedamage.models.database.correction import Correction as CorrectionDB

    existing_correction = correction_repo.find_by_user_and_original_partner(
        cast(int, user.id), transaction.original_partner  # type: ignore[arg-type]
    )

    correction_data: dict[str, Any] = {}
    if 'partner' in data:
        correction_data['corrected_partner'] = data['partner']
    if 'category_id' in data:
        correction_data['corrected_category_id'] = data['category_id']
    if 'notice' in data:
        correction_data['corrected_notice'] = data['notice']

    if existing_correction:
        if correction_data:
            correction_repo.update(existing_correction.id, **correction_data)
    else:
        correction = CorrectionDB(
            user_id=cast(int, user.id),  # type: ignore[arg-type]
            original_partner=transaction.original_partner,
            corrected_partner=data.get('partner'),
            corrected_category_id=data.get('category_id'),
            corrected_notice=data.get('notice')
        )
        correction_repo.create(correction)


def _format_transaction_response(transaction: TransactionDB) -> dict[str, Any]:
    """Format transaction for JSON response.

    Args:
        transaction: Transaction to format.

    Returns:
        Dictionary with transaction data.
    """
    return {
        'id': transaction.id,
        'user_id': transaction.user_id,
        'date': transaction.date.isoformat() if transaction.date else None,
        'transaction_type': transaction.transaction_type,
        'original_partner': transaction.original_partner,
        'amount': transaction.amount,
        'currency': transaction.currency,
        'account': transaction.account or 'unknown',
        'deduplication_hash': transaction.deduplication_hash,
        'category_id': transaction.category_id,
        'partner': transaction.partner,
        'notice': transaction.notice,
        'confidence': transaction.confidence,
        'created_at': transaction.created_at.isoformat() if transaction.created_at else None,
        'updated_at': transaction.updated_at.isoformat() if transaction.updated_at else None
    }


@v2_bp.route('/transactions/<int:transaction_id>', methods=['PUT'])
@require_authentication
@require_csrf
def update_transaction_entity(transaction_id: int) -> tuple[Response, int]:
    """PUT /api/v2/transactions/<transaction_id> - Update a Transaction entity.

    Updates an individual Transaction entity that belongs to the authenticated user.
    Only non-deduplication fields can be updated (category_id, partner, notice, confidence).

    When updating category/partner/notice, this automatically creates or updates
    a Correction entry for the original_partner to ensure future uploads
    with the same merchant get the same corrections applied.

    Args:
        transaction_id: Transaction identifier.

    Request Body (JSON):
        category_id (str, optional): New category identifier.
        partner (str, optional): New corrected partner name.
        notice (str, optional): New transaction notice/comment.
        confidence (float, optional): New confidence score.

    Returns:
        Updated Transaction entity data.

    Status Codes:
        200: Successfully updated transaction.
        400: Bad request (invalid data).
        401: Not authenticated.
        403: Forbidden (transaction belongs to another user).
        404: Transaction not found.
        500: Internal server error.
    """
    user = cast(UserDB, request.user)  # type: ignore[attr-defined]

    try:
        data = request.get_json()

        # Validate and extract update data
        result = _validate_update_transaction_data(data)
        if result[1] is not None:
            return result[1], result[2]
        update_data: dict[str, Any] = cast(dict[str, Any], result[0])

        # Get transaction and verify
        transaction_repo = _get_transaction_repository()
        transaction = transaction_repo.find_by_id(transaction_id)

        if not transaction:
            return jsonify({'error': 'Transaction not found'}), 404

        if transaction.user_id != cast(int, user.id):  # type: ignore[arg-type]
            return jsonify({'error': 'Transaction does not belong to you'}), 403

        # Update transaction
        transaction_repo.update(transaction_id, **update_data)

        # Get updated transaction
        updated_transaction = transaction_repo.find_by_id(transaction_id)
        if not updated_transaction:
            return jsonify({'error': 'Failed to update transaction'}), 500

        # Handle correction update/creation
        _handle_correction_update(user, transaction, data)

        # Format and return response
        response_data = _format_transaction_response(updated_transaction)
        return jsonify(response_data), 200

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@v2_bp.route('/transactions/<int:transaction_id>', methods=['DELETE'])
@require_authentication
@require_csrf
def delete_transaction_entity(transaction_id: int) -> tuple[Response, int]:
    """DELETE /api/v2/transactions/<transaction_id> - Delete a Transaction entity.

    Deletes an individual Transaction entity that belongs to the authenticated user.
    Requires authentication and CSRF protection.

    Args:
        transaction_id: Transaction identifier.

    Returns:
        Success message.

    Status Codes:
        200: Successfully deleted transaction.
        401: Not authenticated.
        403: Forbidden (transaction belongs to another user).
        404: Transaction not found.
        500: Internal server error.
    """
    user = cast(UserDB, request.user)  # type: ignore[attr-defined]

    try:
        transaction_repo = _get_transaction_repository()
        transaction = transaction_repo.find_by_id(transaction_id)

        if not transaction:
            return jsonify({'error': 'Transaction not found'}), 404

        # Verify ownership
        if transaction.user_id != cast(int, user.id):  # type: ignore[arg-type]
            return jsonify({'error': 'Transaction does not belong to you'}), 403

        # Delete transaction
        transaction_repo.delete(transaction_id)

        return jsonify({'message': 'Transaction deleted successfully'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Correction CRUD endpoints - User correction management

@v2_bp.route('/corrections', methods=['GET'])
@require_authentication
def list_corrections() -> tuple[Response, int]:
    """GET /api/v2/corrections - List all corrections for authenticated user.

    Returns a paginated list of user corrections with optional filtering.

    Query Parameters:
        limit (int): Maximum number of corrections to return (default: 100).
        offset (int): Pagination offset (default: 0).
        original_partner (str): Filter by original partner name.

    Returns:
        ListCorrectionsResponse: Paginated list of corrections.

    Status Codes:
        200: Successfully retrieved corrections.
        401: Not authenticated.
        500: Internal server error.
    """
    user = cast(UserDB, request.user)  # type: ignore[attr-defined]

    try:
        # Parse query parameters
        limit = int(request.args.get('limit', 100))
        offset = int(request.args.get('offset', 0))
        original_partner = request.args.get('original_partner')

        correction_repo = _get_correction_repository()

        # Get corrections for user
        if original_partner:
            # Filter by original partner
            correction = correction_repo.find_by_user_and_original_partner(
                cast(int, user.id), original_partner  # type: ignore[arg-type]
            )
            corrections = [correction] if correction else []
            total_count = len(corrections)
        else:
            # Get all corrections for user
            corrections = correction_repo.find_by_user_id(
                cast(int, user.id)  # type: ignore[arg-type]
            )
            total_count = len(corrections)

        # Apply pagination
        corrections = corrections[offset:offset + limit]

        response_data = {
            'corrections': [
                {
                    'id': c.id,
                    'user_id': c.user_id,
                    'original_partner': c.original_partner,
                    'corrected_partner': c.corrected_partner,
                    'corrected_category_id': c.corrected_category_id,
                    'corrected_notice': c.corrected_notice,
                    'created_at': c.created_at.isoformat() if c.created_at else None,
                    'updated_at': c.updated_at.isoformat() if c.updated_at else None
                }
                for c in corrections
            ],
            'total_count': total_count,
            'limit': limit,
            'offset': offset
        }

        return jsonify(response_data), 200

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Correction CRUD endpoints - User correction management

@v2_bp.route('/corrections/<int:correction_id>', methods=['GET'])
@require_authentication
def get_correction(correction_id: int) -> tuple[Response, int]:
    """GET /api/v2/corrections/<correction_id> - Get a specific correction by ID.

    Returns the correction if it belongs to the authenticated user.

    Args:
        correction_id: Correction identifier.

    Returns:
        CorrectionApiResponse: Correction data.

    Status Codes:
        200: Successfully retrieved correction.
        401: Not authenticated.
        403: Forbidden (correction belongs to another user).
        404: Correction not found.
        500: Internal server error.
    """
    user = cast(UserDB, request.user)  # type: ignore[attr-defined]

    try:
        correction_repo = _get_correction_repository()
        correction = correction_repo.find_by_id(correction_id)

        if not correction:
            return jsonify({'error': 'Correction not found'}), 404

        # Verify ownership
        if correction.user_id != cast(int, user.id):  # type: ignore[arg-type]
            return jsonify({'error': 'Correction does not belong to you'}), 403

        response_data = {
            'id': correction.id,
            'user_id': correction.user_id,
            'original_partner': correction.original_partner,
            'corrected_partner': correction.corrected_partner,
            'corrected_category_id': correction.corrected_category_id,
            'corrected_notice': correction.corrected_notice,
            'created_at': correction.created_at.isoformat() if correction.created_at else None,
            'updated_at': correction.updated_at.isoformat() if correction.updated_at else None
        }

        return jsonify(response_data), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@v2_bp.route('/corrections', methods=['POST'])
@require_authentication
@require_csrf
def create_correction() -> tuple[Response, int]:
    """POST /api/v2/corrections - Create a new correction.

    Creates a new correction entry for the authenticated user.
    Requires authentication and CSRF protection.

    Request Body (JSON):
        original_partner (str, required): Original partner name to correct.
        corrected_partner (str, optional): Corrected partner name.
        corrected_category_id (str, optional): Corrected category ID.
        corrected_notice (str, optional): Corrected notice.

    Returns:
        CorrectionApiResponse: Created correction data.

    Status Codes:
        201: Successfully created correction.
        400: Bad request (missing required fields, invalid data).
        401: Not authenticated.
        409: Conflict (correction already exists).
        500: Internal server error.
    """
    user = cast(UserDB, request.user)  # type: ignore[attr-defined]

    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        # Validate required fields
        if 'original_partner' not in data:
            return jsonify({'error': 'original_partner is required'}), 400

        correction_repo = _get_correction_repository()
        from whatsthedamage.models.database.correction import Correction as CorrectionDB

        # Check if correction already exists for this user and partner
        existing = correction_repo.find_by_user_and_original_partner(
            cast(int, user.id), data['original_partner']  # type: ignore[arg-type]
        )
        if existing:
            return jsonify({
                'error': 'Correction for this partner already exists',
                'code': 'DUPLICATE_CORRECTION'
            }), 409

        # Create new correction
        correction = CorrectionDB(
            user_id=cast(int, user.id),  # type: ignore[arg-type]
            original_partner=data['original_partner'],
            corrected_partner=data.get('corrected_partner'),
            corrected_category_id=data.get('corrected_category_id'),
            corrected_notice=data.get('corrected_notice')
        )

        saved_correction = correction_repo.create(correction)

        response_data = {
            'id': saved_correction.id,
            'user_id': saved_correction.user_id,
            'original_partner': saved_correction.original_partner,
            'corrected_partner': saved_correction.corrected_partner,
            'corrected_category_id': saved_correction.corrected_category_id,
            'corrected_notice': saved_correction.corrected_notice,
            'created_at': saved_correction.created_at.isoformat() if saved_correction.created_at else None,
            'updated_at': saved_correction.updated_at.isoformat() if saved_correction.updated_at else None
        }

        return jsonify(response_data), 201

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@v2_bp.route('/corrections/<int:correction_id>', methods=['PUT'])
@require_authentication
@require_csrf
def update_correction(correction_id: int) -> tuple[Response, int]:
    """PUT /api/v2/corrections/<correction_id> - Update a correction.

    Updates a correction that belongs to the authenticated user.
    Requires authentication and CSRF protection.

    Args:
        correction_id: Correction identifier.

    Request Body (JSON):
        corrected_partner (str, optional): New corrected partner name.
        corrected_category_id (str, optional): New corrected category ID.
        corrected_notice (str, optional): New corrected notice.

    Returns:
        CorrectionApiResponse: Updated correction data.

    Status Codes:
        200: Successfully updated correction.
        400: Bad request (invalid data).
        401: Not authenticated.
        403: Forbidden (correction belongs to another user).
        404: Correction not found.
        500: Internal server error.
    """
    user = cast(UserDB, request.user)  # type: ignore[attr-defined]

    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        correction_repo = _get_correction_repository()
        correction = correction_repo.find_by_id(correction_id)

        if not correction:
            return jsonify({'error': 'Correction not found'}), 404

        # Verify ownership
        if correction.user_id != cast(int, user.id):  # type: ignore[arg-type]
            return jsonify({'error': 'Correction does not belong to you'}), 403

        # Collect update data
        update_data: dict[str, Any] = {}
        if 'corrected_partner' in data:
            update_data['corrected_partner'] = data['corrected_partner']
        if 'corrected_category_id' in data:
            update_data['corrected_category_id'] = data['corrected_category_id']
        if 'corrected_notice' in data:
            update_data['corrected_notice'] = data['corrected_notice']

        if not update_data:
            return jsonify({'error': 'No valid fields to update'}), 400

        # Update correction
        correction_repo.update(correction_id, **update_data)

        # Get updated correction
        updated_correction = correction_repo.find_by_id(correction_id)

        if not updated_correction:
            return jsonify({'error': 'Failed to update correction'}), 500

        response_data = {
            'id': updated_correction.id,
            'user_id': updated_correction.user_id,
            'original_partner': updated_correction.original_partner,
            'corrected_partner': updated_correction.corrected_partner,
            'corrected_category_id': updated_correction.corrected_category_id,
            'corrected_notice': updated_correction.corrected_notice,
            'created_at': updated_correction.created_at.isoformat() if updated_correction.created_at else None,
            'updated_at': updated_correction.updated_at.isoformat() if updated_correction.updated_at else None
        }

        return jsonify(response_data), 200

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@v2_bp.route('/corrections/<int:correction_id>', methods=['DELETE'])
@require_authentication
@require_csrf
def delete_correction(correction_id: int) -> tuple[Response, int]:
    """DELETE /api/v2/corrections/<correction_id> - Delete a correction.

    Deletes a correction that belongs to the authenticated user.
    Requires authentication and CSRF protection.

    Args:
        correction_id: Correction identifier.

    Returns:
        Success message.

    Status Codes:
        200: Successfully deleted correction.
        401: Not authenticated.
        403: Forbidden (correction belongs to another user).
        404: Correction not found.
        500: Internal server error.
    """
    user = cast(UserDB, request.user)  # type: ignore[attr-defined]

    try:
        correction_repo = _get_correction_repository()
        correction = correction_repo.find_by_id(correction_id)

        if not correction:
            return jsonify({'error': 'Correction not found'}), 404

        # Verify ownership
        if correction.user_id != cast(int, user.id):  # type: ignore[arg-type]
            return jsonify({'error': 'Correction does not belong to you'}), 403

        # Delete correction
        correction_repo.delete(correction_id)

        return jsonify({'message': 'Correction deleted successfully'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500
