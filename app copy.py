loop = asyncio.new_event_loop()  # Erstelle einen einzigen Event-Loop
asyncio.set_event_loop(loop)  # Setze ihn als Standard für alle async Tasks

def start_loop(loop):
    asyncio.set_event_loop(loop)
    loop.run_forever()

# Starte den Event-Loop in einem separaten Thread
t = threading.Thread(target=start_loop, args=(loop,))
t.start()

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

# Starte den Worker im globalen Event-Loop
asyncio.run_coroutine_threadsafe(process_queue(), loop)

# Starte den Worker im neuen Event-Loop
worker_task = asyncio.run_coroutine_threadsafe(process_queue(), loop)

# Store version in a variable (or load from a config file)
VERSION = "1.3.0"

# Define fixed tags for buttons
BUTTON_TAGS = {
    "next": ["-Inbox"],
    "send_to_ai": ["ai-title, -Inbox"],
    "investigate": ["check, -Inbox"]
}

#############################################
#FUTURE WORK STARTS HERE
ACCEPTED_DATAFIELDS = {
                        "title": ""
                        #,"correspondend": ""
                        }

#############################################

# Async-Queue für Anfragen
request_queue = asyncio.Queue()

def refresh_metadata_internal():
    """ Interne Methode zur Aktualisierung der Metadaten """
    global api  # Falls api in der Funktion benötigt wird

    taglist = api.get_all_tags()
    pt = taglist.get(PROCESSING_TAG, None)
    et = taglist.get(ERROR_TAG, None)

    if not pt:
        logging.error(f"PROCESSING_TAG {PROCESSING_TAG} not found.")
        stopServer()
    if not et:
        logging.error(f"ERROR_TAG {ERROR_TAG} not found.")
        stopServer()

    app.config['PROCESSING_TAG'] = pt
    app.config['ERROR_TAG'] = et
    app.config['INBOX_TAG'] = INBOX_TAG
    app.config['TAG_LIST'] = taglist
    app.config['COR_LIST'] = api.get_all_correspondents()
    app.config['DOC_LIST'] = api.get_all_documents()
    app.config['PATH_LIST'] = api.get_all_paths()
    app.config['TYPE_LIST'] = api.get_all_types()

if(DEBUG and DEBUG=='True'):
    app.config['DEBUG'] = True
    app.config['TESTING'] = True
    logging.warning("DEBUG MODE enabled")

logging.info(f"Checking Config")
#Config Check

if(OLLAMA_HOST):
    logging.info(f"OLLAMA_HOST is set to: {OLLAMA_HOST}.")
    if(OLLAMA_MODEL):
        logging.info(f"OLLAMA_MODEL is set to: {OLLAMA_MODEL}. Checking now if Ollama is reachable with this model")
        app.config['OLLAMA_HOST'] = OLLAMA_HOST
        app.config['OLLAMA_MODEL'] = OLLAMA_MODEL
        try:
            logging.debug("Creating AI_API Object")

            ai = AI(app.config["OLLAMA_MODEL"], logging)

            logging.debug("AI_API Object successfully created")
            #If the OLLAMA Host is set, then the connection is tested an the model is loaded in order to reduce access time
            if not ai.selfCheck():
                logging.error("Connection to the Ollama Instance could not be established. Please check your Ollama Instance, your environment variables and your firewall.")
                stopServer()
            else:
                logging.info(f"Connection to Ollama instance {app.config['OLLAMA_HOST']} and the model {app.config['OLLAMA_MODEL']} loaded" )

        except Exception as e:
            logging.error(f"Failed to create AI_API object: {e}")
            stopServer()
    else:
        logging.error("Environment Variable OLLAMA_MODEL not set. OLLAMA_MODEL is the LLM model which will be used and is mandatory. Example: gemma2")
        stopServer()
else:
    logging.error("Environment Variable OLLAMA_HOST not set. OLLAMA_HOST is the URL including the port where Ollama is reachable and it is mandatory. Example: http://192.168.1.56:11434 ")
    stopServer()

