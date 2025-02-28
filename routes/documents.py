from flask import Blueprint, jsonify, Response
from services.paperless_api import PaperlessAPI
import requests

documents_bp = Blueprint("documents", __name__)

api = PaperlessAPI()

@documents_bp.route('/doc/list_inbox', methods=['GET'])
def inbox_list():
    try:
        return jsonify(api.get_inbox_documents(app.config['INBOX_TAG'])), 200
    except Exception as e:
        logging.error(f"Fehler beim Abrufen der Inbox-Dokumente: {e}")
        return jsonify({"error": str(e)}), 500
    
@documents_bp.route('/doc/get_thumbnail/<int:doc_id>', methods=['GET'])
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

@documents_bp.route('/doc/set_tag', methods=['POST'])
async def tag_document():
    try:
        data = request.get_json()
        doc_id = data.get("doc_id")
        tag_names = data.get("tag_names", [])  # Now expecting an array of tag names

        if not doc_id or not tag_names:
            return jsonify({"error": "doc_id and tag_names (list) are required"}), 400

        # Get the tag list from the configuration
        tag_list = app.config.get('TAG_LIST', {})

        # Convert tag names to tag IDs
        tag_ids_to_add = []
        tag_ids_to_remove = []

        for tag_name in tag_names:
            remove_tag = tag_name.strip().startswith('-')
            clean_tag_name = tag_name.strip().lstrip('-')  # Remove leading '-'
            tag_id = tag_list.get(clean_tag_name)

            if not tag_id:
                return jsonify({"error": f"Tag '{clean_tag_name}' not found"}), 404

            if remove_tag:
                tag_ids_to_remove.append(tag_id)
            else:
                tag_ids_to_add.append(tag_id)

        # Fetch document from Paperless
        document = api.get_document_by_id(doc_id)

        if not document:
            return jsonify({"error": f"Document with ID {doc_id} not found"}), 404

        # Current tags of the document
        current_tags = document.get('tags', [])

        # Remove tags
        for tag_id in tag_ids_to_remove:
            if tag_id in current_tags:
                current_tags.remove(tag_id)

        # Add tags
        for tag_id in tag_ids_to_add:
            if tag_id not in current_tags:
                current_tags.append(tag_id)

        # Send PATCH request to update tags
        success = await api.patch_document(doc_id, {'tags': current_tags})

        if success:
            return jsonify({"message": f"Tags successfully updated for document {doc_id}"}), 200
        else:
            return jsonify({"error": "Error updating document tags"}), 500

    except Exception as e:
        logging.error(f"Error while tagging document: {e}")
        return jsonify({"error": str(e)}), 500
    
@documents_bp.route('/doc/get_info/<int:doc_id>', methods=['GET'])
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