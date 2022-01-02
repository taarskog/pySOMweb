"""
A client library to control garage door operators produced by SOMMER through their SOMweb device.

The package is created as part of an extension to Home Assistant. There are no dependencies and no
references to Home Assistant, so you can use the package directly from python or integrate it with
any other home automation system.
"""
import asyncio
from logging import exception
from typing import List  # , Tuple
from aiohttp.client import ClientSession
from .httpclient import HttpClient

from .const import (
    CHECK_DOOR_STATE_INTERVAL,
    DEFAULT_DOOR_STATE_CHANGE_TIMEOUT,
    LOGGER,
    RE_WEBTOKEN,
    RE_DOORS,
    SOMWEB_ALIVE_URI,
    SOMWEB_AUTH_URI,
    SOMWEB_DOOR_STATUS_URI,
    SOMWEB_TOGGLE_DOOR_STATUS_URI,
)
from .models import (
    AuthResponse,
    Credentials,
    Door,
    DoorActionType,
    DoorStatusType,
)


class SomwebClient:
    """
    Client for performing operation on SOMMER garage doors, barriers, etc.
    connected to a Somweb device.
    """

    __udi: int
    __credentials: Credentials
    __http_client: HttpClient
    __current_token: str
    __current_page_content: str

    __door_status_types = {
        "OK": DoorStatusType.CLOSED,
        "FAIL": DoorStatusType.OPEN,
    }

    def __init__(
        self,
        somweb_udi: int,
        username: str,
        password: str,
        session: ClientSession = None,
    ):
        """
        Parameters
        ----------
        somweb_udi: int, required
            SOMweb UDI as found on the physical device
            (and under information on the SOMweb logged in page)

        username: str, required
            Username

        password: str, required
            Password

        session: ClientSession, optional
            The connection pool to use. A new is created if none is provided
        """
        self.__udi = somweb_udi
        self.__credentials = Credentials(username, password)
        self.__http_client = HttpClient(somweb_udi, session)

        self.__current_token = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, *excinfo):
        LOGGER.info("Closing http client")
        await self.__http_client.close()

    async def close(self) -> None:
        """Close the client

        Release all acquired resources such as the underlying http client.
        """
        if not self.closed:
            await self.__http_client.close()
            self.__http_client = None

    @property
    def closed(self) -> bool:
        """Is client closed.

        A readonly property indicating if the client is in a closed state.

        Returns
        -------
        bool: True if the client is in a closed state; otherwise False
        """
        return self.__http_client is None or self.__http_client.closed

    @property
    def udi(self) -> int:
        """SOMweb UDI.

        A readonly property.
        """
        return self.__udi

    async def is_alive(self) -> bool:
        """SOMweb device available and responding

        Does not require authentication and should be called to verify that
        the SOMweb device is available and ready to accept calls.

        Returns
        -------
        bool: True if SOMweb is available; otherwise False
        """
        try:
            response = await self.__http_client.get(SOMWEB_ALIVE_URI)
            return response.ok and "1" == await response.text()
        # pylint: disable=broad-except
        except Exception as ex:
            LOGGER.exception("SomWeb not reachable.", exc_info=ex)
            return False

    async def authenticate(self) -> AuthResponse:
        """Authenticate or re-authenticate

        Called for initial authentication and to re-authenticate if token has expired.
        It is a good idea to call autjenticate and retry if an operation fails.

        Returns
        -------
        AuthResponse: Current token and logged in webpage containing information
        on available doors (use get_doors_from_page_content)
        """
        form_data = {
            "login": self.__credentials.username,
            "pass": self.__credentials.password,
            "send-login": "Sign in",
        }

        try:
            response = await self.__http_client.post(SOMWEB_AUTH_URI, form_data)
            if not response.ok:
                LOGGER.error("Authentication failed. Reason: %s", response.reason)
                return AuthResponse()

            self.__current_page_content = await response.text()
            self.__current_token = self.__extract_web_token(self.__current_page_content)
            if self.__current_token is None:
                return AuthResponse(False, None, self.__current_page_content)

            return AuthResponse(True, self.__current_token, self.__current_page_content)
        # pylint: disable=broad-except
        except Exception as ex:
            LOGGER.exception("Authentication failed", exc_info=ex)
            return AuthResponse()

    async def get_door_status(self, door_id: int) -> DoorStatusType:
        """Get door status

        Get the current door status/state. Note that this integration does not provide
        information on an ongoing operation. Thus a door being closed will be reported
        as open until it has been completly closed and vice versa.

        Parameters
        ----------
        door_id: int, required
            Id of the door

        Returns
        -------
        DoorStatusType: Door status
        """
        status = (
            1  # 1 = closed and 0 = open - SOMweb returns "OK" if sent status equals
        )
        # actual status or "FAIL" if status is the opposite
        bit = 0  # When set to 1 seems to define that 1 is to be returned if sent status
        # matches actual status - if they don't match return is always FALSE
        url = f"{SOMWEB_DOOR_STATUS_URI}?numdoor={door_id}&status={status}&bit={bit}"

        response = await self.__http_client.get(url)
        if not response.ok:
            LOGGER.error("Failed getting door status. Reason: %s", response.reason)
            exception("Failed getting door status. Reason: %s", response.reason)

        return self.__door_status_types.get(
            await response.text(), DoorStatusType.UNKNOWN
        )

    def get_doors(self) -> List[Door]:
        """Get list of available doors

        Uses page content from last authentication to parse out a list of doors

        Returns
        -------
        List[Door]: List of doors connected to the SOMweb device
        """
        return self.get_doors_from_page_content(self.__current_page_content)

    def get_doors_from_page_content(self, page_content: str) -> List[Door]:
        """Get list of available doors

        Returns a list of available doors from the parsed SOMweb page

        Parameters
        ----------
        page_content: str, required
            Page content as returned in AuthResponse after a call to authenticate

        Returns
        -------
        List[Door]: List of doors connected to the SOMweb device
        """
        matches = RE_DOORS.finditer(page_content)
        doors = list(map(lambda m: Door(int(m.group("id")), m.group("name")), matches))
        return doors

    async def wait_for_door_state(
        self,
        door_id: int,
        state: DoorStatusType,
        timeout_in_seconds: float = DEFAULT_DOOR_STATE_CHANGE_TIMEOUT,
    ) -> bool:
        """Wait for a door to reach the requested state

        Call this after performing a door action to wait for the operation to complete or
        until maximum wait time has been reached.

        Parameters
        ----------
        door_id: int, required
            Id of the door

        state: DoorStatusType, required
            The requested door state to wait for

        timeout_in_seconds: float, optional
            Maximum time in seconds to wait for the door to reach the epxted state
            (default is 60 seconds)

        Returns
        -------
        bool: True when door has reached the expected state, or False if timeout occurred
        """

        async def wait_for_state_loop(door_id: int, state: DoorStatusType) -> None:
            while DoorStatusType(state) != DoorStatusType(
                await self.get_door_status(door_id)
            ):
                await asyncio.sleep(CHECK_DOOR_STATE_INTERVAL)

        try:
            await asyncio.wait_for(
                wait_for_state_loop(door_id, state), timeout_in_seconds
            )
            return True
        except asyncio.TimeoutError:
            LOGGER.warning("Timeout waiting for door state")
            return False

    async def open_door(self, door_id: int, token: str = None) -> bool:
        """Open door

        Open a door. No action is taken if the door is already open.

        Parameters
        ----------
        door_id: int, required
            Id of the door to perform the action on

        token: str, optional
            Usually not provided as the token is tracked internally

        Returns
        -------
        bool: True if operation succeeded. Note that this does not mean that the door operation
        has completed, just that the operation has been accpeted by the SOMweb device
        """
        return await self.door_action(door_id, DoorActionType.OPEN, token)

    async def close_door(self, door_id: int, token: str = None) -> bool:
        """Close door

        Close a door. No action is taken if the door is already closed.

        Parameters
        ----------
        door_id: int, required
            Id of the door to perform the action on

        token: str, optional
            Usually not provided as the token is tracked internally

        Returns
        -------
        bool: True if operation succeeded. Note that this does not mean that the door operation
        has completed, just that the operation has been accpeted by the SOMweb device
        """
        return await self.door_action(door_id, DoorActionType.CLOSE, token)

    async def door_action(
        self, door_id: int, door_action: DoorActionType, token: str = None
    ) -> bool:
        """Perform an action on a door

        Open or close a door. No action is taken if the door is already in the requested postion.

        Parameters
        ----------
        door_id: int, required
            Id of the door to perform the action on

        door_action: DoorActionType, required
            The action to perform on the door

        token: str, optional
            Usually not provided as the token is tracked internally

        Returns
        -------
        bool: True if operation succeeded. Note that this does not mean that the door operation
        has completed, just that the operation has been accpeted by the SOMweb device
        """
        door_action_to_status_switcher = {
            DoorActionType.CLOSE: DoorStatusType.CLOSED,
            DoorActionType.OPEN: DoorStatusType.OPEN,
        }
        requested_door_status = door_action_to_status_switcher.get(door_action)
        return await self.get_door_status(
            door_id
        ) == requested_door_status or await self.toogle_door_position(door_id, token)

    async def toogle_door_position(self, door_id: int, token: str = None) -> bool:
        """Toggles a door postion

        Open a closed door or vice versa. If token is not provided, then the internally tracked
        token is used (this is the normal operation and this property may be deprecated and
        removed in the near future)

        Parameters
        ----------
        door_id: int, required
            Id of the door to open/close

        token: str, optional
            Usually not provided as the token is tracked internally

        Returns
        -------
        bool: True if operation succeeded. Note that this does not mean that the door operation
        has completed, just that the operation has been accpeted by the SOMweb device
        """
        web_token = token if token is not None else self.__current_token
        LOGGER.debug("Using %s token", "provided" if token is not None else "internal")
        url = f"{SOMWEB_TOGGLE_DOOR_STATUS_URI}?numdoor={door_id}&status=0&webtoken={web_token}"
        response = await self.__http_client.get(url)
        return response.ok and "OK" == await response.text()

    def __extract_web_token(self, html_content: str) -> str:
        """Parse web token from SOMweb HTML"""
        match = RE_WEBTOKEN.search(html_content)
        return None if match is None else match.group("webtoken")
