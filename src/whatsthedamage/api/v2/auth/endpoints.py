"""Authentication API endpoints.

Provides REST API endpoints for user authentication including:
- Registration (POST /api/v2/auth/register)
- Login (POST /api/v2/auth/login)
- Logout (POST /api/v2/auth/logout)
- Current user (GET /api/v2/auth/me)
- Update account data (PUT /api/v2/auth/me)
- Change password (PUT /api/v2/auth/me/password)
- Data export (GET /api/v2/auth/me/export)
- Account deletion (DELETE /api/v2/auth/account)
- CSRF token (GET /api/v2/auth/csrf-token)
"""

from datetime import datetime, UTC
from flask import Blueprint, current_app, request, jsonify, Response
from typing import Any, Optional, Tuple, cast
from werkzeug.exceptions import BadRequest

from whatsthedamage.services.account_service import AccountService
from whatsthedamage.services.auth_session_service import AuthSessionService
from whatsthedamage.services.auth_errors import (
    AccountDeletionPendingError,
    AccountInactiveError,
    InvalidCredentialsError,
    InvalidPasswordError,
    PasswordTooWeakError,
    UsernameExistsError,
)
from whatsthedamage.services.rate_limit_service import RateLimitService
from whatsthedamage.config.auth_config import get_auth_config
from whatsthedamage.models.database.user import User as UserDB
from whatsthedamage.api.auth_decorators import require_auth_and_csrf
from whatsthedamage.api.helpers import json_error_response
from whatsthedamage.api.middleware import (
    PUBLIC_AUTH_ROUTES,
    get_client_ip,
    rate_limit_response,
    register_api_middleware,
)
from whatsthedamage.utils.logging import get_logger

logger = get_logger(__name__)

# Create auth blueprint
auth_bp = Blueprint('auth', __name__, url_prefix='/api/v2/auth')

# Guard auth routes with rate limiting and require a session on all
# of them except the public routes in PUBLIC_AUTH_ROUTES.
register_api_middleware(auth_bp, PUBLIC_AUTH_ROUTES)


def _get_auth_service() -> AuthSessionService:
    """Get the AuthSessionService instance from Flask extensions.

    Returns:
        AuthSessionService instance.

    Raises:
        RuntimeError: If the service is not available.
    """
    auth_service = current_app.extensions.get('auth_service')
    if auth_service is None:
        raise RuntimeError("Authentication service not available")
    return cast(AuthSessionService, auth_service)


def _get_account_service() -> AccountService:
    """Get the AccountService instance from Flask extensions.

    Returns:
        AccountService instance.

    Raises:
        RuntimeError: If the service is not available.
    """
    account_service = current_app.extensions.get('account_service')
    if account_service is None:
        raise RuntimeError("Account service not available")
    return cast(AccountService, account_service)


def _get_rate_limit_service() -> RateLimitService:
    """Get the RateLimitService instance from Flask extensions.

    Returns:
        RateLimitService instance.

    Raises:
        RuntimeError: If rate limit service is not available.
    """
    rate_limit_service = current_app.extensions.get('rate_limit_service')
    if rate_limit_service is None:
        raise RuntimeError("Rate limit service not available")
    return cast(RateLimitService, rate_limit_service)


def _get_user_agent() -> str:
    """Get client user agent from request.

    Returns:
        User agent string, truncated to 512 characters.
    """
    ua = request.user_agent.string if request.user_agent else ''
    return ua[:512]


def _cookie_kwargs() -> dict[str, Any]:
    """Common attributes of the session cookie.

    Uses the configured SameSite and Secure values; on localhost the
    cookie domain is pinned to 'localhost' so it works across the
    dev ports (3000, 5000), with Lax and non-Secure cookies because
    the Vite proxy makes frontend and backend same-origin.

    Returns:
        Keyword arguments for Flask's set_cookie / delete_cookie.
    """
    if request.host == 'localhost' or request.host.startswith('localhost:'):
        return {'domain': 'localhost', 'samesite': 'Lax', 'secure': False}

    auth_config = get_auth_config()
    return {
        'domain': None,
        'samesite': auth_config.SESSION_COOKIE_SAMESITE,
        'secure': auth_config.SESSION_COOKIE_SECURE
    }


