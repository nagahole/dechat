"""
Event system for tests
"""

import time
import threading
import sys
sys.path.append("..")
from client import Client


class ClientWrapper:
    """
    Wrapper class for a client object to store output of client
    """
    def __init__(self, client: Client) -> None:
        self.client = client
        self._all_lines = []
        self._buffer_lines = []
        client.log = self.on_log

    def get_all_lines(self) -> list[str]:
        """
        Getter for _all_lines
        """
        return self._all_lines

    def get_buffer(self) -> list[str]:
        """
        Getter for _buffer_lines
        """
        return self._buffer_lines

    def clear_buffer(self) -> list[str]:
        """
        Clears buffer
        """
        self._buffer_lines.clear()

    def on_log(self, *args, **kwargs) -> None:
        """
        Hook function to redirect client logs into this wrapper
        """
        evaluated_string = " ".join(map(str, args))

        if "end" in kwargs:
            evaluated_string += kwargs["end"].replace("\n", "")

        self._all_lines.append(evaluated_string)
        self._buffer_lines.append(evaluated_string)

    def feed_input(self, inpt: str) -> None:
        """
        Middleman for making the client handle an input
        """
        self.client.handle_input(inpt)


def execute_await(inpt: str, client_wrapper: ClientWrapper,
                  timeout: float = 1, throw_error: bool = False) -> str:
    """
    Automatically handles storing initial lines

    Returns response
    """

    client_wrapper.clear_buffer()
    client_wrapper.feed_input(inpt)

    response = await_response(client_wrapper, timeout)

    if response is None and throw_error:
        raise RuntimeError(f"No response received (timeout {timeout})")

    return response


def await_response(client_wrapper: ClientWrapper, timeout: float = 1,
                   buffer_cleared: bool = True) -> list[str]:
    """
    Blocking function that waits for a response

    Returns response if received else None
    """

    if not buffer_cleared:
        client_wrapper.clear_buffer()

    # Whether timed out or response received
    state = [[False]]

    def timeout_timer() -> None:
        start_time = time.time()

        while time.time() - start_time <= timeout and not state[0][0]:
            pass

        state[0][0] = True  # Timed out

    thread = threading.Thread(target=timeout_timer)
    thread.start()

    logs = None

    while not state[0][0]:
        buffer = client_wrapper.get_buffer()
        if len(buffer) > 0:
            state[0][0] = True
            logs = buffer

    thread.join()

    return logs
