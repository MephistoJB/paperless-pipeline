from quart import Blueprint, request, jsonify, current_app
import httpx
import logging

documents_bp = Blueprint("documents", __name__)

@documents_bp.route('/doc/get_info/<int:doc_id>', methods=['GET'])
async def document_info(doc_id):
    api = current_app.config["PAPERLESS_API"]
    #if not api.is_initialized:
    #await api.initialize()
    doc = await api.documents(doc_id)
    cache = current_app.config["CACHE"]
    #doc_types = await api.document_types.all()
    #type = await api.document_types(doc.document_type)
    type = await cache.getDocumentTypeNameByID(doc.document_type)
    correspondent = await cache.getCorrespondentNameByID(doc.correspondent)
    path = await cache.getStoragePathNameByID(doc.storage_path)
    tags = await cache.getTagListNamesByID(doc.tags)
    thumb = f"{current_app.config['PAPERLESS_BASE_URL']}/api/documents/{doc_id}/thumb/"
    #thumb = await doc.get_thumbnail()
    response_data = {
        "title": doc.title,
        "correspondent": correspondent,
        "type": type,
        "storage_path": path,
        "tags": tags,
        "thumbnail_url": thumb  # Jetzt verweist es auf die neue Proxy-Route
    }
    logging.debug(f"Document '{doc.title}' is an {type} from {correspondent} at {path}.")
    return jsonify(response_data), 200

@documents_bp.route('/doc/list_inbox', methods=['GET'])
async def inbox_list():
    inboxlist = []
    search = f"tag:{current_app.config['INBOX_TAG']}"
    async for document in current_app.config["PAPERLESS_API"].documents.search(search):
        inboxlist.append(document.id)
    logging.debug(inboxlist)
    return jsonify(inboxlist), 200

async def set_tag(doc_id, tag_names):
    api = current_app.config["PAPERLESS_API"]
    cache = current_app.config["CACHE"]

    if not doc_id or not tag_names:
        return jsonify({"error": "doc_id and tag_names (list) are required"}), 400

    # Convert tag names to tag IDs
    tag_ids_to_add = []
    tag_ids_to_remove = []

    for tag_name in tag_names:
        remove_tag = tag_name.strip().startswith('-')
        clean_tag_name = tag_name.strip().lstrip('-')  # Remove leading '-'
        tag_id = await cache.getTagIDByName(clean_tag_name)

        if not tag_id:
            return jsonify({"error": f"Tag '{clean_tag_name}' not found"}), 404

        if remove_tag:
            tag_ids_to_remove.append(tag_id)
        else:
            tag_ids_to_add.append(tag_id)
        
    # Fetch document from Paperless
    document = await api.documents(doc_id)

    # Current tags of the document
    current_tags = document.tags

    # Remove tags
    for tag_id in tag_ids_to_remove:
        if tag_id in current_tags:
            current_tags.remove(tag_id)

    # Add tags
    for tag_id in tag_ids_to_add:
        if tag_id not in current_tags:
            current_tags.append(tag_id)

    # Send PATCH request to update tags
    
    document.tags = current_tags
    success = await document.update()
    return success

@documents_bp.route('/doc/set_tag', methods=['POST'])
async def tag_document():
    data = await request.get_json()
    doc_id = data.get("doc_id")
    tag_names = data.get("tag_names", [])  
    
    success= tag_document(doc_id, tag_names)
    if success:
        return jsonify({"message": f"Tags {tag_names} successfully updated for document {doc_id}"}), 200
    else:
        return jsonify({"error": "Error updating document tags"}), 500