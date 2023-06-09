"""
Testcases for dechat
"""

# pylint: disable=import-error, wrong-import-order, wrong-import-position

import unittest
import time
from rick_utils import (
    execute_await,
    execute_sequence_await,
    await_response,
    set_output_file,
    DechatTestcase,
    SERVERS
)

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

        client = DechatTestcase.create_client()

        self.clients = [client]

        DechatTestcase.connect(client, SERVERS[0])

        execute_await("/create hello_world", client)
        response = execute_await("Hello world!", client)

        assert "Hello world!" in response[-1]

    def test_msg(self):
        """
        Messaging between two clients
        """
        client_1 = DechatTestcase.create_client()
        client_2 = DechatTestcase.create_client()

        self.clients = [client_1, client_2]

        execute_await("/nick client_1", client_1)
        execute_await("/nick client_2", client_2)

        DechatTestcase.connect(client_1, SERVERS[0])
        DechatTestcase.connect(client_2, SERVERS[0])

        execute_await("/create msg", client_1)
        execute_await("/join msg", client_2)

        client_2.clear_buffer()
        response = execute_await("/msg client_2 This is a message!", client_1)

        assert (
            "This is a message" in response[-1] and
            "client_1->client_2" in response[-1]
        )

        response = await_response(client_2)

        assert (
            "This is a message" in response[-1] and
            "client_1->client_2" in response[-1]
        )

    def test_reply(self):
        """
        Tests replies between two clients
        """
        client_1 = DechatTestcase.create_client()
        client_2 = DechatTestcase.create_client()

        self.clients = [client_1, client_2]

        execute_await("/nick client_1", client_1)
        execute_await("/nick client_2", client_2)

        DechatTestcase.connect(client_1, SERVERS[0])
        DechatTestcase.connect(client_2, SERVERS[0])

        execute_await("/create reply", client_1)
        execute_await("/join reply", client_2)

        execute_await("/msg client_2 This is a message!", client_1)
        execute_await("/reply This should not work", client_1)

        client_1.clear_buffer()

        execute_await("/reply Hi client 1", client_2)
        execute_await("/reply Hi client 1 again", client_2)

        response = await_response(client_1)

        assert (
            "Hi client 1" in response[-2] and
            "Hi client 1 again" in response[-1]
        )

    def test_emote(self):
        """
        Testing the /emote command
        """
        emoter = DechatTestcase.create_client()
        observer = DechatTestcase.create_client()

        self.clients = [emoter, observer]

        execute_await("/nick emoter", emoter)
        execute_await("/nick observer", observer)

        DechatTestcase.connect(emoter, SERVERS[0])
        DechatTestcase.connect(observer, SERVERS[0])

        execute_await("/create emote", emoter)
        execute_await("/join emote", observer)

        observer.clear_buffer()

        execute_sequence_await(
            [
                "/emote is cool!",
                "/emote died",
                "/emote emote 1",
                "/emote emote 2",
                "/emote emote 3"
            ],
            emoter,
            period=1.5
        )

        response = await_response(observer, period=1)

        assert "emoter emote 3" in response[-1], "Got: " + response[-1]

    def test_admin(self):
        """
        Test if the admin command works
        """
        admin = DechatTestcase.create_client()
        regular = DechatTestcase.create_client()

        self.clients = [admin, regular]

        execute_await("/nick admin", admin)
        execute_await("/nick regular", regular)

        DechatTestcase.connect(admin, SERVERS[0])
        DechatTestcase.connect(regular, SERVERS[0])

        execute_await("/create admin", admin)
        execute_await("/join admin", regular)

        response = execute_await("/admin admin", admin)

        assert "admin is an operator" in response[-1]

        response = execute_await("/admin regular", regular)

        assert "regular is a regular" in response[-1]

    def test_quit_message(self) -> None:
        """
        Tests for correct quit messages
        """
        quitter = DechatTestcase.create_client()
        observer = DechatTestcase.create_client()

        self.clients = [quitter, observer]

        execute_await("/nick quitter", quitter)
        execute_await("/nick observer", observer)

        DechatTestcase.connect(quitter, SERVERS[0])
        DechatTestcase.connect(observer, SERVERS[0])

        execute_await("/create quit", quitter)
        execute_await("/join quit", observer)

        observer.clear_buffer()
        execute_await("/quit I am having a bad day", quitter)
        response = await_response(observer)

        assert "(I am having a bad day)" in response[-1]

    def test_nick_in_channel(self) -> None:
        """
        Changing nick in channel
        """
        observer = DechatTestcase.create_client()
        multi_nick = DechatTestcase.create_client()

        self.clients = [observer, multi_nick]

        execute_await("/nick observer", observer)
        execute_await("/nick multi_nick", multi_nick)

        DechatTestcase.connect(observer, SERVERS[0])
        DechatTestcase.connect(multi_nick, SERVERS[0])

        execute_await("/create multi_nick", observer)
        execute_await("/join multi_nick", multi_nick)

        observer.clear_buffer()

        multi_nick.feed_input("/nick nick_a")
        execute_await("/msg observer Hi", multi_nick)
        multi_nick.feed_input("/nick nick_b")
        execute_await("/msg observer Hii", multi_nick)
        multi_nick.feed_input("/nick nick_c")
        execute_await("/msg observer Hiii", multi_nick)

        response = await_response(observer)

        response = "".join(response)

        assert (
            "nick_a->observer" in response and
            "nick_b->observer" in response and
            "nick_c->observer" in response and
            "Hi" in response and
            "Hii" in response and
            "Hiii" in response
        )

    def test_password_channel(self) -> None:
        """
        Test for password protected channel
        """

        creator = DechatTestcase.create_client()
        smart = DechatTestcase.create_client()
        dumb = DechatTestcase.create_client()

        self.clients = [creator, smart, dumb]

        execute_await("/nick creator", creator)
        execute_await("/nick smart", smart)
        execute_await("/nick dumb", dumb)

        DechatTestcase.connect(creator, SERVERS[0])
        DechatTestcase.connect(smart, SERVERS[0])
        DechatTestcase.connect(dumb, SERVERS[0])

        execute_await("/create password smart_people_only", creator)
        execute_await("/join password smart_people_only", smart, timeout=1)

        smart.clear_buffer()
        execute_await("/join password bruh", dumb)
        response = await_response(smart, timeout=3)

        assert response is None, "Expected none, got: " + "".join(response)

        execute_await("Hi fellow smart guy", creator)
        execute_await("Why hello fellow smart guy", smart)
        execute_await("/quit", dumb)

    def test_message_limit(self) -> None:
        """
        One guy shouldn't see all the previous messages
        """

        creator = DechatTestcase.create_client()
        ignorant = DechatTestcase.create_client()

        self.clients = [creator, ignorant]

        execute_await("/nick creator", creator)
        execute_await("/nick ignorant", ignorant)

        DechatTestcase.connect(creator, SERVERS[0])
        DechatTestcase.connect(ignorant, SERVERS[0])

        execute_await("/create message_limit", creator)
        creator.feed_input("/message_limit 5")
        time.sleep(0.5)
        execute_await("You shouldn't see this", creator)
        execute_sequence_await(
            ["You should see this 5 times"] * 5, creator, period=2.5
        )

        response = execute_await("/join message_limit", ignorant, period=1)

        assert "You shouldn't see this" not in "".join(response)

    def test_change_pass(self) -> None:
        """
        Change password during channel creation
        """

        creator = DechatTestcase.create_client()
        lucky = DechatTestcase.create_client()
        unlucky = DechatTestcase.create_client()

        self.clients = [creator, lucky, unlucky]

        execute_await("/nick creator", creator)
        execute_await("/nick lucky", lucky)
        execute_await("/nick unlucky", unlucky)

        DechatTestcase.connect(creator, SERVERS[0])
        DechatTestcase.connect(lucky, SERVERS[0])
        DechatTestcase.connect(unlucky, SERVERS[0])

        execute_await("/create change_pass old_pass", creator)
        execute_await("/join change_pass old_pass", lucky)
        creator.feed_input("/pass new_pass")
        time.sleep(0.05)

        creator.clear_buffer()
        execute_await("/join change_pass old_pass", unlucky)
        response = await_response(creator, timeout=1)

        assert response is None

        execute_await("/quit", unlucky)

        execute_await(
            "Hahaha look at that loser can't join the channel", lucky
        )

    def test_owner_joins_pass(self) -> None:
        """
        Owner joins his own password protected channel
        """

        creator = DechatTestcase.create_client()
        observer = DechatTestcase.create_client()

        self.clients = [creator, observer]

        execute_await("/nick creator", creator)
        execute_await("/nick observer", observer)

        DechatTestcase.connect(creator, SERVERS[0])
        DechatTestcase.connect(observer, SERVERS[0])

        execute_await("/create owner_pass owner_pass", creator)
        execute_await("/join owner_pass owner_pass", observer)

        execute_await("/quit", creator)

        execute_await("/join owner_pass", creator)

        response = execute_await("I am in!", creator)

        assert "I am in!" in response[-1], f"Got: {response[-1]}"

    def test_info(self) -> None:
        """
        /info
        """
        client = DechatTestcase.create_client()

        self.clients = [client]

        execute_await("/nick creator", client)

        DechatTestcase.connect(client, SERVERS[0])

        response = execute_await("/info", client)

        assert "Server:" in "".join(response)

    def test_motd(self) -> None:
        """
        /motd
        """
        client = DechatTestcase.create_client()

        self.clients = [client]

        execute_await("/nick creator", client)

        DechatTestcase.connect(client, SERVERS[0])

        execute_await("/motd", client)

    def test_rules(self) -> None:
        """
        /rules
        """
        client = DechatTestcase.create_client()

        self.clients = [client]

        execute_await("/nick creator", client)

        DechatTestcase.connect(client, SERVERS[0])

        execute_await("/rules", client)

    def test_help(self) -> None:
        """
        /help
        """
        client = DechatTestcase.create_client()

        self.clients = [client]

        execute_await("/nick creator", client)

        DechatTestcase.connect(client, SERVERS[0])

        execute_await("/help", client)

    def test_invite(self) -> None:
        """
        Tests the /invite server function
        """
        inviter = DechatTestcase.create_client()
        invitee = DechatTestcase.create_client()

        self.clients = [inviter, invitee]

        execute_await("/nick inviter", inviter)
        execute_await("/nick invitee", invitee)

        DechatTestcase.connect(inviter, SERVERS[0])
        DechatTestcase.connect(invitee, SERVERS[0])

        # Needed so that server can extract nickname from this message
        invitee.feed_input("INPUT")

        execute_await("/create invite", inviter)
        execute_await("/quit", inviter)
        invitee.clear_buffer()
        inviter.feed_input("/invite invitee invite")
        response = await_response(invitee)

        assert "You've been invited to" in response[-1]

    def test_invite_2(self) -> None:
        """
        An edge case for my implementation of /invite
        """
        inviter = DechatTestcase.create_client()
        invitee = DechatTestcase.create_client()

        self.clients = [inviter, invitee]

        execute_await("/nick inviter", inviter)
        execute_await("/nick invitee", invitee)

        DechatTestcase.connect(inviter, SERVERS[0])
        DechatTestcase.connect(invitee, SERVERS[0])

        # Needed so that server can extract nickname from this message
        invitee.feed_input("INPUT")
        time.sleep(0.3)
        execute_await("/quit", invitee)

        execute_await("/create invite_2", inviter)
        execute_await("/quit", inviter)
        invitee.clear_buffer()
        inviter.feed_input("/invite invitee invite_2")

        response = await_response(invitee, timeout=1)

        assert response is None

    def test_stress(self) -> None:
        """
        Stress tests spam
        """
        client = DechatTestcase.create_client()

        self.clients = [client]

        execute_await("/nick spammer", client)
        DechatTestcase.connect(client, SERVERS[0])
        execute_await("/create spam", client)

        response = execute_sequence_await(
            (["SPAM"] * 50) + ["You should see this"], client, period=5
        )

        assert "You should see this" in response[-1]


if __name__ == "__main__":
    set_output_file("test/logs/base_logs.txt")
    unittest.main() # run all tests