def _set_session_cookie(
    response: Response,
    token: str,
    expires: datetime,
    remember_me: bool = False
) -> Response:
    """Set HttpOnly session cookie.

    Args:
        response: Flask response to set cookie on.
        token: Session token value.
        expires: Token expiration datetime.
        remember_me: Whether to use extended expiration.

    Returns:
        Response with session cookie set.
    """
    # Calculate max age based on expiration
    max_age_seconds = (expires - datetime.now(UTC)).total_seconds()
    max_age = int(max_age_seconds)
    if max_age <= 0:
        max_age = get_auth_config().SESSION_TOKEN_LENGTH

    response.set_cookie(
        'session_token',
        value=token,
        httponly=True,
        max_age=max_age,
        expires=expires,
        path='/',
        **_cookie_kwargs()
    )
    return response


def _clear_session_cookie(response: Response) -> Response:
    """Clear the session cookie.

    Args:
        response: Flask response to clear cookie from.

    Returns:
        Response with session cookie cleared.
    """
    response.delete_cookie(
        'session_token',
        path='/',
        httponly=True,
        **_cookie_kwargs()
    )
    return response


def _set_csrf_cookie(response: Response, token: str) -> Response:
    """Set the readable CSRF token cookie.

    The cookie is deliberately not HttpOnly because the SPA must read
    the token to send it in the X-CSRF-Token header. An XSS payload
    can already drive requests as the user in-page, so readability
    adds no new capability; the win over persisting the token on the
    client is that its lifetime is tied to the session and every tab
    of the origin immediately sees a rotated token.

    Args:
        response: Flask response to set cookie on.
        token: CSRF token value.

    Returns:
        Response with the CSRF cookie set.
    """
    response.set_cookie(
        'csrf_token',
        value=token,
        httponly=False,
        path='/',
        **_cookie_kwargs()
    )
    return response


def _clear_csrf_cookie(response: Response) -> Response:
    """Clear the CSRF token cookie.

    Args:
        response: Flask response to clear cookie from.

    Returns:
        Response with the CSRF cookie cleared.
    """
    response.delete_cookie(
        'csrf_token',
        path='/',
        httponly=False,
        **_cookie_kwargs()
    )
    return response


def _to_iso(value: Any) -> Optional[str]:
    """Serialize a datetime-or-string value as an ISO 8601 string.

    Args:
        value: DateTime, string, or None.

    Returns:
        ISO 8601 string, the original string, or None.
    """
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


def _user_payload(user: UserDB) -> dict[str, Any]:
    """Build the API representation of a user.

    Args:
        user: User entity.

    Returns:
        Dictionary of user attributes for API responses.
    """
    return {
        'id': int(user.id) if user.id is not None else 0,
        'username': user.username,
        'created_at': _to_iso(user.created_at),
        'last_login_at': _to_iso(user.last_login_at),
        'is_active': user.is_active,
        'opt_in_sharing': user.opt_in_sharing,
        'opted_in_at': _to_iso(user.opted_in_at),
        'opted_out_at': _to_iso(user.opted_out_at),
        'scheduled_deletion_at': _to_iso(user.scheduled_deletion_at)
    }


