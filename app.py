import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
login_manager = LoginManager()

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY") or "a secret key"
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

db.init_app(app)
login_manager.init_app(app)
login_manager.login_view = 'auth.login'

with app.app_context():
    import models
    import routes
    
    app.register_blueprint(routes.main_bp)
    app.register_blueprint(routes.auth_bp)
    app.register_blueprint(routes.games_bp)
    app.register_blueprint(routes.news_bp)
    app.register_blueprint(routes.reviews_bp)
    app.register_blueprint(routes.profile_bp)
    
    db.create_all()
