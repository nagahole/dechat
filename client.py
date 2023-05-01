'''
    client.py
    dechat client
'''

import socket
import threading
import time
from src.protocol import message_send, message_recv, conn_socket_setup

def main():
    '''
    main
    Entrypoint for the client
    '''
    hostname = 'localhost'
    port = 9996

    state = [[True]]
    connection = conn_socket_setup(hostname, port)

    if connection is None:
        return

    # Start the listener, don't worry about this bit unless 
    # you need multiple connections from one client
    listener = threading.Thread(
        target=client_listener,
        args=(connection, state),
        kwargs={'tickrate':0.5})
    listener.start()

    # Start the sender
    client_sender(connection)

    # Stop the listener
    state[0][0] = False

    # Close the listener thread
    listener.join()

    # Close the connection
    connection.close()
    return

def client_sender(connection):
    '''
        client_sender
        Sends messages from the client
        :: connection :: Socket connection
    '''
    message_send("Hello!", connection, debug=True)

    # Close the connection on an empty message
    while len((msg := input())) > 0:
        message_send(msg, connection, debug=True)

    # Send an empty message to close the connection
    # You may want something more sophisticated
    message_send('', connection)
    return

def client_listener(connection, state, tickrate=0.5):
    '''
        client_listener
        This function will listen and print in parallel with the main program.
        Use the state variable to share state where needed.
        :: connection :: The connection to listen to
        :: state :: Shares state with the main thread
    '''
    # Using a list as a pointer to avoid Python's reallocation problems
    # A class would be much better here, you might want to consider it
    print("Listening!", id(state[0]))
    while state[0][0] is True:
        try:
            print(message_recv(connection, debug=True).decode('utf-8'))
        except socket.timeout:
            continue
        time.sleep(tickrate)
    return

main()
