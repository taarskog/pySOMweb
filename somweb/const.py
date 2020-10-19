"""Constants for the SOMweb lib."""
import logging
import re

LOGGER = logging.getLogger(__package__)

# CONF_URL = "url"
# CONF_USERNAME = "username"
# CONF_PASSWORD = "password"

RE_DOORS = re.compile(r'<\s*input\s+type\s*=\s*"submit"\s+class\s*=\s*"tab-door[\s\w-]*"\s+name\s*=\s*"tab-door\d+"\s+id\s*=\s*"tab-door(?P<id>\d+)"\s+value="(?P<name>[\w\s]+)"\s*\/?>', re.MULTILINE)
RE_WEBTOKEN = re.compile(r'<\s*input\s+id\s*=\s*"webtoken".*value="(?P<webtoken>\w+)"\/>', re.MULTILINE)
