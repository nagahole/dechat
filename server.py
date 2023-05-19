"""
    server.py
    dechat server
"""

import socket
import time
import sys
import src.utilities as utilities
from src.message import Message
from src.protocol import message_recv, bind_socket_setup
from src.commons import ServerVariables
from src.commands.server_commands import server_command_map, echo_conn

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

    tickrate = 8
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
        print("Server setup not successful, please try again")
        return

    s_vars = ServerVariables(hostname, port)

    while not s_vars.quitted:

        prev = time.time()

        try:  # Check for a new connection
            connection, addr = sock.accept()
            connection.settimeout(0.1)
            s_vars.conns.append(connection)

            server_command_map["motd"](Message(), connection, s_vars)

            print(f"New Connection! {addr}")

        except socket.timeout:
            pass

        # Check currently connected sessions
        i = 0
        while i < len(s_vars.conns):

            message_obj = None

            try:  # Check if any data has been passed in and print it

                message_obj = message_recv(s_vars.conns[i])

                print(f"Message received from {i}")

            # Connection exists, but no message received
            except socket.timeout:
                pass
            except ConnectionResetError:
                print(f"Connection {i} unexpectedly got reset")
                s_vars.conns.pop(i)
                i -= 1

            connection_closed = False

            if message_obj is not None:

                msg = message_obj.message

                # We assume that an empty message closes the connection.
                if msg == "":

                    print("Closing user " + str(i))

                    conn = s_vars.conns.pop(i)

                    if conn in s_vars.conn_channel_map:
                        channel = s_vars.conn_channel_map[conn]
                        channel.remove_connection(conn)
                        del s_vars.conn_channel_map[conn]

                    if message_obj.nickname in s_vars.nick_conn_map:
                        del s_vars.nick_conn_map[message_obj.nickname]

                    conn.close()
                    i -= 1

                    connection_closed = True
                    
            if message_obj is not None and not connection_closed:

                conn = s_vars.conns[i]
                s_vars.nick_conn_map[message_obj.nickname] = conn

                is_command = msg and msg[0] == "/"

                if conn in s_vars.conn_channel_map:

                    channel = s_vars.conn_channel_map[conn]

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

                        func(message_obj, conn, s_vars)
                    
                    else:

                        echo_conn(conn, "Command not recognized")

            i += 1

        # Sleep until the next server tick
        time.sleep(max((1 / tickrate) - (time.time() - prev), 0))


if __name__ == "__main__":
    main()
