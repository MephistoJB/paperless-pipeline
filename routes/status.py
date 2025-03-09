from quart import Blueprint, request, jsonify, current_app, Response, stream_with_context  # Import necessary modules
import logging, subprocess  # Consolidating imports
from services.config import initializeAIConnection, initializePaperlessConnection

# Blueprint for status-related API endpoints
status_bp = Blueprint("status", __name__)

@status_bp.route('/status/check', methods=['GET'])
async def check_status():
    """
    API-Route zur Überprüfung der aktuellen Verbindungszustände.
    """
    return jsonify({
        "aiconnection": current_app.config.get("AICONNECTION", False),
        "paperlessconnection": current_app.config.get("PAPERLESSCONNECTION", False)
    })

"""
Streams the application log in real-time by reading from stdout.

Returns:
- A streamed response with the live application logs.
"""
@status_bp.route('/status/log', methods=['GET'])
def stream_log():
    def generate():
        # Open the log stream from stdout & stderr
        process = subprocess.Popen(
            ['tail', '-f', '/proc/1/fd/1'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        try:
            for line in process.stdout:  # Stream log lines in real-time
                yield line
        except GeneratorExit:
            process.kill()  # Kill the process if the client disconnects
    
    return Response(stream_with_context(generate()), content_type="text/plain")

"""
Debugging endpoint that captures and returns incoming request data.

Handles:
- GET, POST, PUT, DELETE, PATCH, OPTIONS methods.

Returns:
- JSON response containing request details such as method, headers, query parameters, body, and client IP.
"""
@status_bp.route('/status/debug_custom', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'])
async def debug():
    try:
        client_ip = request.remote_addr  # Retrieve the client IP
        request_data = {
            "client_ip": client_ip,
            "method": request.method,
            "headers": dict(request.headers),
            "query_params": request.args.to_dict(),
            "body": await request.get_data(as_text=True),
            "json": await request.get_json(silent=True)
        }

        logging.debug(f"Incoming request:\n{request_data}\n")  # Log request details

        return jsonify({
            "message": "Received request",
            "request_data": request_data,
            "version": current_app.config["VERSION"]  # Retrieve the application version from config
        }), 200

    except Exception as e:
        logging.error(f"Error processing debug request: {e}")
        return jsonify({"error": "An error occurred while processing the request"}), 500  # Return error response if necessary

@status_bp.route('/status/connectToAI', methods=['POST'])
async def connect_to_ai():
    """
    API-Route zur Initialisierung der KI-Verbindung.
    
    Returns:
    - JSON-Response mit Status der Verbindung.
    """
    try:
        success = initializeAIConnection(current_app)
        if success:
            return jsonify({"status": "success", "message": "AI connection established"}), 200
        else:
            return jsonify({"status": "error", "message": "Failed to connect to AI"}), 500
    except Exception as e:
        logging.error(f"Error connecting to AI: {e}")
        return jsonify({"status": "error", "message": "Internal server error"}), 500


@status_bp.route('/status/connectToPaperless', methods=['POST'])
async def connect_to_paperless():
    """
    API-Route zur Initialisierung der Paperless-Verbindung.
    
    Returns:
    - JSON-Response mit Status der Verbindung.
    """
    try:
        success = await initializePaperlessConnection(current_app)
        if success:
            return jsonify({"status": "success", "message": "Paperless connection established"}), 200
        else:
            return jsonify({"status": "error", "message": "Failed to connect to Paperless"}), 500
    except Exception as e:
        logging.error(f"Error connecting to Paperless: {e}")
        return jsonify({"status": "error", "message": "Internal server error"}), 500