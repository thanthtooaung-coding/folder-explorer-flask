from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import platform
import psutil
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask app setup
app = Flask(__name__)

# Load CORS origins from the environment
CORS_ALLOWED_ORIGINS = os.getenv('FOLDER_EXPLORER_CORS_ALLOWED_ORIGINS', 'http://localhost:4200').split(',')

# CORS setup
CORS(app, resources={r"/api/*": {"origins": CORS_ALLOWED_ORIGINS}})

@app.route('/api/system-info', methods=['GET'])
def get_system_info():
    """Fetch system information."""
    return jsonify({
        'os': platform.system(),
        'release': platform.release(),
        'version': platform.version(),
        'machine': platform.machine()
    })

@app.route('/api/drives', methods=['GET'])
def get_drives():
    """Fetch drive information for Windows."""
    if platform.system() == "Windows":
        drives = []
        try:
            for partition in psutil.disk_partitions():
                if partition.fstype:
                    usage = psutil.disk_usage(partition.mountpoint)
                    drives.append({
                        'name': os.path.splitdrive(partition.mountpoint)[0],
                        'label': partition.mountpoint,
                        'total': usage.total,
                        'free': usage.free,
                        'used': usage.used,
                        'path': partition.mountpoint
                    })
            return jsonify(drives)
        except Exception as e:
            logger.error(f"Error fetching drives: {str(e)}")
            return jsonify({'error': 'Unable to fetch drives'}), 500
    else:
        return jsonify([{'name': '/', 'path': '/'}])

@app.route('/api/files', methods=['GET'])
def list_files():
    """List files in a given directory with security checks."""
    path = request.args.get('path', '/')
    try:
        path = os.path.abspath(path)        

        if not os.path.exists(path) or not os.path.isdir(path):
            return jsonify({'error': 'Invalid path'}), 400

        items = []
        for item in os.listdir(path):
            full_path = os.path.join(path, item)
            try:
                stats = os.stat(full_path)
                items.append({
                    'name': item,
                    'isDirectory': os.path.isdir(full_path),
                    'path': full_path,
                    'size': stats.st_size if not os.path.isdir(full_path) else 0,
                    'modified': stats.st_mtime
                })
            except Exception as e:
                logger.warning(f"Error processing {full_path}: {str(e)}")
        return jsonify(items)
    except Exception as e:
        logger.error(f"Error listing files in {path}: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    from waitress import serve
    logger.info("Starting server...")
    serve(app, host="0.0.0.0", port=5000)
