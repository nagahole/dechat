"""
Testcases for dechat
"""

import unittest
import sys
sys.path.append("..")
from .. import client
from testing.rick_utils import execute_await, ClientWrapper
from testing.test_utils import start_server

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
        self.client = ClientWrapper(client.Client(ui_enabled=False))

    def tearDown(self):
        """
        Destructor
        """
        print("Closing client")
        # Just to make sure absolutely has quit from channel to server to
        # bare client to exit
        for _ in range(3):
            self.client.feed_input("/quit")

    def test_hello_world(self):
        """
        Simple hello world test
        """
        print("Test hello world")

        execute_await(
            f"/connect {servers[0][0]}:{servers[0][1]}",
            self.client,
            throw_error=False
        )

        execute_await(
            "/create hello_world", self.client, throw_error=False
        )

        response = execute_await(
            "Hello world!", self.client, throw_error=False
        )

        print(response)


if __name__ == "__main__":
    for server in servers:
        start_server(server[0], server[1])
    unittest.main() # run all tests
