# app.py - Main Flask application
from flask import Flask, render_template, request, jsonify, send_from_directory
import os
import json
import uuid
from datetime import datetime
from PIL import Image, ExifTags
import exifread
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Configuration
UPLOAD_FOLDER = 'uploads'
THUMBNAIL_FOLDER = 'thumbnails'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
PHOTOS_JSON = 'photos.json'

# Create necessary directories
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(THUMBNAIL_FOLDER, exist_ok=True)
os.makedirs('static', exist_ok=True)

def allowed_file(filename):
    """Check if uploaded file has allowed extension"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def load_photos_data():
    """Load photos metadata from JSON file"""
    if os.path.exists(PHOTOS_JSON):
        with open(PHOTOS_JSON, 'r') as f:
            return json.load(f)
    return []

def save_photos_data(photos_data):
    """Save photos metadata to JSON file"""
    with open(PHOTOS_JSON, 'w') as f:
        json.dump(photos_data, indent=2, fp=f)

def extract_exif_data(image_path):
    """Extract EXIF data from image using both PIL and exifread"""
    exif_data = {}
    
    try:
        # Try with PIL first
        with Image.open(image_path) as img:
            if hasattr(img, '_getexif'):
                exif = img._getexif()
                if exif:
                    for tag, value in exif.items():
                        decoded = ExifTags.TAGS.get(tag, tag)
                        exif_data[decoded] = str(value)
        
        # Also try with exifread for more detailed info
        with open(image_path, 'rb') as f:
            tags = exifread.process_file(f)
            for tag in tags.keys():
                if tag not in ['JPEGThumbnail', 'TIFFThumbnail', 'Filename', 'EXIF MakerNote']:
                    exif_data[tag] = str(tags[tag])
    
    except Exception as e:
        print(f"Error extracting EXIF data: {e}")
    
    # Extract key information
    date_taken = None
    time_taken = None
    camera_info = {}
    
    # Look for date/time in various EXIF fields
    date_fields = ['DateTime', 'EXIF DateTimeOriginal', 'EXIF DateTimeDigitized', 'Image DateTime']
    for field in date_fields:
        if field in exif_data:
            try:
                dt_str = exif_data[field]
                # Parse datetime string (format: YYYY:MM:DD HH:MM:SS)
                dt = datetime.strptime(dt_str, '%Y:%m:%d %H:%M:%S')
                date_taken = dt.strftime('%Y-%m-%d')
                time_taken = dt.strftime('%H:%M:%S')
                break
            except:
                continue
    
    # Extract camera information
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

def create_thumbnail(image_path, thumbnail_path, size=(300, 300)):
    """Create thumbnail for uploaded image"""
    try:
        with Image.open(image_path) as img:
                # Auto-rotate image based on EXIF Orientation
            try:
                exif = img._getexif()
                if exif:
                    orientation_key = next(
                        (k for k, v in ExifTags.TAGS.items() if v == 'Orientation'), None
                    )
                    if orientation_key and orientation_key in exif:
                        orientation = exif[orientation_key]
                        if orientation == 3:
                            img = img.rotate(180, expand=True)
                        elif orientation == 6:
                            img = img.rotate(270, expand=True)
                        elif orientation == 8:
                            img = img.rotate(90, expand=True)
            except Exception as e:
                print(f"EXIF orientation handling failed: {e}")
            # Convert to RGB if necessary (for PNG with transparency)
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            
            # Create thumbnail maintaining aspect ratio
            img.thumbnail(size, Image.Resampling.LANCZOS)
            img.save(thumbnail_path, 'JPEG', quality=85)
            return True
    except Exception as e:
        print(f"Error creating thumbnail: {e}")
        return False

@app.route('/')
def index():
    """Main page displaying photo journal"""
    photos_data = load_photos_data()
    # Sort by upload date (newest first)
    photos_data.sort(key=lambda x: x.get('upload_date', ''), reverse=True)
    return render_template('index.html', photos=photos_data)

@app.route('/upload', methods=['POST'])
def upload_photos():
    """Handle photo uploads"""
    if 'photos' not in request.files:
        return jsonify({'error': 'No photos selected'}), 400
    
    files = request.files.getlist('photos')
    if not files or all(f.filename == '' for f in files):
        return jsonify({'error': 'No photos selected'}), 400
    
    photos_data = load_photos_data()
    uploaded_photos = []
    
    for file in files:
        if file and allowed_file(file.filename):
            # Generate unique filename
            filename = secure_filename(file.filename)
            unique_id = str(uuid.uuid4())
            file_extension = filename.rsplit('.', 1)[1].lower()
            unique_filename = f"{unique_id}.{file_extension}"
            
            # Save original image
            image_path = os.path.join(UPLOAD_FOLDER, unique_filename)
            file.save(image_path)
            
            # Create thumbnail
            thumbnail_filename = f"thumb_{unique_filename}"
            thumbnail_path = os.path.join(THUMBNAIL_FOLDER, thumbnail_filename)
            create_thumbnail(image_path, thumbnail_path)
            
            # Extract EXIF data
            exif_data = extract_exif_data(image_path)
            
            # Create photo metadata
            photo_data = {
                'id': unique_id,
                'original_filename': filename,
                'filename': unique_filename,
                'thumbnail': thumbnail_filename,
                'upload_date': datetime.now().isoformat(),
                'date_taken': exif_data['date_taken'],
                'time_taken': exif_data['time_taken'],
                'camera_info': exif_data['camera_info'],
                'raw_exif': exif_data['raw_exif']
            }
            
            photos_data.append(photo_data)
            uploaded_photos.append(photo_data)
    
    # Save updated photos data
    save_photos_data(photos_data)
    
    return jsonify({
        'success': True,
        'message': f'Successfully uploaded {len(uploaded_photos)} photo(s)',
        'photos': uploaded_photos
    })

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    """Serve uploaded images"""
    return send_from_directory(UPLOAD_FOLDER, filename)

@app.route('/thumbnails/<filename>')
def thumbnail_file(filename):
    """Serve thumbnail images"""
    return send_from_directory(THUMBNAIL_FOLDER, filename)

@app.route('/photo/<photo_id>')
def get_photo_details(photo_id):
    """Get detailed information about a specific photo"""
    photos_data = load_photos_data()
    photo = next((p for p in photos_data if p['id'] == photo_id), None)
    
    if not photo:
        return jsonify({'error': 'Photo not found'}), 404
    
    return jsonify(photo)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5080)
