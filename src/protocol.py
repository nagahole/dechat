"""
    protocol.py
    A few wrappers for network functions for the dechat client and server
"""

import socket
from src.message import Message
# YOU WILL NEED TO MODIFY THESE FUNCTIONS TO SUIT THE HEADER FORMAT IN THE SPEC


def message_send(message_obj: Message, connection: socket.socket) -> bytes:
    """
    message_send
    Converts a string message into a collection of bytes
    :: msg :: A string to send
    """
    encoding = message_obj.to_bytes()
    connection.sendall(encoding)

    return encoding


def message_recv(connection) -> Message:
    """
    message_recv
    Waits for a message on the connection and attempts to decode it
    :: connection : socket :: The connection to wait on
    """
    header = connection.recv(38)
    type_and_length_bytes = connection.recv(2)

    message_length = Message.decode_type_and_length(type_and_length_bytes)[1]

    message_bytes = connection.recv(message_length)

    all_bytes = header + type_and_length_bytes + message_bytes

    message_obj = Message.from_bytes(all_bytes)

    return message_obj


# You should probably not have to touch these functions
def bind_socket_setup(hostname: str, port: int,
                      timeout=0.1) -> tuple[bool, socket.socket | None]:
    """
        Sets up the socket
        :: hostname : str :: hostname to bind to
        :: port : int :: port to bind to
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    
    successful = False

    try:
        print(f"Trying to bind to {hostname}:{port}")
        sock.bind((hostname, port))
        successful = True
    except OSError:
        print("Address already in use")
        print("Please start the client on a different port, or wait for the "
              "address to unbind")

    if successful:
        print(f"Hosting on {sock.getsockname()[0]}:{sock.getsockname()[1]}")

        sock.listen()
        return True, sock
    else:
        return False, None


def conn_socket_setup(hostname: str, port: int, timeout=0.1):
    """
        Connects to a socket
        :: hostname : str :: hostname to connect to
        :: port : int :: port to connect to
    """
    print(f"Setting up socket at {hostname}:{port}")
    connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    connection.settimeout(timeout)
    successful = False
    try:
        connection.connect((hostname, port))
        successful = True
    except ConnectionRefusedError:
        print("Connection Refused")
        print(f"It is possible that no server is running at {hostname}:{port}")
        connection = None
    except OSError as e:
        print(str(e))

    if successful:
        return True, connection
    else:
        return False, None
