'''
    server.py
    dechat server
'''

import socket
import time
from src.protocol import message_send, message_recv, bind_socket_setup

# A better solution to this would be to poll rather than try and except
# But due to Windows compatability issues Python's socket object does not
# support native polling. As a result we will be emulating a non-blocking
# stream using exceptions. This implementation is hopefully also easier to
# understand.

def main():
    '''
        main
        Entrypoint for the server
    '''

    # Sets the server tick rate
    tickrate = 1.0
    port = 9996
    host = 'localhost'

    run_server(host, port, tickrate)


def run_server(hostname='localhost', port=9996, tickrate=1):
    '''
        Runs the server
        :: hostname : str :: hostname to run on, default 'localhost'
        :: port : int :: port to run on, default 9996
        :: tickrate : float :: How often the server should poll, default 1 second
    '''

    # Bound socket
    sock = bind_socket_setup(hostname, port)
    # List of active connections
    conns = []

    # Loop server, you will want a better exit condition
    while True:
        prev = time.time()

        print("TICK")
        try: # Check for a new connection
            connection, addr = sock.accept()
            connection.settimeout(0.1)
            conns.append(connection)
            print(f"New Connection! {addr}")
        except socket.timeout:
            pass

        # Check currently connected sessions
        i = 0
        while i < len(conns):
            try: # Check if any data has been passed in and print it
                msg = message_recv(conns[i])

               # We assume that an empty message closes the connection.
                if msg is None:
                    conn = conns.pop(i)
                    conn.close()
                    i -= 1

                # If the connection has not closed then echo the message
                else:
                    # Convert from bytes to str
                    msg_str = msg.decode('utf-8')
                    print(msg_str)
                    message_send(msg_str, conns[i])

            # Connection exists, but no message received
            except socket.timeout:
                print(f"Nothing on {i}")
            i += 1

        # Sleep until the next server tick
        time.sleep(max(tickrate - (prev - time.time()), 0))

if __name__ == '__main__':
    main()
