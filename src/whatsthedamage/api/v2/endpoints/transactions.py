"""Transaction entity endpoints.

Direct Transaction entity CRUD (scoped to the authenticated user)
plus the drilldown aggregation endpoint.
"""

from typing import Any, Optional, cast

from flask import Blueprint, Response, jsonify, request

from whatsthedamage.api.auth_decorators import require_authentication, require_csrf
from whatsthedamage.api.helpers import (
    handle_error,
    _get_correction_repository,
    _get_correction_service,
    _get_deduplication_service,
    _get_statistical_service,
    _get_transaction_repository,
)
from whatsthedamage.models.api.responses import TransactionApi
from whatsthedamage.models.database.user import User as UserDB
from whatsthedamage.models.database.transaction import (
    Transaction as TransactionDB
)
from whatsthedamage.utils.date_converter import DateConverter

transactions_bp = Blueprint('api_v2_transactions', __name__)


def _transaction_to_dict(t: TransactionDB) -> dict[str, Any]:
    """Serialize a Transaction entity for JSON responses.

    Args:
        t: Transaction entity.

    Returns:
        Dictionary matching the TransactionListItem type expected by
        the frontend.
    """
    return TransactionApi.model_validate(t).model_dump(mode='json')


def _validate_update_transaction_data(
    data: Any | None
) -> tuple[dict[str, Any] | None, tuple[Response, int] | None]:
    """Validate and extract update data from request.

    Args:
        data: JSON data from request.

    Returns:
        Tuple of (update_data, error_response). If valid, update_data
        contains the fields to update and the apply_to_future flag
        controlling merchant rule creation and error_response is
        None. If invalid, update_data is None and error_response is
        set.
    """
    if not data:
        return None, (jsonify({'error': 'No data provided'}), 400)

    update_data: dict[str, Any] = {}
    valid_fields = {'category_id', 'partner', 'notice', 'confidence'}

    for field in valid_fields:
        if field in data:
            update_data[field] = data[field]

    if not update_data:
        return None, (jsonify({'error': 'No valid fields to update'}), 400)

    apply_to_future = data.get('apply_to_future', True)
    if not isinstance(apply_to_future, bool):
        return None, (
            jsonify({'error': 'apply_to_future must be a boolean'}), 400
        )
    update_data['apply_to_future'] = apply_to_future

    return update_data, None


@transactions_bp.route('/transactions', methods=['GET'])
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
        result_id = request.args.get('result_id')

        # Parse amount filters
        min_amount: Optional[float] = None
        max_amount: Optional[float] = None
        raw_min = request.args.get('min_amount')
        if raw_min:
            min_amount = float(raw_min)
        raw_max = request.args.get('max_amount')
        if raw_max:
            max_amount = float(raw_max)

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
            result_id=result_id,
            limit=limit,
            offset=offset,
            sort_by=sort_by,
            sort_order=sort_order
        )

        # Build response
        response_data = {
            'transactions': [
                _transaction_to_dict(t) for t in transactions
            ],
            'total_count': total_count,
            'limit': limit,
            'offset': offset
        }

        return jsonify(response_data), 200

    except Exception as e:
        return handle_error(e)


@transactions_bp.route('/transactions/aggregate', methods=['GET'])
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
        group_by = request.args.get('group_by')

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

        statistical_service = _get_statistical_service()
        try:
            groups = statistical_service.group_transactions(
                transactions, group_by
            )
        except ValueError:
            return jsonify(
                {'error': f'Invalid group_by value: {group_by}'}
            ), 400

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

        scope_transactions = transaction_repo.find_all_by_user(
            user_id=cast(int, user.id),  # type: ignore[arg-type]
            result_id=result_id,
            account=account
        )
        highlights = statistical_service.compute_group_highlights(
            scope_transactions,
            groups,
            algorithms=algorithms,
            direction=direction
        )

        # Serialize TransactionDB objects to dictionaries for JSON response
        serialized_groups: dict[str, list[dict[str, Any]]] = {
            group_key: [_transaction_to_dict(t) for t in txns]
            for group_key, txns in groups.items()
        }

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
        return handle_error(e)


