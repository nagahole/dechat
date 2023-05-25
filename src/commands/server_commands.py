"""
Implementation of all server commands and stores a map associating each
command to their functions
"""

import os
import socket
import time
import threading
from src import utilities
from src.commons import ServerMembers, ServerConnectionInfo
from src.channel import Channel
from src.message import Message
from src.protocol import message_send, conn_socket_setup
from src.constants import (
    SERVER_CHANNEL_ID,
    CONFIG_FOLDER,
    LINK_FLAG,
    UNLINK_FLAG,
    MIGRATE_FLAG,
    SEP
)

PROJECT_PATH = os.getcwd()


def echo_conn(conn: socket.socket, message: str) -> None:
    """
    Messages a connection with a predefined format for a Message object so
    only a message string has to be passed in
    """

    message_obj = Message(SERVER_CHANNEL_ID, "", time.time(),
                          0b01, message)

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
    else:
        echo_conn(conn, "Server has no MOTD file")


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
    else:
        echo_conn(conn, "Server has no HELP file")


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
    else:
        echo_conn(conn, "Server has no RULES file")


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

    client_conns = list(filter(lambda i: not i.is_server, s_mems.conns))

    server_name = f"Server: {s_mems.hostname}:{s_mems.port}"
    channels_str = f"{len(s_mems.channels)} channels"
    users_str = f"{len(client_conns)} connected users"
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
        echo_conn(conn, f"Channel {channel_name} already exists")
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
        echo_conn(conn, "Usage: /join <channel name> [password]")
        return

    channel_name = splits[1]

    if channel_name not in s_mems.channels:  # Channel doesn't exist
        echo_conn(conn, f"Channel {channel_name} doesn't exist")
        return

    channel = s_mems.channels[channel_name]

    # Joining the same channel
    if channel == s_mems.conn_channel_map.get(conn):
        echo_conn(conn, f"You are already in {channel_name}!")
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
    else:
        echo_conn(
            conn, f"Could not join {channel_name} (wrong password?)"
        )


def c_invite(obj: Message, conn: socket.socket,
             s_mems: ServerMembers) -> None:
    """
    Invites a connection in a server to a channel

    Will simply echo to the invitee "You've been invited to <channel_name>"

    # TODO Maybe take channel names instead of server names?
    """

    splits = utilities.smart_split(obj.message)

    if len(splits) < 3:
        echo_conn(conn, "Usage: /invite <nickname> <channel name>")
        return

    target_nick = splits[1]
    channel_name = splits[2]

    if target_nick not in s_mems.nick_conn_map:
        echo_conn(conn, f"User {target_nick} doesn't exist")
        return

    if channel_name not in s_mems.channels:
        echo_conn(conn, f"Channel {channel_name} doesn't exist")
        return

    target_conn = s_mems.nick_conn_map[target_nick]

    if target_conn in s_mems.conn_channel_map:
        echo_conn(conn, f"Unclear who {target_nick} is")
        return

    channel = s_mems.channels[channel_name]

    echo_conn(target_conn, f"You've been invited to {channel.name}")


def c_die(_obj: Message, _conn: socket.socket, s_mems: ServerMembers) -> None:
    """
    Kills the server
    """
    s_mems.quitted = True


def c_link(obj: Message, conn: socket.socket, s_mems: ServerMembers) -> None:
    """
    /link <channel name> <server host name>:<port>

    Sends a link request to the target server to synchronise a room of the
    same name between the two servers
    """

    splits = utilities.smart_split(obj.message)

    if len(splits) < 3:
        echo_conn(
            conn, "Usage: /link <channel name> <server host name>:<port>"
        )
        return

    channel_name = splits[1]
    channel = None

    for i_channel in s_mems.channels.values():
        if i_channel.name == channel_name:
            channel = i_channel
            break

    if channel is None:  # No channels with the inputted name found
        echo_conn(
            conn, f"Channel {channel_name} does not exist in this server"
        )
        return

    hostname, port = utilities.split_hostname_port(splits[2])

    if None in (hostname, port):
        echo_conn(conn, "Invalid hostname:port")
        return

    if channel.linked_to_channel(channel_name, hostname, port):
        echo_conn(
            conn, f"Already linked with {channel_name} on {hostname}:{port}"
        )
        return

    threading.Thread(
        target=link_thread,
        args=(channel.id, channel_name, hostname, port, conn, s_mems)
    ).start()


