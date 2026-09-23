from datetime import datetime
from pathlib import Path

from flask import Flask, render_template

from config import Config
from .extensions import csrf, db, login_manager, migrate


def create_app(config_class=Config):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_class)
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    from . import models
    from .auth import auth_bp
    from .main import main_bp
    from .schema import ensure_category_schema
    from .seed import seed_defaults

    with app.app_context():
        db.create_all()
        ensure_category_schema()
        seed_defaults()

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(models.User, int(user_id))

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)

    @app.errorhandler(404)
    def not_found(error):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(error):
        db.session.rollback()
        return render_template("errors/500.html"), 500

    @app.context_processor
    def inject_helpers():
        from decimal import Decimal
        return {
            "format_currency": lambda value: f"₹{Decimal(value or 0):,.2f}",
            "now": datetime.utcnow,
        }

    @app.cli.command("init-db")
    def init_db():
        db.create_all()
        from .seed import seed_defaults
        seed_defaults()
        print("Database initialized.")

    return app
