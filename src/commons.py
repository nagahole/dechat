"""
Common information containers to be used between files
"""

import socket
import time
from src.alias_dictionary import AliasDictionary
from src.message import Message


class ServerMembers:
    """
    Information container class for server variables / members. Exists
    so functions in server_commands.py can mutate server members by
    passing in an instance of this class
    """
    def __init__(self, hostname: str, port: int) -> None:
        self.hostname = hostname
        self.port = port

        self.created_timestamp = time.time()
        self.conns = []
        self.channels = AliasDictionary()

        # To help remove users from previous channels when they join a new one
        self.conn_channel_map = {}

        self.nick_conn_map = {}

        self.quitted = False


class ClientStates:
    """
    Saves information for state to be shared between the main thread and
    listener thread in client.py
    """
    def __init__(self, listening: bool = True, last_whisperer: str = None,
                 in_channel: bool = False, active: bool = False) -> None:
        self.listening = listening
        self.last_whisperer = last_whisperer
        self.in_channel = in_channel
        self.active = active

        self.pinging_for_info = False
        self.joining_channel = False
        self.sender_started = False

    # For debugging purposes
    def __str__(self) -> str:
        return "\n".join((
            f"Listening: {self.listening}",
            f"Last whisperer: {self.last_whisperer}",
            f"In channel: {self.in_channel}",
            f"Active: {self.active}",
            f"Pinging for info: {self.pinging_for_info}",
            f"Joining channel: {self.joining_channel}"
        ))


class ClientConnectionWrapper:
    """
    A wrapper that stores a client-server socket connection and other relevant
    information related
    """
    def __init__(self, connection: socket.socket | None,
                 messages_to_store: int = 50) -> None:

        self.connection = connection
        self.name = None
        self.channel_name = None
        self.listener = None
        self.states = ClientStates()

        self.message_obj = Message()
        self.messages_to_store = messages_to_store
        self.messages = []
        self.closed = False

    def close(self) -> None:
        """
        Closes the connection and its associated listener
        """
        if self.states is not None:
            self.states.listening = False
            self.states.active = False

        if self.listener is not None:
            self.listener.join()

        if self.connection is not None:
            self.connection.close()

        self.closed = True

    def store_message(self, message_obj: Message) -> None:
        """
        Stores messages to be displayed when switching displays.

        Does so intelligently to abide the max number of messages to store
        """
        self.messages.insert(0, message_obj)

        if len(self.messages) > self.messages_to_store:
            self.messages = self.messages[:self.messages_to_store]


class ChannelLinkInfo:
    """
    Stores information for a channel link
    """
    def __init__(self, channel_name: str, hostname: str, port: int,
                 connection: socket.socket, channel_id: int) -> None:
        self.channel_name = channel_name
        self.hostname = hostname
        self.port = port
        self.connection = connection
        self.channel_id = channel_id
