import logging.handlers, asyncio, os, logging, sys, signal, subprocess
from quart import Quart, current_app, render_template, request, jsonify, Response, stream_with_context,Blueprint
import httpx
from services import config
from services.cache import Cache
from services.ai_api import AI
from services.paperless_api_old import PaperlessAPI
import hypercorn.asyncio
import asyncio, debugpy
from routes.documents import documents_bp
from routes.status import status_bp
from routes.frontend import frontend_bp
from routes.processing import process_queue, processing_bp

# Quart-App-Instanz erstellen
app = Quart(__name__)

request_queue = asyncio.Queue()

config.setConfig(app)

app.config["CACHE"] = Cache(app.config["PAPERLESS_API"], app.config["CACHE_TIME"])

app.register_blueprint(documents_bp)
app.register_blueprint(status_bp)
app.register_blueprint(frontend_bp)
app.register_blueprint(processing_bp)

shutdown_event = asyncio.Event()
async def stopServer():
    """ Beendet den Quart-Server sauber """
    logging.info("Server wird heruntergefahren...")
    shutdown_event.set()  # Signal für Shutdown setzen
    await asyncio.sleep(1)  # Warte kurz für sauberen Shutdown
    sys.exit(0)

# Globale Warteschlange für die Verarbeitung

async def background_task():
    logging.info("Starting background queue processor...")

    while True:
        queue_entry = await request_queue.get()  # Wartet, bis ein Eintrag in der Queue ist
        try:
            async with app.app_context():
                logging.info(f"Processing queue entry: {queue_entry}")
                await process_queue(queue_entry)  # Verarbeitet den Eintrag
        except Exception as e:
            logging.error(f"Error in queue processing: {e}")
        finally:
            request_queue.task_done()  # Markiert den Task als abgeschlossen

@app.before_serving
async def init_before_serving():
    config.checkConfig(app)
    logging.info("Starte Initialisierung vor Server-Start...")
    
    await app.config["PAPERLESS_API"].initialize()
    app.config["REQUEST_QUEUE"] = request_queue
    
    # Starte die Hintergrundaufgabe, wenn der Server gestartet wird
    app.config["BACKGROUND_TASK"] = asyncio.create_task(background_task())
    
    logging.info("Initialisierung abgeschlossen.")

""" 

async def refresh_metadata_internal():
    global api  # Falls api in der Funktion benötigt wird

    logging.info("Aktualisiere Metadaten von Paperless...")

    taglist = await api.get_all_tags()
    pt = taglist.get(PROCESSING_TAG, None)
    et = taglist.get(ERROR_TAG, None)

    if not pt:
        logging.error(f"PROCESSING_TAG {PROCESSING_TAG} nicht gefunden.")
        await stopServer()
    if not et:
        logging.error(f"ERROR_TAG {ERROR_TAG} nicht gefunden.")
        await stopServer()

    app.config['PROCESSING_TAG'] = pt
    app.config['ERROR_TAG'] = et
    app.config['INBOX_TAG'] = INBOX_TAG
    app.config['TAG_LIST'] = taglist
    app.config['COR_LIST'] = await api.get_all_correspondents()
    app.config['DOC_LIST'] = await api.get_all_documents()
    app.config['PATH_LIST'] = await api.get_all_paths()
    app.config['TYPE_LIST'] = await api.get_all_types()

    logging.info("Metadaten wurden erfolgreich aktualisiert.")"""

async def main():
    debug = os.getenv('DEBUG', 'False')
    logLevel = ""
    if debug:
        logLevel = "DEBUG"
    else:
        logLevel = "INFO"
    # Logger konfigurieren
    logging.basicConfig(level=getattr(logging, logLevel, logging.INFO),
                    format="%(asctime)s [%(levelname)s] %(message)s",
                    handlers=[logging.StreamHandler(sys.stdout)])
    
    logging.info(f"LogLevel is set to {logLevel}")

    # Debugpy nur starten, wenn DEBUG=True
    if logLevel:  # Falls nicht in config, Default = True
        logging.info("Starte Debugpy...")
        debugpy.listen(("0.0.0.0", 5679))  # Debugger läuft auf Port 5679
        logging.info("Warte auf Debugger-Verbindung...")
        debugpy.wait_for_client()  # Hält an, bis sich ein Debugger verbindet

    """ Initialisiert die App und startet den Server """
    logging.info("Starte Initialisierung...")
    
    await init_before_serving()  # Hier manuell aufrufen
    logging.info("Initialisierung abgeschlossen, starte Server...")

    conf = hypercorn.Config()
    conf.bind = ["0.0.0.0:5000"]  # Port anpassen falls nötig
    conf.accesslog = "-"  # Aktiviert das Logging für Hypercorn
    conf.errorlog = "-"  # Fehlerlog aktivieren

    await hypercorn.asyncio.serve(app, conf)

if __name__ == '__main__':
    asyncio.run(main())  # Nutze eine eigene `main()`-Funktion

#if __name__ == '__main__':
#    asyncio.run(hypercorn.asyncio.serve(app, config=hypercorn.Config()))