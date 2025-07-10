# app/utils.py
from PIL import Image, ExifTags

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
THUMBNAIL_SIZE = (800, 600)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def resize_image(image_path, max_size=THUMBNAIL_SIZE):
    try:
        with Image.open(image_path) as img:
            if img.mode in ("RGBA", "LA"):
                background = Image.new("RGB", img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[-1] if img.mode == "RGBA" else None)
                img = background

            img.thumbnail(max_size, Image.Resampling.LANCZOS)
            img.save(image_path, "JPEG", quality=85, optimize=True)
    except Exception as e:
        print(f"Error resizing image: {e}")


def auto_orient_image(img):
    try:
        exif = img._getexif()
        if exif is not None:
            orientation = None
            for tag, value in exif.items():
                if ExifTags.TAGS.get(tag) == 'Orientation':
                    orientation = value
                    break
            if orientation == 3:
                img = img.rotate(180, expand=True)
            elif orientation == 6:
                img = img.rotate(270, expand=True)
            elif orientation == 8:
                img = img.rotate(90, expand=True)
    except Exception as e:
        print(f"Auto-orient failed: {e}")
    return img