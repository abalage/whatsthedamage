"""Authentication API endpoints.

Provides REST API endpoints for user authentication including:
- Registration (POST /api/v2/auth/register)
- Login (POST /api/v2/auth/login)
- Logout (POST /api/v2/auth/logout)
- Current user (GET /api/v2/auth/me)
- CSRF token (GET /api/v2/auth/csrf-token)
"""

import os
from datetime import datetime, UTC
from flask import Blueprint, request, jsonify, make_response, Response
from typing import Any, Optional, Tuple, cast
from werkzeug.exceptions import BadRequest

from whatsthedamage.services.authentication_service import AuthenticationService
from whatsthedamage.services.rate_limit_service import RateLimitService
from whatsthedamage.config.auth_config import get_auth_config

# Create auth blueprint
auth_bp = Blueprint('auth', __name__, url_prefix='/api/v2/auth')

# Global storage for services (initialized in app factory)
_auth_service: Optional[AuthenticationService] = None
_rate_limit_service: Optional[RateLimitService] = None


def init_auth_services(
    auth_service: AuthenticationService,
    rate_limit_service: RateLimitService
) -> None:
    """Initialize authentication services for the blueprint.

    Args:
        auth_service: AuthenticationService instance.
        rate_limit_service: RateLimitService instance.
    """
    global _auth_service, _rate_limit_service
    _auth_service = auth_service
    _rate_limit_service = rate_limit_service


def _get_auth_service() -> AuthenticationService:
    """Get the AuthenticationService instance.

    Returns:
        AuthenticationService instance.

    Raises:
        RuntimeError: If authentication service is not initialized.
    """
    if _auth_service is None:
        raise RuntimeError("Authentication service not initialized")
    return _auth_service


def _get_rate_limit_service() -> RateLimitService:
    """Get the RateLimitService instance.

    Returns:
        RateLimitService instance.

    Raises:
        RuntimeError: If rate limit service is not initialized.
    """
    if _rate_limit_service is None:
        raise RuntimeError("Rate limit service not initialized")
    return _rate_limit_service


def _get_client_ip() -> str:
    """Get client IP address from request.

    Handles X-Forwarded-For header for proxied requests.

    Returns:
        Client IP address string.
    """
    # Check for X-Forwarded-For header (for nginx, load balancers, etc.)
    forwarded_for = request.headers.get('X-Forwarded-For', '')
    if forwarded_for:
        # Take the first IP in the list (original client)
        return forwarded_for.split(',')[0].strip()  # type: ignore[no-any-return]
    remote_addr = request.remote_addr or '0.0.0.0'
    return str(remote_addr)  # type: ignore[no-any-return]


def _get_user_agent() -> str:
    """Get client user agent from request.

    Returns:
        User agent string, truncated to 512 characters.
    """
    ua = request.user_agent.string if request.user_agent else ''
    return ua[:512]


def _set_session_cookie(
    response: Response,
    token: str,
    expires: datetime,
    remember_me: bool = False
) -> Response:
    """Set HttpOnly, Secure, SameSite=Strict session cookie.

    Args:
        response: Flask response to set cookie on.
        token: Session token value.
        expires: Token expiration datetime.
        remember_me: Whether to use extended expiration.

    Returns:
        Response with session cookie set.
    """
    auth_config = get_auth_config()
    
    # Calculate max age based on expiration
    max_age_seconds = (expires - datetime.now(UTC)).total_seconds()
    max_age = int(max_age_seconds)
    if max_age <= 0:
        max_age = auth_config.SESSION_TOKEN_LENGTH

    response.set_cookie(
        'session_token',
        value=token,
        httponly=True,
        secure=auth_config.SESSION_COOKIE_SECURE,
        samesite=auth_config.SESSION_COOKIE_SAMESITE,
        max_age=max_age,
        expires=expires,
        path='/',
        domain=None
    )
    return response


def _clear_session_cookie(response: Response) -> Response:
    """Clear the session cookie.

    Args:
        response: Flask response to clear cookie from.

    Returns:
        Response with session cookie cleared.
    """
    auth_config = get_auth_config()
    response.delete_cookie(
        'session_token',
        path='/',
        domain=None,
        httponly=True,
        secure=auth_config.SESSION_COOKIE_SECURE,
        samesite=auth_config.SESSION_COOKIE_SAMESITE
    )
    return response


