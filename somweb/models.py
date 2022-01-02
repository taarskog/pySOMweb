""" Models for SOMweb Client """
from enum import Enum
from typing import NamedTuple


class Credentials(NamedTuple):
    """SOMweb device credentials"""

    username: str
    password: str


class AuthResponse(NamedTuple):
    """Result from an authentication request"""

    success: bool = False
    token: str = None
    page_content: str = None


class DoorStatusType(Enum):
    """Door status type"""

    OPEN = 1
    CLOSED = 2
    UNKNOWN = 3


class DoorActionType(Enum):
    """Door action type"""

    CLOSE = 0
    OPEN = 1


class Door(NamedTuple):
    """Door information"""

    id: int
    name: str


# class DoorStatus:
#     def __init__(self, id: int, status: DoorStatusType):
#         self.id = id
#         self.status = status
