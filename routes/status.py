from flask import Blueprint, jsonify, Response
from services.paperless_api import PaperlessAPI
import requests

status_bp = Blueprint("status", __name__)

@app.route('/status/log', methods=['GET'])
def stream_log():
    def generate():
        # Öffne den aktuellen Log-Stream von stdout & stderr
        process = subprocess.Popen(['tail', '-f', '/proc/1/fd/1'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        try:
            for line in process.stdout:
                yield line
        except GeneratorExit:
            process.kill()
    
    return Response(stream_with_context(generate()), content_type="text/plain")

#Just for debugging purposes
@app.route('/status/debug', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'])
def debug():
    client_ip = request.remote_addr
    request_data = {
        "client_ip": client_ip,
        "method": request.method,
        "headers": dict(request.headers),
        "query_params": request.args.to_dict(),
        "body": request.get_data(as_text=True),
        "json": request.get_json(silent=True)
    }

    logging.debug(f"Incoming request:\n{request_data}\n")

    return jsonify({
        "message": "Received request",
        "request_data": request_data,
        "version": VERSION
    }), 200