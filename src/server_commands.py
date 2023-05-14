import os
import socket
import time
import src.utilities as utilities
from src.alias_dictionary import AliasDictionary
from src.channel import Channel
from src.message import Message
from src.protocol import message_send
from src.constants import SERVER_CHANNEL_ID, CONFIG_FOLDER

PROJECT_PATH = os.getcwd()


class ServerCommandArgs:
    def __init__(self, message_obj: Message, created_timestamp: float, 
                 conns: list[socket.socket], channels: AliasDictionary, 
                 connection_channel_map: dict[socket.socket, Channel],
                 nickname_connection_map: dict[str, socket.socket],
                 hostname: str, port: int):

        self.message_obj = message_obj
        self.created_timestamp = created_timestamp
        self.conns = conns
        self.channels = channels
        self.connection_channel_map = connection_channel_map
        self.nickname_connection_map = nickname_connection_map
        self.hostname = hostname
        self.port = port


def c_motd(conn: socket.socket, args: ServerCommandArgs) -> None:
    file_path = f"{PROJECT_PATH}/{CONFIG_FOLDER}/MOTD.txt"
    file_exists = os.path.isfile(file_path)

    if file_exists:
        with open(file_path) as file:

            echo_conn(conn, file.read())


def c_help(conn: socket.socket, args: ServerCommandArgs) -> None:
    file_path = f"{PROJECT_PATH}/{CONFIG_FOLDER}/HELP.txt"
    file_exists = os.path.isfile(file_path)

    print(file_path)
    print(file_exists)

    if file_exists:
        with open(file_path) as file:
            
            echo_conn(conn, file.read())


def c_rules(conn: socket.socket, args: ServerCommandArgs) -> None:
    file_path = f"{PROJECT_PATH}/{CONFIG_FOLDER}/RULES.txt"
    file_exists = os.path.isfile(file_path)

    if file_exists:
        with open(file_path) as file:

            echo_conn(conn, file.read())


def c_info(conn: socket.socket, args: ServerCommandArgs) -> None:
    uptime = time.time() - args.created_timestamp

    server_name = f"Server: {args.hostname}:{args.port}"
    channels_str = f"{len(args.channels)} channels"
    users_str = f"{len(args.conns)} connected users"
    uptime_str = f"Uptime: {utilities.format_time_period(uptime)}"

    echo = "\n".join([
        server_name,
        channels_str,
        users_str,
        uptime_str
    ])

    echo_conn(conn, echo)


def c_list(conn: socket.socket, args: ServerCommandArgs) -> None:

    all_channels = args.channels.values()

    if len(all_channels) == 0:
        echo_conn(conn, "No channels in server")
        return

    channels_string = "Channels:\n"
    channels_string += ", ".join(
        map(lambda c: c.get_name(), all_channels)
    )

    echo_conn(conn, channels_string)


def c_create(conn: socket.socket, args: ServerCommandArgs) -> None:
    splits = args.message_obj.message.split(" ")
    splits = list(filter(lambda s: s != "", splits))

    if len(splits) < 2:
        return

    channel_name = splits[1]

    if channel_name in args.channels:
        return

    password = None

    if len(splits) >= 3:
        password = splits[2]

    def on_connection_removed(n_conn: socket.socket) -> None:
        del args.connection_channel_map[n_conn]
        print(f"Removing connection from channel")

    channel = Channel(conn, on_connection_removed, channel_name, password)

    args.channels[channel.id, channel_name] = channel

    join_user_to_channel(
        conn, args, channel, password
    )

    channel.send_message_history(conn)
    channel.welcome(conn)


def c_join(conn: socket.socket, args: ServerCommandArgs) -> None:
    splits = args.message_obj.message.split(" ")
    splits = list(filter(lambda s: s != "", splits))

    if len(splits) < 2:
        return

    channel_name = splits[1]
    
    if channel_name not in args.channels:  # Channel doesn't exist
        return

    channel = args.channels[channel_name]

    # Joining the same channel
    if channel == args.connection_channel_map.get(conn):
        return

    password = ""

    if len(splits) >= 3:
        password = splits[2]

    successful_join = join_user_to_channel(
        conn, args, channel, password
    )

    if successful_join:
        channel.send_message_history(conn)
        channel.welcome(conn)


def c_invite(conn: socket.socket, args: ServerCommandArgs) -> None:
    splits = args.message_obj.message.split(" ")
    splits = list(filter(lambda s: s != "", splits))

    if len(splits) < 3:
        return

    target_nick = splits[1]
    channel_name = splits[2]

    if target_nick not in args.nickname_connection_map:
        echo_conn(conn, f"{target_nick} doesn't exist")
        return

    if channel_name not in args.channels:
        echo_conn(conn, f"{channel_name} doesn't exist")
        return
    
    target_conn = args.nickname_connection_map[target_nick]
    channel = args.channels[channel_name]

    echo_conn(target_conn, f"You've been invited to {channel.name}")


def echo_conn(conn: socket.socket, message: str) -> None:

    message_obj = Message(SERVER_CHANNEL_ID, "", time.time(),
                          0b01, message)

    message_send(message_obj, conn)


def leave_old_channel(conn: socket.socket, args: ServerCommandArgs) -> None:

    if conn in args.connection_channel_map:
        channel = args.connection_channel_map[conn]

        channel.remove_connection(conn)

        del args.connection_channel_map[conn]


def join_user_to_channel(conn: socket.socket, args: ServerCommandArgs,
                         channel: Channel, password: str = "") -> bool:

    leave_old_channel(conn, args)

    nickname = args.message_obj.nickname

    successful_join = channel.add_connection(conn, nickname, password)

    if successful_join:
        args.connection_channel_map[conn] = channel

    return successful_join


server_command_map = {
    "motd": c_motd,
    "help": c_help,
    "rules": c_rules,
    "info": c_info,
    "list": c_list,
    "create": c_create,
    "join": c_join,
    "invite": c_invite
}
