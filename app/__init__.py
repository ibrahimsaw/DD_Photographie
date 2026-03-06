from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__, static_folder='static')

    app.config["SECRET_KEY"] = "super-secret-key"
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///dd_photographie.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Initialisation des extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = "admin.login"

    # On importe les modèles pour que Migrate les voit
    from app.models import User, Category, Photo, Content, Settings

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # --- INJECTION GLOBALE (Doit être DANS create_app) ---
    @app.context_processor
    def inject_global_vars():
        try:
            settings = Settings.query.first()
            if not settings:
                settings = Settings() 
        except Exception:
            settings = None
        return dict(site_settings=settings)

    # Blueprints
    from app.routes import main
    from app.admin.routes import admin_bp
    app.register_blueprint(main)
    app.register_blueprint(admin_bp)

    return app # L'application est retournée ici