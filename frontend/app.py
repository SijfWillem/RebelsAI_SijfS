from flask import Flask, render_template, request, jsonify, send_from_directory
import os
import logging
import shutil
import requests
from werkzeug.utils import secure_filename
import sys
from typing import Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024 * 1024  # 1GB max file size
app.config['UPLOAD_FOLDER'] = 'temp_uploads'
app.config['BACKEND_URL'] = os.getenv('BACKEND_URL', 'http://localhost:8000')

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
logger.info(f"Created upload folder: {app.config['UPLOAD_FOLDER']}")

# Store the current folder path
current_folder_path: Optional[str] = None

def cleanup_upload_folder():
    """Remove all files in the upload folder and recreate the directory."""
    try:
        if os.path.exists(app.config['UPLOAD_FOLDER']):
            shutil.rmtree(app.config['UPLOAD_FOLDER'])
        os.makedirs(app.config['UPLOAD_FOLDER'])
        logger.info("Cleaned up upload folder")
    except Exception as e:
        logger.error(f"Error cleaning up upload folder: {str(e)}")
        raise

@app.route('/')
def index():
    """Render the main page."""
    logger.info("Rendering index page")
    return render_template('index.html')

@app.route('/api/upload-folder', methods=['POST'])
def upload_folder():
    """Handle folder upload and analysis."""
    global current_folder_path
    
    try:
        logger.info("Received upload request")
        if 'files' not in request.files:
            return jsonify({"error": "No files provided"}), 400
        
        files = request.files.getlist('files')
        logger.info(f"Processing {len(files)} files")
        
        if not files or files[0].filename == '':
            return jsonify({"error": "No files selected"}), 400
        
        # Clean up previous uploads
        cleanup_upload_folder()
        
        # Save all files
        for file in files:
            if file and file.filename:
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                logger.info(f"Saved file: {file_path}")
        
        # Store the absolute path of the upload folder
        current_folder_path = os.path.abspath(app.config['UPLOAD_FOLDER'])
        logger.info(f"Stored folder path: {current_folder_path}")
        
        # Send folder path to backend for analysis
        logger.info("Sending folder path to backend for analysis")
        response = requests.post(
            f"{app.config['BACKEND_URL']}/api/analyze-folder",
            params={"folder_path": current_folder_path}
        )
        
        if response.status_code == 200:
            logger.info("Successfully received analysis from backend")
            return jsonify(response.json())
        else:
            logger.error(f"Error from backend: {response.text}")
            return jsonify({"error": "Failed to analyze folder"}), 500
            
    except Exception as e:
        logger.error(f"Error processing upload: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/folder-insights')
def get_folder_insights():
    """Get insights for the current folder."""
    global current_folder_path
    
    try:
        if not current_folder_path:
            return jsonify({"error": "No folder path available"}), 404
            
        logger.info(f"Getting insights for folder: {current_folder_path}")
        response = requests.get(
            f"{app.config['BACKEND_URL']}/api/folder-insights",
            params={"folder_path": current_folder_path}
        )
        
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            logger.error(f"Error from backend: {response.text}")
            return jsonify({"error": "Failed to get folder insights"}), 500
            
    except Exception as e:
        logger.error(f"Error getting folder insights: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/documents')
def get_documents():
    """Get list of documents in the current folder."""
    global current_folder_path
    
    try:
        if not current_folder_path:
            return jsonify({"error": "No folder path available"}), 404
            
        logger.info(f"Getting documents for folder: {current_folder_path}")
        response = requests.get(
            f"{app.config['BACKEND_URL']}/api/documents",
            params={"folder_path": current_folder_path}
        )
        
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            logger.error(f"Error from backend: {response.text}")
            return jsonify({"error": "Failed to get documents"}), 500
            
    except Exception as e:
        logger.error(f"Error getting documents: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/health')
def health_check():
    """Health check endpoint."""
    return jsonify({"status": "healthy"})

@app.errorhandler(413)
def request_entity_too_large(error):
    """Handle file size limit exceeded error."""
    logger.error("File size limit exceeded")
    return jsonify({"error": "File size limit exceeded"}), 413

@app.errorhandler(404)
def not_found_error(error):
    """Handle 404 error."""
    logger.error("Resource not found")
    return jsonify({"error": "Resource not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 error."""
    logger.error("Internal server error", exc_info=True)
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    try:
        logger.info("Starting Flask application")
        port = int(os.environ.get('PORT', 5001))
        logger.info(f"Using port: {port}")
        app.run(debug=True, port=port, host='0.0.0.0')
    except Exception as e:
        logger.error(f"Failed to start Flask application: {str(e)}", exc_info=True)
        sys.exit(1) 