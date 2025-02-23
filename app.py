import logging.handlers
from flask import Flask, request, jsonify
import yaml, os, logging, sys, json, asyncio, signal

from services.ai_api import AI
from services.paperless_api import PaperlessAPI

# Flask-App-Instanz erstellen
app = Flask(__name__)

#############################################
#FUTURE WORK STARTS HERE
ACCEPTED_DATAFIELDS = {
                        "title": ""
                        #,"correspondend": ""
                        }

#############################################

def stopServer():
    logging.info("Server is shutting down...")
    os.kill(os.getpid(), signal.SIGINT)

LOG_LEVEL = os.getenv('LOG_LEVEL', None)
PAPERLESS_BASE_URL = os.getenv('PAPERLESS_BASE_URL', None)
AUTH_TOKEN=os.getenv('AUTH_TOKEN', None)
AI_USAGE = 'OLLAMA' #Currently on OLLAMA is support. So we leave this env out now.
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', None)
OLLAMA_HOST = os.getenv('OLLAMA_HOST', None)
PROCESSING_TAG = os.getenv('ai_processed', 'ai-processed')
ERROR_TAG = os.getenv('ai_error', 'ai-error')
DEBUG = os.getenv('DEBUG', 'False')


# Create Logger
logger = logging.getLogger(__name__)

if LOG_LEVEL:
    if LOG_LEVEL == "ERROR":
        logger.setLevel(logging.ERROR)
    elif LOG_LEVEL == "WARNING":
        logger.setLevel(logging.WARNING)
    elif LOG_LEVEL == "INFO":
        logger.setLevel(logging.INFO)
    elif LOG_LEVEL == "DEBUG":
        logger.setLevel(logging.DEBUG)
    else:
        logging.basicConfig(
            level=logging.DEBUG,
            format="%(asctime)s [%(levelname)s] %(message)s",
            handlers=[
                logging.StreamHandler(sys.stdout)
            ]
        )
        logging.error("Log Level not set correctly. Please choose from ERROR, WARNING, INFO or DEBUG")
        stopServer()
else:
    if(DEBUG and DEBUG==True):
        logger.setLevel(logging.DEBUG)
        LOG_LEVEL = "DEBUG"
    else:
        logger.setLevel(logging.INFO)
        LOG_LEVEL = "INFO"

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logging.info(f"LogLevel is set to {LOG_LEVEL}")

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
                taglist = api.get_all_tags()
                pt = taglist.get(PROCESSING_TAG,'None')
                et = taglist.get(ERROR_TAG,'None')
                if not pt:           
                    logging.error(f"PROCESSING_TAG {PROCESSING_TAG} not found.")
                    stopServer()
                if not et:
                    logging.error(f"PROCESSING_TAG {ERROR_TAG} not found. Creating it")
                    stopServer()
                app.config['PROCESSING_TAG'] = pt
                app.config['ERROR_TAG'] = et

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

#Just for debugging purposes
@app.route('/debug', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'])
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
        "request_data": request_data
    }), 200


@app.route('/api/data', methods=['POST'])
async def receive_data():
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
    app.run(host='0.0.0.0', port=5000, debug=True)
    #app.run(debug=True)
