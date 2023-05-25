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


class ServerConnectionInfo:
    """
    Information wrapper for connections on server-side
    """
    def __init__(self, connection: socket.socket,
                 is_server: bool = False) -> None:
        self.connection = connection
        self.is_server = is_server


class ClientStates:
    """
    Saves information for state to be shared between the main thread and
    listener and sender threads in client.py
    """
    def __init__(self, listening: bool = True,
                 in_channel: bool = False, active: bool = False) -> None:
        self.listening = listening
        self.in_channel = in_channel
        self.active = active

        self.pinging_for_info = False
        self.just_messaged = True

    # For debugging purposes
    def __str__(self) -> str:
        return "\n".join((
            f"Listening: {self.listening}",
            f"In channel: {self.in_channel}",
            f"Active: {self.active}",
            f"Pinging for info: {self.pinging_for_info}"
        ))


class ClientConnectionWrapper:
    """
    A wrapper that stores a client-server socket connection and other relevant
    information related
    """
    def __init__(self, connection: socket.socket | None,
                 messages_to_store: int = 50) -> None:

        self.connection = connection
        self.last_whisperer = None

        self.name = None
        self.confirmed_channel_name = None
        self.pending_channel_name = None

        self.listener = None
        self.sender = None

        self.input_queue = []
        self.states = ClientStates()

        self.messages_to_store = messages_to_store
        self.messages = []

        # This is the only attribute that should never be accessed directly
        # because it should only be set to false when .close() is called
        self._closed = False

    def is_closed(self) -> bool:
        """
        Safely checks whether connection is closed or not
        """
        return self._closed

    def close_listener(self) -> None:
        """
        Should not be called by the listener thread
        """
        self.states.listening = False
        self.listener.join()
        self.listener = None

    def close_sender(self) -> None:
        """
        Should not be called by the sender thread
        """
        self.sender.join()
        self.sender = None

    def close(self) -> None:
        """
        Closes the connection and its associated senders and listeners

        Listeners and senders should never call this function because
        closing attempts to .join() the listener and sender threads to the
        thread that called close()
        """

        self._closed = True
        self.states.active = False

        if self.listener is not None:
            self.close_listener()

        if self.sender is not None:
            self.close_sender()

        if self.connection is not None:
            self.connection.close()
            self.connection = None

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
