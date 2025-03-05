from quart import Blueprint, jsonify, render_template, current_app
from services.paperless_api_old import PaperlessAPI

frontend_bp = Blueprint("frontend", __name__)

@frontend_bp.route('/')
async def index():
    return await render_template("index.html", version=current_app.config["VERSION"], button_tags=current_app.config["BUTTON_TAGS"])

'''@frontend_bp.route('/refreshMetadata', methods=['GET'])
def refreshMetaData():
    refresh_metadata_internal()
    return jsonify({"message": "Metadata refreshed successfully"}), 200'''