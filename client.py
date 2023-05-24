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
from src.protocol import message_send, message_recv, conn_socket_setup
from src.constants import MIGRATE_FLAG, SEP

INPUT_PROMPT = "> "
SERVER_NAME_REF = "Server: "
CHANNEL_JOIN_STR = " joined the channel!"
QUIT_STR = "has quit"
WHISPER_SEP = "->"


def main():
    """
    main
    Entrypoint for the client
    """

    ui_enabled = "--ui" in sys.argv

    client = Client(ui_enabled)
    client.start()


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

        self.wrappers_to_close = []
        self.migration_threads = []

        self.printed_prompt = False

    def clear_closed_wrappers(self) -> None:
        """
        Removes closed wrappers from self.con_wrappers
        """

        actives = filter(
            lambda tup: not tup[1].is_closed(), self.con_wrappers.items()
        )

        self.con_wrappers = { tup[0]: tup[1] for tup in actives }

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

        if wrapper.is_closed():
            raise RuntimeError(
                "Attempting to activate a closed connection wrapper"
            )

        if self.current_wrapper == wrapper:
            print("Already on that server!")
            return

        if clear_terminal and self.ui_enabled:
            ansi.clear_terminal()

        self.current_wrapper = wrapper
        wrapper.states.active = True

        self.print_wrapper_history(wrapper)

        if wrapper.listener is None:
            self.start_listening(wrapper)

        if wrapper.sender is None:
            self.start_sending(wrapper)

        for i_wrapper in self.con_wrappers.values():
            if i_wrapper != wrapper:
                i_wrapper.states.active = False

        if self.ui_enabled and ping_for_info:
            self.ping_for_info(wrapper)

    def print_wrapper_history(self, wrapper: ClientConnectionWrapper) -> None:
        """
        Extracts all the messages stored in a wrapper and prints them out
        """

        # Don't want handle_message_received to
        # change states in actual wrapper
        dummy = ClientConnectionWrapper(None)

        # To get printing processed messages working correctly
        dummy.states.active = True

        for message in reversed(wrapper.messages):
            self.process_received_message(message, dummy, real_message=False)

    def start_listening(self, wrapper: ClientConnectionWrapper) -> None:
        """
        Starts listening to a wrapper
        """
        wrapper.listener = threading.Thread(
            target=self.listener,
            args=(wrapper,),
            kwargs={"tickrate": 32}
        )

        wrapper.listener.start()

    def start_sending(self, wrapper: ClientConnectionWrapper) -> None:
        """
        Starts a client sender
        """
        wrapper.sender = threading.Thread(
            target=self.client_sender,
            args=(wrapper,)
        )

        wrapper.sender.start()

    def ping_for_info(self, wrapper: ClientConnectionWrapper) -> None:
        """
        Implicitly calls /info and extracts hostname and port quietly
        """
        wrapper.states.pinging_for_info = True
        wrapper.input_queue.insert(0, "/info")

    def start(self) -> None:
        """
        Starts running the client
        """
        threading.Thread(target=self.input_loop).start()

        # Purpose of this is to join all sender and listener threads from the
        # main thread. All wrappers should be closed from here to avoid
        # threads trying to join with themselves
        while not self.quitted:

            for wrapper in self.wrappers_to_close:
                if wrapper == self.current_wrapper:
                    self.current_wrapper = None
                wrapper.close()

            self.wrappers_to_close.clear()

        for thread in self.migration_threads:
            thread.join()

    def stop(self) -> None:
        """
        Stops the client. Will take one final input if quit runs while
        sender is taking input
        """
        self.quitted = True

    def input_loop(self) -> None:
        """
        Continuously takes user input while client has not quit
        """
        while not self.quitted:
            self.printed_prompt = True
            user_input = input(INPUT_PROMPT)
            self.printed_prompt = False

            # Just in case the client closes while waiting for input
            # not likely but just in case
            if self.quitted:
                return

            if self.ui_enabled:
                ansi.clear_line()

            self.handle_input(user_input)

    def match_input_to_map(self, user_input: str,
                           command_map: dict[str, callable],
                           print_unrecognized_commands: bool = True) -> bool:
        """
        Matches user input to a command map

        Returns whether user input was a command or not
        """

        if user_input != "" and user_input[0] == "/":

            splits = utilities.smart_split(user_input)

            command = splits[0][1:].lower()

            if command in command_map:
                func = command_map[command]
                func(user_input, self)
                return True

            if print_unrecognized_commands:
                print(f"Command /{command} not recognized")

        return False

    def handle_input(self, user_input: str) -> None:
        """
        Handles a user input intelligently based on whether he is displaying
        a server, in a server but not displaying any, or not in any server
        """

        if self.current_wrapper is None:  # Not displaying a server

            command_map = None

            if not self.exists_cons():  # Not connected to a server
                if self.ui_enabled:
                    command_map = multicon_client_command_map
                else:
                    command_map = client_command_map
            else:
                # Connected to a server but not displaying any
                if not self.ui_enabled:
                    # Should only be possible in multicon
                    raise RuntimeError(
                        "There exists connections the client is not "
                        "connected to while multi-con is not enabled"
                    )

                command_map = limbo_command_map

            if command_map is not None:
                self.match_input_to_map(user_input, command_map)

        else:  # Currently displaying a server

            if self.ui_enabled:
                command_map = multicon_client_sender_command_map
            else:
                command_map = client_sender_command_map

            is_clientside_command = self.match_input_to_map(
                user_input, command_map, print_unrecognized_commands=False
            )

            if not is_clientside_command:
                self.current_wrapper.input_queue.append(user_input)

    def client_sender(self, wrapper: ClientConnectionWrapper) -> None:
        """
        Listens for a queue of messages to send
        """

        empty_message = False

        # Sender should keep running even when not active but not closed
        # either
        while not wrapper.is_closed() and not empty_message:

            # Should send even if not active for pinging for info in
            # /migration
            while not empty_message and len(wrapper.input_queue) > 0:

                user_input = wrapper.input_queue.pop(0)

                if len(user_input) > 0:
                    self.handle_input_to_server(user_input, wrapper)
                else:
                    empty_message = True

            if empty_message and not wrapper.states.is_closed():
                message_send(CLOSE_MESSAGE, wrapper.connection)

        # Should only come to this point when the connection to the server
        # has closed. Need to close wrapper from an outside thread so the
        # sender doesn't .join() itself
        self.wrappers_to_close.append(wrapper)

    def handle_input_to_server(self, user_input: str,
                               wrapper: ClientConnectionWrapper) -> None:
        """
        The handle_input equivelant but for user input intended for
        servers

        User input should be handled to be not empty prior to being passed
        in
        """

        # /quit should always be a relay from cs_quit. It should never
        # be from raw input since it maps to cs_quit and hence will not
        # be added to input queue
        if user_input.startswith("/quit") and not wrapper.is_closed():
            if wrapper.states.in_channel:
                wrapper.states.in_channel = False
                wrapper.confirmed_channel_name = None
                wrapper.pending_channel_name = None
            else:
                message_send(CLOSE_MESSAGE, wrapper.connection)
                self.wrappers_to_close.append(wrapper)
                return

        # Defaults to server type messages
        message_type = 0b01

        if wrapper.states.in_channel:
            message_type = 0b00

        message = Message(
            0,
            self.default_nickname,
            time.time(),
            message_type,
            user_input
        )

        if user_input[0] == "/":
            # Is a command. NOT A CLIENTSIDE COMMAND, SERVER COMMANDS ONLY
            # FROM NOW ON

            splits = utilities.smart_split(user_input)
            command = splits[0][1:].lower()

            # Required for scraping channel name
            if command in ("join", "create") and len(splits) >= 2:
                wrapper.pending_channel_name = splits[1]

        if not wrapper.is_closed():
            message_send(message, wrapper.connection)

    def listener(self, wrapper: ClientConnectionWrapper,
                 tickrate: float = 0.5) -> None:
        """
        This function will listen and print in parallel with the main program.
        Use the wrapper variable to share state where needed.
        """

        while wrapper.states.listening and not wrapper.is_closed():
            try:
                # While message_obj isn't None

                while ((message_obj := message_recv(wrapper.connection)) and
                       wrapper.states.listening and not wrapper.is_closed()):

                    self.process_received_message(message_obj, wrapper)

            except socket.timeout:
                continue
            except ConnectionResetError:
                if not wrapper.is_closed():
                    self.wrappers_to_close.append(wrapper)
                return

            time.sleep(1/tickrate)

    def smart_print_response(self, string: str,
                             print_prompt: bool = True) -> None:
        """
        Intelligently prints responses to received messages with or without
        special / ansi escape characters depending on whether ui is enabled
        or not
        """

        if self.ui_enabled:
            print("\r" + string, end="")
            sys.stdout.flush()
            if print_prompt and self.printed_prompt:
                print(f"\n{INPUT_PROMPT}", end="")
            else:
                print()
        else:
            print(string)

    def process_received_message(self, message: Message,
                                 wrapper: ClientConnectionWrapper,
                                 real_message: bool = True) -> None:
        """
        Prints received messages accordingly
        """

        store_message = real_message

        msg = message.message

        if message.message_type == 0b00:  # Channel posts

            if (wrapper.pending_channel_name is not None and
                CHANNEL_JOIN_STR in msg):

                wrapper.confirmed_channel_name = wrapper.pending_channel_name
                wrapper.pending_channel_name = None
                wrapper.states.in_channel = True

            if WHISPER_SEP in message.nickname:  # Is a whisper
                wrapper.states.last_whisperer = (
                    message.nickname.split(WHISPER_SEP)[0].strip()
                )

            if wrapper.states.active:
                self.smart_print_response(
                    message.format(), print_prompt=real_message
                )

        elif message.message_type == 0b01:  # Server messages
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

                    self.smart_print_response(
                        message.format(), print_prompt=real_message
                    )

        elif message.message_type == 0b10:  # Migration broadcasts

            # Don't want to store instructions to migrate
            store_message = False

            # Probably don't need to check for migrate flag as well but
            # just to be safe
            if msg.startswith(MIGRATE_FLAG) and real_message:
                # Format is like:
                # "--migrate|<channel_name>|<hostname>|<port>"
                # Where | is the special separator character

                splits = msg.split(SEP)

                channel_name = splits[1]
                hostname = splits[2]
                port = int(splits[3])

                thread = threading.Thread(
                    target=self.migrate,
                    args=(wrapper, channel_name, hostname, port)
                )

                self.migration_threads.append(thread)
                thread.start()

        if store_message:
            wrapper.store_message(message)

    def migrate(self, old_wrapper: ClientConnectionWrapper,
                channel_name: str, hostname: str, port: int) -> None:
        """
        Migrates to a channel on a linked server
        """

        was_active = old_wrapper.states.active

        self.smart_print_response(
            f"Migrating from {channel_name} on {old_wrapper.name} to"
            f" {channel_name} on {hostname}:{port}"
        )

        wrapper = None

        self.clear_closed_wrappers()

        for i_wrapper in self.con_wrappers.values():
            if f"{hostname}:{port}" == i_wrapper.name:
                wrapper = i_wrapper
                break

        if wrapper is not None:  # Already in server

            if wrapper.confirmed_channel_name == channel_name:
                # Already in target channel
                self.smart_print_response(
                    f"Already in target server {hostname}:{port} and "
                    f" target channel {channel_name}"
                )

                return

            if wrapper.confirmed_channel_name is not None:
                # Already in other channel
                self.smart_print_response(
                    f"Already in target server {hostname}:{port} and "
                    "different channel. Will not force join "
                    f"{channel_name}"
                )

                return

            else:
                # In target server but not in any channel
                self.smart_print_response(
                    f"Already in target server {hostname}:{port}"
                )

        else:  # Not in server

            successful, connection = conn_socket_setup(hostname, port)

            if not successful:
                self.smart_print_response(
                    "Connection unsuccessful. Staying in migrating server"
                )
                return

            # Connection successful
            self.smart_print_response(
                "Connection successful. Disconnecting from migrating server"
            )

            self.wrappers_to_close.append(old_wrapper)

            wrapper = ClientConnectionWrapper(connection)
            self.add_wrapper(wrapper)

            self.start_listening(wrapper)
            self.start_sending(wrapper)
            self.ping_for_info(wrapper)

        self.smart_print_response(
            f"Attempting to join linked channel {channel_name}"
        )

        if was_active:
            self.activate_wrapper(
                wrapper, clear_terminal=False, ping_for_info=False
            )

        wrapper.input_queue.append(f"/join {channel_name}")


if __name__ == "__main__":
    main()
