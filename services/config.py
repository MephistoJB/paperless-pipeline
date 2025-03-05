import logging
import os
import sys
from services.ai_api import AI
from services.paperless_api_old import PaperlessAPI
from pypaperless import Paperless

LOG_LEVEL = os.getenv('LOG_LEVEL', None)
PAPERLESS_BASE_URL = os.getenv('PAPERLESS_BASE_URL', None)
AUTH_TOKEN=os.getenv('AUTH_TOKEN', None)
AI_USAGE = 'OLLAMA' #Currently on OLLAMA is support. So we leave this env out now.
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', None)
OLLAMA_HOST = os.getenv('OLLAMA_HOST', None)
PROCESSING_TAG = os.getenv('PROCESSING_TAG', 'ai-processed')
ERROR_TAG = os.getenv('ERROR_TAG', 'ai-error')
INBOX_TAG = os.getenv('INBOX_TAG', 'Inbox')
DEBUG = os.getenv('DEBUG', 'False')
CACHE_TIME = os.getenv('CACHE_TIME', 60)

# Store version in a variable (or load from a config file)
VERSION = "1.4.0"

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

paperless = Paperless(PAPERLESS_BASE_URL, AUTH_TOKEN)

def setConfig(app):
    app.config["VERSION"] = VERSION
    app.config["PAPERLESS_BASE_URL"] = PAPERLESS_BASE_URL
    app.config["AUTH_TOKEN"] = AUTH_TOKEN
    app.config["PAPERLESS_API"] = paperless
    app.config["CACHE_TIME"] = CACHE_TIME
    app.config['INBOX_TAG'] = INBOX_TAG
    app.config['LOG_LEVEL'] = LOG_LEVEL
    app.config['AI_USAGE'] = 'OLLAMA' #Currently on OLLAMA is support. So we leave this env out now.
    app.config['OLLAMA_MODEL'] = OLLAMA_MODEL
    app.config['OLLAMA_HOST'] = OLLAMA_HOST
    app.config['PROCESSING_TAG'] = PROCESSING_TAG
    app.config['ERROR_TAG'] = ERROR_TAG
    app.config['DEBUG'] = DEBUG
    app.config['BUTTON_TAGS'] = BUTTON_TAGS
    app.config['ACCEPTED_DATAFIELDS'] = ACCEPTED_DATAFIELDS

def checkConfig(app):
    """ Prüft die Konfiguration und setzt die Werte in app.config """
    if OLLAMA_HOST:
        logging.info(f"OLLAMA_HOST is set to: {OLLAMA_HOST}.")
        if OLLAMA_MODEL:
            logging.info(f"OLLAMA_MODEL is set to: {OLLAMA_MODEL}.")
            app.config['OLLAMA_HOST'] = OLLAMA_HOST
            app.config['OLLAMA_MODEL'] = OLLAMA_MODEL
            try:
                ai = AI(app.config["OLLAMA_MODEL"], logging)
                if not ai.selfCheck():
                    logging.error("Ollama Verbindung fehlgeschlagen.")
                    app.stopServer()
                else:
                    app.config["AI_API"] = ai
            except Exception as e:
                logging.error(f"Fehler bei AI-Initialisierung: {e}")
                app.stopServer()
        else:
            logging.error("OLLAMA_MODEL nicht gesetzt.")
            app.stopServer()
    else:
        logging.error("OLLAMA_HOST nicht gesetzt.")
        app.stopServer()

'''   if PAPERLESS_BASE_URL:
        if not PAPERLESS_BASE_URL.endswith('/api'):
            PAPERLESS_BASE_URL += '/api'
        logging.info(f"PAPERLESS_BASE_URL is set to: {PAPERLESS_BASE_URL}")

        if AUTH_TOKEN and len(AUTH_TOKEN) >= 6:
            app.config['PAPERLESS_BASE_URL'] = PAPERLESS_BASE_URL
            app.config['AUTH_TOKEN'] = AUTH_TOKEN
            try:
                api = PaperlessAPI(PAPERLESS_BASE_URL, AUTH_TOKEN, logger=logging)
                if not api.test_connection:
                    logging.error("Verbindung zu Paperless fehlgeschlagen.")
                    app.stopServer()
            except Exception as e:
                logging.error(f"Fehler bei Paperless-API-Initialisierung: {e}")
                app.stopServer()
        else:
            logging.error("AUTH_TOKEN nicht korrekt gesetzt.")
            app.stopServer()
    else:
        logging.error("PAPERLESS_BASE_URL nicht gesetzt.")
        app.stopServer()'''