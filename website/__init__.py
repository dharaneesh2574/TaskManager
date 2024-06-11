from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from datetime import timedelta
from werkzeug.security import generate_password_hash
from .models import db, User

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'your_secret_key'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # Session lifetime in seconds
    app.config['REMEMBER_COOKIE_DURATION'] = timedelta(days=7)  # Duration for the remember me cookie

    
    db.init_app(app)
    migrate = Migrate(app, db)

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    with app.app_context():
        db.create_all()
        create_default_admin()

    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint)

    from .routes import main as main_blueprint
    app.register_blueprint(main_blueprint)
    
    return app

def create_default_admin():
    admin_username = 'admin'
    admin_password = 'admin'
    admin_role = 'admin'
    admin_email = 'admin@example.com' 

    admin = User.query.filter_by(username=admin_username).first()
    if not admin:
        admin = User(username=admin_username, 
                    password=generate_password_hash(admin_password, method='pbkdf2:sha256'), 
                    role=admin_role,
                    email=admin_email)
        db.session.add(admin)
        db.session.commit()
