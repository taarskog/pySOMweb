from enum import Enum
from typing import NamedTuple

class Credentials(NamedTuple):
    username: str
    password: str

class AuthResponse(NamedTuple):
    success: bool = False
    token: str = None
    page_content: str = None

class DoorStatusType(Enum):
    Open = 1
    Closed = 2
    Unknown = 3

class DoorActionType(Enum):
    Close = 0
    Open = 1

class Door(NamedTuple):
    id: str
    name: str

class DoorStatus:
    def __init__(self, id: int, status: DoorStatusType):
        self.id = id
        self.status = status
