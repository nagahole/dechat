"""
Event system for tests
"""

# pylint: disable=wrong-import-position, protected-access, import-error,
# pylint: disable=wrong-import-order, global-statement

import time
import threading
import sys
import unittest
from test_utils import start_server
import os

from os import path
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
from client import Client

DEFAULT_PERIOD = 0.2
DEFAULT_TIMEOUT = 3
OUTPUT_FILE = "test/test_logs.txt"

SERVERS: list[tuple[str, int]] = [
    ("localhost", 9996),
    ("localhost", 9997),
    ("localhost", 9998),
    ("localhost", 9999)
]

server_instances = []

DO_LOG = False

def set_output_file(file_path: str) -> None:
    """
    Redirects output file path
    """
    global OUTPUT_FILE
    OUTPUT_FILE = file_path

def log(*args, **kwargs) -> None:
    """
    Log
    """
    if DO_LOG:
        print(*args, **kwargs)

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

    def feed_input(self, inpt: str, do_log: bool = True) -> None:
        """
        Middleman for making the client handle an input
        """
        if do_log:
            print(f"Executing '{inpt}'")
        self.client.handle_input(inpt)

    def stop(self) -> None:
        """
        Stops the client
        """
        for wrapper in self.client.con_wrappers.values():
            self.client.wrappers_to_close.append(wrapper)

        self.client.stop()


class DechatTestcase(unittest.TestCase):
    """
    Base dechat TestCase class that automatically handles setups, teardowns,
    and setupclass
    """

    @staticmethod
    def setUpClass() -> None:
        os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

        # Clears log file
        open(OUTPUT_FILE, "w", encoding="ascii").close()
        print("Starting servers")
        for hostname, port in SERVERS:
            server_instances.append(start_server(hostname, port))

        time.sleep(0.5)  # Gives time for servers to start

        for server in server_instances:
            poll = server.poll()
            if poll is not None:  # Finished running
                for server in server_instances:
                    server.kill()
                raise RuntimeError("Failure to start server")

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
    def create_clients(num: int,
                       ui_enabled: bool = False) -> list[ClientWrapper]:
        """
        Creates multiple client wrappers and returns them all
        """
        clients = []
        for _ in range(num):
            clients.append(DechatTestcase.create_client(ui_enabled))
        return clients

    @staticmethod
    def connect(client: ClientWrapper, server: tuple[str, int],
                throw_error: bool = True) -> None:
        """
        Helepr function to connect clients to a server
        """
        execute_await(
            f"/connect {server[0]}:{server[1]}",
            client,
            throw_error=throw_error
        )

    @staticmethod
    def write_client_lines(*clients: tuple[ClientWrapper],
                           auto_close: bool = True) -> None:
        """
        Writes client wrapper logs
        """
        with open(OUTPUT_FILE, "a", encoding="ascii") as file:
            for i, client in enumerate(clients):
                nick = client.client.default_nickname
                file.write(f"[Client {nick} contents]".center(80) + "\n")
                file.write("\n".join(client.get_all_lines()))
                file.write("\n")
                file.write(f"[End of {nick} contents]".center(80) + "\n")

                if i < len(clients) - 1:
                    file.write(("-" * 80) + "\n")

        if auto_close:
            for client in clients:
                client.stop()

    def setUp(self):
        """
        Setup
        """
        testcase_str = f"TESTCASE [{self._testMethodName}]"

        with open(OUTPUT_FILE, "a", encoding="ascii") as file:
            file.write(testcase_str.center(80, "=") + "\n")

        print(testcase_str)

    def tearDown(self):
        """
        Destructor
        """
        with open(OUTPUT_FILE, "a", encoding="ascii") as file:
            file.write("END OF TESTCASE".center(80, "=") + "\n")
        print("END OF TESTCASE")


def execute_await(inpt: str, client_wrapper: ClientWrapper,
                  period: float = DEFAULT_PERIOD,
                  timeout: float = DEFAULT_TIMEOUT,
                  throw_error: bool = True) -> list[str]:
    """
    Automatically handles storing initial lines

    Period is the time to wait between consecutive messages

    Returns response
    """

    return execute_sequence_await(
        [inpt], client_wrapper, period, timeout, throw_error
    )


def execute_sequence_await(inputs: list[str], client_wrapper: ClientWrapper,
                           period: float = DEFAULT_PERIOD,
                           timeout: float = DEFAULT_TIMEOUT,
                           throw_error: bool = True) -> list[str]:
    """
    Executes a sequence of commands then awaits response
    """
    client_wrapper.clear_buffer()

    for inpt in inputs:
        client_wrapper.feed_input(inpt)

    response = await_response(
        client_wrapper, period, timeout, buffer_cleared=True
    )

    if response is None and throw_error:
        raise RuntimeError(
            f"No response received from inputs (timeout {timeout})"
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

    log("Awaiting")

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

    start = time.time()

    while not state[0][0]:

        buffer = client_wrapper.get_buffer()

        if len(buffer) > 0:  # First contact

            log("First contact")
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

                    log("Additional contact")

                    logs += buffer
                    client_wrapper.clear_buffer()
                    n_state[1][0] = time.time()

    log(f"Total wait: {time.time() - start}")

    return logs
