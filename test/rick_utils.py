"""
Event system for tests
"""

import time
import threading
from test_utils import client_read, client_write


def execute_await_raw(inpt: str, client, timeout: float = 1,
                      throw_error: bool = False) -> str:
    """
    Like execute_await but takes in an input instead of a function
    """
    return execute_await(
        lambda: client_write(client, inpt), client, timeout, throw_error
    )


def execute_await(func: callable, client, timeout: float = 1,
                  throw_error: bool = False) -> str:
    """
    Automatically handles storing initial lines

    Returns response
    """
    func()
    initial_lines = client_read(client)

    response = await_response(initial_lines, client, timeout)
    if response is None and throw_error:
        raise RuntimeError(f"No response received (timeout {timeout})")

    return response


def await_response(initial_lines: list[str], client,
                   timeout: float = 1) -> str:
    """
    Blocking function that waits for a response

    Returns response if received else None
    """
    initial_str = "\n".join(initial_lines)

    # Whether timed out or response received
    state = [[False]]

    def timeout_timer() -> None:
        start_time = time.time()

        while time.time() - start_time <= timeout and not state[0][0]:
            pass

        state[0][0] = True  # Timed out

    thread = threading.Thread(target=timeout_timer)
    thread.start()

    response_received = False

    while not state[0][0]:
        new_lines = client_read(client)
        new_str = "\n".join(new_lines)

        if len(new_str) > len(initial_str):
            state[0][0] = True
            response_received = True

    thread.join()

    if response_received:
        return new_str.replace(initial_str, "")

    return None


def connect(client, server_info: tuple[str, int]) -> None:
    """
    Helper function to quickly connect clients to a server
    """
    client_write(client, f"/connect {server_info[0]}:{server_info[1]}")
