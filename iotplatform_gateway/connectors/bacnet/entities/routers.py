

from asyncio import Lock


class Routers:
    def __init__(self):
        self.__lock = Lock()
        self.__router_info_cache = {}

    async def add_router_info(self, address, info):
        await self.__lock.acquire()
        try:
            if address not in self.__router_info_cache:
                self.__router_info_cache[address] = info
        finally:
            self.__lock.release()

    async def get_router_info_by_address(self, address):
        await self.__lock.acquire()
        try:
            return self.__router_info_cache.get(address)
        finally:
            self.__lock.release()
