from flask import Flask, g
import os
from whatsthedamage.controllers.routes import bp as main_bp
from whatsthedamage.config.flask_config import FlaskAppConfig
from whatsthedamage.utils.flask_locale import get_locale
from typing import Optional, Any
import gettext


def create_app(config_class: Optional[FlaskAppConfig] = None) -> Flask:
    app: Flask = Flask(__name__, template_folder='view/templates', static_folder='view/static')

    # Load default configuration from a class
    app.config.from_object(FlaskAppConfig)

    if config_class:
        app.config.from_object(config_class)

    # Check if external config file exists and load it
    config_file = 'config.py'
    if os.path.exists(config_file):
        app.config.from_pyfile(config_file)

    # Ensure the upload folder exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # --- BEGIN: Gettext integration for templates ---
    @app.before_request
    def set_gettext() -> None:
        lang = get_locale()
        try:
            translations = gettext.translation(
                'messages',  # domain
                localedir='locale',  # adjust if needed
                languages=[lang],
                fallback=True
            )
        except Exception:
            translations = gettext.NullTranslations()
        g._ = translations.gettext
        g.ngettext = translations.ngettext
        # Store language in g for templates if needed
        g.lang = lang

    @app.context_processor
    def inject_gettext() -> dict[str, Any]:
        return dict(_=g._, ngettext=g.ngettext)
    # --- END: Gettext integration for templates ---

    app.register_blueprint(main_bp)

    return app


# Create the app instance for Gunicorn
app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
