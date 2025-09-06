import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv

db = SQLAlchemy()

def create_app():
    load_dotenv()
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev_secret_key")
    db_url = os.getenv("DATABASE_URL", "sqlite:///data.db")
    app.config["SQLALCHEMY_DATABASE_URI"] = db_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    with app.app_context():
        from .models import Agent, Policy, PolicyHolder, Member, Payment, Commission, Sequence
        db.create_all()

    from .routes import bp as core_bp
    app.register_blueprint(core_bp)

    return app
