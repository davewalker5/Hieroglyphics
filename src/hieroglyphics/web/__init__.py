import json
from os import environ
from os.path import dirname, join
from pathlib import Path
from secrets import token_hex

from flask import Flask

from .alphabet import alphabet_bp
from .home import home_bp
from .learn.learn_blueprint import learn_bp
from .logging_wrapper import configure_logger, get_logger
from .signs.signs_blueprint import signs_bp
from .transliterate import transliterate_bp


def create_app() -> Flask:
    """
    Flask Application Factory

    :return: An instance of the Flask application.
    :raises ValueError: If the configured quiz length is invalid.
    """
    app = Flask(
        "Hieroglyphics",
        static_folder=join(dirname(__file__), "static"),
        template_folder=join(dirname(__file__), "templates"),
    )

    app.config.update(
        SESSION_COOKIE_SAMESITE="Strict",
        SESSION_COOKIE_HTTPONLY=True,
        PERMANENT_SESSION_LIFETIME=600,
    )

    override_path = environ.get("HIEROGLYPHICS_QUIZ_CONFIG")
    quiz_config = (
        Path(override_path)
        if override_path
        else Path(__file__).with_name("quiz_config.json")
    )
    quiz_settings = json.loads(quiz_config.read_text(encoding="utf-8"))
    if not isinstance(quiz_settings, dict):
        raise ValueError("Quiz configuration must be a JSON object.")
    question_limit = quiz_settings.get("QUIZ_QUESTION_LIMIT")
    if type(question_limit) is not int or question_limit < 1:
        raise ValueError("QUIZ_QUESTION_LIMIT must be a positive integer.")
    app.config["QUIZ_QUESTION_LIMIT"] = question_limit
    app.secret_key = environ.get("HIEROGLYPHICS_SECRET_KEY") or token_hex(32)

    # Register the blueprints
    app.register_blueprint(home_bp, url_prefix="")
    app.register_blueprint(transliterate_bp, url_prefix="/transliterate")
    app.register_blueprint(alphabet_bp, url_prefix="/alphabet")
    app.register_blueprint(signs_bp, url_prefix="/signs")
    app.register_blueprint(learn_bp, url_prefix="/learn")

    # Configure the logger that's used across Werkzeug, Flask and the application-specific
    # logging
    configure_logger("hieroglyphics.log", 100000)
    app.logger = get_logger()

    @app.after_request
    def add_security_headers(response):
        """
        Enforce security-related response headers

        :param response: Response object
        :return: Response object with headers set
        """
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; frame-ancestors 'none'; form-action 'self'"
        )
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        return response

    return app