def link_thread(channel_id: int, channel_name: str, hostname: str,
                port: int, requester: socket.socket,
                s_mems: ServerMembers) -> None:
    """
    Links in a separate thread to not block the main thread
    """

    echo_conn(requester, f"Establishing connection with {hostname}:{port}...")

    successful, connection = conn_socket_setup(hostname, port)

    if not successful:
        echo_conn(requester, "Connection unsuccessful")
        return

    echo_conn(requester, "Connection successful. Sending link request")

    s_mems.conns.append(ServerConnectionInfo(connection, is_server=True))

    request = Message(
        channel_id,
        "",
        time.time(),
        0b10,
        SEP.join((
            LINK_FLAG,
            channel_name,
            s_mems.hostname,
            str(s_mems.port)
        ))
    )

    message_send(request, connection)


def c_unlink(obj: Message, conn: socket.socket,
             s_mems: ServerMembers) -> None:
    """
    /unlink <channel name> <server host name>:<port>

    Unlinks the channel from the target server
    """
    splits = utilities.smart_split(obj.message)

    if len(splits) < 3:
        echo_conn(
            conn, "Usage: /unlink <channel name> <server host name>:<port>"
        )
        return

    channel_name = splits[1]
    channel = None

    for i_channel in s_mems.channels.values():
        if i_channel.name == channel_name:
            channel = i_channel
            break

    if channel is None:  # No channels with the inputted name found
        echo_conn(
            conn, f"Channel {channel_name} does not exist in this server"
        )
        return

    hostname, port = utilities.split_hostname_port(splits[2])

    if None in (hostname, port):
        echo_conn(conn, "Invalid hostname:port")
        return

    if channel.linked_to_channel(channel_name, hostname, port):
        echo_conn(conn, "Unlinked channel on current end")
        channel.unlink_channel(channel_name, hostname, port)

    threading.Thread(
        target=unlink_thread,
        args=(channel.id, channel_name, hostname, port, conn, s_mems)
    ).start()


def unlink_thread(channel_id: int, channel_name: str, hostname: str,
                  port: int, requester: socket.socket,
                  s_mems: ServerMembers) -> None:
    """
    Links in a separate thread to not block the main thread
    """

    echo_conn(requester, f"Establishing connection with {hostname}:{port}...")

    successful, connection = conn_socket_setup(hostname, port)

    if not successful:
        echo_conn(requester, "Connection unsuccessful")
        return

    echo_conn(requester, "Connection successful. Sending unlink request")

    request = Message(
        channel_id,
        "",
        time.time(),
        0b10,
        SEP.join((
            UNLINK_FLAG,
            channel_name,
            s_mems.hostname,
            str(s_mems.port)
        ))
    )

    message_send(request, connection)


def c_migrate(obj: Message, conn: socket.socket,
              s_mems: ServerMembers) -> None:
    """
    /migrate <channel name> <server host name>:<port>

    Migrates the channel to a new linked server, connected users should
    be migrated by receiving the same command.
    """
    splits = utilities.smart_split(obj.message)

    if len(splits) < 3:
        echo_conn(
            conn, "Usage: /migrate <channel name> <server host name>:<port>"
        )
        return

    channel_name = splits[1]
    channel = None

    for i_channel in s_mems.channels.values():
        if i_channel.name == channel_name:
            channel = i_channel
            break

    if channel is None:  # No channels with the inputted name found
        echo_conn(
            conn, f"Channel {channel_name} does not exist in this server"
        )
        return

    hostname, port = utilities.split_hostname_port(splits[2])

    if None in (hostname, port):
        echo_conn(conn, "Invalid hostname:port")
        return

    if not channel.linked_to_channel(channel_name, hostname, port):
        echo_conn(conn, f"Not linked to {channel_name} on {hostname}:{port}")
        return

    # Valid input

    echo = (
        f"Broadcasting to users in {channel_name} to migrate to "
        f"{channel_name} in {hostname}:{port}"
    )

    echo_conn(conn, echo)

    link_info = channel.linked_channels[(channel_name, hostname, port)]

    unlink_request = Message(
        link_info.channel_id,
        "",
        time.time(),
        0b10,
        SEP.join((
            UNLINK_FLAG,
            channel_name,
            s_mems.hostname,
            str(s_mems.port)
        ))
    )

    message_send(unlink_request, link_info.connection)

    broadcast = Message(
        link_info.channel_id,  # This will probably be unused since channel
        "",                    # name is also being broadcasted
        time.time(),
        0b10,  # Not sure about this message type??
        SEP.join((
            MIGRATE_FLAG,
            channel_name,
            link_info.hostname,
            str(link_info.port)
        ))
    )

    # Save message probably doesn't matter since channel is being destroyed
    # anyways but just to be safe
    channel.broadcast_message(broadcast, save_message=False, do_relay=False)
    channel.destroy()


server_command_map = {
    "motd": c_motd,
    "help": c_help,
    "rules": c_rules,
    "info": c_info,
    "list": c_list,
    "create": c_create,
    "join": c_join,
    "invite": c_invite,
    "die": c_die,

    "link": c_link,
    "unlink": c_unlink,
    "migrate": c_migrate
}
