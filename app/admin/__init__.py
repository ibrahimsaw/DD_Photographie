from flask_login import LoginManager
from app.models import User

login_manager = LoginManager()
login_manager.login_view = "admin.login"

def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "secret-key"

    db.init_app(app)
    login_manager.init_app(app)

    from app.admin.routes import admin_bp
    app.register_blueprint(admin_bp)

    from app.routes import main
    app.register_blueprint(main)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    return app