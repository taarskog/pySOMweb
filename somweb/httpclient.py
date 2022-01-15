""" SOMweb Client """
from asyncio import AbstractEventLoop, get_event_loop
from typing import Any, Tuple
import aiohttp

from aiohttp.client import ClientSession
from aiohttp.client_reqrep import ClientResponse

from .const import LOGGER, REQUEST_TIMEOUT, SOMWEB_URI_TEMPLATE

class HttpClient:
    """ HttpClient for the SOMweb lib."""
    __base_url: Tuple[str]
    __session: ClientSession = None
    __private_session: bool = False

    def __init__(
        self,
        somweb_udi: int,
        session: ClientSession = None,
        loop: AbstractEventLoop = None,
    ):
        """
        Initialize SOMweb authenticator
        """
        self.__base_url = (SOMWEB_URI_TEMPLATE.format(somweb_udi),)
        if session is None:
            self.__session = aiohttp.ClientSession()
            self.__private_session = True
        else:
            self.__session = session

        self.loop = get_event_loop() if loop is None else loop

    async def __aenter__(self):
        return self

    async def __aexit__(self, *excinfo):
        if self.__private_session:
            LOGGER.info("Closing my http session")
            await self.close()

    async def close(self) -> None:
        """Close underlying session.

        Release all acquired resources.
        """
        if not self.closed:
            await self.__session.close()
            self.__session = None

    @property
    def closed(self) -> bool:
        """Is session closed.

        A readonly property.
        """
        return self.__session is None or self.__session.closed

    async def get(self, relative_url: str) -> ClientResponse:
        """SOMweb device available and responding"""
        url = f"{self.__base_url[0]}{relative_url}"
        try:
            async with self.__session.get(url, timeout=REQUEST_TIMEOUT) as response:
                assert 400 > response.status  # response.ok
                await response.text()
                return response
        except Exception as ex:
            LOGGER.exception("Not reachable %s", url, exc_info=ex)
            raise

    async def post(self, relative_url: str, form_data: Any = None) -> ClientResponse:
        """SOMweb device available and responding"""
        url = f"{self.__base_url[0]}{relative_url}"
        try:
            async with self.__session.post(
                url, data=form_data, timeout=REQUEST_TIMEOUT
            ) as response:
                assert 400 > response.status  # response.ok
                await response.text()
                return response
        except Exception as ex:
            LOGGER.exception("POST to '%s' failed", url, exc_info=ex)
            raise
