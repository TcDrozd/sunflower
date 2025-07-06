from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, session
import os
from datetime import datetime
from werkzeug.utils import secure_filename
from PIL import Image
import uuid
import json
from functools import wraps

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this'  # Change this to a random secret key

# Configuration
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB
THUMBNAIL_SIZE = (800, 600)  # Max dimensions for display
ADMIN_USERNAME = 'admin'  # Change this
ADMIN_PASSWORD = 'sunflower2024'  # Change this to something secure
METADATA_FILE = 'photo_metadata.json'

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session:
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

def load_metadata():
    """Load photo metadata from JSON file"""
    if os.path.exists(METADATA_FILE):
        with open(METADATA_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_metadata(metadata):
    """Save photo metadata to JSON file"""
    with open(METADATA_FILE, 'w') as f:
        json.dump(metadata, f, indent=2)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def resize_image(image_path, max_size=THUMBNAIL_SIZE):
    """Resize image to fit within max_size while maintaining aspect ratio"""
    try:
        with Image.open(image_path) as img:
            # Convert RGBA to RGB if necessary
            if img.mode in ('RGBA', 'LA'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
            img.save(image_path, 'JPEG', quality=85, optimize=True)
    except Exception as e:
        print(f"Error resizing image: {e}")

def get_photo_list():
    """Get list of photos sorted by newest first"""
    photos = []
    metadata = load_metadata()
    
    if os.path.exists(UPLOAD_FOLDER):
        for filename in os.listdir(UPLOAD_FOLDER):
            if allowed_file(filename):
                filepath = os.path.join(UPLOAD_FOLDER, filename)
                
                # Use custom metadata timestamp if available, otherwise file mtime
                if filename in metadata and 'timestamp' in metadata[filename]:
                    timestamp_str = metadata[filename]['timestamp']
                    timestamp = datetime.fromisoformat(timestamp_str)
                else:
                    # Get file modification time as fallback
                    mtime = os.path.getmtime(filepath)
                    timestamp = datetime.fromtimestamp(mtime)
                
                photos.append({
                    'filename': filename,
                    'timestamp': timestamp,
                    'url': url_for('uploaded_file', filename=filename)
                })
    
    # Sort by timestamp, newest first
    photos.sort(key=lambda x: x['timestamp'], reverse=True)
    return photos

@app.route('/')
def index():
    photos = get_photo_list()
    return render_template('index.html', photos=photos)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        flash('No file selected')
        return redirect(url_for('index'))
    
    file = request.files['file']
    
    if file.filename == '':
        flash('No file selected')
        return redirect(url_for('index'))
    
    if file and allowed_file(file.filename):
        # Generate unique filename
        ext = file.filename.rsplit('.', 1)[1].lower()
        filename = f"{uuid.uuid4().hex}.{ext}"
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        
        try:
            file.save(filepath)
            
            # Resize image for web display
            resize_image(filepath)
            
            flash('Photo added to the sunflower log! 🌻')
        except Exception as e:
            flash('Error uploading photo. Please try again.')
            print(f"Upload error: {e}")
    else:
        flash('Invalid file type. Please upload an image (PNG, JPG, JPEG, GIF, WebP)')
    
    return redirect(url_for('index'))

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            flash('Welcome to the admin panel! 🌻')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid credentials')
    
    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    flash('Logged out successfully')
    return redirect(url_for('index'))

@app.route('/admin')
@login_required
def admin_dashboard():
    photos = get_photo_list()
    return render_template('admin_dashboard.html', photos=photos)

@app.route('/admin/edit/<filename>', methods=['GET', 'POST'])
@login_required
def admin_edit_photo(filename):
    metadata = load_metadata()
    
    if request.method == 'POST':
        new_date = request.form.get('date')
        new_time = request.form.get('time')
        
        if new_date and new_time:
            try:
                # Combine date and time
                datetime_str = f"{new_date} {new_time}"
                new_datetime = datetime.strptime(datetime_str, '%Y-%m-%d %H:%M')
                
                # Update metadata
                if filename not in metadata:
                    metadata[filename] = {}
                metadata[filename]['timestamp'] = new_datetime.isoformat()
                
                save_metadata(metadata)
                flash(f'Updated timestamp for {filename}')
                return redirect(url_for('admin_dashboard'))
            except ValueError:
                flash('Invalid date/time format')
    
    # Get current timestamp for the form
    current_timestamp = None
    if filename in metadata and 'timestamp' in metadata[filename]:
        current_timestamp = datetime.fromisoformat(metadata[filename]['timestamp'])
    else:
        # Use file modification time as fallback
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        if os.path.exists(filepath):
            mtime = os.path.getmtime(filepath)
            current_timestamp = datetime.fromtimestamp(mtime)
    
    return render_template('admin_edit.html', filename=filename, current_timestamp=current_timestamp)

@app.route('/admin/delete/<filename>', methods=['POST'])
@login_required
def admin_delete_photo(filename):
    try:
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        if os.path.exists(filepath):
            os.remove(filepath)
            
            # Remove from metadata if exists
            metadata = load_metadata()
            if filename in metadata:
                del metadata[filename]
                save_metadata(metadata)
            
            flash(f'Deleted {filename}')
        else:
            flash('File not found')
    except Exception as e:
        flash(f'Error deleting file: {e}')
    
    return redirect(url_for('admin_dashboard'))

if __name__ == '__main__':
    # Create templates directory and files if they don't exist
    os.makedirs('templates', exist_ok=True)
    
    # Create the HTML templates
    index_html = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🌻 Sunflower Photo Log</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #ffeaa7 0%, #fab1a0 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 800px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        
        .header {
            background: linear-gradient(135deg, #fdcb6e 0%, #e17055 100%);
            padding: 30px;
            text-align: center;
            color: white;
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }
        
        .header p {
            font-size: 1.1em;
            opacity: 0.9;
        }
        
        .upload-section {
            padding: 30px;
            background: #f8f9fa;
            border-bottom: 1px solid #e9ecef;
        }
        
        .upload-form {
            display: flex;
            flex-direction: column;
            gap: 15px;
            align-items: center;
        }
        
        .file-input-wrapper {
            position: relative;
            display: inline-block;
        }
        
        .file-input {
            position: absolute;
            opacity: 0;
            width: 100%;
            height: 100%;
            cursor: pointer;
        }
        
        .file-input-button {
            display: inline-block;
            padding: 15px 30px;
            background: linear-gradient(135deg, #00b894 0%, #00a085 100%);
            color: white;
            border-radius: 50px;
            font-size: 1.1em;
            font-weight: bold;
            text-decoration: none;
            cursor: pointer;
            transition: all 0.3s ease;
            border: none;
            box-shadow: 0 4px 15px rgba(0,184,148,0.3);
        }
        
        .file-input-button:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(0,184,148,0.4);
        }
        
        .upload-button {
            padding: 12px 25px;
            background: linear-gradient(135deg, #fdcb6e 0%, #e17055 100%);
            color: white;
            border: none;
            border-radius: 25px;
            font-size: 1em;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s ease;
            display: none;
        }
        
        .upload-button:hover {
            transform: translateY(-1px);
            box-shadow: 0 4px 15px rgba(253,203,110,0.4);
        }
        
        .flash-messages {
            padding: 0 30px;
        }
        
        .flash {
            padding: 15px;
            margin: 10px 0;
            border-radius: 10px;
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        
        .gallery {
            padding: 30px;
        }
        
        .gallery h2 {
            text-align: center;
            margin-bottom: 30px;
            color: #2d3436;
            font-size: 1.8em;
        }
        
        .photo-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
        }
        
        .photo-item {
            background: white;
            border-radius: 15px;
            overflow: hidden;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            transition: all 0.3s ease;
        }
        
        .photo-item:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 25px rgba(0,0,0,0.15);
        }
        
        .photo-item img {
            width: 100%;
            height: 200px;
            object-fit: cover;
            display: block;
        }
        
        .photo-info {
            padding: 15px;
            text-align: center;
        }
        
        .photo-date {
            color: #636e72;
            font-size: 0.9em;
        }
        
        .no-photos {
            text-align: center;
            color: #636e72;
            font-size: 1.1em;
            padding: 50px;
            background: #f8f9fa;
            border-radius: 15px;
            margin: 20px 0;
        }
        
        .no-photos .sunflower {
            font-size: 3em;
            margin-bottom: 20px;
        }
        
        @media (max-width: 600px) {
            .container {
                margin: 10px;
                border-radius: 15px;
            }
            
            .header {
                padding: 20px;
            }
            
            .header h1 {
                font-size: 2em;
            }
            
            .upload-section {
                padding: 20px;
            }
            
            .gallery {
                padding: 20px;
            }
            
            .photo-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🌻 Sunflower Growth Log</h1>
            <p>Share a moment with our community sunflower!</p>
        </div>
        
        <div class="upload-section">
            <form class="upload-form" action="{{ url_for('upload_file') }}" method="post" enctype="multipart/form-data">
                <div class="file-input-wrapper">
                    <input type="file" name="file" class="file-input" accept="image/*" id="file-input" required>
                    <label for="file-input" class="file-input-button">
                        📷 Take Photo!
                    </label>
                </div>
                <button type="submit" class="upload-button" id="upload-button">
                    🌻 Add to Log
                </button>
            </form>
        </div>
        
        {% with messages = get_flashed_messages() %}
            {% if messages %}
                <div class="flash-messages">
                    {% for message in messages %}
                        <div class="flash">{{ message }}</div>
                    {% endfor %}
                </div>
            {% endif %}
        {% endwith %}
        
        <div class="gallery">
            <h2>Recent Photos</h2>
            {% if photos %}
                <div class="photo-grid">
                    {% for photo in photos %}
                        <div class="photo-item">
                            <img src="{{ photo.url }}" alt="Sunflower photo from {{ photo.timestamp.strftime('%B %d, %Y') }}">
                            <div class="photo-info">
                                <div class="photo-date">{{ photo.timestamp.strftime('%B %d, %Y at %I:%M %p') }}</div>
                            </div>
                        </div>
                    {% endfor %}
                </div>
            {% else %}
                <div class="no-photos">
                    <div class="sunflower">🌻</div>
                    <p>No photos yet! Be the first to capture our sunflower's journey.</p>
                </div>
            {% endif %}
        </div>
    </div>
    
    <script>
        // Show upload button when file is selected
        document.getElementById('file-input').addEventListener('change', function(e) {
            const uploadButton = document.getElementById('upload-button');
            if (e.target.files.length > 0) {
                uploadButton.style.display = 'inline-block';
                uploadButton.textContent = '🌻 Add "' + e.target.files[0].name + '" to Log';
            } else {
                uploadButton.style.display = 'none';
            }
        });
        
        // Auto-hide flash messages after 5 seconds
        setTimeout(function() {
            const flashMessages = document.querySelectorAll('.flash');
            flashMessages.forEach(function(message) {
                message.style.opacity = '0';
                setTimeout(function() {
                    message.style.display = 'none';
                }, 300);
            });
        }, 5000);
    </script>
</body>
</html>'''
    
    # Write the template file
    with open('templates/index.html', 'w') as f:
        f.write(index_html)
    
    print("🌻 Sunflower Photo Log is starting...")
    print("📁 Make sure to create the 'static/uploads' directory")
    print("🔑 Remember to change the secret key in production!")
    print("🌐 Visit http://localhost:5000 to see your sunflower log")
    
    app.run(debug=True, host='0.0.0.0', port=5010)
