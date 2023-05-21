import time
import threading
import src.utilities as utilities
from src.message import Message, CLOSE_MESSAGE
from src.commons import (
    ClientConnectionWrapper,
    ClientStates
)
from src.protocol import conn_socket_setup, message_send
from src.constants import MAX_NICK_LENGTH


"""
Prefix meanings:

- c: client
- cs: client sender
- m: mutual

"""

def c_c(user_input: str, client) -> None:
    c_connect("/connect localhost:9996", client)


def c_connect(user_input: str, client) -> None:
    splits = utilities.smart_split(user_input)

    if len(splits) < 2:
        return

    display_num = None

    if len(splits) >= 3 and client.ui_enabled:
        if utilities.is_integer(splits[2]):
            display_num = int(splits[2])
        else:
            print(f"{splits[2]} is an invalid display num")
            return

    if display_num in client.con_wrappers:
        print(f"{display_num} is already a display number!")
        return

    hostname, port = utilities.split_hostname_port(splits[1])

    if hostname is None or port is None:
        return

    print("Connecting to server...")

    successful, connection = conn_socket_setup(hostname, port)

    if successful:
        wrapper = ClientConnectionWrapper(connection)
        client.add_wrapper(wrapper, display_num)
        client.activate_wrapper(
            wrapper, clear_terminal=False, ping_for_info=True
        )
    else:
        print(f"Failed to connect to server {hostname}:{port}")


def c_quit(user_input: str, client) -> None:
    client.quitted = True


def c_nick(user_input: str, client) -> None:
    splits = utilities.smart_split(user_input)

    if len(splits) < 2:
        return

    new_nick = splits[1]

    if len(new_nick) > MAX_NICK_LENGTH:
        print(f"Maximum nickname length is {MAX_NICK_LENGTH}")
    else:
        client.default_nickname = new_nick
        print(f"Default nickname set to {new_nick}")


def cs_reply(user_input: str, client,
             wrapper: ClientConnectionWrapper) -> None:

    splits = utilities.smart_split(user_input)

    if len(splits) < 2:
        print("Usage: /reply <message>")
        wrapper.message_obj = None
        return

    if not wrapper.states.last_whisperer:
        print("No one messaged you recently!")
        wrapper.message_obj = None
        return

    msg = user_input.split(' ', 1)[1].strip()
    echo = f"/msg {wrapper.states.last_whisperer} {msg}"

    wrapper.message_obj.set_message(echo)


def cs_quit(user_input: str, client,
            wrapper: ClientConnectionWrapper) -> str:

    if not wrapper.states.in_channel:
        print("Disconnecting from server...")
        message_send(CLOSE_MESSAGE, wrapper.connection)
        wrapper.close()
    else:  # Is in channel and quitting the channel
        wrapper.channel_name = None
        wrapper.states.in_channel = False


def cs_connect(user_input: str, client,
               wrapper: ClientConnectionWrapper) -> None:

    if wrapper is not None:
        wrapper.message_obj = None

    splits = utilities.smart_split(user_input)

    if len(splits) < 2:
        return

    hostname, port = utilities.split_hostname_port(splits[1])

    if hostname is None or port is None:
        return

    display_num = None

    if len(splits) >= 3 and client.ui_enabled:
        if utilities.is_integer(splits[2]):
            display_num = int(splits[2])
        else:
            print(f"{splits[2]} is an invalid display number")
            return

    if display_num in client.con_wrappers:
        print(f"{display_num} is already a display number!")
        return

    successful, connection = conn_socket_setup(hostname, port)

    if successful and client.ui_enabled:
        utilities.clear_terminal()

    print("Connecting to server...")

    if not successful:
        print(f"Failed to connect to server {hostname}:{port}")
    else:

        new_wrapper = ClientConnectionWrapper(connection)

        # Close every other connection to servers if multi-con not enabled
        if not client.ui_enabled:
            for i_wrapper in client.con_wrappers.values():
                i_wrapper.close()
            client.con_wrappers.clear()

        client.add_wrapper(new_wrapper, display_num)
        client.activate_wrapper(
            new_wrapper, clear_terminal=False, ping_for_info=True
        )


# The _ parameter is there just to make the function signature work with both
# client commands and client sender commands
def m_list_displays(user_input: str, client,
                    wrapper: ClientConnectionWrapper=None) -> None:
    if wrapper is not None:
        wrapper.message_obj = None

    if len(client.con_wrappers) == 0:
        print("Not connected to any server")
        return

    sorted_items = sorted(client.con_wrappers.items(), key=lambda kv: kv[0])

    for key, i_wrapper in sorted_items:
        postfix = ""
        if wrapper == i_wrapper:
            postfix = " <- current"  # To indicate current server

        name = i_wrapper.name
        if name is None:
            name = "Unknown name"

        echo = f"{key} : {name}"

        if (not i_wrapper.states.joining_channel and
            i_wrapper.channel_name is not None):

            echo += f" | {i_wrapper.channel_name}"

        echo += postfix

        print(echo)


def m_display(user_input: str, client,
              wrapper: ClientConnectionWrapper=None) -> None:
    if wrapper is not None:
        wrapper.message_obj = None

    splits = utilities.smart_split(user_input)

    display_num = splits[1]

    if utilities.is_integer(display_num):
        display_num = int(display_num)
        if display_num in client.con_wrappers:
            client.change_display(display_num, ping_for_info=False)
        else:
            print(f"No display on {display_num}")
    else:
        print("Please enter a number for display [#]")


client_command_map = {
    "c": c_c,
    "connect": c_connect,
    "quit": c_quit,
    "nick": c_nick,
}


multicon_client_command_map = {
    "c": c_c,
    "connect": c_connect,
    "quit": c_quit,
    "nick": c_nick,
    "list_displays": m_list_displays,
    "display": m_display
}


# For in multicon when client quits a server but is connected to other servers
# but haven't switched to display them yet
limbo_command_map = {
    "connect": c_connect,
    "quit": lambda *args, **kwargs: print("Display a server to quit"),
    "list_displays": m_list_displays,
    "display": m_display
}


client_sender_command_map = {
    "reply": cs_reply,
    "quit": cs_quit,
    "connect": cs_connect,
}


multicon_client_sender_command_map = {
    "reply": cs_reply,
    "quit": cs_quit,
    "connect": cs_connect,
    "list_displays": m_list_displays,
    "display": m_display
}