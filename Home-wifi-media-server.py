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
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Wi-Fi Media Hub</title>
    <style>
        :root { --bg: #f8fafc; --surface: #ffffff; --primary: #6366f1; --primary-hover: #4f46e5; --text-main: #1e293b; --text-muted: #64748b; --border: #e2e8f0; --radius: 12px; --shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1); --shadow-hover: 0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1); }
        body { font-family: system-ui, -apple-system, sans-serif; background: var(--bg); color: var(--text-main); margin: 0; padding: 20px; line-height: 1.5; }
        .container { max-width: 1200px; margin: 0 auto; display: flex; flex-direction: column; gap: 24px; }
        .header { background: var(--surface); padding: 20px 24px; border-radius: var(--radius); box-shadow: var(--shadow); display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 16px; border: 1px solid var(--border); }
        .header h2 { margin: 0; font-size: 1.5rem; font-weight: 600; color: var(--text-main); letter-spacing: -0.025em; }
        .storage { font-size: 0.875rem; font-weight: 500; color: var(--primary); background: #e0e7ff; padding: 6px 12px; border-radius: 9999px; }
        .upload-section { background: var(--surface); padding: 24px; border-radius: var(--radius); box-shadow: var(--shadow); border: 1px solid var(--border); }
        .upload-form { display: flex; gap: 12px; align-items: center; flex-wrap: wrap; }
        input[type="file"] { flex: 1; min-width: 200px; padding: 8px 12px; border: 1px dashed #cbd5e1; border-radius: 8px; background: #f8fafc; cursor: pointer; color: var(--text-muted); font-size: 0.875rem; transition: border-color 0.2s; }
        input[type="file"]:hover { border-color: var(--primary); }
        button { background: var(--primary); color: white; border: none; padding: 10px 20px; border-radius: 8px; font-weight: 500; cursor: pointer; transition: background-color 0.2s; font-size: 0.875rem; }
        button:hover { background: var(--primary-hover); }
        .error-msg { background: #fee2e2; color: #dc2626; padding: 12px 16px; border-radius: 8px; font-size: 0.875rem; font-weight: 500; border: 1px solid #fecaca; }
        .gallery { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 24px; }
        .card { background: var(--surface); border-radius: var(--radius); overflow: hidden; box-shadow: var(--shadow); transition: all 0.2s ease; border: 1px solid var(--border); display: flex; flex-direction: column; }
        .card:hover { transform: translateY(-4px); box-shadow: var(--shadow-hover); border-color: #cbd5e1; }
        .card-img, .card-icon { width: 100%; height: 160px; object-fit: cover; border-bottom: 1px solid var(--border); }
        .card-icon { display: flex; align-items: center; justify-content: center; font-size: 3rem; background: #f1f5f9; color: #94a3b8; }
        .card-body { padding: 16px; display: flex; flex-direction: column; gap: 12px; flex-grow: 1; }
        .card-title { font-size: 0.875rem; font-weight: 500; color: var(--text-main); word-break: break-all; margin: 0; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
        .btn { display: inline-flex; align-items: center; justify-content: center; width: 100%; padding: 8px 0; background: #f1f5f9; color: var(--text-main); text-decoration: none; border-radius: 8px; font-size: 0.875rem; font-weight: 500; transition: all 0.2s; box-sizing: border-box; }
        .btn:hover { background: #e2e8f0; color: var(--primary); }
    </style>
</head>
<body>
<div class="container">
    <div class="header">
        <h2>Wi-Fi Media Hub</h2>
        <div class="storage">Drive: {{ free_gb }} GB Free / {{ total_gb }} GB Total</div>
    </div>
    {% if error %}
    <div class="error-msg">{{ error }}</div>
    {% endif %}
    <div class="upload-section">
        <form method="POST" class="upload-form" enctype="multipart/form-data">
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
                <p class="card-title">{{ file.name }}</p>
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
