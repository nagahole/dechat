'''
Dechat Testing Utils
'''
from subprocess import Popen, PIPE
from functools import partial

# This should be the relative path from whever this script is launched to DECHAT
DECHAT_DIRECTORY = '.'
SERVER_START_CMD = 'python3 server.py {hostname} {port}'
CLIENT_START_CMD = 'python3 client.py'

# Replacing POPEN so that we don't need to worry about fds and cwd
Popen = partial(Popen, cwd=DECHAT_DIRECTORY, stdin=PIPE, stdout=PIPE)

def start_server(hostname='localhost', port=8889):
    '''
        Starts a server
        Returns the python process object for of the server process
        You may find that if you try to re-use a port between servers
        in short succession that the old port is still bound.
        As a result this lets you shift which port your server is on
        between tests.
    '''
    server = Popen(SERVER_START_CMD.format(hostname=hostname, port=port).split())
    return server

def start_client():
    '''
        Starts a client
        Returns the python process object for of the server process

    '''
    client = Popen(CLIENT_START_CMD.split())
    return client

def client_write(client, msg : str):
    '''
        client_write
        Sends stdin to that client
    '''
    client.stdin.write(msg.encode('ascii'))
    client.stdin.flush()

def client_read(client) -> list:
    '''
        client_read
        Reads stdout from that client
    '''
    n_lines = client.stdout.peek().count('\n'.encode('ascii'))
    lines = [client.stdout.readline() for _ in range(n_lines)]
    lines_str = list(map(lambda x: x.decode('utf-8'), lines))
    return lines_str