def _create_error_response(
    message: str,
    status_code: int = 400,
    error_code: Optional[str] = None,
    retry_after: Optional[int] = None
) -> Tuple[dict[str, Any], int]:
    """Create a standardized error response.

    Args:
        message: Human-readable error message.
        status_code: HTTP status code.
        error_code: Machine-readable error code.
        retry_after: Seconds to wait before retry (for rate limiting).

    Returns:
        Tuple of (error_dict, status_code).
    """
    error_dict: dict[str, Any] = {'error': message}
    if error_code:
        error_dict['code'] = error_code
    if retry_after is not None:
        error_dict['retry_after'] = str(retry_after)
    return error_dict, status_code


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
            "session_token": "string",
            "session_expires_at": "ISO8601 timestamp"
        }

    Status Codes:
        201: Successfully registered
        400: Validation error (missing fields, invalid input)
        409: Username already exists
        422: Password too weak

    Note:
        The recovery_code is displayed only once and must be saved by the user.
        It cannot be retrieved later.
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify(_create_error_response(
                "Request body is required",
                400,
                "MISSING_BODY"
            )[0]), 400

        username = data.get('username')
        password = data.get('password')

        if not username or not isinstance(username, str):
            return jsonify(_create_error_response(
                "Username is required",
                400,
                "MISSING_USERNAME"
            )[0]), 400

        if not password or not isinstance(password, str):
            return jsonify(_create_error_response(
                "Password is required",
                400,
                "MISSING_PASSWORD"
            )[0]), 400

        ip_address = _get_client_ip()
        user_agent = _get_user_agent()

        # Register user
        user, recovery_code, session_token, session_expiry = (
            _get_auth_service().register_user(
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

        # Create response with session cookie
        response = jsonify(response_data)
        response = _set_session_cookie(response, session_token, session_expiry)

        return response, 201

    except ValueError as e:
        error_message = str(e)
        if "already exists" in error_message.lower():
            return jsonify(_create_error_response(
                error_message,
                409,
                "USERNAME_EXISTS"
            )[0]), 409
        elif "password must be at least" in error_message.lower():
            return jsonify(_create_error_response(
                error_message,
                422,
                "PASSWORD_TOO_WEAK"
            )[0]), 422
        else:
            return jsonify(_create_error_response(
                error_message,
                400,
                "VALIDATION_ERROR"
            )[0]), 400


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
            "session_token": "string",
            "session_expires_at": "ISO8601 timestamp"
        }

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
            return jsonify(_create_error_response(
                "Request body is required",
                400,
                "MISSING_BODY"
            )[0]), 400

        username = data.get('username')
        password = data.get('password')
        remember_me = data.get('remember_me', False)

        if not username or not isinstance(username, str):
            return jsonify(_create_error_response(
                "Username is required",
                400,
                "MISSING_USERNAME"
            )[0]), 400

        if not password or not isinstance(password, str):
            return jsonify(_create_error_response(
                "Password is required",
                400,
                "MISSING_PASSWORD"
            )[0]), 400

        # Check rate limiting
        rate_limit_exceeded, retry_after = _get_rate_limit_service().check_login_rate_limit(
            username=username.strip(),
            ip_address=_get_client_ip()
        )
        if rate_limit_exceeded:
            error_response = _create_error_response(
                f"Too many login attempts. Try again in {retry_after} seconds.",
                429,
                "RATE_LIMIT_EXCEEDED",
                retry_after
            )
            response = jsonify(error_response[0])
            response.headers['Retry-After'] = str(retry_after)
            return response, 429

        ip_address = _get_client_ip()
        user_agent = _get_user_agent()

        # Login user
        user, session_token, session_expiry = _get_auth_service().login_user(
            username=username.strip(),
            password=password,
            remember_me=remember_me,
            ip_address=ip_address,
            user_agent=user_agent
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

        # Create response with session cookie
        response = jsonify(response_data)
        response = _set_session_cookie(
            response, session_token, session_expiry, remember_me
        )

        return response, 200

    except ValueError as e:
        error_message = str(e)
        if "invalid username or password" in error_message.lower():
            return jsonify(_create_error_response(
                "Invalid username or password",
                401,
                "INVALID_CREDENTIALS"
            )[0]), 401
        elif "account is inactive" in error_message.lower():
            return jsonify(_create_error_response(
                "Account is inactive",
                403,
                "ACCOUNT_INACTIVE"
            )[0]), 403
        else:
            return jsonify(_create_error_response(
                "Login failed",
                401,
                "AUTHENTICATION_FAILED"
            )[0]), 401
    except Exception as e:
        return jsonify(_create_error_response(
            "Login failed",
            500,
            "INTERNAL_ERROR"
        )[0]), 500


@auth_bp.route('/logout', methods=['POST'])
def logout() -> Tuple[Response, int]:
    """Log out the current user.

    Revokes the current session and clears the session cookie.

    Request JSON:
        {} (empty body allowed)

    Response JSON:
        {
            "message": "Successfully logged out"
        }

    Status Codes:
        200: Successfully logged out
        401: Not authenticated
    """
    try:
        # Get session token from cookie
        session_token = request.cookies.get('session_token')
        if not session_token:
            return jsonify(_create_error_response(
                "No session found",
                401,
                "NOT_AUTHENTICATED"
            )[0]), 401

        # Logout user
        success = _get_auth_service().logout_user(session_token)

        if not success:
            return jsonify(_create_error_response(
                "Session not found",
                401,
                "INVALID_SESSION"
            )[0]), 401

        # Create response with cleared cookie
        response = jsonify({'message': 'Successfully logged out'})
        response = _clear_session_cookie(response)

        return response, 200

    except Exception as e:
        return jsonify(_create_error_response(
            "Logout failed",
            500,
            "INTERNAL_ERROR"
        )[0]), 500


@auth_bp.route('/me', methods=['GET'])
def get_me() -> Tuple[Response, int]:
    """Get current user information.

    Returns information about the currently authenticated user.
    Also returns a CSRF token for use in subsequent requests.

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
            "csrf_token": "string"
        }

    Status Codes:
        200: Authenticated
        401: Not authenticated
    """
    try:
        # Get session token from cookie
        session_token = request.cookies.get('session_token')
        if not session_token:
            return jsonify(_create_error_response(
                "No session found",
                401,
                "NOT_AUTHENTICATED"
            )[0]), 401

        # Get user info with CSRF token
        result = _get_auth_service().get_me(session_token)
        if not result:
            return jsonify(_create_error_response(
                "Invalid or expired session",
                401,
                "INVALID_SESSION"
            )[0]), 401

        user, session, csrf_token = result

        # Build response
        user_id = int(user.id) if user.id is not None else 0
        created_at_str = user.created_at.isoformat() if user.created_at else None
        last_login_str = user.last_login_at.isoformat() if user.last_login_at else None
        response_data: dict[str, Any] = {
            'user': {
                'id': user_id,
                'username': user.username,
                'created_at': created_at_str,
                'last_login_at': last_login_str,
                'is_active': user.is_active,
                'opt_in_sharing': user.opt_in_sharing
            },
            'csrf_token': csrf_token
        }

        return jsonify(response_data), 200

    except Exception as e:
        return jsonify(_create_error_response(
            "Failed to get user information",
            500,
            "INTERNAL_ERROR"
        )[0]), 500


@auth_bp.route('/csrf-token', methods=['GET'])
def get_csrf_token() -> Tuple[Response, int]:
    """Get a new CSRF token.

    Generates and returns a new CSRF token for the current session.
    Requires an authenticated session. This token should be included in
    the X-CSRF-Token header for state-changing requests (POST, PUT, DELETE, PATCH).

    Request:
        Requires valid session_token cookie (authenticated user)

    Response JSON:
        {
            "csrf_token": "string"
        }

    Status Codes:
        200: CSRF token generated
        401: Not authenticated
    """
    try:
        # Require authenticated session
        session_token = request.cookies.get('session_token')
        if not session_token:
            return jsonify(_create_error_response(
                "No session found",
                401,
                "NOT_AUTHENTICATED"
            )[0]), 401

        # Validate session exists (don't need to check user for CSRF token)
        result = _get_auth_service().validate_session(session_token)
        if not result:
            return jsonify(_create_error_response(
                "Invalid or expired session",
                401,
                "INVALID_SESSION"
            )[0]), 401

        csrf_token, _ = _get_auth_service().generate_csrf_token()
        return jsonify({'csrf_token': csrf_token}), 200
    except Exception as e:
        return jsonify(_create_error_response(
            "Failed to generate CSRF token",
            500,
            "INTERNAL_ERROR"
        )[0]), 500
