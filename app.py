from flask import Flask, request, redirect, url_for, send_from_directory, jsonify
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
UPLOAD_FOLDER = 'static/skins'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET'])
def index():
    skins = os.listdir(app.config['UPLOAD_FOLDER'])
    html_skins = ''.join(f'<li><img src="/skins/{skin}" width="100"> {skin}</li>' for skin in skins)
    html = f"""
    <html>
    <head>
        <title>Skin Mods</title>
        <style>
            body {{ font-family: Arial; }}
            #drop-area {{
                border: 2px dashed #ccc;
                padding: 20px;
                width: 300px;
                text-align: center;
            }}
        </style>
    </head>
    <body>
        <h1>欢迎来到 Skin Mods!</h1>
        <div id="drop-area">拖拽文件到这里上传</div>
        <ul id="skins-list">{html_skins}</ul>
        <script>
            const dropArea = document.getElementById('drop-area');
            dropArea.addEventListener('dragover', e => e.preventDefault());
            dropArea.addEventListener('drop', e => {{
                e.preventDefault();
                const files = e.dataTransfer.files;
                const formData = new FormData();
                for (let i = 0; i < files.length; i++) {{
                    formData.append('file', files[i]);
                }}
                fetch('/upload', {{
                    method: 'POST',
                    body: formData
                }}).then(() => location.reload());
            }});
        </script>
    </body>
    </html>
    """
    return html

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': '没有文件'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '文件名为空'}), 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return jsonify({'success': True})
    return jsonify({'error': '不允许的文件类型'}), 400

@app.route('/skins/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)

