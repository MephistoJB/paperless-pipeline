from quart import Blueprint, request, jsonify, current_app  # Import necessary modules
import logging  # Consolidating imports

# Blueprint for document-related API endpoints
documents_bp = Blueprint("documents", __name__)

"""
Fetches detailed information about a document by its ID.

Parameters:
- doc_id (int): The unique identifier of the document.

Returns:
- JSON response containing document details such as title, correspondent, type, storage path, tags, and thumbnail URL.
"""
@documents_bp.route('/doc/get_info/<int:doc_id>', methods=['GET'])
async def document_info(doc_id):
    api = current_app.config["PAPERLESS_API"]  # Retrieve Paperless API instance
    doc = await api.documents(doc_id)  # Fetch document details
    cache = current_app.config["CACHE"]  # Retrieve cache instance

    # Retrieve related metadata from cache
    type = await cache.getDocumentTypeNameByID(doc.document_type)
    correspondent = await cache.getCorrespondentNameByID(doc.correspondent)
    path = await cache.getStoragePathNameByID(doc.storage_path)
    tags = await cache.getTagListNamesByID(doc.tags)

    # Construct the thumbnail URL
    thumb = f"{current_app.config['PAPERLESS_BASE_URL']}/api/documents/{doc_id}/thumb/"

    # Prepare response data
    response_data = {
        "title": doc.title,
        "correspondent": correspondent,
        "type": type,
        "storage_path": path,
        "tags": tags,
        "thumbnail_url": thumb  # Now references the new proxy route
    }

    logging.debug(f"Document '{doc.title}' is an {type} from {correspondent} at {path}.")
    return jsonify(response_data), 200


@documents_bp.route('/doc/list_correspondents', methods=['GET'])
async def list_correspondents():
    cache = current_app.config["CACHE"]  # Retrieve cache instance
    correspondents = await cache.getAllCorrespondents()
    return jsonify(correspondents)

@documents_bp.route('/doc/list_types', methods=['GET'])
async def list_types():
    cache = current_app.config["CACHE"]  # Retrieve cache instance
    types = await cache.getAllTypes()
    return jsonify(types)

@documents_bp.route('/doc/list_paths', methods=['GET'])
async def list_paths():
    cache = current_app.config["CACHE"]  # Retrieve cache instance
    paths = await cache.getAllPaths()
    return jsonify(paths)

"""
Lists all documents that are currently in the inbox.

Returns:
- JSON response containing a list of document IDs tagged as inbox documents.
"""
@documents_bp.route('/doc/list_inbox', methods=['GET'])
async def inbox_list():
    if current_app.config["PAPERLESS_API"].is_initialized:
        inboxlist = []
        search = f"tag:{current_app.config['INBOX_TAG']}"  # Search for inbox-tagged documents

        # Fetch all matching documents asynchronously
        async for document in current_app.config["PAPERLESS_API"].documents.search(search):
            inboxlist.append(document.id)
        return jsonify(inboxlist), 200
    else:
        return jsonify({"Error: Connection to Paperless-NGX not established "}), 404


"""
Assigns or removes tags from a document.

Parameters:
- doc_id (int): The ID of the document to modify.
- tag_names (list of str): List of tag names to add or remove.

Returns:
- JSON success message if successful.
- JSON error message if tag not found or an error occurs.
"""
async def set_tag(doc_id, tag_names):
    api = current_app.config["PAPERLESS_API"]  # Retrieve API instance
    cache = current_app.config["CACHE"]  # Retrieve cache instance

    if not doc_id or not tag_names:
        return jsonify({"error": "doc_id and tag_names (list) are required"}), 400

    # Prepare lists for tag IDs to add and remove
    tag_ids_to_add = []
    tag_ids_to_remove = []

    for tag_name in tag_names:
        remove_tag = tag_name.strip().startswith('-')  # Determine if it's a removal operation
        clean_tag_name = tag_name.strip().lstrip('-')  # Clean tag name for lookup
        tag_id = await cache.getTagIDByName(clean_tag_name)  # Retrieve tag ID

        if not tag_id:
            return jsonify({"error": f"Tag '{clean_tag_name}' not found"}), 404  # Return error if tag does not exist

        if remove_tag:
            tag_ids_to_remove.append(tag_id)
        else:
            tag_ids_to_add.append(tag_id)

    # Fetch the document from Paperless
    document = await api.documents(doc_id)

    # Get the current tags assigned to the document
    current_tags = document.tags

    # Remove specified tags
    for tag_id in tag_ids_to_remove:
        if tag_id in current_tags:
            current_tags.remove(tag_id)

    # Add new tags if they are not already assigned
    for tag_id in tag_ids_to_add:
        if tag_id not in current_tags:
            current_tags.append(tag_id)

    # Update document tags
    document.tags = current_tags
    success = await document.update()  # Commit changes asynchronously

    return success  # Return success status

