"""Authentication decorators for Flask API endpoints.

This module provides decorators for handling authentication and authorization
in a DRY (Don't Repeat Yourself) manner across API endpoints.
"""
from functools import wraps
from typing import Callable, TypeVar, Any, Tuple
from flask import current_app, request, jsonify, Response

T = TypeVar('T')


# State-changing HTTP methods that require CSRF protection
CSRF_PROTECTED_METHODS = {'POST', 'PUT', 'DELETE', 'PATCH'}


def require_authentication(f: Callable[..., T]) -> Callable[..., Any]:
    """Decorator to require authentication for API endpoints.

    This decorator checks for a valid session token in the request cookies
    and validates it using the AuthenticationService. If authentication fails,
    it returns a 401 Unauthorized response.

    The authenticated user is attached to the Flask request context as `request.user`.

    Args:
        f: The endpoint function to decorate

    Returns:
        Decorated function that requires authentication

    Example:
        @v2_bp.route('/protected')
        @require_authentication
        def protected_endpoint():
            user = request.user  # Access authenticated user
            return jsonify({'message': 'Authenticated'})
    """
    @wraps(f)
    def decorated_function(*args: Any, **kwargs: Any) -> Any:
        # Get authentication service
        auth_service = current_app.extensions.get('auth_service')
        if not auth_service:
            return jsonify({'error': 'Authentication service not available'}), 500

        # Get session token from cookie
        session_token = request.cookies.get('session_token')
        if not session_token:
            return jsonify({'error': 'Authentication required'}), 401

        # Validate session
        result = auth_service.validate_session(session_token)
        if not result:
            return jsonify({'error': 'Authentication required'}), 401

        user, session = result

        # Attach user to request context for convenience
        request.user = user  # type: ignore[attr-defined]
        request.session = session  # type: ignore[attr-defined]

        return f(*args, **kwargs)

    return decorated_function


def optional_authentication(f: Callable[..., T]) -> Callable[..., Any]:
    """Decorator to optionally get authentication for API endpoints.

    This decorator attempts to authenticate the user but allows the request
    to proceed even if authentication fails. The user (or None) is attached
    to the Flask request context as `request.user`.

    Useful for endpoints that work differently for authenticated vs anonymous users.

    Args:
        f: The endpoint function to decorate

    Returns:
        Decorated function that optionally gets authentication

    Example:
        @v2_bp.route('/public')
        @optional_authentication
        def public_endpoint():
            user = getattr(request, 'user', None)
            if user:
                return jsonify({'message': 'Authenticated user'})
            return jsonify({'message': 'Anonymous user'})
    """
    @wraps(f)
    def decorated_function(*args: Any, **kwargs: Any) -> Any:
        # Get authentication service
        auth_service = current_app.extensions.get('auth_service')

        user = None
        session = None

        if auth_service:
            # Get session token from cookie
            session_token = request.cookies.get('session_token')
            if session_token:
                # Validate session
                result = auth_service.validate_session(session_token)
                if result:
                    user, session = result

        # Attach user to request context for convenience
        request.user = user  # type: ignore[attr-defined]
        request.session = session  # type: ignore[attr-defined]

        return f(*args, **kwargs)

    return decorated_function


def require_csrf(f: Callable[..., T]) -> Callable[..., Any]:
    """Decorator to require CSRF token validation for state-changing requests.

    This decorator validates the X-CSRF-Token header against the session's
    stored CSRF token hash. Only applies to POST, PUT, DELETE, and PATCH methods.
    Requires an authenticated session (must be used after @require_authentication
    or on endpoints that already have a session).

    The CSRF token should be sent by the client in the X-CSRF-Token header.

    Args:
        f: The endpoint function to decorate

    Returns:
        Decorated function that validates CSRF tokens for state-changing requests

    Example:
        @v2_bp.route('/data', methods=['POST'])
        @require_authentication
        @require_csrf
        def create_data():
            # CSRF token is automatically validated for POST requests
            return jsonify({'message': 'Data created'})
    """
    @wraps(f)
    def decorated_function(*args: Any, **kwargs: Any) -> Any:
        # Only validate CSRF for state-changing methods
        if request.method not in CSRF_PROTECTED_METHODS:
            return f(*args, **kwargs)

        # Get authentication service
        auth_service = current_app.extensions.get('auth_service')
        if not auth_service:
            return jsonify({'error': 'Authentication service not available'}), 500

        # Get session from request context (set by @require_authentication)
        session = getattr(request, 'session', None)
        if not session:
            return jsonify({'error': 'CSRF token requires authenticated session'}), 403

        # Get CSRF token from header
        csrf_token = request.headers.get('X-CSRF-Token')
        if not csrf_token:
            return jsonify({'error': 'CSRF token required for state-changing requests'}), 403

        # Validate CSRF token
        if not session.csrf_token_hash:
            return jsonify({'error': 'Session has no CSRF token'}), 403

        if not auth_service.validate_csrf_token(csrf_token, session.csrf_token_hash):
            return jsonify({'error': 'Invalid CSRF token'}), 403

        return f(*args, **kwargs)

    return decorated_function


def require_auth_and_csrf(f: Callable[..., T]) -> Callable[..., Any]:
    """Decorator that combines authentication and CSRF validation.

    This is a convenience decorator that applies both @require_authentication
    and @require_csrf in the correct order. For state-changing requests (POST,
    PUT, DELETE, PATCH), it validates both the session token and the CSRF token.

    Args:
        f: The endpoint function to decorate

    Returns:
        Decorated function that requires both authentication and CSRF validation

    Example:
        @v2_bp.route('/data', methods=['POST'])
        @require_auth_and_csrf
        def create_data():
            user = request.user  # Access authenticated user
            return jsonify({'message': 'Data created'})
    """
    @wraps(f)
    def decorated_function(*args: Any, **kwargs: Any) -> Any:
        # First authenticate
        auth_service = current_app.extensions.get('auth_service')
        if not auth_service:
            return jsonify({'error': 'Authentication service not available'}), 500

        # Get session token from cookie
        session_token = request.cookies.get('session_token')
        if not session_token:
            return jsonify({'error': 'Authentication required'}), 401

        # Validate session
        result = auth_service.validate_session(session_token)
        if not result:
            return jsonify({'error': 'Authentication required'}), 401

        user, session = result

        # Attach user to request context for convenience
        request.user = user  # type: ignore[attr-defined]
        request.session = session  # type: ignore[attr-defined]

        # Now validate CSRF for state-changing methods
        if request.method in CSRF_PROTECTED_METHODS:
            csrf_token = request.headers.get('X-CSRF-Token')
            if not csrf_token:
                return jsonify({'error': 'CSRF token required for state-changing requests'}), 403

            if not session.csrf_token_hash:
                return jsonify({'error': 'Session has no CSRF token'}), 403

            if not auth_service.validate_csrf_token(csrf_token, session.csrf_token_hash):
                return jsonify({'error': 'Invalid CSRF token'}), 403

        return f(*args, **kwargs)

    return decorated_function
