"""Constants for the SOMweb lib."""
import logging
import re

LOGGER = logging.getLogger(__package__)

SOMWEB_URI_TEMPLATE = "https://{}.somweb.world"
SOMWEB_ALIVE_URI = "/blank.html"
SOMWEB_AUTH_URI = "/index.php"
SOMWEB_DOOR_STATUS_URI = "/isg/statusDoor.php"
#SOMWEB_ALL_DOORS_STATUS_URI = "/isg/statusDoorAll.php"
SOMWEB_TOGGLE_DOOR_STATUS_URI = "/isg/opendoor.php"

CHECK_DOOR_STATE_INTERVAL = 2
REQUEST_TIMEOUT = 30

DEFAULT_DOOR_STATE_CHANGE_TIMEOUT = 60

RE_DOORS = re.compile(
    # pylint: disable=line-too-long
    r'<\s*input\s+type\s*=\s*"submit"\s+class\s*=\s*"tab-door[\s\w-]*"\s+name\s*=\s*"tab-door\d+"\s+id\s*=\s*"tab-door(?P<id>\d+)"\s+value="(?P<name>[\w\s]+)"\s*\/?>',
    re.MULTILINE,
)
RE_WEBTOKEN = re.compile(
    r'<\s*input\s+id\s*=\s*"webtoken".*value="(?P<webtoken>\w+)"\/>', re.MULTILINE
)
