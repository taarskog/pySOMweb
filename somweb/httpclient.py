"""HttpClient for the SOMweb lib."""
from asyncio import AbstractEventLoop, get_event_loop
from typing import Any, tuple
import aiohttp

from aiohttp.client import ClientSession
from aiohttp.client_reqrep import ClientResponse

from .const import LOGGER, REQUEST_TIMEOUT

class HttpClient:
    """HttpClient for the SOMweb lib."""

    __base_url: tuple[str]
    __session: ClientSession = None
    __private_session: bool = False

    def __init__(
        self,
        somweb_url: str,
        session: ClientSession = None,
        loop: AbstractEventLoop = None,
    ):
        """Initialize SOMweb authenticator."""
        self.__base_url = (somweb_url,)
        if session is None:
            self.__session = aiohttp.ClientSession()
            self.__private_session = True
        else:
            self.__session = session

        self.loop = get_event_loop() if loop is None else loop

    async def __aenter__(self):  # noqa: D105
        return self

    async def __aexit__(self, *excinfo):  # noqa: D105
        if self.__private_session:
            LOGGER.info("Closing my http session")
            await self.async_close()

    async def async_close(self) -> None:
        """
        Close underlying session.

        Release all acquired resources.
        """
        if not self.closed:
            if self.__private_session:
                await self.__session.close()
            self.__session = None

    @property
    def closed(self) -> bool:
        """
        Is session closed.

        A readonly property.
        """
        return self.__session is None or self.__session.closed

    async def async_get(self, relative_url: str) -> ClientResponse:
        """
        Asynchronously sends a GET request to the specified relative URL and returns the response.

        Args:
            relative_url (str): The relative URL to send the GET request to.

        Returns:
            ClientResponse: The response object representing the result of the GET request.

        Raises:
            Exception: If an error occurs during the GET request.

        """
        url = f"{self.__base_url[0]}{relative_url}"

        try:
            async with self.__session.get(url, timeout=REQUEST_TIMEOUT) as response:
                # Setting cookie manually so it works with IP-addresses
                # not using aiohttp.ClientSession(cookie_jar=aiohttp.CookieJar(unsafe=True))
                # as we allow use of external ClientSession
                self.__session.cookie_jar.update_cookies(response.cookies) # Manually set cookies

                assert response.status < 400  # response.ok
                await response.text()
                return response
        except Exception: #as ex:
            #LOGGER.exception("Not reachable %s", url, exc_info=ex)
            raise

    async def async_post(self, relative_url: str, form_data: Any = None) -> ClientResponse:
        """
        Asynchronously sends a POST request to the specified relative URL and returns the response.

        Args:
            relative_url (str): The relative URL to send the POST request to.
            form_data (Any, optional): The form data to send with the POST request. Defaults to None.

        Returns:
            ClientResponse: The response object representing the result of the POST request.

        Raises:
            Exception: If an error occurs during the POST request.

        """
        url = f"{self.__base_url[0]}{relative_url}"
        try:
            async with self.__session.post(
                url, data=form_data, timeout=REQUEST_TIMEOUT
            ) as response:
                # Setting cookie manually so it works with IP-addresses
                # not using aiohttp.ClientSession(cookie_jar=aiohttp.CookieJar(unsafe=True))
                # as we allow use of external ClientSession
                self.__session.cookie_jar.update_cookies(response.cookies) # Manually set cookies

                assert response.status < 400  # response.ok
                await response.text()
                return response
        except Exception: # as ex:
            #LOGGER.exception("POST to '%s' failed", url, exc_info=ex)
            raise
