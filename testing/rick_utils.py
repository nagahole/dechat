"""
Event system for tests
"""

# pylint: disable=wrong-import-position, protected-access, import-error,
# pylint: disable=wrong-import-order

import time
import threading
import sys
import unittest
from test_utils import start_server

from os import path
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
from client import Client

DEFAULT_PERIOD = 0.5
DEFAULT_TIMEOUT = 1
OUTPUT_FILE = "testing/test_logs.txt"
SERVERS: list[tuple[str, int]] = [
    ("localhost", 9996),
    ("localhost", 9997),
    ("localhost", 9998),
    ("localhost", 9999)
]

server_instances = []


class ClientWrapper:
    """
    Wrapper class for a client object to store output of client
    """
    def __init__(self, client: Client) -> None:
        self.client = client
        self._all_lines: list[str] = []
        self._buffer_lines: list[str] = []
        client.log = self.on_log

        self.client.start()

    def get_all_lines(self) -> list[str]:
        """
        Getter for _all_lines
        """
        return self._all_lines

    def get_buffer(self) -> list[str]:
        """
        Getter for _buffer_lines
        """

        # Returns a copy as to not have references of _buffer_lines be empty
        # when it is cleared
        return self._buffer_lines.copy()

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

    def stop(self) -> None:
        """
        Stops the client
        """
        while not self.client._quitted:
            self.feed_input("/quit")
            time.sleep(0.05)


class DechatTestcase(unittest.TestCase):
    """
    Base dechat TestCase class that automatically handles setups, teardowns,
    and setupclass
    """

    @staticmethod
    def setUpClass() -> None:
        # Clears log file
        open(OUTPUT_FILE, "w", encoding="ascii").close()
        print("Starting servers")
        for hostname, port in SERVERS:
            server_instances.append(start_server(hostname, port))

    @staticmethod
    def tearDownClass() -> None:
        # Stops all servers
        print("Killing servers")
        for subprocess in server_instances:
            subprocess.kill()

    @staticmethod
    def create_client(ui_enabled: bool = False) -> ClientWrapper:
        """
        Helper method to create client wrappers in-case a test case requires
        multiple clients
        """
        return ClientWrapper(
            Client(ui_enabled=ui_enabled, testing_mode=True)
        )

    @staticmethod
    def write_client_lines(client: ClientWrapper) -> None:
        """
        Writes client wrapper logs
        """
        with open(OUTPUT_FILE, "a", encoding="ascii") as file:
            nick = client.client.default_nickname
            file.write(f"Client {nick} contents")
            file.write("\n".join(client.get_all_lines()))
            file.write("\n")
            file.write(f"End of {nick} contents")

    def setUp(self):
        """
        Setup
        """
        testcase_str = f"TESTCASE [{self._testMethodName}]"

        with open(OUTPUT_FILE, "a", encoding="ascii") as file:
            file.write(testcase_str + "\n")

        self.client = ClientWrapper(
            Client(ui_enabled=False, testing_mode=True)
        )

        print(testcase_str)

    def tearDown(self):
        """
        Destructor
        """
        DechatTestcase.write_client_lines(self.client)
        with open(OUTPUT_FILE, "a", encoding="ascii") as file:
            file.write("END OF TESTCASE\n")
        self.client.stop()
        print("END OF TESTCASE")


def execute_await(inpt: str, client_wrapper: ClientWrapper,
                  period: float = DEFAULT_PERIOD,
                  timeout: float = DEFAULT_TIMEOUT,
                  throw_error: bool = True) -> str:
    """
    Automatically handles storing initial lines

    Period is the time to wait between consecutive messages

    Returns response
    """

    client_wrapper.clear_buffer()
    client_wrapper.feed_input(inpt)

    response = await_response(
        client_wrapper, period, timeout, buffer_cleared=True
    )

    if response is None and throw_error:
        raise RuntimeError(
            f"No response received from \"{inpt}\"(timeout {timeout})"
        )

    return response


def await_response(client_wrapper: ClientWrapper,
                   period: float = DEFAULT_PERIOD,
                   timeout: float = DEFAULT_TIMEOUT,
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

        if len(buffer) > 0:  # First contact
            state[0][0] = True
            logs = buffer

            # Now we need a state for receiving consecutive messages
            # First is timed out or not, and second is time that last message
            # was removed
            n_state = [[False], [time.time()]]

            def n_timeout_timer() -> None:
                while time.time() - n_state[1][0] <= period:
                    pass
                n_state[0][0] = True

            n_thread = threading.Thread(target=n_timeout_timer)
            n_thread.start()

            client_wrapper.clear_buffer()

            while not n_state[0][0]:

                buffer = client_wrapper.get_buffer()

                if len(buffer) > 0:
                    logs += buffer
                    client_wrapper.clear_buffer()
                    n_state[1][0] = time.time()

            n_thread.join()

    thread.join()

    return logs
