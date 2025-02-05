import logging
import os
import copy
import requests
from datetime import date
from pathlib import Path

class PaperlessAPI:
    def __init__(self, api_url, auth_token, logger=None):
        if logger is None:
            raise ValueError("Logger cannot be None")
        if api_url is None:
            raise ValueError("Paperless URL cannot be None")
        if auth_token is None:
            raise ValueError("Paperless Auth Token cannot be None")
        self._logger = logger
        self._api_url = api_url
        self._auth_token = auth_token

    def get_document_metadata_by_id(self, document_id):
        response = requests.get(f"{self._api_url}/documents/{document_id}/metadata/",
                                headers = {"Authorization": f"Token {self._auth_token}"})
        if response.ok:
            return response.json()
        else:
            return {}
    
    def get_document_by_id(self, document_id):
        response = requests.get(f"{self._api_url}/documents/{document_id}/",
                                headers = {"Authorization": f"Token {self._auth_token}"})
        if response.ok:
            return response.json()
        else:
            return {}
        
    def test_connection(self):
        response = requests.get(f"{self._api_url}/",
                                headers = {"Authorization": f"Token {self._auth_token}"})
        if response and response.ok:
            return True
        else:
            return False
        
 
    async def patch_document(self, document_id, data):
        return requests.patch(f"{self._api_url}/documents/{document_id}/",
                               headers = {"Authorization": f"Token {self._auth_token}", 'Content-type': "application/json" },
                               json = data)
    

    #######maybe for later
    
    def _get_item_by_id(self, item_type, item_id):
        if item_id:
            response = requests.get(f"{self._api_url}/{item_type}/{item_id}/",
                                headers = {"Authorization": f"Token {self._auth_token}"})
            if response.ok:
                return response.json()
        return {}


    
    def get_customfield_from_name(self, customfield_name):
        result = {}

        # rework underscore's into url spaces
        url_reworked_customfield_name = customfield_name.replace("_","%20")

        response = requests.get(f"{self._api_url}/custom_fields/?name__icontains={url_reworked_customfield_name}", headers = {"Authorization": f"Token {self._auth_token}"})

        if len(response.json().get("results")) > 1:
            self._logger.error("Found more than one custom_field with specified name in filter. Name has to be unique.")
        elif len(response.json().get("results")) == 0:
            self._logger.error("Found no custom fields with this name.")
        else:
            self._logger.debug(f"Found custom_field: \"{response.json().get('results')[0].get('name')}\" with id {response.json().get('results')[0].get('id')}. Building custom_fields object definition.")

        result = copy.deepcopy(response.json().get("results")[0])

        return result