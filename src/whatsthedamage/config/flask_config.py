import os

from whatsthedamage.config.auth_config import AuthConfig


class FlaskAppConfig:
    UPLOAD_FOLDER: str = 'uploads'
    MAX_CONTENT_LENGTH: int = 16 * 1024 * 1024  # 16 MB

    # Flask session signing key; sourced from the auth configuration
    # so the key cannot diverge between Flask and the auth services
    SECRET_KEY: bytes = AuthConfig.SECRET_KEY

    # Database configuration
    SQLALCHEMY_DATABASE_URI: str = os.getenv(
        'WHATSTHEDAMAGE_DATABASE_URI',
        'sqlite:///app.db'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False

    # Rate limiting configuration
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
