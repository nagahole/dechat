import socket
import time
import src.utilities as utilities
from src.protocol import message_send
from src.message import Message
from src.constants import MAX_NICK_LENGTH, CHANNEL_NICK


class Channel:

    instances = 0

    def __init__(self, creator: socket.socket, on_connection_remove: callable,
                 name: str, password: str = None) -> None:

        self.creator = creator
        self.on_connection_remove = on_connection_remove
        self.name = name
        self.password = password
        self.id = Channel.instances
        Channel.instances += 1

        self.no_of_messages_saved = 50
        self.messages = []
        self.connections = set()
        self.connection_nickname_map = {}
        self.nickname_connection_map = {}

    def get_name(self) -> str:
        return self.name

    def get_messages(self) -> list:
        return self.messages

    def set_no_of_messages_saved(self, n: int) -> None:
        self.no_of_messages_saved = n

    def set_nickname(self, connection: socket.socket, nickname: str) -> str:
        """
        Returns the set nickname
        """
        if connection in self.connection_nickname_map:
            old_nick = self.connection_nickname_map[connection]

            if old_nick in self.nickname_connection_map:
                del self.nickname_connection_map[old_nick]

            del self.connection_nickname_map[connection]
        
        if nickname in self.nickname_connection_map:
            i = 1

            new_nick = f"{nickname}({i})"

            while new_nick in self.nickname_connection_map:
                i += 1
                new_nick = f"{nickname}({i})"

            nickname = new_nick

        self.connection_nickname_map[connection] = nickname
        self.nickname_connection_map[nickname] = connection

        return nickname

    def add_connection(self, connection: socket.socket, nickname: str, 
                       password: str = "") -> bool:
        """
        Adds a connection to the channel

        Returns True if they get the password right (or there is no password)
        and False if it's wrong
        """

        # Password exists and it doesn't match
        if self.password and self.password != password:
            return False

        self.connections.add(connection)
        self.set_nickname(connection, nickname)

        return True

    def welcome(self, connection: socket.socket) -> None:
        nickname = self.connection_nickname_map[connection]

        self.announce(f"{nickname} joined the channel")

    def send_message_history(self, connection: socket.socket,
                             ignore_recent: int = 0) -> None:
        for i, msg in enumerate(reversed(self.messages)):
            if i < len(self.messages) - ignore_recent:
                message_send(msg, connection)

    def get_connections(self) -> set[socket.socket]:
        return self.connections

    def remove_connection(self, connection: socket.socket) -> None:

        self.on_connection_remove(connection)

        self.connections.remove(connection)

        if connection in self.connection_nickname_map:
            nickname = self.connection_nickname_map[connection]

            if nickname in self.nickname_connection_map:
                del self.nickname_connection_map[nickname]
            
            del self.connection_nickname_map[connection]

    def broadcast_message(self, message_obj: Message):
        self.messages.insert(0, message_obj)

        while len(self.messages) > self.no_of_messages_saved:
            self.messages.pop()

        for conn in self.connections:
            message_send(message_obj, conn)

    def announce(self, s: str) -> None:
        message_obj = Message(self.id, "*", time.time(), 0b00, s)
        self.broadcast_message(message_obj)

    def handle_user_message(self, connection: socket.socket,
                            message_obj: Message) -> None:

        if connection in self.connection_nickname_map:
            nickname = self.connection_nickname_map[connection]
            message_obj.set_nickname(nickname)

        self.broadcast_message(message_obj)

    def echo_conn(self, conn: socket.socket, message: str) -> None:

        message_obj = Message(
            self.id, CHANNEL_NICK, time.time(), 0b00, message
        )

        message_send(message_obj, conn)

    def handle_command_input(self, connection: socket.socket,
                             message_obj: Message) -> bool:
        """
        Returns whether the input is a recognized command
        """

        splits = message_obj.message.split(" ")
        splits = list(filter(lambda s: s != "", splits))

        if splits[0] != "" and splits[0][0] == "/":

            command = splits[0][1:].lower()

            valid_command = True

            match command:
                case "nick":

                    if len(splits) >= 2:
                        new_nick = splits[1]

                        if len(new_nick) <= MAX_NICK_LENGTH:

                            self.set_nickname(connection, new_nick)

                case "list":

                    def nick_extractor(c: socket.socket) -> str:
                        return self.connection_nickname_map[c]

                    echo = "\n".join(map(nick_extractor, self.connections))

                    self.echo_conn(connection, echo)

                case "emote":
                    if len(splits) >= 2:
                        msg = message_obj.message.split(" ", 1)[1]

                        nick = self.connection_nickname_map[connection]
                        
                        self.announce(f"{nick} {msg}")

                case "admin":
                    if len(splits) >= 2:
                        target_name = splits[1]

                        user_exists = False
                        is_admin = False

                        if target_name in self.nickname_connection_map:
                            user_exists = True
                            conn = self.nickname_connection_map[target_name]
                            is_admin = self.creator == conn

                        echo = target_name

                        if not user_exists:

                            echo += " doesn't exist"

                        elif is_admin:
                            
                            echo += " is an operator"
                        else:

                            echo += " is a regular"

                        self.echo_conn(connection, echo)

                case "message_limit":

                    if (len(splits) >= 2 and 
                            utilities.is_integer(splits[1]) and
                            self.creator == connection):

                        message_limit = int(splits[1])

                        self.set_no_of_messages_saved(message_limit)

                case "pass":
                    
                    is_admin = self.creator == connection

                    if not is_admin:
                        echo = "You are not the admin of the channel!"
                        self.echo_conn(connection, echo)

                    else:

                        password = None

                        if len(splits) > 1:
                            password = splits[1]

                        self.password = password

                case "msg":
                    
                    target_conn = None
                    target_name = ""

                    if len(splits) >= 3:

                        target_name = splits[1]
                        target_conn = self.nickname_connection_map.get(
                            target_name, None
                        )

                    if target_conn is not None:

                        message = message_obj.message.split(" ", 2)[2]

                        sender_name = self.connection_nickname_map[connection]

                        nick_field = f"{sender_name} -> {target_name}"

                        message_obj = Message(self.id, nick_field, time.time(),
                                              0b00, message)

                        message_send(message_obj, connection)
                        message_send(message_obj, target_conn)

                case "quit":
                    
                    quit_message = ""

                    if len(splits) >= 2:
                        quit_message = message_obj.message.split(" ", 1)[1]

                    nick = self.connection_nickname_map[connection]

                    if quit_message != "":
                        self.announce(f"{nick} has quit ({quit_message})")
                    else:
                        self.announce(f"{nick} has quit")

                    self.remove_connection(connection)
                    
                case _:
                    valid_command = False

            return valid_command

        else:
            return False
