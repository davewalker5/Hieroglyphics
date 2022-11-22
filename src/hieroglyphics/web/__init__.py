from os.path import dirname, join
from flask import Flask
from .home import home_bp
from .transliterate import transliterate_bp
from .alphabet import alphabet_bp
from .logging_wrapper import configure_logger, get_logger


def create_app():
    """
    Flask Application Factory

    :return: An instance of the Flask application
    """
    app = Flask("Hieroglyphics",
                static_folder=join(dirname(__file__), "static"),
                template_folder=join(dirname(__file__), "templates"))

    app.config.update(
        SESSION_COOKIE_SAMESITE="Strict",
        SESSION_COOKIE_HTTPONLY=True,
        PERMANENT_SESSION_LIFETIME=600
    )

    # Register the blueprints
    app.register_blueprint(home_bp, url_prefix="")
    app.register_blueprint(transliterate_bp, url_prefix="/transliterate")
    app.register_blueprint(alphabet_bp, url_prefix="/alphabet")

    # Configure the logger that's used across Werkzeug, Flask and the application-specific
    # logging
    project_folder = dirname(dirname(dirname(dirname(__file__))))
    log_file_path = join(project_folder, "logs", "hieroglyphics.log")
    configure_logger(log_file_path, 100000)
    app.logger = get_logger()

    @app.after_request
    def add_security_headers(response):
        """
        Enforce security-related response headers

        :param response: Response object
        :return: Response object with headers set
        """
        response.headers["Content-Security-Policy"] = "default-src 'self'; frame-ancestors 'none'; form-action 'self'"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        return response

    return app


