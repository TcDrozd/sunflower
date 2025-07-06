# app/routes.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_from_directory
import os
from datetime import datetime
import uuid
from werkzeug.utils import secure_filename
from app.utils import allowed_file, resize_image

bp = Blueprint("routes", __name__)

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}

@bp.route("/")
def index():
    photos = []
    upload_folder = os.getenv("UPLOAD_FOLDER", "app/static/uploads")
    if os.path.exists(upload_folder):
        for filename in os.listdir(upload_folder):
            if allowed_file(filename):
                filepath = os.path.join(upload_folder, filename)
                mtime = os.path.getmtime(filepath)
                photos.append({
                    "filename": filename,
                    "timestamp": datetime.fromtimestamp(mtime),
                    "url": url_for("static", filename=f"uploads/{filename}")
                })
        photos.sort(key=lambda x: x["timestamp"], reverse=True)
    return render_template("index.html", photos=photos)

@bp.route("/upload", methods=["POST"])
def upload_file():
    upload_folder = os.getenv("UPLOAD_FOLDER", "app/static/uploads")
    if "file" not in request.files:
        flash("No file selected")
        return redirect(url_for("routes.index"))

    file = request.files["file"]

    if file.filename == "":
        flash("No file selected")
        return redirect(url_for("routes.index"))

    if file and allowed_file(file.filename):
        ext = file.filename.rsplit(".", 1)[1].lower()
        filename = f"{uuid.uuid4().hex}.{ext}"
        filepath = os.path.join(upload_folder, filename)

        try:
            file.save(filepath)
            resize_image(filepath)
            flash("Photo added to the sunflower log! 🌻")
        except Exception as e:
            flash("Error uploading photo.")
            print(f"Upload error: {e}")
    else:
        flash("Invalid file type.")
    return redirect(url_for("routes.index"))
