import time, logging

"""
Cache class for storing and retrieving document-related metadata to reduce API calls.

Parameters:
- paperless: API instance to fetch document-related data.
- cache_time (int): Time in minutes before cache expiration.
"""
class Cache:
    def __init__(self, paperless, cache_time: int):
        self._cache_time = cache_time
        self._api = paperless
        self._documentTypeCache = {"lastRefresh": None, "cache": []}
        self._storagePathCache = {"lastRefresh": None, "cache": []}
        self._correspondentCache = {"lastRefresh": None, "cache": []}
        self._tagsCache = {"lastRefresh": None, "cache": []}

    """
    Retrieves the document type name by its ID.

    Parameters:
    - key (int): Document type ID.

    Returns:
    - str: Corresponding document type name, or None if not found.
    """
    async def getDocumentTypeNameByID(self, key: int) -> str:
        return await self.getItemByID(self._documentTypeCache, self._api.document_types, key)

    """
    Retrieves the correspondent name by its ID.

    Parameters:
    - key (int): Correspondent ID.

    Returns:
    - str: Corresponding correspondent name, or None if not found.
    """
    async def getCorrespondentNameByID(self, key: int) -> str:
        return await self.getItemByID(self._correspondentCache, self._api.correspondents, key)

    """
    Retrieves the storage path name by its ID.

    Parameters:
    - key (int): Storage path ID.

    Returns:
    - str: Corresponding storage path name, or None if not found.
    """
    async def getStoragePathNameByID(self, key: int) -> str:
        return await self.getItemByID(self._storagePathCache, self._api.storage_paths, key)

    """
    Retrieves the tag name by its ID.

    Parameters:
    - key (int): Tag ID.

    Returns:
    - str: Corresponding tag name, or None if not found.
    """
    async def getTagNameByID(self, key: int) -> str:
        return await self.getItemByID(self._tagsCache, self._api.tags, key)

    """
    Retrieves a list of tag names by their IDs.

    Parameters:
    - keys (list[int]): List of tag IDs.

    Returns:
    - list[str]: List of corresponding tag names.
    """
    async def getTagListNamesByID(self, keys: list[int]) -> list[str]:
        return [await self.getTagNameByID(key) for key in keys]

    """
    Retrieves the tag ID by its name.

    Parameters:
    - name (str): Name of the tag.

    Returns:
    - int: Corresponding tag ID, or None if not found.
    """
    async def getTagIDByName(self, name: str) -> int:
        return await self.getItemByName(self._tagsCache, self._api.tags, name)
    
    async def getCorrespondantIDByName(self, name: str) -> int:
        return await self.getItemByName(self._correspondentCache, self._api.correspondents, name)
    
    async def getTypeIDByName(self, name: str) -> int:
        return await self.getItemByName(self._documentTypeCache, self._api.document_types, name)
    
    async def getPathIDByName(self, name: str) -> int:
        return await self.getItemByName(self._storagePathCache, self._api.storage_paths, name)
    

    async def getAllCorrespondents(self):
        return await self.getAllItems(self._correspondentCache, self._api.correspondents)
    
    async def getAllTypes(self):
        return await self.getAllItems(self._documentTypeCache, self._api.document_types)
    
    async def getAllPaths(self):
        return await self.getAllItems(self._storagePathCache, self._api.storage_paths)
    
    async def getAllItems(self, cacheContainer: dict, cachingElement):
        if cacheContainer["lastRefresh"] is None or cacheContainer["lastRefresh"] < time.time() - (self._cache_time * 60):
            await self.refreshCacheOfContainer(cacheContainer, cachingElement)
        return cacheContainer["cache"]

    """
    Retrieves an item ID by its name from the cache or API.

    Parameters:
    - cacheContainer (dict): Cache container for the specific data type.
    - cachingElement (async iterator): API source for the data.
    - name (str): The name of the item to search for.

    Returns:
    - int: ID of the item if found, otherwise None.
    """
    async def getItemByName(self, cacheContainer: dict, cachingElement, name: str) -> int:
        if cacheContainer["lastRefresh"] is None or cacheContainer["lastRefresh"] < time.time() - (self._cache_time * 60):
            await self.refreshCacheOfContainer(cacheContainer, cachingElement)

        for item in cacheContainer["cache"]:
            if item["name"] == name:
                return item["id"]
        return None

    """
    Retrieves an item name by its ID from the cache or API.

    Parameters:
    - cacheContainer (dict): Cache container for the specific data type.
    - cachingElement (async iterator): API source for the data.
    - key (int): The ID of the item to search for.

    Returns:
    - str: Name of the item if found, otherwise None.
    """
    async def getItemByID(self, cacheContainer: dict, cachingElement, key: int) -> str:
        if cacheContainer["lastRefresh"] is None or cacheContainer["lastRefresh"] < time.time() - (self._cache_time * 60):
            await self.refreshCacheOfContainer(cacheContainer, cachingElement)

        for item in cacheContainer["cache"]:
            if item["id"] == key:
                return item["name"]
        return None

    """
    Refreshes the cache for a given container by fetching the latest data.

    Parameters:
    - cacheContainer (dict): The cache container to refresh.
    - cachingElement (async iterator): API source for the data.

    Updates:
    - Resets cache and fetches the latest items asynchronously.
    """
    async def refreshCacheOfContainer(self, cacheContainer: dict, cachingElement) -> None:
        cacheContainer["lastRefresh"] = None  # Reset cache timestamp
        cacheContainer["cache"] = []  # Clear existing cache

        async for item in cachingElement:
            logging.debug(item.name)  # Log item name for debugging
            cacheContainer["cache"].append({"id": item.id, "name": item.name})  # Store new cache entry

        cacheContainer["lastRefresh"] = time.time()  # Update last refresh timestamp
        logging.debug(cacheContainer)  # Log updated cache contents