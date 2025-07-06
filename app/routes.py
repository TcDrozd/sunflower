from PIL import Image
from flask import Blueprint, current_app, render_template, request, redirect, url_for, flash, send_from_directory
import os
from datetime import datetime
import uuid
from werkzeug.utils import secure_filename
from app.utils import allowed_file, resize_image


from PIL.ExifTags import TAGS

def get_photo_timestamp(filepath):
    try:
        with Image.open(filepath) as img:
            exif_data = img._getexif()
            if exif_data:
                for tag, value in exif_data.items():
                    decoded = TAGS.get(tag, tag)
                    if decoded == "DateTimeOriginal":
                        return datetime.strptime(value, "%Y:%m:%d %H:%M:%S")
    except Exception as e:
        print(f"EXIF read failed for {filepath}: {e}")
    # fallback
    mtime = os.path.getmtime(filepath)
    return datetime.fromtimestamp(mtime)


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
                timestamp = get_photo_timestamp(filepath)
                photos.append({
                    "filename": filename,
                    "timestamp": timestamp,
                    "url": url_for("static", filename=f"uploads/{filename}")
                })
        photos.sort(key=lambda x: x["timestamp"], reverse=True)
    return render_template("index.html", photos=photos)

@bp.route("/upload", methods=["POST"])
def upload_file():
    if 'file' not in request.files:
        flash("No file part")
        return redirect(url_for("routes.index"))
    print("FILES:", request.files)
    print("FORM:", request.form)
    
    files = request.files.getlist("file")
    temp_folder = os.path.join(current_app.static_folder, "temp_uploads")
    os.makedirs(temp_folder, exist_ok=True)
    
    for file in files:
        if file and allowed_file(file.filename):
            ext = file.filename.rsplit(".", 1)[1].lower()
            filename = f"{uuid.uuid4().hex}.{ext}"
            filepath = os.path.join(temp_folder, filename)
            file.save(filepath)

            # make sure thumbs dir exists
            os.makedirs(os.path.join(temp_folder, "thumbs"), exist_ok=True)

            # now make a thumbnail
            from PIL import Image
            with Image.open(filepath) as img:
                img.thumbnail((500, 500))  # max 500px
                thumb_path = os.path.join(temp_folder, "thumbs", filename)
                img.save(thumb_path)
    return redirect(url_for("routes.confirm_upload"))

@bp.route("/confirm", methods=["GET", "POST"])
def confirm_upload():
    temp_folder = os.path.join(current_app.static_folder, "temp_uploads")
    photos = []
    for filename in os.listdir(temp_folder):
        if filename == "thumbs":
            continue
        if allowed_file(filename):
            photos.append(filename)
    if not photos:
        flash("No photos to confirm.")
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
        # move the thumbnail
        thumb_src = os.path.join(temp_folder, "thumbs", filename)
        thumb_dest = os.path.join(upload_folder, "thumbs", filename)
        os.makedirs(os.path.join(upload_folder, "thumbs"), exist_ok=True)
        if os.path.exists(thumb_src):
            os.rename(thumb_src, thumb_dest)
    flash("Photos saved to sunflower log!")
    return redirect(url_for("routes.index"))

@bp.route("/rotate_photo/<filename>", methods=["POST"])
def rotate_photo(filename):
    temp_folder = os.path.join(current_app.static_folder, "temp_uploads")
    filepath = os.path.join(temp_folder, filename)
    try:
        with Image.open(filepath) as img:
            exif = img.info.get('exif')  # preserve EXIF block
            rotated = img.rotate(-90, expand=True)
            rotated.save(filepath, exif=exif)  # re-attach EXIF
        flash("Photo rotated, EXIF preserved.")
    except Exception as e:
        flash(f"Error rotating photo: {e}")
    return redirect(url_for("routes.confirm_upload"))
