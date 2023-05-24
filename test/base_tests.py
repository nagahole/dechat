"""
Testcases for dechat
"""

import time
import unittest
from rick_utils import execute_await, execute_await_raw, connect
from test_utils import start_server, start_client, client_write

servers = [
    ("localhost", 9996),
    ("localhost", 9997),
    ("localhost", 9998),
    ("localhost", 9999)
]

class BaseDechatTest(unittest.TestCase):
    """
    Base dechat test cases - no optional components
    """
    def setUp(self):
        """
        Setup
        """
        print("Starting up client")
        self.client = start_client()

    def tearDown(self):
        """
        Destructor
        """
        print("Closing client")
        # Just to make sure absolutely has quit from channel to server to
        # bare client to exit
        for _ in range(3):
            client_write(self.client, "/quit")

    def test_hello_world(self):
        """
        Simple hello world test
        """
        print("Test hello world")

        execute_await(
            lambda: connect(self.client, servers[0]),
            self.client,
            throw_error=False
        )

        execute_await_raw(
            "/create hello_world", self.client, throw_error=False
        )

        response = execute_await_raw(
            "Hello world!", self.client, throw_error=False
        )

        print(response)


if __name__ == "__main__":
    for server in servers:
        start_server(server[0], server[1])
    unittest.main() # run all tests