"""
API endpoint to update document tags via a POST request.

Parameters:
- doc_id (int): The unique identifier of the document.

Expected JSON payload:
- "tag_names" (list of str): A list of tag names to assign or remove.

Returns:
- 200 OK if tags were successfully updated.
- 500 Internal Server Error if an issue occurred.
"""
@documents_bp.route('/doc/set_tag/<int:doc_id>', methods=['POST'])
async def tag_document(doc_id):
    data = await request.get_json()  # Parse incoming JSON request
    #doc_id = data.get("doc_id")  # Extract document ID
    tag_names = data.get("tags", [])  # Extract tag names, default to empty list

    success = await set_tag(doc_id, tag_names)  # Call set_tag function asynchronously

    if success:
        return jsonify({"message": f"Tags {tag_names} successfully updated for document {doc_id}"}), 200
    else:
        return jsonify({"error": "Error updating document tags"}), 500  # Return error if operation failed
    
@documents_bp.route('/doc/set_correspondant/<int:doc_id>', methods=['POST'])
async def cor_document(doc_id):
    api = current_app.config["PAPERLESS_API"]  # Retrieve API instance
    cache = current_app.config["CACHE"]  # Retrieve cache instance
    data = await request.get_json()  # Parse incoming JSON request
    #doc_id = data.get("doc_id")  # Extract document ID
    correspondent = data.get("correspondent", "")  # Extract tag names, default to empty list
    # Fetch the document from Paperless
    document = await api.documents(doc_id)
    document.correspondent = await cache.getCorrespondantIDByName(correspondent)

    success = await document.update()  # Commit changes asynchronously

    if success:
        return jsonify({"message": f"Correspondant {correspondent} successfully updated for document {doc_id}"}), 200
    else:
        return jsonify({"error": "Error updating document correspondant"}), 500  # Return error if operation failed
    
@documents_bp.route('/doc/set_type/<int:doc_id>', methods=['POST'])
async def type_document(doc_id):
    api = current_app.config["PAPERLESS_API"]  # Retrieve API instance
    cache = current_app.config["CACHE"]  # Retrieve cache instance
    data = await request.get_json()  # Parse incoming JSON request
    #doc_id = data.get("doc_id")  # Extract document ID
    type = data.get("type", "")  # Extract tag names, default to empty list
    # Fetch the document from Paperless
    document = await api.documents(doc_id)
    document.type = await cache.getTypeIDByName(type)


    #########TEST AREA###############
    # Get the current tags assigned to the document
    current_tags = document.tags
    testTag = await cache.getTagIDByName("test")
    current_tags.append(testTag)
    document.tags = current_tags


    success = await document.update()  # Commit changes asynchronously

    if success:
        return jsonify({"message": f"Type {type} successfully updated for document {doc_id}"}), 200
    else:
        return jsonify({"error": "Error updating document type"}), 500  # Return error if operation failed
    
@documents_bp.route('/doc/set_path/<int:doc_id>', methods=['POST'])
async def path_document(doc_id):
    api = current_app.config["PAPERLESS_API"]  # Retrieve API instance
    cache = current_app.config["CACHE"]  # Retrieve cache instance
    data = await request.get_json()  # Parse incoming JSON request
    #doc_id = data.get("doc_id")  # Extract document ID
    path = data.get("path", "")  # Extract tag names, default to empty list
    # Fetch the document from Paperless
    document = await api.documents(doc_id)
    document.path = await cache.getPathIDByName(path)


    #########TEST AREA###############
    # Get the current tags assigned to the document
    current_tags = document.tags
    testTag = await cache.getTagIDByName("test")
    current_tags.append(testTag)
    document.tags = current_tags


    success = await document.update()  # Commit changes asynchronously

    if success:
        return jsonify({"message": f"Correspondant {correspondant} successfully updated for document {doc_id}"}), 200
    else:
        return jsonify({"error": "Error updating document tags"}), 500  # Return error if operation failed