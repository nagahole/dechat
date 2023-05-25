"""
    protocol.py
    A few wrappers for network functions for the dechat client and server
"""

import socket
from src.message import Message
# YOU WILL NEED TO MODIFY THESE FUNCTIONS TO SUIT THE HEADER FORMAT IN THE SPEC


DO_LOG = False


def log(*args, **kwargs):
    """
    Just a wrapper for print so I can easily enable or disable it
    """
    if DO_LOG:
        print(*args, **kwargs)


def message_send(message_obj: Message, connection: socket.socket) -> bytes:
    """
    message_send
    Converts a string message into a collection of bytes
    :: msg :: A string to send
    """
    encoding = message_obj.to_bytes()

    try:
        connection.sendall(encoding)
    except BrokenPipeError:
        pass

    return encoding


def message_recv(connection: socket.socket) -> Message:
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
                      timeout=0.5) -> tuple[bool, socket.socket | None]:
    """
    Sets up the socket
    :: hostname : str :: hostname to bind to
    :: port : int :: port to bind to

    Returns (successful, connection)
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)

    successful = False

    try:
        log(f"Trying to bind to {hostname}:{port}")
        sock.bind((hostname, port))
        successful = True
    except OSError:
        log("Address already in use")
        log("Please start the client on a different port, or wait for the "
            "address to unbind")

    if successful:
        log(f"Hosting on {sock.getsockname()[0]}:{sock.getsockname()[1]}")

        sock.listen()
        return True, sock

    return False, None


def conn_socket_setup(hostname: str, port: int, timeout=0.01):
    """
    Connects to a socket
    :: hostname : str :: hostname to connect to
    :: port : int :: port to connect to

    Returns (successful, connection)
    """
    log(f"Setting up socket at {hostname}:{port}")
    connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    connection.settimeout(1)
    successful = False
    try:
        log(f"Connecting to {hostname}:{port}")
        connection.connect((hostname, port))
        successful = True
    except ConnectionRefusedError:
        log("Connection Refused")
        log(f"It is possible that no server is running at {hostname}:{port}")
        connection = None
    except OSError as err:
        log(str(err))

    connection.settimeout(timeout)

    if successful:
        log("Successfully set up socket")
        return True, connection

    return False, None
