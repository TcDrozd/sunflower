import os
import json
from datetime import datetime
from PIL import Image, ImageOps, ExifTags
import exifread

def allowed_file(filename: str, allowed: set) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed

def load_photos_data(json_path: str):
    if os.path.exists(json_path):
        with open(json_path, 'r') as f:
            try:
                print(f"Loading photos data from {json_path}")
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []

def save_photos_data(json_path: str, photos_data):
    with open(json_path, 'w') as f:
        json.dump(photos_data, f, indent=2)

def extract_exif_data(image_path: str):
    exif_data = {}
    date_taken = None
    time_taken = None
    camera_info = {}

    try:
        # PIL
        with Image.open(image_path) as img:
            if hasattr(img, '_getexif'):
                exif = img._getexif()
                if exif:
                    for tag, value in exif.items():
                        decoded = ExifTags.TAGS.get(tag, tag)
                        exif_data[decoded] = str(value)

        # exifread for extra richness
        with open(image_path, 'rb') as f:
            tags = exifread.process_file(f)
            for tag in tags.keys():
                if tag not in ['JPEGThumbnail', 'TIFFThumbnail', 'Filename', 'EXIF MakerNote']:
                    exif_data[tag] = str(tags[tag])
    except Exception as e:
        print(f"Error extracting EXIF data: {e}")

    # Date/time extraction
    date_fields = ['DateTime', 'EXIF DateTimeOriginal', 'EXIF DateTimeDigitized', 'Image DateTime']
    for field in date_fields:
        if field in exif_data:
            try:
                dt = datetime.strptime(exif_data[field], '%Y:%m:%d %H:%M:%S')
                date_taken = dt.strftime('%Y-%m-%d')
                time_taken = dt.strftime('%H:%M:%S')
                break
            except Exception:
                continue

    # Camera info
    camera_fields = {
        'make': ['Image Make', 'Make'],
        'model': ['Image Model', 'Model'],
        'lens': ['EXIF LensModel', 'LensModel'],
        'focal_length': ['EXIF FocalLength', 'FocalLength'],
        'aperture': ['EXIF FNumber', 'FNumber'],
        'iso': ['EXIF ISOSpeedRatings', 'ISOSpeedRatings'],
        'shutter_speed': ['EXIF ExposureTime', 'ExposureTime']
    }
    for key, fields in camera_fields.items():
        for field in fields:
            if field in exif_data:
                camera_info[key] = exif_data[field]
                break

    return {
        'date_taken': date_taken,
        'time_taken': time_taken,
        'camera_info': camera_info,
        'raw_exif': exif_data
    }

def create_thumbnail_versions(src_path: str, thumb_path: str, preview_path: str,
                              thumb_max_size=(300, 300), preview_max_size=(1200, 1200),
                              thumb_quality=85, preview_quality=90):
    try:
        with Image.open(src_path) as img:
            img = ImageOps.exif_transpose(img)

            thumb = img.copy()
            thumb.thumbnail(thumb_max_size, Image.LANCZOS)
            thumb.save(thumb_path, format="JPEG", quality=thumb_quality, optimize=True)

            preview = img.copy()
            preview.thumbnail(preview_max_size, Image.LANCZOS)
            preview.save(preview_path, format="JPEG", quality=preview_quality, optimize=True)
    except Exception as e:
        print(f"Thumbnail generation failed for {src_path}: {e}")