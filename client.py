"""
    client.py
    dechat client
"""

import socket
import time
import sys
import threading
from src import utilities
from src import ansi
from src.commons import (
    ClientConnectionWrapper,
)
from src.commands.client_commands import (
    client_command_map,
    client_sender_command_map,
    multicon_client_command_map,
    multicon_client_sender_command_map,
    limbo_command_map
)
from src.message import Message, CLOSE_MESSAGE
from src.protocol import message_send, message_recv

INPUT_PROMPT = "> "
SERVER_NAME_REF = "Server: "
CHANNEL_JOIN_STR = " joined the channel!"
QUIT_STR = "has quit"
WHISPER_SEP = "->"


class Client:
    """
    Client class
    """
    def __init__(self, ui_enabled: bool = False) -> None:
        self.quitted = False
        self.default_nickname = "anon"
        self.ui_enabled = ui_enabled
        self.con_wrappers = {}

        self.current_wrapper = None

    def clear_closed_wrappers(self) -> None:
        """
        Removes closed wrappers from self.con_wrappers
        """
        keys_to_delete = []

        for key, wrapper in self.con_wrappers.items():
            if wrapper.closed:
                keys_to_delete.append(key)

        for key in keys_to_delete:
            del self.con_wrappers[key]

    def exists_cons(self) -> bool:
        """
        Intelligently checks if there are any non-closed wrappers
        """
        self.clear_closed_wrappers()

        return len(self.con_wrappers) > 0

    def add_wrapper(self, wrapper: ClientConnectionWrapper,
                    num: int = None) -> int:
        """
        Intelligently adds wrappers to con_wrappers dictionary

        Returns the key of the newly added wrapper
        """
        self.clear_closed_wrappers()

        if num is None:
            i = 0
            while i in self.con_wrappers:
                i += 1
            self.con_wrappers[i] = wrapper
            return i

        # else n is given
        if num in self.con_wrappers:
            raise KeyError(f"Key {num} already exists in con_wrappers!")
            # This is so I know mistakes early

        self.con_wrappers[num] = wrapper
        return num

    def change_display(self, num: int, clear_terminal: bool = True,
                       ping_for_info: bool = False) -> None:
        """
        Changes to the display specified by its num
        """
        if num in self.con_wrappers:
            self.activate_wrapper(
                self.con_wrappers[num],
                clear_terminal=clear_terminal,
                ping_for_info=ping_for_info
            )
        else:
            raise KeyError(f"Display {num} doesn't exist!")

    def activate_wrapper(self, wrapper: ClientConnectionWrapper,
                         clear_terminal: bool = True,
                         ping_for_info: bool = False) -> None:
        """
        Activates a wrapper, setting up client listeners and client senders
        for that wrapper
        """

        if wrapper.closed:
            raise RuntimeError(
                "Attempting to activate a closed connection wrapper"
            )

        if self.current_wrapper == wrapper:
            print("Already on that server!")
            return

        for i_wrapper in self.con_wrappers.values():
            if i_wrapper != wrapper:
                i_wrapper.states.active = False

        wrapper.states.active = True

        self.current_wrapper = wrapper

        if clear_terminal and self.ui_enabled:
            utilities.clear_terminal()

        # Don't want handle_message_received to
        # change states in actual wrapper
        dummy = ClientConnectionWrapper(None)

        # To get printing processed messages working correctly
        dummy.states.active = True

        for message in reversed(wrapper.messages):
            self.process_received_message(message, dummy, real_message=False)

        if wrapper.listener is None:

            wrapper.listener = threading.Thread(
                target=self.client_listener,
                args=(wrapper,),
                kwargs={"tickrate": 8}
            )

            wrapper.listener.start()

        if self.ui_enabled and ping_for_info:
            wrapper.states.pinging_for_info = True
            ping = Message(
                0, self.default_nickname, time.time(), 0b01, "/info"
            )
            message_send(ping, wrapper.connection)

        self.client_sender(wrapper)

        self.current_wrapper = None

    def start(self) -> None:
        """
        Starts running the client
        """
        while not self.quitted:
            self.loop()

    def take_user_input(self, command_map: dict[str, callable]) -> None:
        """
        Handles user input against a command map
        """
        user_input = input(INPUT_PROMPT)

        if self.ui_enabled:
            ansi.clear_line()

        if user_input != "" and user_input[0] == "/":

            splits = utilities.smart_split(user_input)

            command = splits[0][1:].lower()

            if command in command_map:

                func = command_map[command]

                func(user_input, self)

            else:
                print(f"Command /{command} not recognized")

    def loop(self) -> None:
        """
        Command loop
        """
        while not self.exists_cons() and not self.quitted:
            if self.ui_enabled:
                self.take_user_input(multicon_client_command_map)
            else:
                self.take_user_input(client_command_map)

        while (self.exists_cons() and
               self.current_wrapper is None and
               not self.quitted):
            # Quit a server, but it's multicon and connected to others
            self.take_user_input(limbo_command_map)

    def client_sender(self, wrapper: ClientConnectionWrapper) -> None:
        """
        Sends messages from the client
        """

        empty_message = False

        # Close the connection on an empty message
        while not wrapper.closed and not empty_message:

            if not wrapper.states.active:
                return

            user_input = input(INPUT_PROMPT)

            if self.ui_enabled:
                ansi.clear_line()

            if len(user_input) > 0:

                message_type = 0b01

                if wrapper.states.in_channel:
                    message_type = 0b00

                wrapper.message_obj = Message(
                    0,
                    self.default_nickname,
                    time.time(),
                    message_type,
                    user_input
                )

                if user_input[0] == "/":

                    splits = utilities.smart_split(user_input)
                    command = splits[0][1:].lower()

                    if self.ui_enabled:
                        command_map = multicon_client_sender_command_map
                    else:
                        command_map = client_sender_command_map

                    if command in command_map:
                        func = command_map[command]

                        func(user_input, self, wrapper)

                    if self.ui_enabled and command in ("join", "create"):

                        wrapper.states.joining_channel = True
                        if len(splits) >= 2:
                            wrapper.channel_name = splits[1]

                if wrapper.message_obj is not None and not wrapper.closed:
                    message_send(wrapper.message_obj, wrapper.connection)

            else:
                empty_message = True

        if empty_message and not wrapper.closed:

            message_send(CLOSE_MESSAGE, wrapper.connection)

            wrapper.close()

    def client_listener(self, wrapper: ClientConnectionWrapper,
                        tickrate: float = 0.5) -> None:
        """
        This function will listen and print in parallel with the main program.
        Use the wrapper variable to share state where needed.
        """

        while wrapper.states.listening:

            try:

                # While message_obj isn't None
                while ((message_obj := message_recv(wrapper.connection))
                       and wrapper.states.listening):

                    self.process_received_message(message_obj, wrapper)

            except socket.timeout:
                continue

            time.sleep(1/tickrate)

    def process_received_message(self, message: Message,
                                 wrapper: ClientConnectionWrapper,
                                 real_message: bool = True) -> None:
        """
        Prints received messages accordingly
        """

        store_message = real_message
        channel_join_successful = False

        msg = message.message

        if message.message_type == 0b11:
            print(message)

        match message.message_type:
            case 0b00:  # Channel posts

                # Client is in a channel
                if QUIT_STR not in msg:
                    wrapper.states.in_channel = True

                if wrapper.states.joining_channel and CHANNEL_JOIN_STR in msg:
                    channel_join_successful = True

                if WHISPER_SEP in message.nickname:  # Is a whisper
                    wrapper.states.last_whisperer = (
                        message.nickname.split(WHISPER_SEP)[0].strip()
                    )

                if wrapper.states.active:

                    if self.ui_enabled and real_message:
                        print("\r" + message.format(), end="")
                        sys.stdout.flush()
                        print(f"\n{INPUT_PROMPT}", end="")
                    else:
                        print(message.format())

            case 0b01:
                if msg != "":

                    print_message = True

                    if wrapper.states.pinging_for_info:
                        index = msg.find(SERVER_NAME_REF)
                        if index != -1:
                            print_message = False
                            store_message = False

                            raw = msg[index + len(SERVER_NAME_REF):]
                            name = raw.replace("\n", " ").split(" ", 1)[0]

                            wrapper.name = name
                            wrapper.states.pinging_for_info = False

                    if print_message and wrapper.states.active:
                        if self.ui_enabled and real_message:
                            print("\r" + message.format(), end="")
                            sys.stdout.flush()
                            print(f"\n{INPUT_PROMPT}", end="")
                        else:
                            print(message.format())

        if not channel_join_successful and wrapper.states.joining_channel:
            wrapper.channel_name = None

        wrapper.states.joining_channel = False

        if store_message:
            wrapper.store_message(message)


def main():
    """
    main
    Entrypoint for the client
    """

    ui_enabled = "--ui" in sys.argv

    client = Client(ui_enabled)
    client.start()


if __name__ == "__main__":
    main()
