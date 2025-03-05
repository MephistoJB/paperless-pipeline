from quart import Blueprint, request, jsonify, current_app
import httpx
import logging

status_bp = Blueprint("status", __name__)

'''@status_bp.route('/status/log', methods=['GET'])
def stream_log():
    def generate():
        # Öffne den aktuellen Log-Stream von stdout & stderr
        process = subprocess.Popen(['tail', '-f', '/proc/1/fd/1'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        try:
            for line in process.stdout:
                yield line
        except GeneratorExit:
            process.kill()
    
    return Response(stream_with_context(generate()), content_type="text/plain")'''

#Just for debugging purposes
@status_bp.route('/status/debug_custom', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'])
async def debug():
    """ Debugging-Route, die alle eingehenden Request-Daten ausgibt """
    client_ip = request.remote_addr
    request_data = {
        "client_ip": client_ip,
        "method": request.method,
        "headers": dict(request.headers),
        "query_params": request.args.to_dict(),
        "body": await request.get_data(as_text=True),
        "json": await request.get_json(silent=True)
    }

    logging.debug(f"Incoming request:\n{request_data}\n")

    return jsonify({
        "message": "Received request",
        "request_data": request_data,
        "version": current_app.config["VERSION"]  # Holt die Version aus app.config
    }), 200