@auth_bp.route('/register', methods=['POST'])
def register() -> Tuple[Response, int]:
    """Register a new user account.

    Creates a new user with username and password. Generates a recovery
    code that is displayed only once. Creates an initial session.

    Request JSON:
        {
            "username": "string",
            "password": "string"
        }

    Response JSON:
        {
            "user": {
                "id": int,
                "username": "string",
                "created_at": "ISO8601 timestamp"
            },
            "recovery_code": "string",
            "session_expires_at": "ISO8601 timestamp"
        }

    Set-Cookie:
        session_token (HttpOnly), csrf_token (readable)

    Status Codes:
        201: Successfully registered
        400: Validation error (missing fields, invalid input)
        409: Username already exists
        422: Password too weak
        429: Registration rate limit exceeded

    Note:
        The recovery_code is displayed only once and must be saved by the user.
        It cannot be retrieved later.
    """
    try:
        # Check rate limiting (per IP, before any validation work)
        rate_limit_exceeded, retry_after = _get_rate_limit_service().check_register_rate_limit(
            ip_address=get_client_ip()
        )
        if rate_limit_exceeded:
            return rate_limit_response(retry_after), 429

        data = request.get_json()
        if not data:
            return json_error_response(
                "Request body is required",
                400,
                "MISSING_BODY"
            )

        username = data.get('username')
        password = data.get('password')

        if not username or not isinstance(username, str):
            return json_error_response(
                "Username is required",
                400,
                "MISSING_USERNAME"
            )

        if not password or not isinstance(password, str):
            return json_error_response(
                "Password is required",
                400,
                "MISSING_PASSWORD"
            )

        ip_address = get_client_ip()
        user_agent = _get_user_agent()

        # Register user
        user, recovery_code, session_token, session_expiry, csrf_token = (
            _get_account_service().register_user(
                username=username.strip(),
                password=password,
                ip_address=ip_address,
                user_agent=user_agent
            )
        )

        # Build response (session_token removed for security - only in HttpOnly cookie)
        user_id = int(user.id) if user.id is not None else 0
        created_at_str = user.created_at.isoformat() if user.created_at else None
        response_data: dict[str, Any] = {
            'user': {
                'id': user_id,
                'username': user.username,
                'created_at': created_at_str
            },
            'recovery_code': recovery_code,
            'session_expires_at': session_expiry.isoformat()
        }

        # Create response with session and CSRF cookies
        response = jsonify(response_data)
        response = _set_session_cookie(response, session_token, session_expiry)
        response = _set_csrf_cookie(response, csrf_token)

        return response, 201

    except UsernameExistsError as e:
        return json_error_response(
            str(e), 409, "USERNAME_EXISTS"
        )
    except PasswordTooWeakError as e:
        return json_error_response(
            str(e), 422, "PASSWORD_TOO_WEAK"
        )
    except ValueError as e:
        return json_error_response(
            str(e), 400, "VALIDATION_ERROR"
        )


@auth_bp.route('/login', methods=['POST'])
def login() -> Tuple[Response, int]:
    """Authenticate a user and create a session.

    Verifies username and password, creates a new session token.
    Subject to rate limiting.

    Request JSON:
        {
            "username": "string",
            "password": "string",
            "remember_me": boolean (optional, default false)
        }

    Response JSON:
        {
            "user": {
                "id": int,
                "username": "string",
                "last_login_at": "ISO8601 timestamp or null"
            },
            "session_expires_at": "ISO8601 timestamp"
        }

    Set-Cookie:
        session_token (HttpOnly), csrf_token (readable)

    Status Codes:
        200: Successfully logged in
        400: Validation error (missing fields)
        401: Invalid credentials
        429: Too many login attempts (rate limited)

    Rate Limiting:
        Limited to 5 attempts per 15 minutes per username+IP combination.
        Returns 429 with Retry-After header when limit is exceeded.
    """
    try:
        data = request.get_json()
        if not data:
            return json_error_response(
                "Request body is required",
                400,
                "MISSING_BODY"
            )

        username = data.get('username')
        password = data.get('password')
        remember_me = data.get('rememberMe') or data.get('remember_me', False)

        if not username or not isinstance(username, str):
            return json_error_response(
                "Username is required",
                400,
                "MISSING_USERNAME"
            )

        if not password or not isinstance(password, str):
            return json_error_response(
                "Password is required",
                400,
                "MISSING_PASSWORD"
            )

        # Check rate limiting
        rate_limit_exceeded, retry_after = _get_rate_limit_service().check_login_rate_limit(
            username=username.strip(),
            ip_address=get_client_ip()
        )
        if rate_limit_exceeded:
            return rate_limit_response(retry_after), 429

        ip_address = get_client_ip()
        user_agent = _get_user_agent()

        # Login user
        user, session_token, session_expiry, csrf_token = (
            _get_account_service().login_user(
                username=username.strip(),
                password=password,
                remember_me=remember_me,
                ip_address=ip_address,
                user_agent=user_agent
            )
        )

        # Build response (session_token removed for security - only in HttpOnly cookie)
        user_id = int(user.id) if user.id is not None else 0
        last_login_str = user.last_login_at.isoformat() if user.last_login_at else None
        response_data: dict[str, Any] = {
            'user': {
                'id': user_id,
                'username': user.username,
                'last_login_at': last_login_str
            },
            'session_expires_at': session_expiry.isoformat()
        }

        # Create response with session and CSRF cookies
        response = jsonify(response_data)
        response = _set_session_cookie(
            response, session_token, session_expiry, remember_me
        )
        response = _set_csrf_cookie(response, csrf_token)

        return response, 200

    except InvalidCredentialsError:
        return json_error_response(
            "Invalid username or password", 401, "INVALID_CREDENTIALS"
        )
    except AccountInactiveError:
        return json_error_response(
            "Account is inactive", 403, "ACCOUNT_INACTIVE"
        )
    except AccountDeletionPendingError:
        return json_error_response(
            "Account is scheduled for deletion",
            403,
            "ACCOUNT_DELETION_PENDING"
        )
    except ValueError:
        return json_error_response(
            "Login failed", 401, "AUTHENTICATION_FAILED"
        )
    except Exception:
        logger.exception("Login failed with unexpected exception")
        return json_error_response(
            "Login failed",
            500,
            "INTERNAL_ERROR"
        )


