from logging import exception
from typing import List
import requests
import json
from enum import Enum

from requests.sessions import Session

from .const import LOGGER, RE_WEBTOKEN, RE_DOORS, SOMWEB_URI_TEMPLATE

#
# TODO: Requests should include timeouts and also handle excpetions gracefully - see https://requests.readthedocs.io/en/master/user/quickstart/#timeouts
#

class DoorStatusType(Enum):
    Open = 1
    Closed = 2
    Unknown = 3

class DoorActionType(Enum):
    Close = 0
    Open = 1

class Door:
    def __init__(self, id: int, name: str):
        self.id = id
        self.name = name

class DoorStatus:
    def __init__(self, id: int, status: DoorStatusType):
        self.id = id
        self.status = status

class SomwebClient:
    __somWebPageContent = None
    __currentToken = None
    __username = None
    __password = None
    __doors = None
    __req = requests.Session()

    __door_status_types = {
        "OK": DoorStatusType.Closed,
        "FAIL": DoorStatusType.Open,
    }

    def __init__(self, somWebUDI: int, username: str, password: str):
        """
        Initialize SOMweb authenticator
        """
        self.__base_url = SOMWEB_URI_TEMPLATE.format(somWebUDI)
        self.__udi = somWebUDI
        self.__username = username
        self.__password = password

    @property
    def udi(self) -> int:
        return self.__udi

    @udi.setter
    def udi(self, value: int):
        raise exception("UDI cannot be set")

    @udi.deleter
    def udi(self):
        raise exception("UDI cannot be deleted")

    def isReachable(self) -> bool:
        """SOMweb device available and responding"""
        url = f"{self.__base_url}/blank.html"
        try:
            response = self.__req.get(url)
            return response.ok and "1" == response.text
        except Exception as e:
                LOGGER.error("Not reachable. Exception: %s", str(e))
                return False

    def authenticate(self) -> bool:
        """"Authenticate or re-authenticate"""
        form_data = {
            "login": self.__username,
            "pass": self.__password,
            "send-login": "Sign in",
        }

        url = f"{self.__base_url}/index.php"
        response = self.__req.post(url, form_data)
        if not response.ok:
            LOGGER.error("Authentication failed. Reason: %s", response.reason)
            return False

        self.__somWebPageContent = response.text
        self.__currentToken = self.__extractWebToken(self.__somWebPageContent)

        return bool(self.__currentToken)

    def getDoorStatus(self, doorId: int) -> DoorStatusType:
        """Get status of specified door id"""
        status = 1  # 1 = closed and 0 = open - SOMweb returns "OK" if sent status equals actual status or "FAIL" if status is the opposite
        bit = 0  # When set to 1 seems to define that 1 is to be returned if sent status matches actual status - if they don't match return is always FALSE
        url = f"{self.__base_url}/isg/statusDoor.php?numdoor={doorId}&status={status}&bit={bit}"
        response = self.__req.get(url)
        if not response.ok:
            LOGGER.error("Failed getting door status. Reason: %s", response.reason)
            exception("Failed getting door status. Reason: %s", response.reason)

        return self.__door_status_types.get(response.text, DoorStatusType.Unknown)

    def getDoors(self) -> List[Door]:
        if not self.__doors:
            matches = RE_DOORS.finditer(self.__somWebPageContent)
            self.__doors = list(map(lambda m: Door(m.group("id"), m.group("name")), matches))

        return self.__doors

    def getAllDoorStatuses(self) -> List[DoorStatus]:
        doorIds = list(map(lambda d: d.id, self.getDoors()))
        url = f"{self.__base_url}/isg/statusDoorAll.php?webtoken={self.__currentToken}"
        response = self.__req.get(url)
        data = json.loads(response.text)
        self.__currentToken = data["11"]

        #statuses = {k: data[k] for k in doorIds}

        # SOMweb returns string on closed ("0") and int on open (1)
        door_state_switcher = {
            "0": DoorStatusType.Closed,
            1: DoorStatusType.Open,
        }

        return list(map(lambda id: DoorStatus(id, door_state_switcher.get(data[id], DoorStatusType.Unknown)), doorIds))

    def openDoor(self, doorId: int) -> bool:
        return self.doorAction(doorId, DoorActionType.Open)

    def closeDoor(self, doorId: int) -> bool:
        return self.doorAction(doorId, DoorActionType.Close)

    def doorAction(self, doorId: int, doorAction: DoorActionType) -> bool:
        door_action_to_status_switcher = {
            DoorActionType.Close: DoorStatusType.Closed,
            DoorActionType.Open: DoorStatusType.Open,
        }
        requestedDoorStatus = door_action_to_status_switcher.get(doorAction)

        return self.getDoorStatus(doorId) == requestedDoorStatus or self.toogleDoorPosition(doorId)

    def toogleDoorPosition(self, doorId: int) -> bool:
        url = f"{self.__base_url}/isg/opendoor.php?numdoor={doorId}&status=0&webtoken={self.__currentToken}"
        response = self.__req.get(url)
        return response.ok and "OK" == response.text

    def __extractWebToken(self, html_content: str) -> str:
        """Parse web token from SOMweb HTML"""
        match = RE_WEBTOKEN.search(html_content)
        return None if match is None else match.group("webtoken")
