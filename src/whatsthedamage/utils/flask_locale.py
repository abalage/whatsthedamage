from flask import session, request, current_app
from whatsthedamage.config.flask_config import FlaskAppConfig
from typing import Iterator


def get_locale() -> str:
    # 1. Check session
    lang = session.get('lang')
    if lang and lang in FlaskAppConfig.LANGUAGES:
        return str(lang)  # Ensure return type is str

    # 2. Try to detect from browser
    accept_languages: Iterator[str] = request.accept_languages.values()
    for browser_lang in accept_languages:
        if isinstance(browser_lang, str):  # Type guard
            code = browser_lang.split('-')[0]
            if code in FlaskAppConfig.LANGUAGES:
                return code

    # 3. Fallback to config default
    return FlaskAppConfig.DEFAULT_LANGUAGE


def get_languages() -> list[str]:
    langs = current_app.config.get('LANGUAGES', [])
    return list(langs) if isinstance(langs, (list, tuple)) else []


def get_default_language() -> str:
    lang = current_app.config.get('DEFAULT_LANGUAGE', 'en')
    return str(lang)  # Ensure return type is str
