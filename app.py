import os
from flask import Flask
from pathlib import Path

def create_app():
    app = Flask(__name__)

    # === config ===
    app.config.setdefault('MAX_CONTENT_LENGTH', 64 * 1024 * 1024)  # 64MB
    app.config['UPLOAD_FOLDER']    = os.path.join(app.static_folder, 'uploads')
    app.config['THUMBNAIL_FOLDER'] = os.path.join(app.static_folder, 'thumbnails')
    app.config.setdefault('PHOTOS_JSON', 'static/photos.json')
    app.config.setdefault('ALLOWED_EXTENSIONS', {'png', 'jpg', 'jpeg', 'gif'})

    # ensure directories exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['THUMBNAIL_FOLDER'], exist_ok=True)

    # register routes blueprint
    from app.routes import bp as routes_bp
    app.register_blueprint(routes_bp)

    return app

# instantiate for running
app = create_app()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5080)