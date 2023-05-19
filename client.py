"""
    client.py
    dechat client
"""

import socket
import threading
import time
import sys
import src.utilities as utilities
import src.ansi as ansi
from src.commons import ClientVariables, ClientStates, ClientSenderVariables
from src.commands.client_commands import client_command_map, client_sender_command_map
from src.message import Message
from src.protocol import message_send, message_recv, conn_socket_setup

INPUT_PROMPT = "> "


class Client:
    def __init__(self, ui_enabled: bool=False) -> None:
        self.ui_enabled = ui_enabled
        self.c_vars = ClientVariables()

    def start(self) -> None:
    
        while not self.c_vars.quitted:
            self.loop()

    def loop(self) -> None:

        while self.c_vars.connection is None and not self.c_vars.quitted:

            user_input = input(INPUT_PROMPT)

            if self.ui_enabled:
                ansi.clear_line()

            if user_input != "" and user_input[0] == "/":

                splits = utilities.smart_split(user_input)
                
                command = splits[0][1:].lower()

                if command in client_command_map:

                    func = client_command_map[command]

                    func(user_input, self.c_vars)
                
                else:
                    print(f"Command /{command} not recognized")
                    
        if self.c_vars.connection is not None and not self.c_vars.quitted:

            states = ClientStates()

            # Start the listener, don"t worry about this bit unless 
            # you need multiple connections from one client
            listener = threading.Thread(
                target=self.client_listener,
                args=(self.c_vars.connection, states),
                kwargs={"tickrate": 8}
            )

            listener.start()

            # Start the sender
            self.client_sender(states)

            # Stop the listener
            states.listening = False

            # Close the listener thread
            listener.join()

            # Close the connection
            self.c_vars.connection.close()
        
    def client_sender(self, states: ClientStates) -> None:
        """
            client_sender
            Sends messages from the client
            :: connection :: Socket connection
        """

        cs_vars = ClientSenderVariables(Message(), quitted=False)

        # Close the connection on an empty message
        while not cs_vars.quitted and len(user_input := input(INPUT_PROMPT)) > 0:

            if self.ui_enabled:
                ansi.clear_line()

            if states.in_channel:
                message_type = 0b00
            else:
                message_type = 0b01

            cs_vars.message_obj = Message(
                0, 
                self.c_vars.default_nickname, 
                time.time(), 
                message_type, 
                user_input
            )
            
            if user_input != "" and user_input[0] == "/":

                splits = utilities.smart_split(user_input)
                command = splits[0][1:].lower()

                if command in client_sender_command_map:
                    func = client_sender_command_map[command]

                    func(user_input, states, cs_vars)


            if cs_vars.message_obj is not None:
                message_send(cs_vars.message_obj, self.c_vars.connection)

        # Send an empty message to close the connection
        # You may want something more sophisticated
        message_send(
            Message(0, "", time.time(), 0b00, ""),
            self.c_vars.connection
        )

        return

    def client_listener(self, connection: socket.socket, states: ClientStates,
                        tickrate: float=0.5) -> None:
        """
            client_listener
            This function will listen and print in parallel with the main program.
            Use the state variable to share state where needed.
            :: connection :: The connection to listen to
            :: state :: Shares state with the main thread
        """

        # Using a list as a pointer to avoid Python's reallocation problems
        # A class would be much better here, you might want to consider it
        print("Listening!", id(states))
        while states.listening:

            try:
                
                # While message_obj isn't None
                while message_obj := message_recv(connection):
                    self.handle_message_received(message_obj, states)

            except socket.timeout:
                continue

            time.sleep(1/tickrate)
        return


    def handle_message_received(self, obj: Message, 
                                states: ClientStates) -> None:

        match obj.message_type:
            case 0b00:  # Channel posts

                # Client is in a channel
                if "has quit" not in obj.message:
                    states.in_channel = True

                if "->" in obj.nickname:  # Is a message
                    states.last_whisperer = obj.nickname.split("->")[0].strip()
                
                if self.ui_enabled:
                    print("\r" + obj.format(), end="")
                    sys.stdout.flush()
                    print(f"\n{INPUT_PROMPT}", end="")
                else:
                    print(obj.format())

            case 0b01:
                if obj.message != "":
                    if self.ui_enabled:
                        print("\r" + obj.format(), end="")
                        sys.stdout.flush()
                        print(f"\n{INPUT_PROMPT}", end="")
                    else:
                        print(obj.format())



def main():
    """
    main
    Entrypoint for the client
    """

    ui_enabled = "--ui" in sys.argv

    client = Client(ui_enabled)

    client.start()

    return


if __name__ == "__main__":
    main()