@auth_bp.route('/logout', methods=['POST'])
@require_auth_and_csrf
def logout() -> Tuple[Response, int]:
    """Log out the current user.

    Revokes the current session and clears the session cookie.
    Requires authentication and CSRF token validation.

    Request JSON:
        {} (empty body allowed)

    Request Headers:
        X-CSRF-Token: Valid CSRF token for the current session

    Response JSON:
        {
            "message": "Successfully logged out"
        }

    Status Codes:
        200: Successfully logged out
        401: Not authenticated
        403: Invalid or missing CSRF token
    """
    try:
        # Get session token from cookie (already validated by decorator)
        session_token = request.cookies.get('session_token')

        # Logout user
        if session_token:
            success = _get_auth_service().logout_user(session_token)
        else:
            success = False

        if not success:
            return json_error_response(
                "Session not found",
                401,
                "INVALID_SESSION"
            )

        # Create response with cleared cookies
        response = jsonify({'message': 'Successfully logged out'})
        response = _clear_session_cookie(response)
        response = _clear_csrf_cookie(response)

        return response, 200

    except Exception as e:
        logger.exception("Logout failed with unexpected exception")
        return json_error_response(
            "Logout failed",
            500,
            "INTERNAL_ERROR"
        )


@auth_bp.route('/me', methods=['GET'])
@require_auth_and_csrf
def get_me() -> Tuple[Response, int]:
    """Get current user information.

    The blueprint guard has already validated the session and attached
    the user and session to the request context. Sets a fresh CSRF
    cookie only when the session does not have a token yet; repeat
    calls do not rotate an existing token.

    Response JSON:
        {
            "user": {...}
        }

    Set-Cookie:
        csrf_token (readable), only when a token was minted

    Status Codes:
        200: Authenticated
        401: Not authenticated
        403: Invalid or missing CSRF token
    """
    user = cast(UserDB, request.user)  # type: ignore[attr-defined]
    session = cast(Any, request.session)  # type: ignore[attr-defined]

    csrf_token: Optional[str] = None
    if not session.csrf_token_hash:
        csrf_token = _get_auth_service().refresh_csrf_token(session)

    response = jsonify({'user': _user_payload(user)})
    if csrf_token is not None:
        response = _set_csrf_cookie(response, csrf_token)

    return response, 200


