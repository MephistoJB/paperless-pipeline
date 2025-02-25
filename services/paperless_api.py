import logging
import copy
import requests

class PaperlessAPI:
    # Initializes the PaperlessAPI client.
    # Parameters:
    # - api_url (str): Base URL of the Paperless API.
    # - auth_token (str): Authentication token for API access.
    # - logger (logging.Logger): Logger instance for logging.
    def __init__(self, api_url, auth_token, logger=None):
        if logger is None:
            raise ValueError("Logger cannot be None")
        if not api_url:
            raise ValueError("Paperless URL cannot be None")
        if not auth_token:
            raise ValueError("Paperless Auth Token cannot be None")

        self._logger = logger
        self._api_url = api_url.rstrip('/')  # Remove trailing slash if present
        self._auth_token = auth_token
        self._headers = {"Authorization": f"Token {self._auth_token}"}

    # Checks if the Paperless API is reachable.
    # Returns:
    # - bool: True if the API is reachable, otherwise False.
    def test_connection(self):
        response = requests.get(f"{self._api_url}/", headers=self._headers)
        return response.ok

    # Retrieves metadata of a document by its ID.
    # Parameters:
    # - document_id (int): The ID of the document.
    # Returns:
    # - dict: Document metadata if found, otherwise an empty dictionary.
    def get_document_metadata_by_id(self, document_id):
        response = requests.get(f"{self._api_url}/documents/{document_id}/metadata/", headers=self._headers)
        if response.ok:
            return response.json()
        self._logger.error(f"Failed to fetch metadata for document {document_id}. Status: {response.status_code}")
        return {}

    # Retrieves full document details by ID.
    # Parameters:
    # - document_id (int): The ID of the document.
    # Returns:
    # - dict: Document details if found, otherwise an empty dictionary.
    def get_document_by_id(self, document_id):
        return self.__get_item_by_id("documents", document_id)

    # Retrieves a document's thumbnail preview by ID.
    # Parameters:
    # - document_id (int): The ID of the document.
    # Returns:
    # - Response: Thumbnail image response if found, otherwise an empty dictionary.
    def get_document_preview_by_id(self, document_id):
        response = requests.get(f"{self._api_url}/documents/{document_id}/thumb/", headers=self._headers)
        if response.ok:
            return response
        self._logger.error(f"Error fetching document preview for ID {document_id}. Status: {response.status_code}")
        return {}

    # Retrieves tag details by ID.
    # Parameters:
    # - tag_id (int): The ID of the tag.
    # Returns:
    # - dict: Tag details if found, otherwise an empty dictionary.
    def get_tag_by_id(self, tag_id):
        return self.__get_item_by_id("tags", tag_id)

    # Retrieves all tags as a dictionary {tag_name: tag_id}.
    # Returns:
    # - dict: Dictionary of all tags.
    def get_all_tags(self):
        return self.__get_all_items_as_dict("tags", "name", "id")

    # Retrieves all correspondents as a dictionary {correspondent_name: correspondent_id}.
    # Returns:
    # - dict: Dictionary of all correspondents.
    def get_all_correspondents(self):
        return self.__get_all_items_as_dict("correspondents", "name", "id")

    # Retrieves all documents as a dictionary {document_title: document_id}.
    # Returns:
    # - dict: Dictionary of all documents.
    def get_all_documents(self):
        return self.__get_all_items_as_dict("documents", "title", "id")

    # Retrieves all document types as a dictionary {type_name: type_id}.
    # Returns:
    # - dict: Dictionary of all document types.
    def get_all_types(self):
        return self.__get_all_items_as_dict("document_types", "name", "id")

    # Retrieves all storage paths as a dictionary {path_name: path_id}.
    # Returns:
    # - dict: Dictionary of all storage paths.
    def get_all_paths(self):
        return self.__get_all_items_as_dict("storage_paths", "name", "id")

    # Retrieves all documents currently in the inbox, ordered by last modified date.
    # Returns:
    # - dict: Dictionary {document_id: document_title} of inbox documents.
    def get_inbox_documents(self, tag):
        response = requests.get(f"{self._api_url}/documents/?tags__name__iexact={tag}&ordering=-modified", headers=self._headers)
        if response.ok:
            results = response.json().get('results', [])
            return {doc['id']: doc['title'] for doc in results} if results else {}
        self._logger.error(f"Failed to fetch inbox documents. Status: {response.status_code}")
        return {}

    # Updates document metadata using a PATCH request.
    # Parameters:
    # - document_id (int): The ID of the document to update.
    # - data (dict): The updated metadata fields.
    # Returns:
    # - Response: The response from the PATCH request.
    async def patch_document(self, document_id, data):
        return requests.patch(
            f"{self._api_url}/documents/{document_id}/",
            headers={**self._headers, 'Content-type': "application/json"},
            json=data
        )

    # Fetches all items of a given type from the API.
    # Parameters:
    # - item_type (str): The API endpoint name (e.g., "tags").
    # Returns:
    # - dict: JSON response with all items, or an empty dictionary if the request fails.
    def __get_all_items(self, item_type):
        response = requests.get(f"{self._api_url}/{item_type}/", headers=self._headers)
        if response.ok:
            return response.json()
        self._logger.error(f"Failed to fetch {item_type}. Status: {response.status_code}")
        return {}

    # Fetches a specific item by ID from the API.
    # Parameters:
    # - item_type (str): The API endpoint name (e.g., "tags").
    # - item_id (int): The ID of the item.
    # Returns:
    # - dict: JSON response with item details, or an empty dictionary if not found.
    def __get_item_by_id(self, item_type, item_id):
        if not item_id:
            return {}

        response = requests.get(f"{self._api_url}/{item_type}/{item_id}/", headers=self._headers)
        if response.ok:
            return response.json()
        self._logger.error(f"Failed to fetch {item_type} with ID {item_id}. Status: {response.status_code}")
        return {}

    # Fetches all items of a given type and returns them as a dictionary.
    # Parameters:
    # - item_type (str): The API endpoint name (e.g., "tags").
    # - key_field (str): The field to use as the dictionary key (e.g., "name").
    # - value_field (str): The field to use as the dictionary value (e.g., "id").
    # Returns:
    # - dict: Dictionary {key_field: value_field} of fetched items.
    def __get_all_items_as_dict(self, item_type, key_field, value_field):
        response = self.__get_all_items(item_type)
        items = response.get('results', [])
        item_dict = {item[key_field]: item[value_field] for item in items} if items else {}

        self._logger.debug(f"Fetched {len(item_dict)} items from {item_type}.")
        return item_dict


 #######maybe for later


    # Fetches a custom field by name. The name must be unique.
    # Parameters:
    # - custom_field_name (str): Name of the custom field.
    # Returns:
    # - dict: Custom field details if found, otherwise an empty dictionary.
    def get_custom_field_by_name(self, custom_field_name):
        if not custom_field_name:
            self._logger.error("Custom field name cannot be empty.")
            return {}

        url_encoded_name = custom_field_name.replace("_", "%20")
        response = requests.get(f"{self._api_url}/custom_fields/?name__icontains={url_encoded_name}", headers=self._headers)

        results = response.json().get("results", [])
        return copy.deepcopy(results[0]) if results else {}