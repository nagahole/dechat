"""
Channels are a component of servers that contains members and can broadcast
to every member messages as well as having its own commands
"""

import threading
import socket
import time
from src import utilities
from src.commons import ServerMembers, ChannelLinkInfo
from src.protocol import message_send
from src.message import Message
from src.constants import MAX_NICK_LENGTH, CHANNEL_NICK


class Channel:
    """
    Channels are a component of servers that contains members and can
    broadcast to every member messages as well as having its own commands
    """

    instances = 0

    def __init__(self, s_mems: ServerMembers, creator: socket.socket,
                 name: str, password: str = None) -> None:

        self.s_mems = s_mems
        self.creator = creator
        self.name = name
        self.password = password
        self.id = Channel.instances
        Channel.instances += 1

        self.messages_to_store = 50
        self.messages = []
        self.connections = set()
        self.connection_nickname_map = {}
        self.nickname_connection_map = {}

        self.linked_channels = {}
        self.seen_messages = set()
        self.marked_for_deletion = set()

    def destroy(self) -> None:
        """
        Intelligently deletes the channel while removing all references to it
        """

        # If I do plan to implement auth I should make destroy also broadcast
        # (optionally) every user quitting the channel so users know they
        # have left the channel

        del self.s_mems.channels[self.id]  # Deleting by name works too

        marked_for_deletion = set()

        for conn, channel in self.s_mems.conn_channel_map.items():
            if channel == self:
                marked_for_deletion.add(conn)

        for conn in marked_for_deletion:
            del self.s_mems.conn_channel_map[conn]

        del self

    def get_name(self) -> str:
        """
        Getter for name
        """
        return self.name

    def get_messages(self) -> list:
        """
        Getter for messages
        """
        return self.messages

    def get_connections(self) -> set[socket.socket]:
        """
        Getter for connections
        """
        return self.connections

    def set_messages_to_store(self, num: int) -> None:
        """
        Setter for messages to store
        """
        self.messages_to_store = num

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

    def link_channel(self, info: ChannelLinkInfo) -> None:
        """
        Links to a channel on another server. LINKS ONE WAY ONLY
        """
        key = (info.channel_name, info.hostname, info.port)

        self.linked_channels[key] = info

    def unlink_channel(self, channel_name: str, hostname: str,
                       port: int) -> None:
        """
        Unlinks a channel from this channel. UNLINKS ONE WAY ONLY

        Will raise error of input is not valid
        """
        del self.linked_channels[(channel_name, hostname, port)]

    def linked_to_channel(self, channel_name: str, hostname: str,
                          port: int) -> None:
        """
        Returns bool on whether inputs correspond to a linked channel
        """
        return (channel_name, hostname, port) in self.linked_channels

    def add_connection(self, connection: socket.socket, nickname: str,
                       password: str = "") -> bool:
        """
        Adds a connection to the channel

        Returns True if they get the password right (or there is no password)
        and False if it's wrong
        """

        # Password exists and it doesn't match
        is_not_owner = connection != self.creator
        invalid_password = self.password and self.password != password

        if is_not_owner and invalid_password:
            return False

        self.connections.add(connection)
        self.set_nickname(connection, nickname)

        return True

    def welcome(self, connection: socket.socket) -> None:
        """
        Announces the welcome of a connection using its nickname
        """
        nickname = self.connection_nickname_map[connection]

        self.announce(f"{nickname} joined the channel!")

    def send_message_history(self, connection: socket.socket,
                             ignore_recent: int = 0) -> None:
        """
        Echoes message history to a connection when they first join
        a channel
        """

        for i, msg in enumerate(reversed(self.messages)):
            if i < len(self.messages) - ignore_recent:
                message_send(msg, connection)

    def remove_connection(self, connection: socket.socket) -> None:
        """
        Intelligently removes a connection along with any relationships it has
        with nicknames
        """

        self.connections.remove(connection)

        if connection in self.connection_nickname_map:
            nickname = self.connection_nickname_map[connection]

            if nickname in self.nickname_connection_map:
                del self.nickname_connection_map[nickname]

            del self.connection_nickname_map[connection]

    def broadcast_message(self, message_obj: Message,
                          save_message: bool = True, do_relay: bool = True):
        """
        Echoes a message of type to all connections in the channel
        """

        # This has 2 purposes:
        # 1. Making handling repeat messages channel id agnostic
        # 2. In case the client needs to know which channel the message came
        # from
        message_obj.set_channel_id(self.id)

        if message_obj in self.seen_messages:

            if message_obj not in self.marked_for_deletion:

                self.marked_for_deletion.add(message_obj)

                def callback() -> None:
                    if message_obj in self.seen_messages:
                        self.seen_messages.remove(message_obj)
                    self.marked_for_deletion.remove(message_obj)

                # Gives some time for linked messages to circulate around
                # multiple linked channels before removing it from the set to
                # free up space
                threading.Timer(10, callback).start()

            return

        self.seen_messages.add(message_obj)

        def cleanup() -> None:
            # If this message isn't relayed back and hence will never
            # be marked for deletion otherwise
            if message_obj in self.seen_messages:
                self.seen_messages.remove(message_obj)

        threading.Timer(20, cleanup).start()

        if save_message:
            self.messages.insert(0, message_obj)

            if len(self.messages) > self.messages_to_store:
                self.messages = self.messages[:self.messages_to_store]

        for conn in self.connections:
            message_send(message_obj, conn)

        if do_relay:

            relay = message_obj.copy()

            relay.set_message_type(0b11)

            for link_info in self.linked_channels.values():
                relay.set_channel_id(link_info.channel_id)
                message_send(relay, link_info.connection)

    def announce(self, msg: str) -> None:
        """
        Broadcasts a message to all connections in the channel from the
        channel itself
        """
        message_obj = Message(self.id, "*", time.time(), 0b00, msg)
        self.broadcast_message(message_obj)

    def handle_user_message(self, connection: socket.socket,
                            message_obj: Message) -> None:
        """
        Intelligently handles user messages by looking up its associated
        nickname (if it exists) before broadcasting a message
        """

        if connection in self.connection_nickname_map:
            nickname = self.connection_nickname_map[connection]
            message_obj.set_nickname(nickname)

        self.broadcast_message(message_obj)

    def echo_conn(self, conn: socket.socket, message: str) -> None:
        """
        Echoes a connection a pre-formatted Message object
        """

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

                    def nick_extractor(conn: socket.socket) -> str:
                        return self.connection_nickname_map[conn]

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

                        self.set_messages_to_store(message_limit)

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

                        message_obj = Message(self.id, nick_field,
                                              time.time(), 0b00, message)

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
                    del self.s_mems.conn_channel_map[connection]

                case _:
                    valid_command = False

            return valid_command

        return False
