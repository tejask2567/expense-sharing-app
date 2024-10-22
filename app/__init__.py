from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
import os
from datetime import timedelta
from datetime import datetime

# Change jwt_blocklist to use a dict to store token expiry
jwt_blocklist = {}

db = SQLAlchemy()
bcrypt = Bcrypt()
jwt = JWTManager()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.urandom(32)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///expense_sharing.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = os.urandom(32)
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)
    app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=30)
    # Add this configuration
    app.config['JWT_ERROR_MESSAGE_KEY'] = 'error'
    
    # Initialize extensions
    db.init_app(app)
    bcrypt.init_app(app)
    jwt.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    
    # Register blueprints
    from app.auth import auth_bp
    from app.expenses import expenses_bp
    from app.users import users_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(expenses_bp)
    app.register_blueprint(users_bp)
    
    with app.app_context():
        db.create_all()
    
    return app