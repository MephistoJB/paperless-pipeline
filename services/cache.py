import asyncio
import time
import logging

class Cache:
    def __init__(self, paperless, cache_time):
        self._cache_time = cache_time
        self._api = paperless
        self._documentTypeCache = {"lastRefresh":None, "cache":[]}
        self._storagePathCache = {"lastRefresh":None, "cache":[]}
        self._correspondentCache = {"lastRefresh":None, "cache":[]}
        self._tagsCache = {"lastRefresh":None, "cache":[]}
    
    async def getDocumentTypeNameByID(self, key):
        docTypeName = await self.getItemByID(self._documentTypeCache, self._api.document_types, key)
        return docTypeName
    
    async def getCorrespondentNameByID(self, key):
        correspondentName = await self.getItemByID(self._correspondentCache, self._api.correspondents, key)
        return correspondentName
    
    async def getStoragePathNameByID(self, key):
        storagePathName = await self.getItemByID(self._storagePathCache, self._api.storage_paths, key)
        return storagePathName

    async def getTagNameByID(self, key):
        tagName = await self.getItemByID(self._tagsCache, self._api.tags, key)
        return tagName
    
    async def getTagListNamesByID(self, keys):
        tagList = []
        for key in keys:
            tagList.append(await self.getTagNameByID(key))
        return tagList
    
    async def getTagIDByName(self, name):
        tagID = await self.getItemByName(self._tagsCache, self._api.tags, name)
        return tagID
    
    async def getItemByName(self, cacheContainer, cachingElement, name):
        if cacheContainer["lastRefresh"] is None or cacheContainer["lastRefresh"] < time.time() - (self._cache_time * 60):
            await self.refreshCacheOfContainer(cacheContainer, cachingElement)

        for item in cacheContainer["cache"]:
            if item["name"] == name:
                return item["id"]
        return None

    async def getItemByID(self, cacheContainer, cachingElement, key):
        if cacheContainer["lastRefresh"] is None or cacheContainer["lastRefresh"] < time.time() - (self._cache_time * 60):
            await self.refreshCacheOfContainer(cacheContainer, cachingElement)

        for item in cacheContainer["cache"]:
            if item["id"] == key:
                return item["name"]
        return None

    async def refreshCacheOfContainer(self, cacheContainer, cachingElement):
        cacheContainer["lastRefresh"] = None
        cacheContainer["cache"] = []
        async for item in cachingElement:
            logging.debug(item.name)
            cacheContainer["cache"].append({"id":item.id, "name":item.name})
        cacheContainer["lastRefresh"] = time.time()
        logging.debug(cacheContainer)

    
