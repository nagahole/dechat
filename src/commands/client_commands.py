"""
Implementation of all client commands and stores a map associating each
command to their functions. Has multiple maps for the multiple possible
different "stages" of client commands
"""

from src import ansi
from src import utilities
from src.commons import (
    ClientConnectionWrapper,
)
from src.protocol import conn_socket_setup
from src.constants import MAX_NICK_LENGTH

# Prefix meanings:

# - c: client
# - cs: client sender
# - m: mutual


def c_connect(user_input: str, client) -> None:
    """
    CLIENT COMMAND

    Attempts to connect to a hostname and port
    """
    splits = utilities.smart_split(user_input)

    if len(splits) < 2:
        return

    display_num = None

    if len(splits) >= 3 and client.ui_enabled:
        if utilities.is_integer(splits[2]):
            display_num = int(splits[2])
        else:
            client.log(f"{splits[2]} is an invalid display num")
            return

    if display_num in client.con_wrappers:
        client.log(f"{display_num} is already a display number!")
        return

    hostname, port = utilities.split_hostname_port(splits[1])

    if None in (hostname, port):
        return

    client.log("Connecting to server...")

    successful, connection = conn_socket_setup(hostname, port)

    if successful:
        wrapper = ClientConnectionWrapper(connection)
        client.add_wrapper(wrapper, display_num)
        client.activate_wrapper(
            wrapper, clear_terminal=False, ping_for_info=True
        )
    else:
        client.log(f"Failed to connect to server {hostname}:{port}")


def c_quit(_user_input: str, client) -> None:
    """
    CLIENT COMMAND

    Quits the client
    """
    client.stop()


def c_nick(user_input: str, client) -> None:
    """
    Sets a new default nickname. In abeyance when in a server
    """
    splits = utilities.smart_split(user_input)

    if len(splits) < 2:
        return

    new_nick = splits[1]

    if len(new_nick) > MAX_NICK_LENGTH:
        client.log(f"Maximum nickname length is {MAX_NICK_LENGTH}")
    else:
        client.default_nickname = new_nick
        client.log(f"Default nickname set to {new_nick}")


def cs_reply(user_input: str, client) -> None:
    """
    CLIENT SENDER COMMAND

    Implicitly calls /msg to the last whisperer to this client
    """

    wrapper = client.current_wrapper

    splits = utilities.smart_split(user_input)

    if len(splits) < 2:
        client.log("Usage: /reply <message>")
        return

    if not wrapper.states.last_whisperer:
        client.log("No one messaged you recently!")
        return

    msg = user_input.split(' ', 1)[1].strip()
    echo = f"/msg {wrapper.states.last_whisperer} {msg}"

    wrapper.input_queue.append(echo)


def cs_quit(user_input: str, client) -> None:
    """
    CLIENT SENDER COMMAND

    Quits channel if in a channel
    Quits server if not in a channel
    """

    wrapper = client.current_wrapper

    if not wrapper.states.in_channel:
        client.log("Disconnecting from server...")

    # Not gonna send close message here as to not block
    wrapper.input_queue.insert(0, user_input)


def cs_connect(user_input: str, client) -> None:

    """
    CLIENT SENDER COMMAND

    Connects to a new server. If multi-con not enabled leaves the previous
    one, else appends to the connection dictionary
    """

    splits = utilities.smart_split(user_input)

    if len(splits) < 2:
        return

    hostname, port = utilities.split_hostname_port(splits[1])

    if hostname is None or port is None:
        return

    for i_wrapper in client.con_wrappers.values():
        if f"{hostname}:{port}" == i_wrapper.name:
            client.log(f"Already in {hostname}:{port}")
            return

    display_num = None

    if len(splits) >= 3 and client.ui_enabled:
        if utilities.is_integer(splits[2]):
            display_num = int(splits[2])
        else:
            client.log(f"{splits[2]} is an invalid display number")
            return

    if display_num in client.con_wrappers:
        client.log(f"{display_num} is already a display number!")
        return

    successful, connection = conn_socket_setup(hostname, port)

    if successful and client.ui_enabled:
        ansi.clear_terminal()

    client.log("Connecting to server...")

    if not successful:
        client.log(f"Failed to connect to server {hostname}:{port}")
    else:
        new_wrapper = ClientConnectionWrapper(connection)

        # Close every other connection to servers if multi-con not enabled
        if not client.ui_enabled:
            for i_wrapper in client.con_wrappers.values():
                client.wrappers_to_close.append(i_wrapper)
            client.con_wrappers.clear()

        client.add_wrapper(new_wrapper, display_num)
        client.activate_wrapper(
            new_wrapper, clear_terminal=False, ping_for_info=True
        )


# The _ parameter is there just to make the function signature work with both
# client commands and client sender commands
def m_list_displays(_user_input: str, client) -> None:
    """
    MUTUAL COMMAND

    Lists all connections to servers and their associated name (hostname:port)
    and joined channel (if it exists)
    """

    client.clear_closed_wrappers()

    wrapper = client.current_wrapper

    if len(client.con_wrappers) == 0:
        client.log("Not connected to any server")
        return

    # Sorts by id in increasing order
    sorted_items = sorted(client.con_wrappers.items(), key=lambda kv: kv[0])

    for key, i_wrapper in sorted_items:
        postfix = ""
        if wrapper == i_wrapper:
            postfix = " <- current"  # To indicate current server

        name = i_wrapper.name
        if name is None:
            name = "Unknown name"

        echo = f"{key} : {name}"

        if i_wrapper.confirmed_channel_name is not None:

            echo += f" | {i_wrapper.confirmed_channel_name}"

        echo += postfix

        client.log(echo)


def m_display(user_input: str, client) -> None:
    """
    MUTUAL COMMAND

    Displays the specified numbered connection
    """

    splits = utilities.smart_split(user_input)

    if len(splits) < 2:
        return

    display_num = splits[1]

    if utilities.is_integer(display_num):
        display_num = int(display_num)
        if display_num in client.con_wrappers:
            client.change_display(display_num, ping_for_info=False)
        else:
            client.log(f"No display on {display_num}")
    else:
        client.log("Please enter a number for display [#]")


client_command_map = {
    "connect": c_connect,
    "quit": c_quit,
    "nick": c_nick,
}


multicon_client_command_map = {
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
    "quit": lambda _, client: client.log("Display a server to quit"),
    "list_displays": m_list_displays,
    "display": m_display
}


client_sender_command_map = {
    "reply": cs_reply,
    "quit": cs_quit,
    "connect": cs_connect
}


multicon_client_sender_command_map = {
    "reply": cs_reply,
    "quit": cs_quit,
    "connect": cs_connect,
    "list_displays": m_list_displays,
    "display": m_display
}