if PAPERLESS_BASE_URL :
    if not PAPERLESS_BASE_URL.endswith('/api'):
        logging.debug(f"PAPERLESS_BASE_URL does not end with /api. Adding it.")
        PAPERLESS_BASE_URL += '/api'
    logging.info(f"PAPERLESS_BASE_URL is set to: {PAPERLESS_BASE_URL}. Checking now if Paperless is reachable.")
    
    if AUTH_TOKEN and len(AUTH_TOKEN) >= 6:
        AUTH_TOKEN_short = AUTH_TOKEN
        logging.info(f"AUTH_TOKEN is set to: {AUTH_TOKEN[:3] + '*' * (len(AUTH_TOKEN) - 6) + AUTH_TOKEN[-3:]}. Checking now if Paperless is reachable.")
        try:
            app.config['PAPERLESS_BASE_URL'] = PAPERLESS_BASE_URL
            app.config['AUTH_TOKEN'] = AUTH_TOKEN
            logging.debug("Creating PaperlessAPI Object")

            api = PaperlessAPI(app.config['PAPERLESS_BASE_URL'],
                                app.config['AUTH_TOKEN'],
                                logger=logging)
            logging.debug("PaperlessAPI Object successfully created")

            if not api.test_connection:
                logging.error(f"Connection to {PAPERLESS_BASE_URL} with AUTH_TOKEN {AUTH_TOKEN[:3] + '*' * (len(AUTH_TOKEN) - 6) + AUTH_TOKEN[-3:]} failed")
                stopServer()
            else:
                refresh_metadata_internal()

        except Exception as e:
            logging.error(f"Failed to create PaperlessAPI object: {e}")
            stopServer()
    else:
        logging.error("Environment Variable AUTH_TOKEN not set or not set correctly. Please follow this https://docs.paperless-ngx.com/api/#authorization to see how to create authentication token in Paperless-ngx.")
        stopServer()
else:
    logging.error("Environment Variable PAPERLESS_BASE_URL not set. PAPERLESS_BASE_URL is the URL including the port where Paperless-ngx is reachable and it is mandatory. Example: http://192.168.1.56:8000 ")
    stopServer()

app.config['ACCEPTED_DATAFIELDS'] = ACCEPTED_DATAFIELDS
app.config['UPLOAD_FOLDER'] = '/app/tmp'

@app.route('/refreshMetadata', methods=['GET'])
def refreshMetaData():
    refresh_metadata_internal()
    return jsonify({"message": "Metadata refreshed successfully"}), 200

@app.route('/')
def index():
    return render_template("index.html", version=VERSION, button_tags=BUTTON_TAGS)

