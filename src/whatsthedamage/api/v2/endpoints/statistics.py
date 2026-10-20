"""Statistics endpoints.

Statistical highlight recalculation over persisted transactions.
"""

from typing import cast

from flask import Blueprint, Response, jsonify, request
from werkzeug.exceptions import BadRequest

from whatsthedamage.api.auth_decorators import require_authentication, require_csrf
from whatsthedamage.api.helpers import (
    handle_error,
    _get_statistical_service,
    _get_transaction_repository,
)
from whatsthedamage.models.api.responses import RecalculateApiResponse
from whatsthedamage.models.database.user import User as UserDB

statistics_bp = Blueprint('api_v2_statistics', __name__)


@statistics_bp.route('/recalculate-statistics', methods=['POST'])
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
