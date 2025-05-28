from flask import Flask
import os
from whatsthedamage.controllers.routes import bp as main_bp
from whatsthedamage.config.flask_config import FlaskAppConfig
from typing import Optional


def create_app(config_class: Optional[FlaskAppConfig] = None) -> Flask:
    app: Flask = Flask(__name__, template_folder='view/templates')

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

    app.register_blueprint(main_bp)

    return app


if __name__ == '__main__':
    app = create_app(None)
    app.run(debug=True)
