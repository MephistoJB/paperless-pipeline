from flask import Flask
from services.config import Config
from services.logging_config import logger
from routes.documents import documents_bp
from routes.processing import processing_bp
import asyncio
import threading

app = Flask(__name__)

# Register Blueprints
app.register_blueprint(documents_bp)
app.register_blueprint(processing_bp)

# Asynchrone Queue starten
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
t = threading.Thread(target=loop.run_forever)
t.start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)