@auth_bp.route('/me', methods=['PUT'])
@require_auth_and_csrf
def update_me() -> Tuple[Response, int]:
    """Update current user account data (right to rectification).

    Updates the authenticated user's username and/or correction
    sharing opt-in preference. Requires authentication and CSRF
    protection.

    Request JSON:
        {
            "username": "string" (optional),
            "opt_in_sharing": boolean (optional)
        }

    At least one field must be present. The consent timestamps
    (opted_in_at / opted_out_at) are recorded with the opt-in
    change for demonstrability (GDPR Art. 7(1)).

    Response JSON:
        {
            "user": {
                "id": int,
                "username": "string",
                "created_at": "ISO8601 timestamp",
                "last_login_at": "ISO8601 timestamp or null",
                "is_active": boolean,
                "opt_in_sharing": boolean,
                "opted_in_at": "ISO8601 timestamp or null",
                "opted_out_at": "ISO8601 timestamp or null",
                "scheduled_deletion_at": "ISO8601 timestamp or null"
            }
        }

    Status Codes:
        200: Successfully updated
        400: Bad request (no valid field present, invalid types)
        401: Not authenticated
        403: Invalid or missing CSRF token
        409: Username already taken
    """
    user = cast(UserDB, request.user)  # type: ignore[attr-defined]

    try:
        data = request.get_json(silent=True)
        if not data:
            return json_error_response(
                "Request body is required",
                400,
                "VALIDATION_ERROR"
            )

        if 'username' not in data and 'opt_in_sharing' not in data:
            return json_error_response(
                "username or opt_in_sharing is required",
                400,
                "VALIDATION_ERROR"
            )

        updated_user: Optional[UserDB] = None

        if 'opt_in_sharing' in data:
            opt_in_sharing = data['opt_in_sharing']
            if not isinstance(opt_in_sharing, bool):
                return json_error_response(
                    "opt_in_sharing must be a boolean",
                    400,
                    "VALIDATION_ERROR"
                )
            updated_user = _get_account_service().update_opt_in_sharing(
                cast(int, user.id), opt_in_sharing
            )

        if 'username' in data:
            new_username = data['username']
            if not isinstance(new_username, str):
                return json_error_response(
                    "username must be a string",
                    400,
                    "VALIDATION_ERROR"
                )
            updated_user = _get_account_service().update_username(
                user, new_username
            )

        if updated_user is None:
            return json_error_response(
                "User not found",
                404,
                "USER_NOT_FOUND"
            )

        return jsonify({'user': _user_payload(updated_user)}), 200

    except UsernameExistsError as e:
        return json_error_response(
            str(e), 409, "USERNAME_EXISTS"
        )
    except ValueError as e:
        return json_error_response(
            str(e), 400, "VALIDATION_ERROR"
        )
    except Exception:
        logger.exception("User settings update failed with unexpected exception")
        return json_error_response(
            "Failed to update user settings",
            500,
            "INTERNAL_ERROR"
        )


@auth_bp.route('/me/password', methods=['PUT'])
@require_auth_and_csrf
def change_password() -> Tuple[Response, int]:
    """Change the current user's password while logged in.

    Verifies the current password, updates the password hash, and
    revokes all other sessions of the user. The current session
    stays valid. Requires authentication and CSRF protection.

    Request JSON:
        {
            "current_password": "string",
            "new_password": "string"
        }

    Request Headers:
        X-CSRF-Token: Valid CSRF token for the current session

    Response JSON:
        {
            "message": "Password changed"
        }

    Status Codes:
        200: Password changed
        400: Validation error (missing fields, new password too weak)
        401: Not authenticated or wrong current password
        403: Invalid or missing CSRF token
        422: New password too short
    """
    user = cast(UserDB, request.user)  # type: ignore[attr-defined]
    session = cast(Any, request.session)  # type: ignore[attr-defined]

    try:
        data = request.get_json(silent=True)
        current_password = data.get('current_password') if data else None
        new_password = data.get('new_password') if data else None

        if not current_password or not isinstance(current_password, str):
            return json_error_response(
                "Current password is required",
                400,
                "MISSING_CURRENT_PASSWORD"
            )

        if not new_password or not isinstance(new_password, str):
            return json_error_response(
                "New password is required",
                400,
                "MISSING_NEW_PASSWORD"
            )

        _get_account_service().change_password(
            user, current_password, new_password, session
        )

        return jsonify({'message': 'Password changed'}), 200

    except PasswordTooWeakError as e:
        return json_error_response(
            str(e), 422, "PASSWORD_TOO_WEAK"
        )
    except InvalidPasswordError:
        return json_error_response(
            "Invalid current password", 401, "INVALID_CREDENTIALS"
        )
    except ValueError as e:
        return json_error_response(
            str(e), 400, "VALIDATION_ERROR"
        )
    except Exception:
        logger.exception("Password change failed with unexpected exception")
        return json_error_response(
            "Failed to change password",
            500,
            "INTERNAL_ERROR"
        )


