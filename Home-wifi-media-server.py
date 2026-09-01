import os
import shutil
import socket
from flask import Flask, request, render_template_string, send_from_directory, Response
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from waitress import serve

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Security & Configuration
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'shared_files')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Hard limits and security constraints
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50 MB max upload size
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'webp', 'mp4', 'mp3', 'zip', 'rar'}

# Fetch credentials securely
USERNAME = os.getenv("APP_USERNAME", "default_admin")
PASSWORD = os.getenv("APP_PASSWORD", "default_password")

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def check_auth(username, password):
    return username == USERNAME and password == PASSWORD

def authenticate():
    return Response('Login Required. Enter credentials to access the server.', 
                    401, {'WWW-Authenticate': 'Basic realm="Login Required"'})

def requires_auth(f):
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    decorated.__name__ = f.__name__
    return decorated

# HTML Template remains exactly as you designed it
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Advanced Local File Server</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f0f2f5; margin: 0; padding: 20px; }
        .container { max-width: 1200px; margin: auto; }
        .header { display: flex; justify-content: space-between; align-items: center; background: #fff; padding: 15px 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 20px; flex-wrap: wrap; gap: 10px;}
        .storage { font-size: 0.9em; color: #555; background: #e4e6eb; padding: 5px 10px; border-radius: 4px; }
        .upload-section { background: #fff; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .gallery { display: grid; grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); gap: 20px; }
        .card { background: #fff; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.1); text-align: center; transition: transform 0.2s; display: flex; flex-direction: column; }
        .card:hover { transform: translateY(-5px); box-shadow: 0 4px 8px rgba(0,0,0,0.2); }
        .card-img { width: 100%; height: 140px; object-fit: cover; background: #fafafa; border-bottom: 1px solid #eee; }
        .card-icon { width: 100%; height: 140px; display: flex; align-items: center; justify-content: center; font-size: 4em; background: #fafafa; border-bottom: 1px solid #eee; }
        .card-body { padding: 10px; flex-grow: 1; display: flex; flex-direction: column; justify-content: space-between; }
        .card-title { font-size: 0.85em; color: #333; word-break: break-all; margin-bottom: 10px; }
        .btn { display: inline-block; padding: 8px; background: #007bff; color: #fff; text-decoration: none; border-radius: 4px; font-size: 0.8em; }
        .btn:hover { background: #0056b3; }
        input[type="file"] { border: 1px solid #ccc; padding: 5px; border-radius: 4px; }
        button { padding: 8px 15px; background: #28a745; color: white; border: none; border-radius: 4px; cursor: pointer; }
        button:hover { background: #218838; }
        .error-msg { color: red; margin-bottom: 10px; font-weight: bold; }
    </style>
</head>
<body>
<div class="container">
    <div class="header">
        <h2 style="margin: 0;">Wi-Fi Media Gallery</h2>
        <div class="storage">Drive: {{ free_gb }} GB Free / {{ total_gb }} GB Total</div>
    </div>
    
    {% if error %}
    <div class="error-msg">{{ error }}</div>
    {% endif %}

    <div class="upload-section">
        <form method="POST" enctype="multipart/form-data" style="display: flex; gap: 10px; align-items: center; flex-wrap: wrap;">
            <input type="file" name="file" required>
            <button type="submit">Upload File</button>
        </form>
    </div>
    <div class="gallery">
        {% for file in files %}
        <div class="card">
            {% if file.is_image %}
            <img src="/download/{{ file.name }}" class="card-img" loading="lazy" alt="{{ file.name }}">
            {% else %}
            <div class="card-icon">📄</div>
            {% endif %}
            <div class="card-body">
                <div class="card-title">{{ file.name }}</div>
                <a href="/download/{{ file.name }}" class="btn" download>Download</a>
            </div>
        </div>
        {% endfor %}
    </div>
</div>
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
@requires_auth
def index():
    error_msg = None
    if request.method == 'POST':
        if 'file' in request.files:
            file = request.files['file']
            if file and file.filename != '':
                if allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                else:
                    error_msg = "Error: File type not allowed for security reasons."
                    
    files = []
    for f in os.listdir(app.config['UPLOAD_FOLDER']):
        if os.path.isfile(os.path.join(app.config['UPLOAD_FOLDER'], f)):
            is_img = f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp'))
            files.append({'name': f, 'is_image': is_img})
            
    total, used, free = shutil.disk_usage("/")
    free_gb = round(free / (1024 ** 3), 2)
    total_gb = round(total / (1024 ** 3), 2)
    return render_template_string(HTML_TEMPLATE, files=files, free_gb=free_gb, total_gb=total_gb, error=error_msg)

@app.route('/download/<filename>')
@requires_auth
def download(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    port = 8000
    
    print("="*50)
    print(f"🔒 Server Secured with Basic Auth")
    print(f"📂 Shared Directory: {UPLOAD_FOLDER}")
    print(f"🌐 Access locally at: http://localhost:{port}")
    print(f"📡 Access on Wi-Fi at: http://{local_ip}:{port}")
    print(f"⚙️  Server Backend: Waitress (Production Mode)")
    print("="*50)
    
    # Replaced app.run with waitress
    serve(app, host='0.0.0.0', port=port)