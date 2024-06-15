"""Constants for the SOMweb lib."""
import logging
import re

LOGGER = logging.getLogger(__package__)

SOMWEB_URI_TEMPLATE = "https://{}.somweb.world"
SOMWEB_ALIVE_URI = "/blank.html"
SOMWEB_AUTH_URI = "/index.php"
SOMWEB_DEVICE_INFO_URI = "/index.php?op=config&opc=deviceinfo&lang=en"
SOMWEB_DOOR_STATUS_URI = "/isg/statusDoor.php"
#SOMWEB_ALL_DOORS_STATUS_URI = "/isg/statusDoorAll.php"
SOMWEB_TOGGLE_DOOR_STATUS_URI = "/isg/opendoor.php"
SOMWEB_CHECK_FOR_UPDATE_URI = "/isg/CheckForUpdates.php"

CHECK_DOOR_STATE_INTERVAL = 2
REQUEST_TIMEOUT = 30

DEFAULT_DOOR_STATE_CHANGE_TIMEOUT = 60

#
# Regex for Index Page
#
RE_DOORS = re.compile(
    # pylint: disable=line-too-long
    r'<\s*input\s+type\s*=\s*"submit"\s+class\s*=\s*"tab-door[\s\w-]*"\s+name\s*=\s*"tab-door\d+"\s+id\s*=\s*"tab-door(?P<id>\d+)"\s+value="(?P<name>[\w\s]+)"\s*\/?>',
    re.MULTILINE,
)
RE_WEBTOKEN = re.compile(
    r'<\s*input\s+id\s*=\s*"webtoken".*value="(?P<webtoken>\w+)".*\/>',
    re.MULTILINE
)

RE_UDI = re.compile(
    r'<meta name="UDI" content="(?P<udi>[0-9a-fA-F]+)" />',
    re.MULTILINE
)

RE_USER_IS_ADMIN = re.compile(
    r'<a href=".*?index.php\?op=config"',
    re.MULTILINE
)

#
# Regex for Device Info Page (requires user to be admin)
#
RE_REMOTE_ACCESS = re.compile(
    r'Remote Access:<\/div>\s*?<\/div>\s*?<div class=\".*?\">\s*<div class=\".*?\">(?P<remote_access>.*?)<\/div>',
    re.MULTILINE | re.U | re.I
)

RE_FIRMWARE_VERSION = re.compile(
    r'Firmware version:<\/div>\s*?<\/div>\s*?<div class=\".*?\">\s*?<div class=\".*?\">(?P<firmware_version>.*?)<\/div>',
    re.MULTILINE | re.U | re.I
)

RE_IP_ADDRESS = re.compile(
    r'IP Address:<\/div>\s*?<\/div>\s*?<div class=\".*?\">\s*?<div class=\".*?\">(?P<ip_address>.*?)<\/div>',
    re.MULTILINE | re.U | re.I
)

RE_WIFI_SIGNAL = re.compile(
    r'WiFi signal level:<\/div>\s*?<\/div>\s*?<div class=\".*?\">\s*?<div class=\".*?\">\s*<div class=.*?wifi-signal-(?P<quality>\d).*?\">(?P<level>-?\d+) (?P<unit>.*?)<\/div>',
    re.MULTILINE | re.U | re.I
)

RE_TIME_ZONE = re.compile(
    r'Time zone:<\/div>\s*?<\/div>\s*?<div class=\".*?\">\s*?<div class=\".*?\">(?P<time_zone>.*?)<\/div>',
    re.MULTILINE | re.U | re.I
)
