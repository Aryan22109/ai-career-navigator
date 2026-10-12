from flask import Flask, jsonify
from flask_cors import CORS

from .config import Config
from .models import make_session_factory, seed_roles


def create_app(config: type = Config, database_url: str | None = None) -> Flask:
    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = config.MAX_UPLOAD_BYTES
    app.config["SPACY_MODEL"] = config.SPACY_MODEL
    app.config["RATE_LIMIT_PER_MIN"] = config.RATE_LIMIT_PER_MIN
    if config.TRUST_PROXY:
        from werkzeug.middleware.proxy_fix import ProxyFix
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1)
    CORS(app, origins=[o.strip() for o in config.CORS_ORIGINS.split(",")])

    app.session_factory = make_session_factory(database_url or config.DATABASE_URL)
    seed_roles(app.session_factory)

    from .routes import api
    app.register_blueprint(api, url_prefix="/api")

    @app.errorhandler(413)
    def too_large(_):
        return jsonify(error="File too large (max 2 MB)."), 413

    @app.after_request
    def security_headers(resp):
        resp.headers.setdefault("X-Content-Type-Options", "nosniff")
        resp.headers.setdefault("Cache-Control", "no-store")
        return resp

    return app
