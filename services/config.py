import os

class Config:
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    PAPERLESS_BASE_URL = os.getenv("PAPERLESS_BASE_URL", None)
    AUTH_TOKEN = os.getenv("AUTH_TOKEN", None)
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", None)
    OLLAMA_HOST = os.getenv("OLLAMA_HOST", None)
    PROCESSING_TAG = os.getenv("PROCESSING_TAG", "ai-processed")
    ERROR_TAG = os.getenv("ERROR_TAG", "ai-error")
    INBOX_TAG = os.getenv("INBOX_TAG", "Inbox")
    DEBUG = os.getenv("DEBUG", "False")
    # Store version in a variable (or load from a config file)
    VERSION = "1.2.0"

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

    app.config['ACCEPTED_DATAFIELDS'] = ACCEPTED_DATAFIELDS
    app.config['UPLOAD_FOLDER'] = '/app/tmp'

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

    def refresh_metadata_internal():
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