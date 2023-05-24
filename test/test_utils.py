"""
Dechat Testing Utils
"""

import threading
import time
from subprocess import Popen, PIPE
from functools import partial

# This should be the relative path from whever this script is launched to DECHAT

DECHAT_DIRECTORY = "."
SERVER_START_CMD = ["python3", "-u", "server.py"]
CLIENT_START_CMD = ["python3", "-u", "client.py"]

# Replacing POPEN so that we don"t need to worry about fds and cwd
Popen = partial(Popen, cwd=DECHAT_DIRECTORY, stdin=PIPE, stdout=PIPE)

def start_server(hostname="localhost", port=8889):
    """
        Starts a server
        Returns the python process object for of the server process
        You may find that if you try to re-use a port between servers
        in short succession that the old port is still bound.
        As a result this lets you shift which port your server is on
        between tests.
    """
    server = Popen(SERVER_START_CMD + [hostname, str(port)])
    return server

def start_client():
    """
        Starts a client
        Returns the python process object for of the server process

    """
    client = Popen(CLIENT_START_CMD)
    return client

def client_write(client, msg : str):
    """
        client_write
        Sends stdin to that client
    """
    client.stdin.write((msg + "\n").encode("ascii"))
    client.stdin.flush()

def client_read(client, timeout: float = 0.05) -> list:
    """
        client_read
        Reads stdout from that client
    """

    response = [[[]]]

    def read() -> None:
        while True:
            response[0][0].append(client.stdout.readline())

    thread = threading.Thread(target=read)
    thread.start()

    time.sleep(timeout)

    lines_str = list(map(lambda x: x.decode("utf-8"), response[0][0]))

    print("response: " + "".join(lines_str))

    # if len(lines_str) == 0:
    #     return None

    return lines_str
