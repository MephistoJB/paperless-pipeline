import logging
import os
from services.ai_api import AI
from pypaperless import Paperless

# Load environment variables for configuration
LOG_LEVEL = os.getenv('LOG_LEVEL', None)
PAPERLESS_BASE_URL = os.getenv('PAPERLESS_BASE_URL', None)
AUTH_TOKEN = os.getenv('AUTH_TOKEN', None)
AI_USAGE = 'OLLAMA'  # Currently only OLLAMA is supported, so this remains fixed
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', None)
OLLAMA_HOST = os.getenv('OLLAMA_HOST', None)
PROCESSING_TAG = os.getenv('PROCESSING_TAG', 'ai-processed')
ERROR_TAG = os.getenv('ERROR_TAG', 'ai-error')
INBOX_TAG = os.getenv('INBOX_TAG', 'Inbox')
DEBUG = os.getenv('DEBUG', 'False')
CACHE_TIME = int(os.getenv('CACHE_TIME', 60))  # Ensure CACHE_TIME is an integer

# Define application version
VERSION = "1.4.0"

# Define fixed tags for button actions
BUTTON_TAGS = {
    "next": ["-Inbox"],
    "send_to_ai": ["ai-title, -Inbox"],
    "investigate": ["check, -Inbox"]
}

# Define accepted data fields (future work can extend this)
ACCEPTED_DATAFIELDS = {
    "title": ""
    # "correspondend": ""  # Uncomment when needed
}

# Initialize Paperless API connection
paperless = Paperless(PAPERLESS_BASE_URL, AUTH_TOKEN)

"""
Configures the Quart application with necessary settings.

Parameters:
- app (Quart): The Quart application instance.

Sets:
- Various configuration values such as AI settings, API endpoints, and debugging options.
"""
def setConfig(app):
    app.config["VERSION"] = VERSION
    app.config["PAPERLESS_BASE_URL"] = PAPERLESS_BASE_URL
    app.config["AUTH_TOKEN"] = AUTH_TOKEN
    app.config["PAPERLESS_API"] = paperless
    app.config["CACHE_TIME"] = CACHE_TIME
    app.config["INBOX_TAG"] = INBOX_TAG
    app.config["LOG_LEVEL"] = LOG_LEVEL
    app.config["AI_USAGE"] = AI_USAGE
    app.config["OLLAMA_MODEL"] = OLLAMA_MODEL
    app.config["OLLAMA_HOST"] = OLLAMA_HOST
    app.config["PROCESSING_TAG"] = PROCESSING_TAG
    app.config["ERROR_TAG"] = ERROR_TAG
    app.config["DEBUG"] = DEBUG
    app.config["BUTTON_TAGS"] = BUTTON_TAGS
    app.config["ACCEPTED_DATAFIELDS"] = ACCEPTED_DATAFIELDS

"""
Checks and initializes the AI configuration.

Parameters:
- app (Quart): The Quart application instance.

Ensures:
- OLLAMA_HOST and OLLAMA_MODEL are properly set.
- Initializes AI instance and verifies connectivity.
- Stops the server if a configuration error occurs.
"""
def checkConfig(app):
    if not OLLAMA_HOST:
        logging.error("OLLAMA_HOST is not set.")
        app.stopServer()
        return

    logging.info(f"OLLAMA_HOST is set to: {OLLAMA_HOST}")

    if not OLLAMA_MODEL:
        logging.error("OLLAMA_MODEL is not set.")
        app.stopServer()
        return

    logging.info(f"OLLAMA_MODEL is set to: {OLLAMA_MODEL}")

    try:
        ai = AI(OLLAMA_MODEL, logging)
        if not ai.selfCheck():
            logging.error("Ollama connection failed.")
            app.stopServer()
        else:
            app.config["AI_API"] = ai
    except Exception as e:
        logging.error(f"Error initializing AI: {e}")
        app.stopServer()