"""
Implementation of all server commands and stores a map associating each
command to their functions
"""

import os
import socket
import time
from src import utilities
from src.commons import ServerMembers
from src.channel import Channel
from src.message import Message
from src.protocol import message_send
from src.constants import SERVER_CHANNEL_ID, CONFIG_FOLDER

PROJECT_PATH = os.getcwd()


def echo_conn(conn: socket.socket, message: str) -> None:
    """
    Messages a connection with a predefined format for a Message object so
    only a message string has to be passed in
    """

    message_obj = Message(SERVER_CHANNEL_ID, "", time.time(),
                          0b01, message)

    print(f"Sending: {message_obj}")
    message_send(message_obj, conn)


def leave_old_channel(conn: socket.socket,
                      s_mems: ServerMembers) -> None:
    """
    Intelligently leaves a connection's old channel (if it exists)

    To be used in conjunction with joining a new channel
    """

    if conn in s_mems.conn_channel_map:
        channel = s_mems.conn_channel_map[conn]

        channel.remove_connection(conn)

        del s_mems.conn_channel_map[conn]


def join_user_to_channel(obj: Message, conn: socket.socket,
                         s_mems: ServerMembers,
                         channel: Channel, password: str = "") -> bool:
    """
    Intelligently joins a user to a channel

    Returns whether join is successful or not
    """

    leave_old_channel(conn, s_mems)

    nickname = obj.nickname

    successful_join = channel.add_connection(conn, nickname, password)

    if successful_join:
        s_mems.conn_channel_map[conn] = channel

    return successful_join


def c_motd(_obj: Message, conn: socket.socket,
           _s_mems: ServerMembers) -> None:
    """
    Displays server's config/MOTD.txt file
    """

    file_path = f"{PROJECT_PATH}/{CONFIG_FOLDER}/MOTD.txt"
    file_exists = os.path.isfile(file_path)

    if file_exists:
        with open(file_path, "r", encoding="ascii") as file:

            echo_conn(conn, file.read())


def c_help(_obj: Message, conn: socket.socket,
           _s_mems: ServerMembers) -> None:
    """
    Displays server's config/HELP.txt file
    """

    file_path = f"{PROJECT_PATH}/{CONFIG_FOLDER}/HELP.txt"
    file_exists = os.path.isfile(file_path)

    if file_exists:
        with open(file_path, "r", encoding="ascii") as file:

            echo_conn(conn, file.read())


def c_rules(_obj: Message, conn: socket.socket,
            _s_mems: ServerMembers) -> None:
    """
    Displays server's config/RULES.txt file
    """

    file_path = f"{PROJECT_PATH}/{CONFIG_FOLDER}/RULES.txt"
    file_exists = os.path.isfile(file_path)

    if file_exists:
        with open(file_path, "r", encoding="ascii") as file:

            echo_conn(conn, file.read())


def c_info(_obj: Message, conn: socket.socket,
           s_mems: ServerMembers) -> None:
    """
    Echoes connection with server info. Formatted with

    - Server name (hostname:port)
    - Number of channels
    - Number of users
    - Uptime

    """

    uptime = time.time() - s_mems.created_timestamp

    server_name = f"Server: {s_mems.hostname}:{s_mems.port}"
    channels_str = f"{len(s_mems.channels)} channels"
    users_str = f"{len(s_mems.conns)} connected users"
    uptime_str = f"Uptime: {utilities.format_time_period(uptime)}"

    echo = "\n".join([
        server_name,
        channels_str,
        users_str,
        uptime_str
    ])

    echo_conn(conn, echo)


def c_list(_obj: Message, conn: socket.socket,
           s_mems: ServerMembers) -> None:
    """
    Echoes connection with the names of the channels in the server
    """

    all_channels = s_mems.channels.values()

    if len(all_channels) == 0:
        echo_conn(conn, "No channels in server")
        return

    channels_string = "Channels:\n"
    channels_string += ", ".join(
        map(lambda c: c.get_name(), all_channels)
    )

    echo_conn(conn, channels_string)


def c_create(obj: Message, conn: socket.socket,
             s_mems: ServerMembers) -> None:
    """
    Attempts to create a channel of a user inputted name in the server
    """

    splits = utilities.smart_split(obj.message)

    if len(splits) < 2:
        return

    channel_name = splits[1]

    if channel_name in s_mems.channels:
        return

    password = None

    if len(splits) >= 3:
        password = splits[2]

    channel = Channel(s_mems, conn, channel_name, password)

    s_mems.channels[channel.id] = channel
    s_mems.channels.add_alias(channel.id, channel_name)

    join_user_to_channel(
        obj, conn, s_mems, channel, password
    )

    channel.send_message_history(conn)
    channel.welcome(conn)


def c_join(obj: Message, conn: socket.socket,
           s_mems: ServerMembers) -> None:
    """
    Attempts to join a user inputted channel (if it exists) in the server
    """

    splits = utilities.smart_split(obj.message)

    if len(splits) < 2:
        return

    channel_name = splits[1]

    if channel_name not in s_mems.channels:  # Channel doesn't exist
        return

    channel = s_mems.channels[channel_name]

    # Joining the same channel
    if channel == s_mems.conn_channel_map.get(conn):
        return

    password = ""

    if len(splits) >= 3:
        password = splits[2]

    successful_join = join_user_to_channel(
        obj, conn, s_mems, channel, password
    )

    if successful_join:
        channel.send_message_history(conn)
        channel.welcome(conn)


def c_invite(obj: Message, conn: socket.socket,
             s_mems: ServerMembers) -> None:
    """
    Invites a connection in a server to a channel

    Will simply echo to the invitee "You've been invited to <channel_name>"
    """

    splits = utilities.smart_split(obj.message)

    if len(splits) < 3:
        return

    target_nick = splits[1]
    channel_name = splits[2]

    if target_nick not in s_mems.nick_conn_map:
        echo_conn(conn, f"{target_nick} doesn't exist")
        return

    if channel_name not in s_mems.channels:
        echo_conn(conn, f"{channel_name} doesn't exist")
        return

    target_conn = s_mems.nick_conn_map[target_nick]
    channel = s_mems.channels[channel_name]

    echo_conn(target_conn, f"You've been invited to {channel.name}")


def c_die(_obj: Message, _conn: socket.socket, s_mems: ServerMembers) -> None:
    """
    Kills the server
    """
    s_mems.quitted = True


server_command_map = {
    "motd": c_motd,
    "help": c_help,
    "rules": c_rules,
    "info": c_info,
    "list": c_list,
    "create": c_create,
    "join": c_join,
    "invite": c_invite,
    "die": c_die
}
