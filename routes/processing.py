from flask import Blueprint, jsonify, Response
from services.paperless_api import PaperlessAPI
import requests

processing_bp = Blueprint("processing", __name__)

@app.route('/ai/request', methods=['POST'])
async def receive_data():
    try:
        client_ip = request.remote_addr
        data = request.get_json()

        if not data or not data.get("tag"):
            # If no call-Tag is given, then  we need to throw an error
            logging.error("No call-Tag was given. Please hand over the tag, which was used to trigger the webhook")
            return jsonify({
                'error': 'Please add a webhook parameter "tag" (without quotes) as key and the tag which was used to trigger the webhook as value',
                'client_ip': client_ip
            }), 400
        if not data or not data.get("url"):
            # If no document url is given, then  we need to throw an error
            logging.error("No Document url was given.")
            return jsonify({
                'error': 'Please add a webhook parameter "url" (without quotes) as key and "\{doc_url\}" as value',
                'client_ip': client_ip
            }), 400

        # Extract the id out of the url
        url = data.get("url")
        logging.debug(f"Handling url: {url}")
        doc_id = url.rstrip('/').split('/')[-1]
        logging.debug(f"The Document ID is: {doc_id}")
        document = api.get_document_by_id(doc_id)
        logging.debug(f"Load document with title {document['title']}")
        content = document['content']
        logging.debug(f"Content of the document loaded")

        if not document:
            logging.error({"error": f"Document {doc_id} not found"})
            return jsonify({"error": f"Document {doc_id} not found"}), 404


        fields = []
        for field in app.config['ACCEPTED_DATAFIELDS']:
            logging.debug(f"Check if field {field} was handed over")
            if data.get(field, None):
                logging.debug(f"Field {field} was handed over. Asking the AI based on the prompt: {data.get(field)}")
                fields.append({field:data.get(field)})
        
        if len(fields) > 0:
            # Create Queue-Entry
            queue_entry = {
                "document": document,
                "client_ip": client_ip,
                "fields": fields,
                "tag": data.get("tag", None)
            }
            # Send to Queue
            logging.info("Adding request to queue...")
            future = asyncio.run_coroutine_threadsafe(request_queue.put(queue_entry), loop)
            future.result()  # Blockiert, bis das Element in die Queue aufgenommen wurde
            return jsonify({
                "message": "Request added to processing queue",
                "queue_length": request_queue.qsize()
            }), 200
        else:
            return jsonify({
                'error': 'No valid fields have been provided',
                'client_ip': client_ip
            }), 400

    except Exception as e:
        logging.error(f"Error in receive_data: {e}")
        return jsonify({"error": str(e)}), 500