@auth_bp.route('/me/export', methods=['GET'])
def export_me() -> Tuple[Response, int]:
    """Export all personal data of the current user.

    Returns a single JSON document containing the user's account
    data, processing results, transactions, and corrections
    (right of access and data portability, GDPR Art. 15 and 20).
    Requires authentication. Password and recovery code hashes are
    never included.

    Response:
        JSON attachment with the user's data.

    Status Codes:
        200: Export generated
        401: Not authenticated
        500: Internal server error
    """
    user = cast(UserDB, request.user)  # type: ignore[attr-defined]

    try:
        export_service = current_app.extensions.get('data_export_service')
        if export_service is None:
            return json_error_response(
                "Data export is not available",
                500,
                "INTERNAL_ERROR"
            )

        payload = export_service.build_export(
            cast(int, user.id), _user_payload(user)
        )

        response = jsonify(payload)
        response.headers['Content-Disposition'] = (
            'attachment; filename="whatsthedamage-export.json"'
        )
        return response, 200

    except Exception:
        logger.exception("Data export failed with unexpected exception")
        return json_error_response(
            "Failed to export data",
            500,
            "INTERNAL_ERROR"
        )


@auth_bp.route('/account', methods=['DELETE'])
@require_auth_and_csrf
def delete_account() -> Tuple[Response, int]:
    """Schedule the deletion of the current user's account.

    Verifies the current password, schedules the account deletion
    after the configured grace period (default 7 days), and revokes
    all sessions. Logging in before the scheduled timestamp cancels
    the deletion. After the grace period the retention job deletes
    the account with all transactions, corrections, and processing
    results. When revoke_shared_corrections is true, the user's
    shared correction contributions are also withdrawn (GDPR
    Art. 7(3)); otherwise the anonymized shared corrections are
    retained.

    Request JSON:
        {
            "password": "string",
            "revoke_shared_corrections": boolean (optional,
                default false)
        }

    Request Headers:
        X-CSRF-Token: Valid CSRF token for the current session

    Response JSON:
        {
            "message": "string",
            "scheduled_deletion_at": "ISO8601 timestamp"
        }

    Status Codes:
        200: Account deletion scheduled
        400: Missing password
        401: Not authenticated or wrong password
        403: Invalid or missing CSRF token
    """
    user = cast(UserDB, request.user)  # type: ignore[attr-defined]

    try:
        data = request.get_json(silent=True)
        password = data.get('password') if data else None
        if not password or not isinstance(password, str):
            return json_error_response(
                "Password is required",
                400,
                "MISSING_PASSWORD"
            )

        revoke_shared_corrections = False
        if data and 'revoke_shared_corrections' in data:
            revoke_shared_corrections = (
                data['revoke_shared_corrections']
            )
            if not isinstance(revoke_shared_corrections, bool):
                return json_error_response(
                    "revoke_shared_corrections must be a boolean",
                    400,
                    "VALIDATION_ERROR"
                )

        retention_service = current_app.extensions.get(
            'retention_service'
        )
        if retention_service is None:
            return json_error_response(
                "Account deletion is not available",
                500,
                "INTERNAL_ERROR"
            )

        scheduled_deletion_at = cast(
            Any, retention_service
        ).request_account_deletion(
            user,
            password,
            revoke_shared_corrections=revoke_shared_corrections
        )

        response = jsonify({
            'message': 'Account deletion scheduled',
            'scheduled_deletion_at': scheduled_deletion_at.isoformat()
        })
        response = _clear_session_cookie(response)
        response = _clear_csrf_cookie(response)
        return response, 200

    except InvalidPasswordError:
        return json_error_response(
            "Invalid password", 401, "INVALID_CREDENTIALS"
        )
    except ValueError as e:
        return json_error_response(
            str(e), 400, "VALIDATION_ERROR"
        )
    except Exception:
        logger.exception("Account deletion scheduling failed with unexpected exception")
        return json_error_response(
            "Failed to schedule account deletion",
            500,
            "INTERNAL_ERROR"
        )


