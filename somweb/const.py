"""Constants for the SOMweb lib."""
import logging
import re

LOGGER = logging.getLogger(__package__)

SOMWEB_URI_TEMPLATE = "https://{}.somweb.world"

REQUEST_TIMEOUT = 1.5

RE_DOORS = re.compile(r'<\s*input\s+type\s*=\s*"submit"\s+class\s*=\s*"tab-door[\s\w-]*"\s+name\s*=\s*"tab-door\d+"\s+id\s*=\s*"tab-door(?P<id>\d+)"\s+value="(?P<name>[\w\s]+)"\s*\/?>', re.MULTILINE)
RE_WEBTOKEN = re.compile(r'<\s*input\s+id\s*=\s*"webtoken".*value="(?P<webtoken>\w+)"\/>', re.MULTILINE)
