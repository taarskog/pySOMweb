from logging import exception
import requests
from enum import Enum

from .const import (
    LOGGER,
    RE_WEBTOKEN,
    RE_DOORS
)

class DoorStatusType(Enum):
    Open = 1
    Closed = 2
    Unknown = 3

class SomwebClient:
    __token = ""
    
    __door_status_types = {
        "OK": DoorStatusType.Open,
        "FAIL": DoorStatusType.Closed,
    }

    def __init__(self, base_url, username, password):
        """
        Initialize SOMweb authenticator
        """
        self.__base_url = base_url
        self.__username = username
        self.__password = password
    
    def authenticate(self):
        form_data = {
            "login": self.__username,
            "pass": self.__password,
            "send-login": "Sign in"
        }

        response = requests.post(self.__base_url + "/index.php", form_data)
        if not response.ok:
            LOGGER.error("Authentication failed. Reason: %s", response.reason)
            return False

        self.__token = self.__extractWebToken(response.text)

        return bool(self.__token)

    def getDoorStatus(self, doorId):
        status = 1 # 1 = closed and 0 = open - SOMweb returns "OK" if sent status equals actual status or "FAIL" if status is the opposite
        bit = 0 # When set to 1 seems to define that 1 is to be returned if sent status matches actual status - if they don't match return is always FALSE
        url = "/isg/statusDoor.php?numdoor={}&status={}&bit={}".format(doorId, status, bit)
        response = requests.get(self.__base_url + url)
        if not response.ok:
            LOGGER.error("Failed getting door status. Reason: %s", response.reason)
            exception("Failed getting door status. Reason: %s", response.reason)

        return self.__door_status_types.get(response.text, DoorStatusType.Unknown)


    def __extractWebToken(self, html_content):
        """Parse web token from SOMweb HTML"""
        matches = RE_WEBTOKEN.search(html_content)
        return None if matches is None else matches.group('webtoken')