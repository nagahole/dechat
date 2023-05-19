import socket
import time
from src.alias_dictionary import AliasDictionary
from src.message import Message


class ServerVariables:
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


class ClientSenderVariables:
    def __init__(self, message_obj: Message=Message(), 
                 quitted: bool=False) -> None:
        self.message_obj = message_obj
        self.quitted = quitted


class ClientVariables:
    def __init__(self, quitted: bool=False, default_nickname: str="anon", 
                 connection: socket.socket=None) -> None:
        self.quitted = quitted
        self.default_nickname = default_nickname
        self.connection = connection


class ClientStates:
    def __init__(self, listening: bool=True, last_messager: str=None, 
                 in_channel: bool=False) -> None:
        self.listening = listening
        self.last_whisperer = last_messager
        self.in_channel = in_channel
