from flask import Blueprint, jsonify, Response
from services.paperless_api import PaperlessAPI
import requests

frontend_bp = Blueprint("frontend", __name__)

@frontend_bp.route('/')
def index():
    return render_template("index.html", version=VERSION, button_tags=BUTTON_TAGS)

@frontend_bp.route('/refreshMetadata', methods=['GET'])
def refreshMetaData():
    refresh_metadata_internal()
    return jsonify({"message": "Metadata refreshed successfully"}), 200