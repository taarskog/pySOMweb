import asyncio
from logging import exception, warning
from .httpclient import HttpClient
from typing import List  # , Tuple
from aiohttp.client import ClientSession

# import json

from .const import (
    CHECK_DOOR_STATE_INTERVAL,
    DEFAULT_DOOR_STATE_CHANGE_TIMEOUT,
    LOGGER,
    RE_WEBTOKEN,
    RE_DOORS,
    SOMWEB_ALIVE_URI,
    SOMWEB_ALL_DOORS_STATUS_URI,
    SOMWEB_AUTH_URI,
    SOMWEB_DOOR_STATUS_URI,
    SOMWEB_TOGGLE_DOOR_STATUS_URI,
)
from .models import (
    AuthResponse,
    Credentials,
    Door,
    DoorActionType,
    DoorStatus,
    DoorStatusType,
)


class SomwebClient:
    __udi: int
    __credentials: Credentials
    __http_client: HttpClient

    __door_status_types = {
        "OK": DoorStatusType.Closed,
        "FAIL": DoorStatusType.Open,
    }

    def __init__(
        self,
        somweb_udi: int,
        username: str,
        password: str,
        session: ClientSession = None,
    ):
        """
        Initialize SOMweb authenticator
        """
        self.__udi = somweb_udi
        self.__credentials = Credentials(username, password)
        self.__http_client = HttpClient(somweb_udi, session)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *excinfo):
        LOGGER.info("Closing http client")
        await self.__http_client.close()

    async def close(self) -> None:
        """Close underlying http client.

        Release all acquired resources.
        """
        if not self.closed:
            await self.__http_client.close()
            self.__http_client = None

    @property
    def closed(self) -> bool:
        """Is http client closed.

        A readonly property.
        """
        return self.__http_client is None or self.__http_client.closed

    @property
    def udi(self) -> int:
        """SOMweb UDI.

        A readonly property.
        """
        return self.__udi

    async def is_alive(self) -> bool:
        """SOMweb device available and responding"""
        try:
            response = await self.__http_client.get(SOMWEB_ALIVE_URI)
            return response.ok and "1" == await response.text()
        except Exception as e:
            LOGGER.exception("SomWeb not reachable.", exc_info=e)
            return False

    async def authenticate(self) -> AuthResponse:
        """"Authenticate or re-authenticate"""
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

            somweb_page_content = await response.text()
            current_token = self.__extract_web_token(somweb_page_content)
            return AuthResponse(True, current_token, somweb_page_content)
        except Exception as e:
            LOGGER.exception("Authentication failed", exc_info=e)
            return AuthResponse()

    async def get_door_status(self, door_id: int) -> DoorStatusType:
        """Get status of specified door id"""
        status = 1  # 1 = closed and 0 = open - SOMweb returns "OK" if sent status equals actual status or "FAIL" if status is the opposite
        bit = 0  # When set to 1 seems to define that 1 is to be returned if sent status matches actual status - if they don't match return is always FALSE
        url = f"{SOMWEB_DOOR_STATUS_URI}?numdoor={door_id}&status={status}&bit={bit}"

        response = await self.__http_client.get(url)
        if not response.ok:
            LOGGER.error("Failed getting door status. Reason: %s", response.reason)
            exception("Failed getting door status. Reason: %s", response.reason)

        return self.__door_status_types.get(
            await response.text(), DoorStatusType.Unknown
        )

    def get_doors_from_page_content(self, page_content: str) -> List[Door]:
        matches = RE_DOORS.finditer(page_content)
        doors = list(map(lambda m: Door(m.group("id"), m.group("name")), matches))
        return doors

    # async def getAllDoorStatuses(self, token: str, doors: List[Door]) -> Tuple(str, List[DoorStatus]):
    #     doorIds = list(map(lambda d: d.id, doors))
    #     url = f"{SOMWEB_ALL_DOORS_STATUS_URI}?webtoken={token}"
    #     async with self.__httpClient.get(url) as response:
    #         data = json.loads(await response.text())
    #         newToken = data["11"]

    #         # SOMweb returns string on closed ("0") and int on open (1)
    #         door_state_switcher = {
    #             "0": DoorStatusType.Closed,
    #             1: DoorStatusType.Open,
    #         }

    #         return (newToken, list(map(lambda id: DoorStatus(id, door_state_switcher.get(data[id], DoorStatusType.Unknown)), doorIds)))

    async def wait_for_door_state(
        self,
        door_id: int,
        state: DoorStatusType,
        timeout_in_seconds: float = DEFAULT_DOOR_STATE_CHANGE_TIMEOUT,
    ) -> bool:
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

    async def open_door(self, token: str, door_id: int) -> bool:
        return await self.door_action(token, door_id, DoorActionType.Open)

    async def close_door(self, token: str, door_id: int) -> bool:
        return await self.door_action(token, door_id, DoorActionType.Close)

    async def door_action(
        self, token: str, door_id: int, door_action: DoorActionType
    ) -> bool:
        door_action_to_status_switcher = {
            DoorActionType.Close: DoorStatusType.Closed,
            DoorActionType.Open: DoorStatusType.Open,
        }
        requested_door_status = door_action_to_status_switcher.get(door_action)
        return await self.get_door_status(
            door_id
        ) == requested_door_status or await self.toogle_door_position(token, door_id)

    async def toogle_door_position(self, token: str, door_id: int) -> bool:
        url = f"{SOMWEB_TOGGLE_DOOR_STATUS_URI}?numdoor={door_id}&status=0&webtoken={token}"
        response = await self.__http_client.get(url)
        return response.ok and "OK" == await response.text()

    def __extract_web_token(self, html_content: str) -> str:
        """Parse web token from SOMweb HTML"""
        match = RE_WEBTOKEN.search(html_content)
        return None if match is None else match.group("webtoken")
