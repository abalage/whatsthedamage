import os


class FlaskAppConfig:
    UPLOAD_FOLDER: str = 'uploads'
    MAX_CONTENT_LENGTH: int = 16 * 1024 * 1024  # 16 MB
    SECRET_KEY: bytes = os.urandom(24)

    # Database configuration
    SQLALCHEMY_DATABASE_URI: str = os.getenv(
        'WHATSTHEDAMAGE_DATABASE_URI',
        'sqlite:///app.db'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False

    # Authentication configuration
    SESSION_COOKIE_SECURE: bool = True
    SESSION_COOKIE_HTTPONLY: bool = True
    SESSION_COOKIE_SAMESITE: str = 'Lax'
    PERMANENT_SESSION_LIFETIME: int = 3600  # 1 hour in seconds

    # Password configuration
    PASSWORD_MIN_LENGTH: int = 12

    # Session configuration
    SESSION_TOKEN_LENGTH: int = 32
    SESSION_MAX_CONCURRENT: int = 5
    SESSION_REMEMBER_ME_DURATION: int = 604800  # 7 days in seconds

    # Rate limiting configuration
    RATE_LIMIT_LOGIN: str = "5 per 15 minutes"
    RATE_LIMIT_API_MAX: int = int(os.getenv(
        'WHATSTHEDAMAGE_RATE_LIMIT_API_MAX',
        '300'
    ))
    RATE_LIMIT_API_WINDOW: int = int(os.getenv(
        'WHATSTHEDAMAGE_RATE_LIMIT_API_WINDOW',
        '60'
    ))
    RATE_LIMIT_HEAVY_MAX: int = int(os.getenv(
        'WHATSTHEDAMAGE_RATE_LIMIT_HEAVY_MAX',
        '10'
    ))
    RATE_LIMIT_HEAVY_WINDOW: int = int(os.getenv(
        'WHATSTHEDAMAGE_RATE_LIMIT_HEAVY_WINDOW',
        '60'
    ))

    # CORS configuration (comma-separated list of allowed origins)
    CORS_ORIGINS: list[str] = [
        origin.strip()
        for origin in os.getenv(
            'WHATSTHEDAMAGE_CORS_ORIGINS',
            'http://localhost:3000,http://127.0.0.1:3000'
        ).split(',')
        if origin.strip()
    ]

    # Security header configuration
    HSTS_ENABLED: bool = os.getenv(
        'WHATSTHEDAMAGE_HSTS_ENABLED',
        'true'
    ).lower() == 'true'
    HSTS_MAX_AGE: int = int(os.getenv(
        'WHATSTHEDAMAGE_HSTS_MAX_AGE',
        '31536000'
    ))

    # CSRF configuration
    CSRF_TOKEN_LENGTH: int = 32

    # Recovery code configuration
    RECOVERY_CODE_LENGTH: int = 16
    RECOVERY_CODE_CHARACTERS: str = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'
