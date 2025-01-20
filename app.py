from flask import Flask, request, jsonify, render_template
import yaml
import os

# Flask-App-Instanz erstellen
app = Flask(__name__)

# Beispiel-YAML-Daten (initialer Inhalt)
yaml_data = {
    "name": "Example",
    "version": 1,
    "settings": {
        "enabled": True,
        "threshold": 0.5
    }
}

# Verzeichnis für gespeicherte Dateien
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


# Startseite mit Editor
@app.route('/')
def home():
    yaml_content = yaml.dump(yaml_data)
    return render_template('editor.html', yaml_content=yaml_content)


# GET-Endpunkt
@app.route('/api', methods=['GET'])
def api_home():
    client_ip = request.remote_addr
    return jsonify({
        'message': 'Hello, this is your REST API!',
        'client_ip': client_ip
    })


# POST-Endpunkt für JSON-Daten
@app.route('/api/data', methods=['POST'])
def receive_data():
    client_ip = request.remote_addr
    data = request.get_json()

    if not data:
        return jsonify({
            'error': 'No data provided',
            'client_ip': client_ip
        }), 400

    processed_data = {key: value.upper() if isinstance(value, str) else value for key, value in data.items()}

    return jsonify({
        'message': 'Data received successfully!',
        'client_ip': client_ip,
        'processed_data': processed_data
    }), 200


# POST-Endpunkt zum Speichern von YAML-Daten
@app.route('/save', methods=['POST'])
def save_yaml():
    try:
        yaml_content = request.json.get('yaml_content')
        parsed_yaml = yaml.safe_load(yaml_content)  # Validierung der YAML-Daten
        filename = 'saved_yaml.yaml'
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        # Speichere die YAML-Datei
        with open(filepath, 'w') as yaml_file:
            yaml.dump(parsed_yaml, yaml_file)

        return jsonify({'message': 'YAML saved successfully!', 'filepath': filepath}), 200
    except yaml.YAMLError as e:
        return jsonify({'error': f'Invalid YAML: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Hauptprogramm
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)