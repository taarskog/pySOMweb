"""
A client library to control garage door operators produced by SOMMER through their SOMweb device.

The package is created as part of an extension to Home Assistant. There are no dependencies and no
references to Home Assistant, so you can use the package directly from python or integrate it with
any other home automation system.
"""
from re import Pattern
import warnings
import asyncio
from logging import exception
from typing import List  # , Tuple
from aiohttp.client import ClientSession
from .httpclient import HttpClient

warnings.simplefilter('always', DeprecationWarning)

from .const import (
    CHECK_DOOR_STATE_INTERVAL,
    DEFAULT_DOOR_STATE_CHANGE_TIMEOUT,
    LOGGER,
    RE_FIRMWARE_VERSION,
    RE_IP_ADDRESS,
    RE_REMOTE_ACCESS,
    RE_TIME_ZONE,
    RE_USER_IS_ADMIN,
    RE_WEBTOKEN,
    RE_DOORS,
    RE_UDI,
    RE_WIFI_SIGNAL,
    SOMWEB_ALIVE_URI,
    SOMWEB_AUTH_URI,
    SOMWEB_CHECK_FOR_UPDATE_URI,
    SOMWEB_DEVICE_INFO_URI,
    SOMWEB_DOOR_STATUS_URI,
    SOMWEB_TOGGLE_DOOR_STATUS_URI,
    SOMWEB_URI_TEMPLATE,
)
from .models import (
    AuthResponse,
    Credentials,
    DeviceInfo,
    Door,
    DoorActionType,
    DoorStatusType,
)

def deprecated(func):
    def wrapper(*args, **kwargs):
        warnings.warn(
            f"{func.__name__} is deprecated and will be removed in the future.",
            category=DeprecationWarning,
            stacklevel=2
        )
        return func(*args, **kwargs)
    return wrapper

def get_value_using_regex(content: str, regex: Pattern, group_name: str) -> str:
    """Get value using regex"""

    match = regex.search(content)
    return None if match is None else match.group(group_name)

