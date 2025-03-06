import logging, asyncio  # Consolidating imports
from quart import Blueprint, request, jsonify, current_app
from routes.documents import set_tag  # Importing required function

# Blueprint for processing AI-based document requests
processing_bp = Blueprint("processing", __name__)

"""
Processes a queued document request using AI and updates the document accordingly.

Parameters:
- data (dict): A dictionary containing:
    - "document" (object): The document to be processed.
    - "fields" (list): A list of fields to extract information from using AI.
    - "tag" (str, optional): A tag associated with the document.
"""
async def process_queue(data: dict) -> None:
    try:
        if not data:
            return  # Skip processing if data is empty

        logging.info(f"Processing request: {data}")

        doc = data.get("document")  # Extract the document object
        if not doc:
            logging.error("Document object is missing in the data.")
            return
        
        results = []
        ai = current_app.config["AI_API"]  # Get AI API configuration

        # Iterate through fields and process AI responses
        for field in data["fields"]:
            for key in current_app.config['ACCEPTED_DATAFIELDS']:
                if key in field:
                    response = ai.getResponse(doc.content, field[key])  # AI processing
                    results.append({"key": key, "value": response})

        # If AI processing generated results, update the document
        if results:
            for result in results:
                setattr(doc, result["key"], result["value"])  # Dynamically set attributes
            
            success = await doc.update()  # Save document changes
            logging.info(f"Document {doc.id} updated: {success}")

        # Handle tagging if a tag is provided
        tagname = data.get("tag")
        if tagname:
            callTag = await current_app.config['CACHE'].getTagIDByName(tagname)
            if callTag in doc.tags:
                await set_tag(doc.id, [f"-{tagname}"])  # Remove existing tag
                logging.debug(f"Removed Call Tag {tagname}")

        # Assign success or error tag based on processing outcome
        if success:
            await set_tag(doc.id, [current_app.config['PROCESSING_TAG']])
        else:
            await set_tag(doc.id, [current_app.config['ERROR_TAG']])

    except Exception as e:
        logging.error(f"Error in queue processing: {e}")
        await set_tag(doc.id, [current_app.config['ERROR_TAG']])  # Assign error tag in case of failure

"""
Handles incoming AI processing requests via HTTP POST.

Returns:
- JSON response with success message if the request is valid.
- JSON response with an error message if the request is invalid or processing fails.
"""
@processing_bp.route('/ai/request', methods=['POST'])
async def receive_data():
    try:
        api = current_app.config["PAPERLESS_API"]  # Get API configuration
        client_ip = request.remote_addr  # Extract client IP
        data = await request.get_json()  # Parse JSON request body

        # Validate required fields in the request
        if not data or not data.get("tag"):
            return jsonify({'error': 'Missing required "tag" parameter'}), 400
        if not data or not data.get("url"):
            return jsonify({'error': 'Missing required "url" parameter'}), 400

        # Extract document ID from the provided URL
        doc_id = data["url"].rstrip('/').split('/')[-1]
        document = await api.documents(doc_id)  # Fetch document details

        if not document:
            return jsonify({"error": f"Document {doc_id} not found"}), 404

        # Extract fields for processing based on the accepted data fields
        fields = [{field: data[field]} for field in current_app.config['ACCEPTED_DATAFIELDS'] if field in data]

        if fields:
            # Create a queue entry for asynchronous processing
            queue_entry = {
                "document": document,
                "client_ip": client_ip,
                "fields": fields,
                "tag": data.get("tag")
            }
            logging.info(f"Adding request for Document {doc_id} to queue...")

            asyncio.create_task(current_app.config["REQUEST_QUEUE"].put(queue_entry))  # Add task to queue

            return jsonify({"message": "Request added to processing queue"}), 200
        else:
            return jsonify({'error': 'No valid fields provided'}), 400

    except Exception as e:
        logging.error(f"Error in receive_data: {e}")
        return jsonify({"error": str(e)}), 500  # Return error response in case of failure