# pylint: disable=wrong-import-order, missing-function-docstring,
# pylint: disable=no-method-argument, unused-variable, missing-class-docstring
# pylint: disable=missing-module-docstring, superfluous-parens

import unittest
from test_utils import start_server, start_client, client_write, client_read

import time

DO_LOG = True

def log(*args, **kwargs):
    if DO_LOG:
        print(*args, **kwargs)

class SimpleTestCases(unittest.TestCase):

    def setUp(self):
        self.processes = []

    def tearDown(self):
        for process in self.processes:
            process.kill()

    def test_client_send(self):
        log("TEST")
        port = 10001
        server = start_server(port=port)
        client = start_client()

        self.processes = [server, client]

        client_write(client, '/nick test_c_send\n')
        client_write(client, f"/connect localhost:{port}\n")

        time.sleep(1)
        response = client_read(client)
        log("".join(response))
        log()
        assert("Connecting to server..." in response[-2])

    def test_client_echo(self):
        port = 10002
        server = start_server(port=port)
        client = start_client()

        self.processes = [server, client]

        client_write(client, '/nick test_c_echo\n')
        client_write(client, f"/connect localhost:{port}\n")
        client_write(client, '/create info1910\n')
        time.sleep(0.5)
        client_write(client, "Hello World!\n")

        time.sleep(1)

        response = client_read(client)
        log("".join(response))
        log()
        assert("Hello World!" in response[-1])

        server.kill()
        client.kill()

    def test_two_client_comms(self):
        port = 10003
        server = start_server(port=port)
        client_a = start_client()
        client_b = start_client()

        self.processes = [server, client_a, client_b]

        client_write(client_a, '/nick test_two_client\n')
        client_write(client_a, f"/connect localhost:{port}\n")
        client_write(client_a, '/create info1910\n')

        client_write(client_b, '/nick test2\n')
        client_write(client_b, f"/connect localhost:{port}\n")
        time.sleep(0.5)
        client_write(client_b, '/join info1910\n')
        time.sleep(0.5)
        client_write(client_a, "Hello World!\n")

        time.sleep(1)

        response = client_read(client_a)
        log("".join(response))
        log()
        assert("Hello World!" in response[-1])
        response = client_read(client_b)
        log("".join(response))
        log()
        assert("Hello World!" in response[-1])

if __name__ == "__main__":
    unittest.main()