class SomwebClient:
    """
    Client for performing operation on SOMMER garage doors, barriers, etc.
    connected to a Somweb device.
    """

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
        url: str,
        username: str,
        password: str,
        session: ClientSession = None,
    ):
        """
        Parameters
        ----------
        somweb_url: str, required
            Url to SOMweb. Can be either the local url to the SomWeb device or the cloud url. Calling createUsingUdi is recommended when accessing device through the cloud service.

        username: str, required
            Username

        password: str, required
            Password

        session: ClientSession, optional
            The connection pool to use. A new is created if none is provided
        """
        self.__credentials = Credentials(username, password)
        self.__http_client = HttpClient(url, session)

        self.__current_token = None

    @classmethod
    def createUsingUdi(
        cls,
        somweb_udi: str,
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
        return cls(SOMWEB_URI_TEMPLATE.format(somweb_udi), username, password, session)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *excinfo):
        LOGGER.info("Closing http client")
        await self.__http_client.async_close()

    async def close(self) -> None:
        """Close the client

        Release all acquired resources such as the underlying http client.
        """
        if not self.closed:
            await self.__http_client.async_close()
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
    def udi(self) -> str:
        """SOMweb UDI.

        A readonly property.
        """
        if self.__current_page_content is None:
            return None
        else:
            match = RE_UDI.search(self.__current_page_content)
            return None if match is None else match.group("udi")

    @property
    def is_admin(self) -> bool:
        """Is user an administrator.

        A readonly property.
        """
        if self.__current_page_content is None:
            return None
        else:
            match = RE_USER_IS_ADMIN.search(self.__current_page_content)
            return False if match is None else True

    @deprecated
    async def is_alive(self):
        return await self.async_is_alive()

    async def async_is_alive(self) -> bool:
        """SOMweb device available and responding

        Does not require authentication and should be called to verify that
        the SOMweb device is available and ready to accept calls.

        Returns
        -------
        bool: True if SOMweb is available; otherwise False
        """
        try:
            response = await self.__http_client.async_get(SOMWEB_ALIVE_URI)
            return 400 > response.status and "1" == await response.text()
        # pylint: disable=broad-except
        except Exception as ex:
            LOGGER.exception("SomWeb not reachable.", exc_info=ex)
            return False

    @deprecated
    async def authenticate(self):
        return await self.async_authenticate()

    async def async_authenticate(self) -> AuthResponse:
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
            response = await self.__http_client.async_post(SOMWEB_AUTH_URI, form_data)
            if not 400 > response.status:
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

    @deprecated
    async def get_door_status(self, door_id: int) -> DoorStatusType:
        return await self.async_get_door_status(door_id)

    async def async_get_door_status(self, door_id: int) -> DoorStatusType:
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

        response = await self.__http_client.async_get(url)
        if not 400 > response.status:
            LOGGER.error("Failed getting door status. Reason: %s", response.reason)
            exception("Failed getting door status. Reason: %s", response.reason)

        resp_content = await response.text()

        return self.__door_status_types.get(
            resp_content, DoorStatusType.UNKNOWN
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

    @deprecated
    async def wait_for_door_state(
        self,
        door_id: int,
        state: DoorStatusType,
        timeout_in_seconds: float = DEFAULT_DOOR_STATE_CHANGE_TIMEOUT,
    ) -> bool:
        return await self.async_wait_for_door_state(door_id, state, timeout_in_seconds)

    async def async_wait_for_door_state(
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

        async def async_wait_for_state_loop(door_id: int, state: DoorStatusType) -> None:
            while DoorStatusType(state) != DoorStatusType(
                await self.get_door_status(door_id)
            ):
                await asyncio.sleep(CHECK_DOOR_STATE_INTERVAL)

        try:
            await asyncio.wait_for(
                async_wait_for_state_loop(door_id, state), timeout_in_seconds
            )
            return True
        except asyncio.TimeoutError:
            LOGGER.warning("Timeout waiting for door state")
            return False

    @deprecated
    async def open_door(self, door_id: int, token: str = None) -> bool:
        return await self.async_open_door(door_id, token)

    async def async_open_door(self, door_id: int, token: str = None) -> bool:
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

    @deprecated
    async def close_door(self, door_id: int, token: str = None) -> bool:
        return await self.async_close_door(door_id, token)

    async def async_close_door(self, door_id: int, token: str = None) -> bool:
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

    @deprecated
    async def door_action(
        self, door_id: int, door_action: DoorActionType, token: str = None
    ) -> bool:
        return await self.async_door_action(door_id, door_action, token)

    async def async_door_action(
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
        has completed, just that the operation has been accepted by the SOMweb device
        """
        door_action_to_status_switcher = {
            DoorActionType.CLOSE: DoorStatusType.CLOSED,
            DoorActionType.OPEN: DoorStatusType.OPEN,
        }
        requested_door_status = door_action_to_status_switcher.get(door_action)
        current_door_status = await self.async_get_door_status(door_id)
        return (current_door_status == requested_door_status) or (await self.async_toogle_door_position(door_id, token))

    @deprecated
    async def toogle_door_position(self, door_id: int, token: str = None) -> bool:
        return await self.async_toogle_door_position(door_id, token)

    async def async_toogle_door_position(self, door_id: int, token: str = None) -> bool:
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
        response = await self.__http_client.async_get(url)
        return 400 > response.status and "OK" == await response.text()

    def __extract_web_token(self, html_content: str) -> str:
        """Parse web token from SOMweb HTML"""
        match = RE_WEBTOKEN.search(html_content)
        return None if match is None else match.group("webtoken")

    async def async_update_available(self) -> bool:
        """Check if an update is available

        Returns
        -------
        bool: True if an update is available
        """
        try:
            response = await self.__http_client.async_get(SOMWEB_CHECK_FOR_UPDATE_URI)
            if 200 != response.status:
                LOGGER.error("Checking for update failed. Reason: %s", response.reason)
                return False

            result = await response.text()      # 0 = no internet connection, 1 = update available, 2 = system has the latest firmvare version
            return "1" == result

        # pylint: disable=broad-except
        except Exception as ex:
            LOGGER.exception("Checking for update failed", exc_info=ex)
            return False

    async def async_get_device_info(self) -> DeviceInfo:
        """Get device info from SOMweb

        Note that the admin rights are required

        Returns
        -------
        dict: Device info
        """
        try:
            if self.is_admin == False:
                LOGGER.warning("Admin rights required to get device info")
                return None

            response = await self.__http_client.async_get(SOMWEB_DEVICE_INFO_URI)
            if 200 != response.status:
                LOGGER.warning("Getting device info failed. Reason: %s", response.reason)
                return None

            page_content = await response.text("utf-8")
            
            return DeviceInfo(
                get_value_using_regex(page_content, RE_REMOTE_ACCESS, "remote_access") == "ENABLED",
                get_value_using_regex(page_content, RE_FIRMWARE_VERSION, "firmware_version"),
                get_value_using_regex(page_content, RE_IP_ADDRESS, "ip_address"),
                get_value_using_regex(page_content, RE_WIFI_SIGNAL, "quality"),
                get_value_using_regex(page_content, RE_WIFI_SIGNAL, "level"),
                get_value_using_regex(page_content, RE_WIFI_SIGNAL, "unit"),
                get_value_using_regex(page_content, RE_TIME_ZONE, "time_zone"),
            )
        except Exception as ex:
            LOGGER.exception("Getting device info failed", exc_info=ex)
            return None
