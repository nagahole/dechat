"""
Testcases for dechat
"""

# pylint: disable=import-error, wrong-import-order, wrong-import-position

import unittest
from rick_utils import (
    execute_await,
    set_output_file,
    DechatTestcase,
    SERVERS
)

import sys
from os import path
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))


class MulticonTest(DechatTestcase):
    """
    Multicon test cases
    """

    def test_hello_world(self) -> None:
        """
        Prints hello world on each server
        """
        client = DechatTestcase.create_client(ui_enabled=True)

        self.clients = [client]

        for server in SERVERS:
            DechatTestcase.connect(client, server)

        for i in range(len(SERVERS)):
            execute_await(f"/display {i}", client)
            execute_await("/create hello_world", client)
            response = execute_await("Hello world!", client)
            assert "Hello world!" in response[-1]

        response = execute_await("/list_displays", client)
        assert len(response) == len(SERVERS)

    def test_big_display_numbers(self) -> None:
        """
        /connect <ex> [BIG NUMBER#]
        """

        big_num = 999999999

        client = DechatTestcase.create_client(ui_enabled=True)

        self.clients = [client]

        for i, server in enumerate(SERVERS):
            execute_await(
                f"/connect {server[0]}:{server[1]} {big_num + i}", client
            )

        for i in range(len(SERVERS)):
            response = execute_await(f"/display {big_num + i}", client)
            assert "*" in response[-1]

        response = execute_await("/list_displays", client)
        assert len(response) == len(SERVERS)

    def test_invalid_display_number(self) -> None:
        """
        Invalid display number for /connect <ex> [#]
        """
        client = DechatTestcase.create_client(ui_enabled=True)

        self.clients = [client]

        execute_await(f"/connect {SERVERS[0][0]}:{SERVERS[0][1]} abc", client)
        response = execute_await("/list_displays", client)

        assert "Not connected to any server" in response[-1]

    def test_negative_display_number(self) -> None:
        """
        Shouldn't crash the client (hopefully)
        """
        client = DechatTestcase.create_client(ui_enabled=True)

        self.clients = [client]

        execute_await(f"/connect {SERVERS[0][0]}:{SERVERS[0][1]} -1", client)
        response = execute_await("/list_displays", client)

        assert "-1:" in response[-1]

    def test_list_display_channels(self) -> None:
        """
        See if list_displays displays the right channels a user is connected
        to
        """
        client = DechatTestcase.create_client(ui_enabled=True)

        self.clients = [client]

        for server in SERVERS:
            DechatTestcase.connect(client, server)

        for i in range(len(SERVERS)):
            execute_await(f"/display {i}", client)
            if i % 3 == 0:
                # Should fail on purpose
                execute_await(f"/join channel_{i}", client)
            else:
                execute_await(f"/create channel_{i}", client)

        response = "".join(execute_await("/list_displays", client))

        for i in range(len(SERVERS)):
            assert f"channel_{i}" in response

    def test_decimal_display_num(self) -> None:
        """
        See how the client parses decimal place display numbers
        """
        client = DechatTestcase.create_client(ui_enabled=True)

        self.clients = [client]

        execute_await(f"/connect {SERVERS[0][0]}:{SERVERS[0][1]} 0.5", client)
        response = execute_await("/list_displays", client)

        assert "Not connected to any server" in response[-1]


if __name__ == "__main__":
    set_output_file("test/logs/multicon_logs.txt")
    unittest.main() # run all tests
