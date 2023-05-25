"""
Wrapper class for the message protocol. Intended to make life easier
"""

# False-positive import error
# pylint: disable=import-error

from src import utilities
from src.constants import NICK_MSG_SEPARATOR, MAX_NICK_LENGTH


class Message:
    """
    Wrapper class to make encoding and decoding bytes easier
    """

    @staticmethod
    def from_bytes(message_bytes: bytes) -> "Message":
        """
        - 2 byte channel ID
        - 32 byte nickname
        - 4 byte timestamp
        - 2 byte message type (2 bits) and length (14 bits)
        - Message up to 8191 characters (bytes)

        Returns None if passed in bytes is invalid
        """
        if len(message_bytes) < 40:
            return None

        channel_id = int.from_bytes(message_bytes[:2], "little")
        nickname = message_bytes[2:34].decode("ascii").strip("\x00")
        timestamp = int.from_bytes(message_bytes[34:38], "little")

        message_type, message_length = Message.decode_type_and_length(
            message_bytes[38:40]
        )

        message = message_bytes[40:40 + message_length].decode("ascii")

        message_obj = Message(channel_id, nickname, timestamp,
                              message_type, message)

        return message_obj

    @staticmethod
    def encode_type_and_length(message_type: int,
                               message_length: int) -> bytes:
        """
        Encodes type and length into 2 bytes, 2 and 14 bits each respectively
        """

        if not 0 <= message_type <= 0b11:
            raise ValueError("Message type must be a 2 bit integer")

        # Type bits have to be on the right because when encoded to
        # little endianness it will become the first 2 bits
        type_bits = 0b11 & message_type
        length_bits = ((0xffff >> 2) & message_length) << 2

        return (type_bits | length_bits).to_bytes(2, "little")

    @staticmethod
    def decode_type_and_length(encoded_bytes: bytes) -> tuple[int, int]:
        """
        Decotes the 2 type and length conjoined bytes into its components
        """

        encoded_int = int.from_bytes(encoded_bytes, "little")

        message_type = 0b11 & encoded_int
        message_length = ((0xffff << 2) & encoded_int) >> 2

        return message_type, message_length

    def __init__(self, channel_id: int = None, nickname: str = None,
                 timestamp: float = None, message_type: int = None,
                 message: str = None) -> None:

        self.channel_id = None
        self.nickname = None
        self.timestamp = None
        self.message_type = None
        self.message_length = None
        self.message = None

        # To avoid super long lines of code
        args = (channel_id, nickname, timestamp, message_type, message)

        if None not in args:
            self.set_all(*args)

    def to_bytes(self) -> bytes:
        """
        Returns the byte representation of itself, or in other words, encodes
        itself to bytes that fit the message protocol
        """

        type_and_length_bytes = Message.encode_type_and_length(
            self.message_type, self.message_length
        )

        encoding = b""

        encoding += self.channel_id.to_bytes(2, "little")
        encoding += self.nickname.rjust(32, "\x00").encode("ascii")
        encoding += self.timestamp.to_bytes(4, "little")
        encoding += type_and_length_bytes
        encoding += self.message.encode("ascii")

        return encoding

    def __bytes__(self) -> bytes:
        return self.to_bytes()

    def set_channel_id(self, channel_id: int) -> None:
        """
        Setter for channel id
        """
        self.channel_id = channel_id

    def set_nickname(self, nickname: str) -> None:
        """
        Setter for nickname
        """
        self.nickname = nickname

    def set_timestamp(self, timestamp: float) -> None:
        """
        Setter for timestamp
        """
        if isinstance(timestamp, float):
            timestamp = int(timestamp)

        self.timestamp = timestamp

    def set_message_type(self, message_type: int) -> None:
        """
        Setter for message type
        """
        if not 0 <= message_type <= 0b11:
            raise ValueError("Message type must be a 2 bit integer")

        self.message_type = message_type

    def set_message(self, message: str) -> None:
        """
        Setter for message
        """
        self.message = message
        self.message_length = len(message)

    def set_all(self, channel_id: int, nickname: str, timestamp: float,
                message_type: int, message: str) -> None:
        """
        Setter for all attributes
        """

        self.set_channel_id(channel_id)
        self.set_nickname(nickname)
        self.set_timestamp(timestamp)
        self.set_message_type(message_type)
        self.set_message(message)

    def format(self) -> str:
        """
        Formats the Message object itself into the client display format
        """

        time_string = utilities.unix_to_str(self.timestamp)

        message_separator = NICK_MSG_SEPARATOR

        if "->" in self.nickname:  # Is a message
            message_separator = ":"

        if self.message_type == 0b01:
            nickname = "*"
        else:
            nickname = self.nickname

        nickname = nickname.rjust(MAX_NICK_LENGTH * 2 + 2)

        lines = self.message.split("\n")

        echo = lines[0]

        for i, line in enumerate(lines):
            if i != 0:
                echo += "\n"
                echo += " " * ((MAX_NICK_LENGTH * 2 + 2) + 10)
                echo += message_separator
                echo += f" {line}"

        return f"{time_string}{nickname}{message_separator} {echo}"

    def copy(self) -> "Message":
        """
        Returns a new Message object with the same exact attributes

        Useful for sending variations of a message while needing to store
        the original
        """
        return Message(
            self.channel_id,
            self.nickname,
            self.timestamp,
            self.message_type,
            self.message
        )

    def __eq__(self, other) -> bool:

        if not isinstance(other, Message):
            return False

        return all((
            self.channel_id == other.channel_id,
            self.nickname == other.nickname,
            self.timestamp == other.timestamp,
            self.message_type == other.message_type,
            self.message_length == other.message_length,
            self.message == other.message
        ))

    def __str__(self) -> str:
        return "|".join((map(str, [
            self.channel_id,
            self.nickname,
            self.timestamp,
            self.message_type,
            self.message_length,
            self.message
        ])))

    def __hash__(self) -> int:
        return hash((
            self.channel_id,
            self.nickname,
            self.timestamp,
            self.message_type,
            self.message_length,
            self.message
        ))


CLOSE_MESSAGE = Message(0, "", 0, 0b00, "")
