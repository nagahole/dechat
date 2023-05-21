import socket
import time
from src.alias_dictionary import AliasDictionary
from src.message import Message


class ServerMembers:
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
    def __init__(self, listening: bool=True, last_messager: str=None,
                 in_channel: bool=False, active: bool=False) -> None:
        self.listening = listening
        self.last_whisperer = last_messager
        self.in_channel = in_channel
        self.active = active

        self.pinging_for_info = False
        self.joining_channel = False

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
    def __init__(self, connection: socket.socket,
                 messages_to_store: int=50) -> None:

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
        if self.states is not None:
            self.states.listening = False
            self.states.active = False

        if self.listener is not None:
            self.listener.join()

        if self.connection is not None:
            self.connection.close()

        self.closed = True

    def store_message(self, message_obj: Message) -> None:
        self.messages.insert(0, message_obj)

        if len(self.messages) > self.messages_to_store:
            self.messages = self.messages[:self.messages_to_store]
