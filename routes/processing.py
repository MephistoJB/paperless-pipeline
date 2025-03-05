from quart import Blueprint, request, jsonify, current_app
import httpx
import logging, asyncio

from routes.documents import set_tag

processing_bp = Blueprint("processing", __name__)

"""@app.route('/api/data', methods=['POST'])
async def receive_data():
    try:
        client_ip = request.remote_addr
        data = await request.get_json()

        if not data or "tag" not in data or "url" not in data:
            return jsonify({'error': 'Missing required parameters'}), 400

        doc_id = data["url"].rstrip('/').split('/')[-1]
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{app.config['PAPERLESS_BASE_URL']}/documents/{doc_id}/",
                                        headers={"Authorization": f"Token {app.config['AUTH_TOKEN']}"})

        if response.status_code != 200:
            return jsonify({'error': f"Document {doc_id} not found"}), 404

        document = response.json()
        fields = [{field: data.get(field)} for field in app.config['ACCEPTED_DATAFIELDS'] if data.get(field)]

        if fields:
            await request_queue.put({"document": document, "client_ip": client_ip, "fields": fields, "tag": data["tag"]})
            return jsonify({"message": "Request added to queue", "queue_length": request_queue.qsize()}), 200
        else:
            return jsonify({'error': 'No valid fields provided'}), 400

    except Exception as e:
        logging.error(f"Error in receive_data: {e}")
        return jsonify({"error": str(e)}), 500"""

async def process_queue(data):
        try:
            if not data:
                return # Falls Daten leer sind, einfach überspringen
            
            logging.info(f"Processing request: {data}")
            doc = data.get("document")
            results = []

            ai = current_app.config["AI_API"]

            # Verarbeitung durch AI
            for field in data["fields"]:
                for key in current_app.config['ACCEPTED_DATAFIELDS']:
                    if key in field:
                        response = ai.getResponse(doc.content, field[key])
                        results.append({"key": key, "value": response})

            # Falls Ergebnisse existieren, speichere sie im Dokument
            if results:
                for result in results:
                    setattr(doc, result["key"], result["value"])

                success = await doc.update()
                logging.info(f"Document {doc.id} updated: {success}")

            # Tags aktualisieren
            tagname = data.get("tag", None)
            if tagname:
                callTag = await current_app.config['CACHE'].getTagIDByName(tagname)
                if callTag in doc.tags:
                    await set_tag(doc.id, [f"-{tagname}"])
                    logging.debug(f"Removed Call Tag {tagname}")

            # Erfolg oder Fehler-Tag setzen
            if success:
                await set_tag(doc.id, [current_app.config['PROCESSING_TAG']])
            else:
                await set_tag(doc.id, [current_app.config['ERROR_TAG']])

        except Exception as e:
            logging.error(f"Error in queue processing: {e}")
            await set_tag(doc.id, [current_app.config['ERROR_TAG']])

@processing_bp.route('/ai/request', methods=['POST'])
async def receive_data():
    try:
        api = current_app.config["PAPERLESS_API"]
        client_ip = request.remote_addr
        data = await request.get_json()

        if not data or not data.get("tag"):
            return jsonify({'error': 'Missing required "tag" parameter'}), 400
        if not data or not data.get("url"):
            return jsonify({'error': 'Missing required "url" parameter'}), 400

        doc_id = data["url"].rstrip('/').split('/')[-1]
        document = await api.documents(doc_id)

        if not document:
            return jsonify({"error": f"Document {doc_id} not found"}), 404

        fields = [{field: data[field]} for field in current_app.config['ACCEPTED_DATAFIELDS'] if field in data]

        if fields:
            queue_entry = {
                "document": document,
                "client_ip": client_ip,
                "fields": fields,
                "tag": data.get("tag")
            }
            logging.info(f"Adding request for Document {doc_id} to queue...")

            asyncio.create_task(current_app.config["REQUEST_QUEUE"].put(queue_entry))

            return jsonify({"message": "Request added to processing queue"}), 200
        else:
            return jsonify({'error': 'No valid fields provided'}), 400

    except Exception as e:
        logging.error(f"Error in receive_data: {e}")
        return jsonify({"error": str(e)}), 500