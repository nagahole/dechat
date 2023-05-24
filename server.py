"""
    server.py
    dechat server
"""

import socket
import time
import sys
from src import ansi
from src import utilities
from src.message import Message, CLOSE_MESSAGE
from src.protocol import message_send, message_recv, bind_socket_setup
from src.commons import ServerMembers, ChannelLinkInfo, ServerConnectionInfo
from src.commands.server_commands import server_command_map, echo_conn
from src.constants import (
    SERVER_CHANNEL_ID,
    LINK_FLAG,
    LINK_RESPONSE_FLAG,
    UNLINK_FLAG,
    SEP
)

# A better solution to this would be to poll rather than try and except
# But due to Windows compatibility issues Python's socket object does not
# support native polling. As a result we will be emulating a non-blocking
# stream using exceptions. This implementation is hopefully also easier to
# understand.


def main():
    """
        main
        Entrypoint for the server
    """

    tickrate = 32
    port = 9996
    host = "localhost"

    if len(sys.argv) >= 3:
        host = sys.argv[1]

        if utilities.is_integer(sys.argv[2]):
            port = int(sys.argv[2])

    run_server(host, port, tickrate)


def run_server(hostname="localhost", port=9996, tickrate=1):
    """
    Runs the server
    :: hostname : str :: hostname to run on, default "localhost"
    :: port : int :: port to run on, default 9996
    :: tickrate : float :: How often the server should poll, default 1 second
    """

    # Bound socket
    successful, sock = bind_socket_setup(hostname, port)

    if not successful:

        if "--auto-retry" in sys.argv:
            while not successful:
                for i in range(3, 0, -1):
                    print(f"Connection not successful. Retrying in {i}")
                    time.sleep(1)
                    ansi.clear_line()

                successful, sock = bind_socket_setup(hostname, port)
        else:
            print("Server setup not successful, please try again")
            return

    print(f"Hosting on {hostname}:{port}")

    s_mems = ServerMembers(hostname, port)

    while not s_mems.quitted:

        prev = time.time()

        try:  # Check for a new connection
            connection, addr = sock.accept()
            connection.settimeout(0.1)
            s_mems.conns.append(ServerConnectionInfo(connection))

            server_command_map["motd"](None, connection, s_mems)

            print(f"New Connection! {addr}")

        except socket.timeout:
            pass

        # Check currently connected sessions
        i = 0
        while i < len(s_mems.conns):

            message_obj = -1

            try:  # Check if any data has been passed in and print it

                message_obj = message_recv(s_mems.conns[i].connection)

                print(f"RECV: {message_obj}")

                print(f"Message received from {i}")

            # Connection exists, but no message received
            except socket.timeout:
                pass
            except ConnectionResetError:
                print(f"Connection {i} unexpectedly got reset")
                s_mems.conns.pop(i)
                i -= 1

            connection_closed = False

            if message_obj is None or message_obj == CLOSE_MESSAGE:

                print("Closing user " + str(i))

                conn = s_mems.conns.pop(i).connection

                if conn in s_mems.conn_channel_map:
                    channel = s_mems.conn_channel_map[conn]
                    channel.remove_connection(conn)
                    del s_mems.conn_channel_map[conn]

                if message_obj is not None:
                    if message_obj.nickname in s_mems.nick_conn_map:
                        del s_mems.nick_conn_map[message_obj.nickname]

                conn.close()
                i -= 1

                connection_closed = True

            if isinstance(message_obj, Message) and not connection_closed:

                msg = message_obj.message
                conn_info = s_mems.conns[i]
                conn = conn_info.connection

                if message_obj.message_type not in (0b11, 0b10):

                    s_mems.nick_conn_map[message_obj.nickname] = conn

                    is_command = msg and msg[0] == "/"

                    if conn in s_mems.conn_channel_map:

                        channel = s_mems.conn_channel_map[conn]

                        if is_command:
                            channel.handle_command_input(conn, message_obj)
                        else:
                            channel.handle_user_message(conn, message_obj)

                    elif is_command:
                        splits = msg.split(" ")
                        splits = list(filter(lambda s: s != "", splits))

                        command = splits[0][1:]

                        if command in server_command_map:

                            func = server_command_map[command]

                            func(message_obj, conn, s_mems)

                        else:

                            echo_conn(conn, "Command not recognized")

                elif message_obj.message_type == 0b10:

                    conn_info.is_server = True

                    if msg.startswith(LINK_FLAG):
                        # Channel linkage requests
                        # Standard is:
                        # '--link|<channel_name>|<hostname>|<port>|'
                        # Where | is the special SEP constant
                        splits = msg.split(SEP)

                        channel_name = splits[1]

                        channel_id = SERVER_CHANNEL_ID
                        channel = None

                        if channel_name in s_mems.channels:
                            channel = s_mems.channels[channel_name]
                            channel_id = channel.id

                        # Requested link channel exists
                        if channel is not None:

                            link_info = ChannelLinkInfo(
                                channel_name=channel_name,
                                hostname=splits[2],
                                port=int(splits[3]),
                                connection=conn,
                                channel_id=message_obj.channel_id
                            )

                            channel.link_channel(link_info)

                        response = Message(
                            channel_id,
                            "",
                            time.time(),
                            0b10,
                            SEP.join((
                                LINK_RESPONSE_FLAG,
                                channel_name,
                                hostname,
                                str(port)
                            ))
                        )

                        print(f"SENT: {response}")
                        message_send(response, conn)

                    elif msg.startswith(UNLINK_FLAG):
                        # Channel unlinkage requests
                        # Standard is:
                        # '--link|<channel_name>|<hostname>|<port>|'
                        # Where | is the special SEP constant

                        splits = msg.split(SEP)

                        channel_name = splits[1]

                        if channel_name in s_mems.channels:
                            channel = s_mems.channels[channel_name]

                            channel.unlink_channel(
                                channel_name,
                                hostname=splits[2],
                                port=int(splits[3])
                            )

                    elif msg.startswith(LINK_RESPONSE_FLAG):
                        # Standard is:
                        # '--response|<channel_name>|<hostname>|<port>|'

                        success = message_obj.channel_id != SERVER_CHANNEL_ID

                        if success:
                            splits = msg.split(SEP)

                            channel_name = splits[1]

                            for channel in s_mems.channels.values():
                                if channel.name == channel_name:

                                    link_info = ChannelLinkInfo(
                                        channel_name=channel_name,
                                        hostname=splits[2],
                                        port=int(splits[3]),
                                        connection=conn,
                                        channel_id = message_obj.channel_id
                                    )

                                    channel.link_channel(link_info)
                                    break

                elif message_obj.message_type == 0b11:
                    # / Cross server channel synchronisation

                    conn_info.is_server = True

                    if message_obj.channel_id in s_mems.channels:
                        channel = s_mems.channels[message_obj.channel_id]
                        message_obj.set_message_type(0b00)
                        channel.broadcast_message(message_obj)
                    else:
                        print(
                            "WARNING: Attempt to relay to a channel that "
                            f"doesn't exist (id:{message_obj.channel_id})"
                        )

            i += 1

        # Sleep until the next server tick
        time.sleep(max((1 / tickrate) - (time.time() - prev), 0))


if __name__ == "__main__":
    main()
