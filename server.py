"""
    server.py
    dechat server
"""

import socket
import time
import sys
import src.utilities as utilities
from src.protocol import message_send, message_recv, bind_socket_setup
from src.message import Message
from src.channel import Channel
from src.alias_dictionary import AliasDictionary
from src.server_commands import ServerCommandArgs, server_command_map

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

    created_timestamp = time.time()
    conns = []
    channels = AliasDictionary()

    # To help remove users from previous channels when they join a new one
    connection_channel_map = {}

    # Loop server, you will want a better exit condition
    while True:
        prev = time.time()

        try:  # Check for a new connection
            connection, addr = sock.accept()
            connection.settimeout(0.1)
            conns.append(connection)
            print(f"New Connection! {addr}")
        except socket.timeout:
            pass

        # Check currently connected sessions
        i = 0
        while i < len(conns):
            
            response_received = False

            try:  # Check if any data has been passed in and print it

                message_obj = message_recv(conns[i])

                if message_obj is not None:
                    response_received = True

                print(f"Message received from {i}")

            # Connection exists, but no message received
            except socket.timeout:
                pass
            except ConnectionResetError:
                print(f"Connection {i} unexpectedly got reset")
                conns.pop(i)
                i -= 1

            connection_closed = False

            if response_received:

                msg = message_obj.message

                # We assume that an empty message closes the connection.
                if msg == "":

                    print("Closing user " + str(i))

                    conn = conns.pop(i)

                    if conn in connection_channel_map:
                        channel = connection_channel_map[conn]
                        channel.remove_connection(conn)
                        del connection_channel_map[conn]

                    conn.close()
                    i -= 1

                    connection_closed = True
                    
            if response_received and not connection_closed:

                conn = conns[i]

                is_command = msg != "" and msg[0] == "/"

                if conn in connection_channel_map:

                    channel = connection_channel_map[conn]

                    if is_command:
                        channel.handle_command_input(conn, message_obj)
                    else:
                        channel.handle_user_message(conn, message_obj)

                elif is_command:
                    splits = msg.split(" ")
                    splits = list(filter(lambda s: s != "", splits))

                    command = splits[0][1:]

                    if command in server_command_map:

                        args = ServerCommandArgs(
                            message_obj,
                            created_timestamp,
                            conns,
                            channels,
                            connection_channel_map,
                            hostname,
                            port
                        )

                        func = server_command_map[command]

                        func(conn, args)

            i += 1

        # Sleep until the next server tick
        time.sleep(max((1 / tickrate) - (time.time() - prev), 0))


if __name__ == "__main__":
    main()
