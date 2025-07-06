from tkinter import Image
from flask import Blueprint, current_app, render_template, request, redirect, url_for, flash, send_from_directory
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
    if 'file' not in request.files:
        flash("No file part")
        return redirect(url_for("routes.index"))
    
    files = request.files.getlist("file")
    temp_folder = os.path.join(current_app.static_folder, "temp_uploads")
    os.makedirs(temp_folder, exist_ok=True)
    
    for file in files:
        if file and allowed_file(file.filename):
            ext = file.filename.rsplit(".", 1)[1].lower()
            filename = f"{uuid.uuid4().hex}.{ext}"
            filepath = os.path.join(temp_folder, filename)
            file.save(filepath)
    return redirect(url_for("routes.confirm_upload"))

@bp.route("/confirm", methods=["GET", "POST"])
def confirm_upload():
    temp_folder = os.path.join(current_app.static_folder, "temp_uploads")
    photos = []
    for filename in os.listdir(temp_folder):
        if allowed_file(filename):
            photos.append(filename)
    return render_template("confirm.html", photos=photos)

@bp.route("/finalize", methods=["POST"])
def finalize_upload():
    temp_folder = os.path.join(current_app.static_folder, "temp_uploads")
    upload_folder = current_app.config["UPLOAD_FOLDER"]
    os.makedirs(upload_folder, exist_ok=True)
    
    confirmed = request.form.getlist("confirm_files")
    rotate = request.form.get("rotate")
    
    for filename in confirmed:
        temp_path = os.path.join(temp_folder, filename)
        perm_path = os.path.join(upload_folder, filename)
        os.rename(temp_path, perm_path)
    flash("Photos saved to sunflower log!")
    return redirect(url_for("routes.index"))

@bp.route("/rotate_photo/<filename>", methods=["POST"])
def rotate_photo(filename):
    temp_folder = os.path.join(current_app.static_folder, "temp_uploads")
    filepath = os.path.join(temp_folder, filename)
    try:
        with Image.open(filepath) as img:
            rotated = img.rotate(-90, expand=True)
            rotated.save(filepath)
        flash("Photo rotated.")
    except Exception as e:
        flash(f"Error rotating photo: {e}")
    return redirect(url_for("routes.confirm_upload"))