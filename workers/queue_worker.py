import asyncio
import logging
from services.ai_api import AI
from services.paperless_api_old import PaperlessAPI

logger = logging.getLogger(__name__)
request_queue = asyncio.Queue()

async def process_queue():
    logging.info("Queue worker started.")
    while True:
        try:
            logging.debug("Waiting for queue item...") 
            data = await request_queue.get()
            logging.info(f"Processing request: {data}")

            results = {}
            for field in data["fields"]:
                # Holen Sie sich die Schlüssel des field-Objekts
                keys = list(field.keys())
                for key in app.config['ACCEPTED_DATAFIELDS']:
                     if key in keys:
                         response = ai.getResponse(data["document"]["content"], field[key])
                         results[key] = response
            tagname = data.get("tag", None)
            callTag = app.config['TAG_LIST'].get(tagname,'None')
            tags = data["document"]['tags']
            if callTag in tags:
                tags.remove(callTag)
                logging.debug(f"Removed Call Tag {tagname}")
            else:
                logging.debug(f"Call Tag {tagname} doesn't seem to be correct. It was not assigned to the document with the title '{data['document']['title']}' and the id '{data['document']['id']}'.")
                return jsonify({
                    'error': f"Call Tag {tagname} doesn't seem to be correct. It was not assigned to the document with the title '{data['document']['title']}' and the id '{data['document']['id']}'.",
                    'client_ip': data["client_ip"]
                }), 400

            results['tags'] = tags
            success = await api.patch_document(data["document"]["id"], results)
            #todo addEndTag (error or success)

            if success:
                logging.debug("Data has been processed successfully!")
                tags.append(app.config['PROCESSING_TAG'])
                jsonTags = {}
                jsonTags['tags'] = tags
                success = await api.patch_document(data["document"]["id"], jsonTags)
                if success:
                    logging.debug("Processing Tag added successfully")
                return jsonify({
                    'message': 'Data has been processed successfully!',
                    'client_ip': data["client_ip"]
                }), 200
            else:
                logging.error(f"Failed to patch document. Status code: {success.status_code}, Response: {success.text}")
                tags.append(app.config['ERROR_TAG'])
                jsonTags = {}
                jsonTags['tags'] = tags
                success = await api.patch_document(data["document"]["id"], jsonTags)
                if success:
                    logging.debug("Error Tag added successfully")
                return jsonify({
                    'error': f"Failed to patch document. Status code: {success.status_code}, Response: {success.text}",
                    'client_ip': data["client_ip"]
                }), 400    

            request_queue.task_done()
        except Exception as e:
            logging.error(f"Error in queue processing: {e}")