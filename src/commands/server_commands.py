import os
import socket
import time
import src.utilities as utilities
from src.commons import ServerVariables
from src.channel import Channel
from src.message import Message
from src.protocol import message_send
from src.constants import SERVER_CHANNEL_ID, CONFIG_FOLDER

PROJECT_PATH = os.getcwd()


def echo_conn(conn: socket.socket, message: str) -> None:

    message_obj = Message(SERVER_CHANNEL_ID, "", time.time(),
                          0b01, message)

    message_send(message_obj, conn)


def leave_old_channel(conn: socket.socket, 
                      s_vars: ServerVariables) -> None:

    if conn in s_vars.conn_channel_map:
        channel = s_vars.conn_channel_map[conn]

        channel.remove_connection(conn)

        del s_vars.conn_channel_map[conn]


def join_user_to_channel(obj: Message, conn: socket.socket, 
                         s_vars: ServerVariables,
                         channel: Channel, password: str = "") -> bool:

    leave_old_channel(conn, s_vars)

    nickname = obj.nickname

    successful_join = channel.add_connection(conn, nickname, password)

    if successful_join:
        s_vars.conn_channel_map[conn] = channel

    return successful_join


def c_motd(obj: Message, conn: socket.socket, 
           s_vars: ServerVariables) -> None:

    file_path = f"{PROJECT_PATH}/{CONFIG_FOLDER}/MOTD.txt"
    file_exists = os.path.isfile(file_path)

    if file_exists:
        with open(file_path) as file:

            echo_conn(conn, file.read())


def c_help(obj: Message, conn: socket.socket, 
           s_vars: ServerVariables) -> None:

    file_path = f"{PROJECT_PATH}/{CONFIG_FOLDER}/HELP.txt"
    file_exists = os.path.isfile(file_path)

    if file_exists:
        with open(file_path) as file:
            
            echo_conn(conn, file.read())


def c_rules(obj: Message, conn: socket.socket, 
            s_vars: ServerVariables) -> None:

    file_path = f"{PROJECT_PATH}/{CONFIG_FOLDER}/RULES.txt"
    file_exists = os.path.isfile(file_path)

    if file_exists:
        with open(file_path) as file:

            echo_conn(conn, file.read())


def c_info(obj: Message, conn: socket.socket, 
           s_vars: ServerVariables) -> None:
           
    uptime = time.time() - s_vars.created_timestamp

    server_name = f"Server: {s_vars.hostname}:{s_vars.port}"
    channels_str = f"{len(s_vars.channels)} channels"
    users_str = f"{len(s_vars.conns)} connected users"
    uptime_str = f"Uptime: {utilities.format_time_period(uptime)}"

    echo = "\n".join([
        server_name,
        channels_str,
        users_str,
        uptime_str
    ])

    echo_conn(conn, echo)


def c_list(obj: Message, conn: socket.socket, 
           s_vars: ServerVariables) -> None:

    all_channels = s_vars.channels.values()

    if len(all_channels) == 0:
        echo_conn(conn, "No channels in server")
        return

    channels_string = "Channels:\n"
    channels_string += ", ".join(
        map(lambda c: c.get_name(), all_channels)
    )

    echo_conn(conn, channels_string)


def c_create(obj: Message, conn: socket.socket, 
             s_vars: ServerVariables) -> None:

    splits = utilities.smart_split(obj.message)

    if len(splits) < 2:
        return

    channel_name = splits[1]

    if channel_name in s_vars.channels:
        return

    password = None

    if len(splits) >= 3:
        password = splits[2]

    def on_connection_removed(conn: socket.socket) -> None:
        del s_vars.conn_channel_map[conn]

    channel = Channel(conn, on_connection_removed, channel_name, password)

    s_vars.channels[channel.id] = channel
    s_vars.channels.add_alias(channel.id, channel_name)

    join_user_to_channel(
        obj, conn, s_vars, channel, password
    )

    channel.send_message_history(conn)
    channel.welcome(conn)


def c_join(obj: Message, conn: socket.socket, 
           s_vars: ServerVariables) -> None:

    splits = utilities.smart_split(obj.message)

    if len(splits) < 2:
        return

    channel_name = splits[1]
    
    if channel_name not in s_vars.channels:  # Channel doesn't exist
        return

    channel = s_vars.channels[channel_name]

    # Joining the same channel
    if channel == s_vars.conn_channel_map.get(conn):
        return

    password = ""

    if len(splits) >= 3:
        password = splits[2]

    successful_join = join_user_to_channel(
        obj, conn, s_vars, channel, password
    )

    if successful_join:
        channel.send_message_history(conn)
        channel.welcome(conn)


def c_invite(obj: Message, conn: socket.socket, 
             s_vars: ServerVariables) -> None:

    splits = utilities.smart_split(obj.message)

    if len(splits) < 3:
        return

    target_nick = splits[1]
    channel_name = splits[2]

    if target_nick not in s_vars.nick_conn_map:
        echo_conn(conn, f"{target_nick} doesn't exist")
        return

    if channel_name not in s_vars.channels:
        echo_conn(conn, f"{channel_name} doesn't exist")
        return
    
    target_conn = s_vars.nick_conn_map[target_nick]
    channel = s_vars.channels[channel_name]

    echo_conn(target_conn, f"You've been invited to {channel.name}")


def c_die(obj: Message, conn: socket.socket, s_vars: ServerVariables) -> None:
    s_vars.quitted = True


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