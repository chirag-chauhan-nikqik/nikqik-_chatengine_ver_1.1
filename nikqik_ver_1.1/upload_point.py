from flask import Flask, request
from werkzeug.utils import secure_filename
import os
import subprocess

app = Flask(__name__)

MAIN_UPLOAD_FOLDER = 'source_documents'
QUERY_UPLOAD_FOLDER = 'query_documents'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}

app.config['MAIN_UPLOAD_FOLDER'] = MAIN_UPLOAD_FOLDER
app.config['QUERY_UPLOAD_FOLDER'] = QUERY_UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

def save_file(file, directory):
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(directory, filename))
        return True
    return False

@app.route('/upload', methods=['POST'])
def upload_main_document():
    if not os.path.exists(MAIN_UPLOAD_FOLDER):
        os.makedirs(MAIN_UPLOAD_FOLDER)
    
    file = request.files['file']
    if save_file(file, app.config['MAIN_UPLOAD_FOLDER']):
        # Call `ingest.py`
        print('Starting ingest.py...')
        process = subprocess.Popen(['python3', 'ingest.py'], stdout=subprocess.PIPE)
        for line in process.stdout:
            print(line.decode().strip())
            if line.decode().strip() == "Ingestion complete! You can now run privateGPT.py to query your documents":
                break
        process.wait()
        return 'File uploaded and ingest.py executed'

    return 'File upload failed or file type not allowed'

@app.route('/query', methods=['POST'])
def upload_query_document():
    if not os.path.exists(QUERY_UPLOAD_FOLDER):
        os.makedirs(QUERY_UPLOAD_FOLDER)
    
    file = request.files['file']
    if save_file(file, app.config['QUERY_UPLOAD_FOLDER']):
        # Perform further actions here after query file is uploaded if needed
        # For example, running another script or updating the database
        return 'Query file uploaded'
    
    return 'Query file upload failed or file type not allowed'

if __name__ == '__main__':
    app.run(port=5001, debug=True)