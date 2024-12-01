from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import platform
import psutil

app = Flask(__name__)
CORS(app)

@app.route('/api/system-info', methods=['GET'])
def get_system_info():
    return jsonify({
        'os': platform.system(),
        'release': platform.release(),
        'version': platform.version(),
        'machine': platform.machine()
    })

@app.route('/api/drives', methods=['GET'])
def get_drives():
    if platform.system() == "Windows":
        drives = []
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
    else:
        return jsonify([{'name': '/', 'path': '/'}])

@app.route('/api/files', methods=['GET'])
def list_files():
    path = request.args.get('path', '/')
    try:
        path = os.path.normpath(path)
        
        if not os.path.exists(path) or not os.path.isdir(path):
            return jsonify({'error': 'Invalid path'}), 400

        items = []
        for item in os.listdir(path):
            full_path = os.path.join(path, item)
            try:
                stats = os.stat(full_path)
                if item != 'app.py' and not item.startswith('.'):
                    items.append({
                        'name': item,
                        'isDirectory': os.path.isdir(full_path),
                        'path': full_path,
                        'size': stats.st_size if not os.path.isdir(full_path) else 0,
                        'modified': stats.st_mtime
                    })
            except Exception as e:
                print(f"Error processing {full_path}: {str(e)}")
                continue
        return jsonify(items)
    except Exception as e:
        print(f"Error listing files in {path}: {str(e)}")
        return jsonify({'error': str(e)}), 400

if __name__ == '__main__':
    app.run(debug=True)

