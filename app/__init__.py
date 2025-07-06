# app/__init__.py
from flask import Flask
# from app.models import db
import os

def create_app():
    app = Flask(__name__, static_folder="static")
    app.secret_key = "change-this"
    app.config["UPLOAD_FOLDER"] = os.path.join(app.root_path, "static", "uploads")
    app.config["MAX_CONTENT_LENGTH"] = 200 * 1024 * 1024  # 50 MB

    # db.init_app(app)

    from app import routes
    app.register_blueprint(routes.bp)

    return app
