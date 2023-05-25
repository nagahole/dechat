"""
Testcases for dechat
"""

# pylint: disable=import-error, wrong-import-order, wrong-import-position

import unittest
from rick_utils import execute_await, DechatTestcase, SERVERS

import sys
from os import path
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))


class BaseDechatTest(DechatTestcase):
    """
    Base dechat test cases - no optional components
    """

    def test_hello_world(self):
        """
        Simple hello world test
        """

        execute_await(
            f"/connect {SERVERS[0][0]}:{SERVERS[0][1]}",
            self.client,
        )

        response = execute_await("/create hello_world", self.client)

        if "already exists" in "".join(response):
            execute_await("/join hello_world", self.client)

        execute_await("Hello world!", self.client)

    def test_msg(self):
        """
        Messaging between two clients
        """
        client = DechatTestcase.create_client()

        execute_await("/nick client_1", self.client)
        execute_await("/nick client_2", client)


if __name__ == "__main__":
    unittest.main() # run all tests