@app.route('/api/inbox_list', methods=['GET'])
def inbox_list():
    try:
        return jsonify(api.get_inbox_documents(app.config['INBOX_TAG'])), 200
    except Exception as e:
        logging.error(f"Fehler beim Abrufen der Inbox-Dokumente: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/document_thumbnail/<int:doc_id>', methods=['GET'])
def document_thumbnail(doc_id):
    try:
        # Erstelle die URL zur Paperless-Thumbnail
        thumbnail_url = f"{app.config['PAPERLESS_BASE_URL']}/documents/{doc_id}/thumb/"

        # Sende eine GET-Anfrage an Paperless, um das Bild zu holen
        headers = {"Authorization": f"Token {app.config['AUTH_TOKEN']}"}
        response = requests.get(thumbnail_url, headers=headers, stream=True)

        # Überprüfe, ob das Bild erfolgreich geladen wurde
        if response.status_code == 200:
            return Response(response.content, content_type=response.headers['Content-Type'])
        else:
            logging.error(f"Fehler beim Abrufen des Thumbnails für Dokument {doc_id}: {response.status_code}")
            return jsonify({"error": "Thumbnail konnte nicht geladen werden"}), response.status_code

    except Exception as e:
        logging.error(f"Fehler beim Abrufen des Thumbnails: {e}")
        return jsonify({"error": str(e)}), 500
    
@app.route('/api/document_info/<int:doc_id>', methods=['GET'])
def document_info(doc_id):
    try:
        document = api.get_document_by_id(doc_id)

        # Correspondent-ID in Name umwandeln
        correspondent_id = document.get('correspondent', None)
        correspondent_name = next(
            (name for name, cid in app.config['COR_LIST'].items() if cid == correspondent_id),
            'Unbekannt'
        )

        path_id = document.get('storage_path', None)
        path_name = next(
            (name for name, pid in app.config['PATH_LIST'].items() if pid == path_id),
            'Unbekannt'
        )

        type_id = document.get('document_type', None)
        type_name = next(
            (name for name, tid in app.config['TYPE_LIST'].items() if tid == type_id),
            'Unbekannt'
        )

        tag_ids = document.get('tags', [])
        tag_names = [name for name, tid in app.config['TAG_LIST'].items() if tid in tag_ids]

        # Proxy-URL für das Thumbnail
        thumbnail_url = f"/api/document_thumbnail/{doc_id}"

        response_data = {
            "title": document.get('title', ''),
            "correspondent": correspondent_name,
            "type": type_name,
            "storage_path": path_name,
            "tags": tag_names,
            "thumbnail_url": thumbnail_url  # Jetzt verweist es auf die neue Proxy-Route
        }

        return jsonify(response_data), 200

    except Exception as e:
        logging.error(f"Fehler beim Abrufen der Dokumentinformationen: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/log', methods=['GET'])
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

@app.route('/api/data', methods=['POST'])
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
    
@app.route('/api/data2', methods=['POST'])
async def receive_data2():
    client_ip = request.remote_addr
    data = request.get_json()
    taglist = None
    callTag = None

    if not data or not data.get("tag", None):
         # If no document url is given, then  we need to throw an error
        logging.error("No call-Tag was given. Please hand over the tag, which was used to trigger the webhook")
        return jsonify({
            'error': 'Please add a webhook parameter "tag" (without quotes) as key and the tag which was used to trigger the webhook as value',
            'client_ip': client_ip
        }), 400
    else:
        taglist = api.get_all_tags()
        temptag = data.get("tag", None)
        callTag = taglist.get(temptag,'None')
        if not callTag:
            logging.error(f"Call-Tag {temptag} was not found. Please check the spelling")
            return jsonify({
                'error': f"Call-Tag {temptag} was not found. Please check the spelling",
                'client_ip': client_ip
            }), 400

    if not data or not data.get("url", None):
         # If no document url is given, then  we need to throw an error
        logging.error("No Document url was given.")
        return jsonify({
            'error': 'Please add a webhook parameter "url" (without quotes) as key and "\{doc_url\}" as value',
            'client_ip': client_ip
        }), 400
    else:
        # Extract the id out of the url
        url = data.get("url")
        logging.debug(f"Handling url: {url}")
        doc_id = url.rstrip('/').split('/')[-1]
        logging.debug(f"The Document ID is: {doc_id}")
        document = api.get_document_by_id(doc_id)
        logging.debug(f"Load document with title {document['title']}")
        content = document['content']
        logging.debug(f"Content of the document loaded")

        for field in app.config['ACCEPTED_DATAFIELDS']:
            logging.debug(f"Check if field {field} was handed over")
            if data.get(field, None):
                logging.debug(f"Field {field} was handed over. Asking the AI based on the prompt: {data.get(field)}")
                app.config['ACCEPTED_DATAFIELDS'][field] = ai.getResponse(content,data.get(field))
            else:
                del app.config['ACCEPTED_DATAFIELDS'][field]
        
        if not app.config['ACCEPTED_DATAFIELDS']: 
            logging.debug("No values to change and no prompt provided. Example: title / prompt for title")
            return jsonify({
                'error': 'No values to change and no prompt provided. Example: title / prompt for title',
                'client_ip': client_ip
            }), 400
        else:
            data = app.config['ACCEPTED_DATAFIELDS']
            tags = document['tags']
            if callTag in tags:
                tags.remove(callTag)
                logging.debug(f"Removed Call Tag {callTag}")
            else:
                logging.debug(f"Call Tag {callTag} doesn´t seem to be correct. It was not assigned to the document with the title {document['title']} and the id {doc_id}")
                return jsonify({
                    'error': f"Call Tag {callTag} doesn´t seem to be correct. It was not assigned to the document with the title {document['title']} and the id {doc_id}",
                    'client_ip': client_ip
                }), 400

            data['tags'] = tags
            success = await api.patch_document(doc_id, data)
            #todo addEndTag (error or success)

            if success:
                logging.debug("Data has been processed successfully!")
                tags.append(app.config['PROCESSING_TAG'])
                jsonTags = {}
                jsonTags['tags'] = tags
                success = await api.patch_document(doc_id, jsonTags)
                if success:
                    logging.debug("Processing Tag added successfully")
                return jsonify({
                    'message': 'Data has been processed successfully!',
                    'client_ip': client_ip,
                    'processed_data': app.config['ACCEPTED_DATAFIELDS']
                }), 200
            else:
                logging.error(f"Failed to patch document. Status code: {success.status_code}, Response: {success.text}")
                tags.append(app.config['ERROR_TAG'])
                jsonTags = {}
                jsonTags['tags'] = tags
                success = await api.patch_document(doc_id, jsonTags)
                if success:
                    logging.debug("Error Tag added successfully")
                return jsonify({
                    'error': f"Failed to patch document. Status code: {success.status_code}, Response: {success.text}",
                    'client_ip': client_ip,
                    'processed_data': app.config['ACCEPTED_DATAFIELDS']
                }), 400
            return False

if __name__ == '__main__':
    #app.run(host='0.0.0.0', port=5000)
    app.run(host='0.0.0.0', port=5000)
    #app.run(debug=True)
