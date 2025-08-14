from flask import Blueprint, render_template, jsonify, request, current_app
from werkzeug.utils import secure_filename
import uuid
from datetime import datetime
import os

from app.utils import (
    allowed_file,
    load_photos_data,
    save_photos_data,
    extract_exif_data,
    create_thumbnail_versions
)

bp = Blueprint('routes', __name__)

@bp.route('/')
def index():
    """Main page displaying photo journal"""
    photos_data = load_photos_data(current_app.config['PHOTOS_JSON'])
    photos_data.sort(key=lambda x: x.get('upload_date', ''), reverse=True)
    return render_template('index.html', photos=photos_data)

@bp.route('/upload', methods=['POST'])
def upload_photos():
    """Handle photo uploads"""
    if 'photos' not in request.files:
        return jsonify({'error': 'No photos selected'}), 400

    files = request.files.getlist('photos')
    if not files or all(f.filename == '' for f in files):
        return jsonify({'error': 'No photos selected'}), 400

    photos_data = load_photos_data(current_app.config['PHOTOS_JSON'])
    uploaded_photos = []

    upload_folder = current_app.config['UPLOAD_FOLDER']
    thumbnail_folder = current_app.config['THUMBNAIL_FOLDER']

    for file in files:
        if file and allowed_file(file.filename, current_app.config['ALLOWED_EXTENSIONS']):
            original_name = secure_filename(file.filename)
            unique_id = str(uuid.uuid4())
            ext = original_name.rsplit('.', 1)[1].lower()
            unique_filename = f"{unique_id}.{ext}"

            # Save original image
            image_path = os.path.join(upload_folder, unique_filename)
            file.save(image_path)

            # Create thumb + preview
            thumbnail_filename = f"thumb_{unique_filename}"
            preview_filename = f"preview_{unique_filename}"
            thumbnail_path = os.path.join(thumbnail_folder, thumbnail_filename)
            preview_path = os.path.join(thumbnail_folder, preview_filename)
            create_thumbnail_versions(image_path, thumbnail_path, preview_path)

            # Extract EXIF
            exif_data = extract_exif_data(image_path)

            # Build metadata
            photo_data = {
                'id': unique_id,
                'original_filename': original_name,
                'filename': unique_filename,
                'thumbnail': thumbnail_filename,
                'preview': preview_filename,
                'upload_date': datetime.now().isoformat(),
                'date_taken': exif_data.get('date_taken'),
                'time_taken': exif_data.get('time_taken'),
                'camera_info': exif_data.get('camera_info', {}),
                'raw_exif': exif_data.get('raw_exif', {})
            }

            photos_data.append(photo_data)
            uploaded_photos.append(photo_data)

    save_photos_data(current_app.config['PHOTOS_JSON'], photos_data)

    return jsonify({
        'success': True,
        'message': f'Successfully uploaded {len(uploaded_photos)} photo(s)',
        'photos': uploaded_photos
    })

@bp.route('/photo/<photo_id>')
def get_photo_details(photo_id):
    """Get detailed information about a specific photo"""
    photos_data = load_photos_data(current_app.config['PHOTOS_JSON'])
    print('id: ' , photo_id, 'photos_data[0]: ', photos_data[0]['id'])
    photo = next((p for p in photos_data if p['id'] == photo_id), None)
    print((p for p in photos_data if p['id'] == photo_id), None)


    if not photo:
        return jsonify({'error': 'Photo not found'}), 404

    return jsonify(photo)

@bp.route('/delete/<photo_id>', methods=['DELETE'])
def delete_photo(photo_id):
    photos_data = load_photos_data(current_app.config['PHOTOS_JSON'])
    photo = next((p for p in photos_data if p['id'] == photo_id), None)
    if not photo:
        return jsonify({'error': 'Photo not found'}), 404

    try:
        os.remove(os.path.join(current_app.config['UPLOAD_FOLDER'], photo['filename']))
        os.remove(os.path.join(current_app.config['THUMBNAIL_FOLDER'], photo['thumbnail']))
        os.remove(os.path.join(current_app.config['THUMBNAIL_FOLDER'], f"preview_{photo['filename']}"))
    except Exception as e:
        current_app.logger.warning(f"Error deleting files: {e}")

    photos_data = [p for p in photos_data if p['id'] != photo_id]
    save_photos_data(current_app.config['PHOTOS_JSON'], photos_data)

    return jsonify({'success': True})

