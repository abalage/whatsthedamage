"""Correction endpoints.

Merchant-rule correction CRUD scoped to the authenticated user.
"""

from typing import Any, Optional, cast

from flask import Blueprint, Response, jsonify, request

from whatsthedamage.api.auth_decorators import require_authentication, require_csrf
from whatsthedamage.api.helpers import (
    handle_error,
    _get_correction_repository,
    _get_correction_service,
)
from whatsthedamage.models.api.responses import CorrectionApi
from whatsthedamage.models.database.correction import (
    Correction as CorrectionDB
)
from whatsthedamage.models.database.user import User as UserDB

corrections_bp = Blueprint('api_v2_corrections', __name__)


def _correction_to_dict(c: CorrectionDB) -> dict[str, Any]:
    """Serialize a Correction entity for JSON responses.

    Args:
        c: Correction entity.

    Returns:
        Dictionary with the correction's data.
    """
    return CorrectionApi.model_validate(c).model_dump(mode='json')


@corrections_bp.route('/corrections', methods=['GET'])
@require_authentication
def list_corrections() -> tuple[Response, int]:
    """GET /api/v2/corrections - List all corrections for authenticated user.

    Returns a paginated list of user corrections with optional filtering.

    Query Parameters:
        limit (int): Maximum number of corrections to return (default: 100).
        offset (int): Pagination offset (default: 0).
        original_partner (str): Filter by original partner name.

    Returns:
        Paginated list of corrections.

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
                _correction_to_dict(c) for c in corrections
            ],
            'total_count': total_count,
            'limit': limit,
            'offset': offset
        }

        return jsonify(response_data), 200

    except Exception as e:
        return handle_error(e)


@corrections_bp.route('/corrections/<int:correction_id>', methods=['GET'])
@require_authentication
def get_correction(correction_id: int) -> tuple[Response, int]:
    """GET /api/v2/corrections/<correction_id> - Get a specific correction by ID.

    Returns the correction if it belongs to the authenticated user.

    Args:
        correction_id: Correction identifier.

    Returns:
        Correction data.

    Status Codes:
        200: Successfully retrieved correction.
        401: Not authenticated.
        404: Correction not found (or belongs to another user).
        500: Internal server error.
    """
    user = cast(UserDB, request.user)  # type: ignore[attr-defined]

    try:
        correction_repo = _get_correction_repository()
        correction = correction_repo.find_by_user_and_id(
            cast(int, user.id), correction_id  # type: ignore[arg-type]
        )

        if not correction:
            return jsonify({'error': 'Correction not found'}), 404

        return jsonify(_correction_to_dict(correction)), 200

    except Exception as e:
        return handle_error(e)


@corrections_bp.route('/corrections', methods=['POST'])
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

    Returns:
        Created correction data.

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
            corrected_category_id=data.get('corrected_category_id')
        )

        saved_correction = correction_repo.create(correction)

        correction_service = _get_correction_service()
        if saved_correction.corrected_category_id:
            correction_service.share_if_opted_in(
                user,
                cast(str, saved_correction.original_partner),
                cast(Optional[str], saved_correction.corrected_partner),
                cast(str, saved_correction.corrected_category_id)
            )

        return jsonify(_correction_to_dict(saved_correction)), 201

    except Exception as e:
        return handle_error(e)


@corrections_bp.route('/corrections/<int:correction_id>', methods=['PUT'])
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

    Returns:
        Updated correction data.

    Status Codes:
        200: Successfully updated correction.
        400: Bad request (invalid data).
        401: Not authenticated.
        404: Correction not found (or belongs to another user).
        500: Internal server error.
    """
    user = cast(UserDB, request.user)  # type: ignore[attr-defined]

    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        correction_repo = _get_correction_repository()
        correction = correction_repo.find_by_user_and_id(
            cast(int, user.id), correction_id  # type: ignore[arg-type]
        )

        if not correction:
            return jsonify({'error': 'Correction not found'}), 404

        # Collect update data
        update_data: dict[str, Any] = {}
        if 'corrected_partner' in data:
            update_data['corrected_partner'] = data['corrected_partner']
        if 'corrected_category_id' in data:
            update_data['corrected_category_id'] = data['corrected_category_id']

        if not update_data:
            return jsonify({'error': 'No valid fields to update'}), 400

        # Update correction
        correction_repo.update(correction_id, **update_data)

        # Get updated correction
        updated_correction = correction_repo.find_by_id(correction_id)

        if not updated_correction:
            return jsonify({'error': 'Failed to update correction'}), 500

        correction_service = _get_correction_service()
        if updated_correction.corrected_category_id:
            correction_service.share_if_opted_in(
                user,
                cast(str, updated_correction.original_partner),
                cast(Optional[str], updated_correction.corrected_partner),
                cast(str, updated_correction.corrected_category_id)
            )

        return jsonify(_correction_to_dict(updated_correction)), 200

    except Exception as e:
        return handle_error(e)


@corrections_bp.route('/corrections/<int:correction_id>', methods=['DELETE'])
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
        404: Correction not found (or belongs to another user).
        500: Internal server error.
    """
    user = cast(UserDB, request.user)  # type: ignore[attr-defined]

    try:
        correction_repo = _get_correction_repository()
        correction = correction_repo.find_by_user_and_id(
            cast(int, user.id), correction_id  # type: ignore[arg-type]
        )

        if not correction:
            return jsonify({'error': 'Correction not found'}), 404

        # Delete correction
        correction_repo.delete(correction_id)

        return jsonify({'message': 'Correction deleted successfully'}), 200

    except Exception as e:
        return handle_error(e)
