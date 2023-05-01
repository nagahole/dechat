'''
    protocol.py
    A few wrappers for network functions for the dechat client and server
'''

import socket
# YOU WILL NEED TO MODIFY THESE FUNCTIONS TO SUIT THE HEADER FORMAT IN THE SPEC


def message_send(msg : str, connection, debug=False) -> bytes:
    '''
    message_send
    Converts a string message into a collection of bytes
    :: msg :: A string to send
    '''
    msg_bytes = msg.encode('ascii')
    length_bytes = len(msg).to_bytes(2, 'little')

    joined_msg = length_bytes + msg_bytes

    if debug:
        print("SENDING: ", joined_msg)

    connection.sendall(joined_msg)
    return joined_msg

def message_recv(connection, header_length=2, debug=False) -> bytes:
    '''
    message_recv
    Waits for a message on the connection and attempts to decode it
    :: connection : socket :: The connection to wait on
    :: header_length:: The length of the header, defaults to 2
    '''
    header = connection.recv(header_length)
    length = int.from_bytes(header, 'little')

    msg =  None
    if length > 0:
        msg = connection.recv(length)

    if debug:
        print("RECIEVED:", header, msg)

    return msg


# You should probably not have to touch these functions
def bind_socket_setup(hostname : str, port : int, timeout=0.1):
    '''
        Sets up the socket
        :: hostname : str :: hostname to bind to
        :: port : int :: port to bind to
    '''
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    try:
        sock.bind((hostname, port))
    except __builtins__.OSerror:
        print("Address already in use")
        print("Please start the client on a different port, or wait for the address to unbind")

    sock.listen()
    return sock

def conn_socket_setup(hostname : str, port : int, timeout=0.1):
    '''
        Connects to a socket
        :: hostname : str :: hostname to connect to
        :: port : int :: port to connect to
    '''
    connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    connection.settimeout(timeout)
    try:
        connection.connect((hostname, port))
    except ConnectionRefusedError:
        print("Connection Refused")
        print(f"It is possible that no server is running at {hostname}:{port}")
        connection = None
    return connection
