"""
    client.py
    dechat client
"""

import socket
import threading
import time
import sys
import src.utilities as utilities
from src.message import Message
from src.protocol import message_send, message_recv, conn_socket_setup
from src.constants import MAX_NICK_LENGTH, MAX_PORT_VALUE, NICK_MSG_SEPARATOR

INPUT_PROMPT = "> "


def main():
    """
    main
    Entrypoint for the client
    """

    quitted = False
    default_nickname = "anon"
    
    while not quitted:

        connection = None
    
        while connection is None and not quitted:
            user_input = input(INPUT_PROMPT)

            utilities.clear_line()

            splits = user_input.split(" ")
            splits = list(filter(lambda s: s != "", splits))

            if len(splits) != 0 and splits[0] != "" and splits[0][0] == "/":
                
                command = splits[0][1:].lower()

                match command:
                    case "c":
                        successful, connection = conn_socket_setup(
                            "localhost", 9996
                        )

                    case "connect":
                        
                        errored = False
                        host_port = ""
                        hostname = ""
                        port = -1

                        if len(splits) < 2:
                            errored = True
                        else:
                            host_port = splits[1].split(":")

                        if not errored and len(host_port) >= 2:

                            hostname = ":".join(host_port[0: -1])

                            if utilities.is_integer(host_port[-1]):
                                port = int(host_port[-1])

                                if not 0 <= port <= MAX_PORT_VALUE:
                                    errored = True

                            else:
                                errored = True

                        else: 
                            errored = True

                        if not errored:
                            print("Connecting to server...")
                            successful, connection = conn_socket_setup(
                                hostname, port
                            )

                            if not successful:
                                print("Failed to connect to server")

                    case "quit":
                        quitted = True

                    case "nick":
                        if len(splits) >= 2:
                            new_nick = splits[1]

                            if len(new_nick) > MAX_NICK_LENGTH:
                                print("Maximum nickname length is 15")
                            else:
                                default_nickname = new_nick
                                print(
                                    f"Default nickname set to {new_nick}"
                                )

                    case unrecognized_command:
                        print(
                            f'Command "{unrecognized_command}" not recognized'
                        )

        if connection and not quitted:

            # Second argument is the last nickname that messaged
            # Third argument is whether user is in a channel
            state = [[True], [None], [False]]

            # Start the listener, don"t worry about this bit unless 
            # you need multiple connections from one client
            listener = threading.Thread(
                target=client_listener,
                args=(connection, state),
                kwargs={"tickrate": 8})
            listener.start()

            # Start the sender
            client_sender(connection, default_nickname, state)

            # Stop the listener
            state[0][0] = False

            # Close the listener thread
            listener.join()

            # Close the connection
            connection.close()

    return


def client_sender(connection: socket.socket, default_nickname: str,
                  state: list) -> None:
    """
        client_sender
        Sends messages from the client
        :: connection :: Socket connection
    """

    quitted = False

    # Close the connection on an empty message

    while not quitted and len((user_input := input(INPUT_PROMPT))) > 0:
        
        utilities.clear_line()

        message_obj = Message(
            0, default_nickname, time.time(), 0b00, user_input
        )
        
        if user_input != "" and user_input[0] == "/":

            splits = list(filter(lambda s: s, user_input.split(" ")))
            command = splits[0][1:].lower()

            message_obj = Message(
                0, default_nickname, time.time(), 0b01, user_input
            )

            match command:
                case "reply":
                    if len(splits) < 2:
                        print("Usage: /reply <message>")
                        message_obj = None
                    else:

                        last_whisperer = state[1][0]

                        if not last_whisperer:
                            print("No one messaged you recently!")
                            message_obj = None
                        else:
                            msg = user_input.split(' ', 1)[1]
                            echo = f"/msg {last_whisperer} {msg}"

                            message_obj = Message(
                                0, default_nickname, time.time(), 0b01, echo
                            )

                case "quit":
                    in_channel = state[2][0]

                    if not in_channel:
                        print("Disconnecting from server...")
                        quitted = True
                        message_obj = None
                    else:  # Is in channel and quitting the channel
                        state[2][0] = False

        if message_obj:
            message_send(message_obj, connection)

    # Send an empty message to close the connection
    # You may want something more sophisticated
    message_send(Message(0, "", time.time(), 0b00, ""), connection) 
    return


def client_listener(connection, state, tickrate=0.5):
    """
        client_listener
        This function will listen and print in parallel with the main program.
        Use the state variable to share state where needed.
        :: connection :: The connection to listen to
        :: state :: Shares state with the main thread
    """
    # Using a list as a pointer to avoid Python's reallocation problems
    # A class would be much better here, you might want to consider it
    print("Listening!", id(state[0]))
    while state[0][0] is True:

        try:
            
            # While message_obj isn't None
            while message_obj := message_recv(connection):
                handle_message_received(message_obj, state)

        except socket.timeout:
            continue

        time.sleep(1/tickrate)
    return


def handle_message_received(obj: Message, state: list) -> None:

    time_string = utilities.unix_to_str(obj.timestamp)

    match obj.message_type:
        case 0b00:  # Channel posts

            # Client is in a channel
            if "has quit" not in obj.message:
                state[2][0] = True

            message_separator = NICK_MSG_SEPARATOR
            
            if "->" in obj.nickname:  # Is a message
                state[1][0] = obj.nickname.split("->")[0].strip()
                message_separator = ":"

            nickname = obj.nickname.rjust(32)

            lines = obj.message.split("\n")

            echo = lines[0]

            for i, line in enumerate(lines):
                if i != 0:
                    echo += "\n"
                    echo += " " * 40
                    echo += message_separator
                    echo += f" {line}"

            echo = "".join([
                time_string,
                nickname,
                message_separator,
                f" {echo}"
            ])
            
            print("\r" + echo, end="")
            sys.stdout.flush()
            print(f"\n{INPUT_PROMPT}", end="")

        case 0b01:
            if obj.message != "":       
                print("\r" + obj.message, end="")
                sys.stdout.flush()
                print(f"\n{INPUT_PROMPT}", end="")


main()