@auth_bp.route('/reset-password', methods=['POST'])
def reset_password() -> Tuple[Response, int]:
    """Reset user password using recovery code.

    Allows users to reset their password using the recovery code provided
    during registration. This is a public endpoint that does not require
    authentication. The recovery code is single-use and a new one is generated
    after successful reset.

    Request JSON:
        {
            "username": "string",
            "recovery_code": "string",
            "new_password": "string"
        }

    Response JSON:
        {
            "user": {
                "id": int,
                "username": "string",
                "created_at": "ISO8601 timestamp",
                "last_login_at": "ISO8601 timestamp or null",
                "is_active": boolean,
                "opt_in_sharing": boolean
            },
            "new_recovery_code": "string"
        }

    Status Codes:
        200: Password successfully reset
        400: Validation error (missing fields, invalid input)
        401: Invalid username or recovery code
        422: Password too weak
        429: Too many attempts (rate limited)
        500: Internal server error

    Rate Limiting:
        Limited to 5 attempts per 15 minutes per IP address.
        Returns 429 with Retry-After header when limit is exceeded.

    Security:
        - No CSRF token required (public endpoint)
        - Generic error messages prevent username enumeration
        - All existing sessions are invalidated on password reset
        - Recovery code is single-use (old code invalidated, new one generated)
        - New recovery code displayed once and must be saved by user
    """
    try:
        data = request.get_json()
        if not data:
            return json_error_response(
                "Request body is required",
                400,
                "MISSING_BODY"
            )

        username = data.get('username')
        recovery_code = data.get('recoveryCode')
        new_password = data.get('newPassword')

        # Validate all fields are present and non-empty strings
        if not username or not isinstance(username, str) or not username.strip():
            return json_error_response(
                "Username is required",
                400,
                "MISSING_USERNAME"
            )

        if not recovery_code or not isinstance(recovery_code, str) or not recovery_code.strip():
            return json_error_response(
                "Recovery code is required",
                400,
                "MISSING_RECOVERY_CODE"
            )

        if not new_password or not isinstance(new_password, str) or not new_password.strip():
            return json_error_response(
                "New password is required",
                400,
                "MISSING_NEW_PASSWORD"
            )

        # Check rate limiting (by IP address only, since username may not be valid)
        rate_limit_exceeded, retry_after = _get_rate_limit_service().check_recovery_rate_limit(
            ip_address=get_client_ip()
        )
        if rate_limit_exceeded:
            return rate_limit_response(retry_after), 429

        # Reset password using recovery code
        user, new_formatted_recovery_code = _get_account_service().reset_password_with_recovery_code(
            username=username.strip(),
            recovery_code=recovery_code.strip(),
            new_password=new_password
        )

        # Reset rate limit on successful recovery
        _get_rate_limit_service().reset_recovery_rate_limit(get_client_ip())

        # Build response
        response_data = {
            'user': _user_payload(user),
            'new_recovery_code': new_formatted_recovery_code
        }

        return jsonify(response_data), 200

    except PasswordTooWeakError as e:
        return json_error_response(
            str(e), 422, "PASSWORD_TOO_WEAK"
        )
    except InvalidCredentialsError:
        return json_error_response(
            "Invalid username or recovery code",
            401,
            "INVALID_CREDENTIALS"
        )
    except ValueError:
        return json_error_response(
            "Password reset failed", 401, "AUTHENTICATION_FAILED"
        )
    except Exception as e:
        logger.exception("Password reset failed with unexpected exception")
        return json_error_response(
            "Password reset failed",
            500,
            "INTERNAL_ERROR"
        )


@auth_bp.route('/csrf-token', methods=['GET'])
def get_csrf_token() -> Tuple[Response, int]:
    """Mint a fresh CSRF token for the current session.

    Generates a new CSRF token (invalidating the previously issued
    one) and delivers it as a readable cookie. The cookie is read by
    the SPA and sent back in the X-CSRF-Token header for
    state-changing requests (POST, PUT, DELETE, PATCH).

    Request:
        Requires valid session_token cookie (authenticated user)

    Response JSON:
        {}

    Set-Cookie:
        csrf_token (readable, not HttpOnly)

    Status Codes:
        200: CSRF token cookie set
        401: Not authenticated
    """
    try:
        # Require authenticated session
        session_token = request.cookies.get('session_token')
        if not session_token:
            return json_error_response(
                "No session found",
                401,
                "NOT_AUTHENTICATED"
            )

        # Validate session and mint a token whose hash is persisted, so the
        # delivered cookie actually validates on subsequent requests
        result = _get_auth_service().validate_session(session_token)
        if not result:
            return json_error_response(
                "Invalid or expired session",
                401,
                "INVALID_SESSION"
            )

        user, session = result
        csrf_token = _get_auth_service().refresh_csrf_token(session)
        response = jsonify({})
        response = _set_csrf_cookie(response, csrf_token)
        return response, 200
    except Exception as e:
        logger.exception("CSRF token generation failed with unexpected exception")
        return json_error_response(
            "Failed to generate CSRF token",
            500,
            "INTERNAL_ERROR"
        )
