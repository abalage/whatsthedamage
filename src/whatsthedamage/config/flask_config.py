import os


class FlaskAppConfig:
    UPLOAD_FOLDER: str = 'uploads'
    MAX_CONTENT_LENGTH: int = 16 * 1024 * 1024  # 16 MB
    SECRET_KEY: bytes = os.urandom(24)
    DEFAULT_WHATSTHEDAMAGE_CONFIG: str = 'config.yml.default'
    LANGUAGES: list[str] = ['en', 'hu']
    DEFAULT_LANGUAGE: str = 'en'