@transactions_bp.route('/transactions/<int:transaction_id>', methods=['GET'])
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
        404: Transaction not found (or belongs to another user).
        500: Internal server error.
    """
    user = cast(UserDB, request.user)  # type: ignore[attr-defined]

    try:
        transaction_repo = _get_transaction_repository()
        transaction = transaction_repo.find_by_user_and_id(
            cast(int, user.id), transaction_id  # type: ignore[arg-type]
        )

        if not transaction:
            return jsonify({'error': 'Transaction not found'}), 404

        return jsonify(_transaction_to_dict(transaction)), 200

    except Exception as e:
        return handle_error(e)


@transactions_bp.route('/transactions', methods=['POST'])
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
        apply_to_future (bool, optional): Whether provided partner/category
            values also upsert a merchant rule for future uploads
            (default: true). Notice values never create rules.

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
            original_category_id=data.get('category_id'),
            original_notice=data.get('notice'),
            confidence=data.get('confidence')
        )

        saved_transaction = transaction_repo.create(transaction)

        _apply_transaction_create_rule(user, data)

        return jsonify(_transaction_to_dict(saved_transaction)), 201

    except Exception as e:
        return handle_error(e)


def _apply_transaction_create_rule(
    user: UserDB,
    data: dict[str, Any]
) -> None:
    """Upsert the merchant rule for a rule-mode transaction create.

    In rule mode (apply_to_future, default true), provided partner and
    category values also upsert a merchant rule so future uploads with
    the same partner get the same values. Notices are per-transaction
    and never create rules. When the user opted in to sharing, the
    resulting rule is contributed to the shared corrections.

    Args:
        user: Authenticated user.
        data: Request data containing the created transaction fields.
    """
    apply_to_future = data.get('apply_to_future', True)
    rule_fields = data.get('partner') or data.get('category_id')
    if not apply_to_future or not rule_fields:
        return

    correction_service = _get_correction_service()
    correction_service.upsert_rule(
        user_id=cast(int, user.id),  # type: ignore[arg-type]
        original_partner=data['original_partner'],
        corrected_partner=data.get('partner'),
        corrected_category_id=data.get('category_id')
    )
    correction_service.share_rule_if_opted_in(
        user, cast(str, data['original_partner'])
    )


def _apply_transaction_update_rule(
    user: UserDB,
    transaction: TransactionDB,
    data: dict[str, Any],
    apply_to_future: bool
) -> None:
    """Upsert the merchant rule for a rule-mode transaction correction.

    Partner and category corrections upsert the merchant rule only in
    rule mode (apply_to_future); in exception mode the rule table is
    left untouched and the correction applies to the edited transaction
    only. Notice corrections never create rules.

    Args:
        user: Authenticated user.
        transaction: Transaction being updated.
        data: Request data containing update fields.
        apply_to_future: Whether the correction should become a
            merchant rule for future uploads.
    """
    if not apply_to_future:
        return

    if 'partner' not in data and 'category_id' not in data:
        return

    correction_service = _get_correction_service()
    correction_service.upsert_rule(
        user_id=cast(int, user.id),  # type: ignore[arg-type]
        original_partner=cast(str, transaction.original_partner),
        corrected_partner=data.get('partner'),
        corrected_category_id=data.get('category_id')
    )
    correction_service.share_rule_if_opted_in(
        user, cast(str, transaction.original_partner)
    )


@transactions_bp.route('/transactions/<int:transaction_id>', methods=['PUT'])
@require_authentication
@require_csrf
def update_transaction_entity(transaction_id: int) -> tuple[Response, int]:
    """PUT /api/v2/transactions/<transaction_id> - Update a Transaction entity.

    Updates an individual Transaction entity that belongs to the authenticated user.
    Only non-deduplication fields can be updated (category_id, partner, notice, confidence).

    With apply_to_future enabled (default), partner and category corrections
    also upsert a merchant rule for the original_partner so future uploads
    with the same merchant get the same corrections applied. With
    apply_to_future disabled, or for notice corrections, the change applies
    to the edited transaction only. The pre-correction category and notice
    values are captured in the original_* columns on first overwrite.

    Args:
        transaction_id: Transaction identifier.

    Request Body (JSON):
        category_id (str, optional): New category identifier.
        partner (str, optional): New corrected partner name.
        notice (str, optional): New transaction notice/comment.
        confidence (float, optional): New confidence score.
        apply_to_future (bool, optional): Whether partner/category
            corrections become a merchant rule for future uploads
            (default: true).

    Returns:
        Updated Transaction entity data.

    Status Codes:
        200: Successfully updated transaction.
        400: Bad request (invalid data).
        401: Not authenticated.
        404: Transaction not found (or belongs to another user).
        500: Internal server error.
    """
    user = cast(UserDB, request.user)  # type: ignore[attr-defined]

    try:
        data = request.get_json()

        # Validate and extract update data
        update_data, error_response = _validate_update_transaction_data(data)
        if error_response is not None:
            return error_response
        assert update_data is not None

        # Get transaction (scoped to the user)
        transaction_repo = _get_transaction_repository()
        transaction = transaction_repo.find_by_user_and_id(
            cast(int, user.id), transaction_id  # type: ignore[arg-type]
        )

        if not transaction:
            return jsonify({'error': 'Transaction not found'}), 404

        # Update transaction, capturing the original category/notice on
        # first overwrite so original-vs-corrected display and undo
        # remain possible
        apply_to_future = update_data.pop('apply_to_future')
        capture_data: dict[str, Any] = {}
        original_category_id = cast(
            Optional[str], transaction.original_category_id
        )
        original_notice = cast(Optional[str], transaction.original_notice)
        if 'category_id' in update_data and original_category_id is None:
            capture_data['original_category_id'] = transaction.category_id
        if 'notice' in update_data and original_notice is None:
            capture_data['original_notice'] = transaction.notice

        transaction_repo.update(transaction_id, **capture_data, **update_data)

        # Get updated transaction
        updated_transaction = transaction_repo.find_by_id(transaction_id)
        if not updated_transaction:
            return jsonify({'error': 'Failed to update transaction'}), 500

        # Handle correction update/creation
        _apply_transaction_update_rule(user, transaction, data, apply_to_future)

        return jsonify(_transaction_to_dict(updated_transaction)), 200

    except Exception as e:
        return handle_error(e)


@transactions_bp.route('/transactions/<int:transaction_id>/undo', methods=['POST'])
@require_authentication
@require_csrf
def undo_transaction_entity(transaction_id: int) -> tuple[Response, int]:
    """POST /api/v2/transactions/<transaction_id>/undo - Undo corrections.

    Restores the correctable fields (category, partner, notice) of a
    Transaction entity from the original values captured at upload or on
    the first correction. The original_partner column always holds the
    original merchant, so the corrected partner is restored to NULL and
    the display falls back to it.

    The merchant rule (correction entity) matching the transaction's
    original_partner is also deleted, so future uploads of this merchant
    are no longer auto-corrected. Other existing transactions of the same
    merchant keep their applied values; rules apply at upload time to
    newly stored rows only.

    Undo is idempotent: restoring a transaction without corrections
    returns its current values unchanged.

    Args:
        transaction_id: Transaction identifier.

    Returns:
        Restored Transaction entity data.

    Status Codes:
        200: Successfully restored the transaction.
        401: Not authenticated.
        404: Transaction not found (or belongs to another user).
        500: Internal server error.
    """
    user = cast(UserDB, request.user)  # type: ignore[attr-defined]

    try:
        transaction_repo = _get_transaction_repository()
        transaction = transaction_repo.find_by_user_and_id(
            cast(int, user.id), transaction_id  # type: ignore[arg-type]
        )

        if not transaction:
            return jsonify({'error': 'Transaction not found'}), 404

        transaction_repo.update(
            transaction_id,
            category_id=transaction.original_category_id,
            partner=None,
            notice=transaction.original_notice
        )

        # Delete the merchant rule of the undone transaction so future
        # uploads of this merchant are no longer auto-corrected
        correction_repo = _get_correction_repository()
        correction = correction_repo.find_by_user_and_original_partner(
            cast(int, user.id),  # type: ignore[arg-type]
            cast(str, transaction.original_partner)
        )
        if correction:
            correction_repo.delete(cast(int, correction.id))

        restored_transaction = transaction_repo.find_by_id(transaction_id)
        if not restored_transaction:
            return jsonify({'error': 'Failed to undo transaction'}), 500

        return jsonify(_transaction_to_dict(restored_transaction)), 200

    except Exception as e:
        return handle_error(e)


@transactions_bp.route('/transactions/<int:transaction_id>', methods=['DELETE'])
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
        404: Transaction not found (or belongs to another user).
        500: Internal server error.
    """
    user = cast(UserDB, request.user)  # type: ignore[attr-defined]

    try:
        transaction_repo = _get_transaction_repository()
        transaction = transaction_repo.find_by_user_and_id(
            cast(int, user.id), transaction_id  # type: ignore[arg-type]
        )

        if not transaction:
            return jsonify({'error': 'Transaction not found'}), 404

        transaction_repo.delete(transaction_id)

        return jsonify({'message': 'Transaction deleted successfully'}), 200

    except Exception as e:
        return handle_error(e)
