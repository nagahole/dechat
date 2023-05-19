import src.utilities as utilities
from src.commons import ClientVariables, ClientStates, ClientSenderVariables
from src.protocol import conn_socket_setup
from src.constants import MAX_PORT_VALUE, MAX_NICK_LENGTH

def c_c(user_input: str, c_vars: ClientVariables) -> None:
    _, c_vars.connection = conn_socket_setup("localhost", 9996)


def c_connect(user_input: str, c_vars: ClientVariables) -> None:
    splits = utilities.smart_split(user_input)

    if len(splits) < 2:
        return

    host_port = splits[1].split(":")

    hostname = ":".join(host_port[0:-1])

    if not utilities.is_integer(host_port[-1]):
        return

    port = int(host_port[-1])

    if not 0 <= port <= MAX_PORT_VALUE:
        return

    print("Connecting to server...")

    successful, c_vars.connection = conn_socket_setup(hostname, port)

    if not successful:
        print(f"Failed to connect to server {hostname}:{port}")


def c_quit(user_input: str, c_vars: ClientVariables) -> None:
    c_vars.quitted = True


def c_nick(user_input: str, c_vars: ClientVariables) -> None:
    splits = utilities.smart_split(user_input)

    if len(splits) < 2:
        return

    new_nick = splits[1]

    if len(new_nick) > MAX_NICK_LENGTH:
        print(f"Maximum nickname length is {MAX_NICK_LENGTH}")
    else:
        c_vars.default_nickname = new_nick
        print(f"Default nickname set to {new_nick}")


client_command_map = {
    "c": c_c,
    "connect": c_connect,
    "quit": c_quit,
    "nick": c_nick
}


def cs_reply(user_input: str, states: ClientStates, 
             cs_vars: ClientSenderVariables) -> None:

    splits = utilities.smart_split(user_input)

    if len(splits) < 2:
        print("Usage: /reply <message>")
        cs_vars.message_obj = None
        return

    if not states.last_whisperer:
        print("No one messaged you recently!")
        cs_vars.message_obj = None
        return

    msg = user_input.split(' ', 1)[1].strip()
    echo = f"/msg {states.last_whisperer} {msg}"

    cs_vars.message_obj.set_message(echo)


def cs_quit(user_input: str, states: ClientStates, 
            cs_vars: ClientSenderVariables) -> str:

    if not states.in_channel:
        print("Disconnecting from server...")
        cs_vars.quitted = True
        cs_vars.message_obj = None
    else:  # Is in channel and quitting the channel
        states.in_channel = False


client_sender_command_map = {
    "reply": cs_reply,
    "quit": cs_quit
}