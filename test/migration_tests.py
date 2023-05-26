"""
Testcases for dechat
"""

# pylint: disable=import-error, wrong-import-order, wrong-import-position

import time
import unittest
from rick_utils import (
    execute_await,
    await_response,
    set_output_file,
    DechatTestcase,
    SERVERS
)

import sys
from os import path
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))


class MigrationTest(DechatTestcase):
    """
    Migration test cases
    """

    def test_hello_world(self) -> None:
        """
        Prints hello world on each server
        """
        client_1 = DechatTestcase.create_client()
        client_2 = DechatTestcase.create_client()

        self.clients = [client_1, client_2]

        execute_await(f"/nick client_{SERVERS[0][1]}", client_1)
        execute_await(f"/nick client_{SERVERS[1][1]}", client_2)

        DechatTestcase.connect(client_1, SERVERS[0])
        DechatTestcase.connect(client_2, SERVERS[1])

        execute_await("/create hello_world", client_1)
        execute_await("/create hello_world", client_2)

        execute_await("/quit", client_1)
        execute_await(
            f"/link hello_world {SERVERS[1][0]}:{SERVERS[1][1]}",
            client_1,
            period=1
        )

        execute_await("/join hello_world", client_1)
        client_2.clear_buffer()

        execute_await("Hello world!", client_1)

        response = await_response(client_2)

        assert "Hello world!" in response[-1]

        execute_await("/quit", client_2)
        execute_await(
            f"/unlink hello_world {SERVERS[0][0]}:{SERVERS[0][1]}",
            client_2,
            period=1
        )

    def test_threeway_link(self) -> None:
        """
        Prints hello world on each server
        """
        client_1 = DechatTestcase.create_client()
        client_2 = DechatTestcase.create_client()
        client_3 = DechatTestcase.create_client()

        self.clients = [client_1, client_2, client_3]

        execute_await(f"/nick client_{SERVERS[0][1]}", client_1)
        execute_await(f"/nick client_{SERVERS[1][1]}", client_2)
        execute_await(f"/nick client_{SERVERS[2][1]}", client_3)

        DechatTestcase.connect(client_1, SERVERS[0])
        DechatTestcase.connect(client_2, SERVERS[1])
        DechatTestcase.connect(client_3, SERVERS[2])

        execute_await("/create three_link", client_1)
        execute_await("/create three_link", client_2)
        execute_await("/create three_link", client_3)

        execute_await("/quit", client_1)
        execute_await(
            f"/link three_link {SERVERS[1][0]}:{SERVERS[1][1]}",
            client_1,
            period=1
        )

        execute_await(
            f"/link three_link {SERVERS[2][0]}:{SERVERS[2][1]}",
            client_1,
            period=1
        )

        execute_await("/join three_link", client_1)

        client_2.clear_buffer()
        client_3.clear_buffer()

        execute_await("Three way link!", client_1)

        response = await_response(client_2)
        assert "Three way link!" in response[-1]
        response = await_response(client_3)
        assert "Three way link!" in response[-1]

        execute_await("/quit bye client 2 and client 3", client_1)

        execute_await(
            f"/unlink three_link {SERVERS[1][0]}:{SERVERS[1][1]}",
            client_1,
            period=1
        )

        execute_await("/join three_link", client_1)

        client_2.clear_buffer()
        execute_await("Only client 3 should see this", client_1)

        response = await_response(client_2, timeout=1)

        assert response is None

        execute_await("/quit bye client 3 only", client_1)

        execute_await(
            f"/unlink three_link {SERVERS[2][0]}:{SERVERS[2][1]}",
            client_1,
            period=1
        )

        client_2.clear_buffer()
        client_3.clear_buffer()
        execute_await("/join three_link", client_1)
        execute_await("Only I should see this", client_1)

        response = await_response(client_2, timeout=1)
        assert response is None
        response = await_response(client_3, timeout=1)
        assert response is None

    def test_void_unlinks(self) -> None:
        """
        Attempts to unlink when it has already been unlinked
        """

        client_1 = DechatTestcase.create_client()
        client_2 = DechatTestcase.create_client()

        self.clients = [client_1, client_2]

        execute_await(f"/nick client_{SERVERS[0][1]}", client_1)
        execute_await(f"/nick client_{SERVERS[1][1]}", client_2)

        DechatTestcase.connect(client_1, SERVERS[0])
        DechatTestcase.connect(client_2, SERVERS[1])

        execute_await("/create void_unlink", client_1)
        execute_await("/create void_unlink", client_2)

        execute_await("/quit", client_1)
        execute_await(
            f"/link void_unlink {SERVERS[1][0]}:{SERVERS[1][1]}",
            client_1,
            period=1
        )

        execute_await("/join void_unlink", client_1)

        client_2.clear_buffer()

        execute_await("Linked for now >:)", client_1)

        await_response(client_2)

        execute_await("/quit", client_1)

        execute_await(
            f"/unlink void_unlink {SERVERS[1][0]}:{SERVERS[1][1]}",
            client_1,
            period=1
        )

        execute_await("/join void_unlink", client_1)

        execute_await("Only I should see this", client_1)
        execute_await("Only I should see this", client_2)

        execute_await("/quit", client_2)

        # Attempts to unlink an already unlinked channel
        execute_await(
            f"/unlink void_unlink {SERVERS[0][0]}:{SERVERS[0][1]}",
            client_2,
            period=1
        )

        execute_await("/quit", client_1)

        execute_await(
            f"/unlink void_unlink {SERVERS[1][0]}:{SERVERS[1][1]}",
            client_1,
            period=1
        )

        # Not crashing is a pass

    def test_migrate(self) -> None:
        """
        Tests /migrate
        """

        client_1 = DechatTestcase.create_client()
        observer = DechatTestcase.create_client()
        client_2 = DechatTestcase.create_client()

        self.clients = [client_1, observer, client_2]

        execute_await(f"/nick client_{SERVERS[0][1]}", client_1)
        execute_await("/nick observer", observer)
        execute_await(f"/nick client_{SERVERS[1][1]}", client_2)

        DechatTestcase.connect(client_1, SERVERS[0])
        DechatTestcase.connect(observer, SERVERS[0])
        DechatTestcase.connect(client_2, SERVERS[1])

        execute_await("/create migration", client_1)
        execute_await("/join migration", observer)
        execute_await("/create migration", client_2)

        execute_await("/quit", client_1)
        execute_await(
            f"/link migration {SERVERS[1][0]}:{SERVERS[1][1]}",
            client_1,
            period=1
        )

        execute_await("/join migration", client_1)
        client_2.clear_buffer()

        execute_await("Hello world!", client_1)

        response = await_response(client_2)

        assert "Hello world!" in response[-1]

        DechatTestcase.connect(client_1, SERVERS[1])

        observer.clear_buffer()
        execute_await(
            f"/migrate migration {SERVERS[0][0]}:{SERVERS[0][1]}", client_1
        )

        response = await_response(observer)

        assert (
            f"client_{SERVERS[1][1]} joined the channel!" in "".join(response)
        )

        response = execute_await("/join migration", client_1)

        assert "doesn't exist" in response[-1]

        DechatTestcase.connect(client_1, SERVERS[0])

        client_2.clear_buffer()
        execute_await("/join migration", client_1)
        execute_await("Hello world!", client_1)

        response = await_response(client_2)

        assert "Hello world!" in response[-1]


if __name__ == "__main__":
    set_output_file("test/logs/migration_logs.txt")
    unittest.main() # run all tests
