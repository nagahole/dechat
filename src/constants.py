"""
Stores constants to be used across multiple files
"""

SERVER_CHANNEL_ID = (2 ** 16) - 1
CONFIG_FOLDER = "config"
MAX_NICK_LENGTH = 15
MAX_PORT_VALUE = 65535
NICK_MSG_SEPARATOR = "|"
CHANNEL_NICK = "*"

LINK_FLAG = "--link"
LINK_RESPONSE_FLAG = "--response"

UNLINK_FLAG = "--unlink"

MIGRATE_FLAG = "--migrate"

# Unit separator. Safe way to separate data in formatted strings
SEP = chr(31)
