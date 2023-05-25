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

        DechatTestcase.connect(client, SERVERS[0])

        execute_await("/create hello_world", client)
        execute_await("Hello world!", client)

        DechatTestcase.write_client_lines(client)

    def test_msg(self):
        """
        Messaging between two clients
        """
        client_1 = DechatTestcase.create_client()
        client_2 = DechatTestcase.create_client()

        execute_await("/nick client_1", client_1)
        execute_await("/nick client_2", client_2)

        DechatTestcase.connect(client_1, SERVERS[0])
        DechatTestcase.connect(client_2, SERVERS[0])

        execute_await("/create msg", client_1)
        execute_await("/join msg", client_2)

        execute_await("/msg client_2 This is a message!", client_1)

        DechatTestcase.write_client_lines(client_1, client_2)

    def test_reply(self):
        """
        Tests replies between two clients
        """
        client_1 = DechatTestcase.create_client()
        client_2 = DechatTestcase.create_client()

        execute_await("/nick client_1", client_1)
        execute_await("/nick client_2", client_2)

        DechatTestcase.connect(client_1, SERVERS[0])
        DechatTestcase.connect(client_2, SERVERS[0])

        execute_await("/create reply", client_1)
        execute_await("/join reply", client_2)

        execute_await("/msg client_2 This is a message!", client_1)
        execute_await("/reply This should not work", client_1)
        execute_await("/reply Hi client 1", client_2)
        execute_await("/reply Hi client 1 again", client_2)

        DechatTestcase.write_client_lines(client_1, client_2)

    def test_emote(self):
        """
        Testing the /emote command
        """
        emoter = DechatTestcase.create_client()
        observer = DechatTestcase.create_client()

        execute_await("/nick emoter", emoter)
        execute_await("/nick observer", observer)

        DechatTestcase.connect(emoter, SERVERS[0])
        DechatTestcase.connect(observer, SERVERS[0])

        execute_await("/create emote", emoter)
        execute_await("/join emote", observer)

        execute_sequence_await(
            [
                "/emote is cool!",
                "/emote died",
                "/emote emote 1",
                "/emote emote 2",
                "/emote emote 3"
            ],
            emoter
        )

        DechatTestcase.write_client_lines(emoter, observer)

    def test_admin(self):
        """
        Test if the admin command works
        """
        admin = DechatTestcase.create_client()
        regular = DechatTestcase.create_client()

        execute_await("/nick admin", admin)
        execute_await("/nick regular", regular)

        DechatTestcase.connect(admin, SERVERS[0])
        DechatTestcase.connect(regular, SERVERS[0])

        execute_await("/create admin", admin)
        execute_await("/join admin", regular)

        execute_await("/admin admin", admin)
        execute_await("/admin admin", regular)
        execute_await("/admin regular", admin)
        execute_await("/admin regular", regular)

        DechatTestcase.write_client_lines(admin, regular)

    def test_quit_message(self) -> None:
        """
        Tests for correct quit messages
        """
        quitter = DechatTestcase.create_client()
        observer = DechatTestcase.create_client()

        execute_await("/nick quitter", quitter)
        execute_await("/nick observer", observer)

        DechatTestcase.connect(quitter, SERVERS[0])
        DechatTestcase.connect(observer, SERVERS[0])

        execute_await("/create quit", quitter)
        execute_await("/join quit", observer)

        execute_await("/quit I am having a bad day", quitter)

        DechatTestcase.write_client_lines(quitter, observer)

    def test_nick_in_channel(self) -> None:
        """
        Changing nick in channel
        """
        observer = DechatTestcase.create_client()
        multi_nick = DechatTestcase.create_client()

        execute_await("/nick observer", observer)
        execute_await("/nick multi_nick", multi_nick)

        DechatTestcase.connect(observer, SERVERS[0])
        DechatTestcase.connect(multi_nick, SERVERS[0])

        execute_await("/create multi_nick", observer)
        execute_await("/join multi_nick", multi_nick)

        multi_nick.feed_input("/nick nick_a")
        execute_await("/msg observer Hi", multi_nick)
        multi_nick.feed_input("/nick nick_b")
        execute_await("/msg observer Hi", multi_nick)
        multi_nick.feed_input("/nick nick_c")
        execute_await("/msg observer Hi", multi_nick)

        DechatTestcase.write_client_lines(observer, multi_nick)

    def test_password_channel(self) -> None:
        """
        Test for password protected channel
        """

        creator = DechatTestcase.create_client()
        smart = DechatTestcase.create_client()
        dumb = DechatTestcase.create_client()

        execute_await("/nick creator", creator)
        execute_await("/nick smart", smart)
        execute_await("/nick dumb", dumb)

        DechatTestcase.connect(creator, SERVERS[0])
        DechatTestcase.connect(smart, SERVERS[0])
        DechatTestcase.connect(dumb, SERVERS[0])

        execute_await("/create password smart_people_only", creator)
        execute_await("/join password smart_people_only", smart)
        execute_await("/join password bruh", dumb)

        execute_await("Hi fellow smart guy", creator)
        execute_await("Why hello fellow smart guy", smart)
        execute_await("/quit", dumb)

        DechatTestcase.write_client_lines(creator, smart, dumb)

    def test_message_limit(self) -> None:
        """
        One guy shouldn't see all the previous messages
        """

        creator = DechatTestcase.create_client()
        ignorant = DechatTestcase.create_client()

        execute_await("/nick creator", creator)
        execute_await("/nick ignorant", ignorant)

        DechatTestcase.connect(creator, SERVERS[0])
        DechatTestcase.connect(ignorant, SERVERS[0])

        execute_await("/create message_limit", creator)
        creator.feed_input("/message_limit 5")
        time.sleep(0.5)
        execute_await("You shouldn't see this", creator)
        execute_sequence_await(["You should see this 5 times"] * 5, creator)

        execute_await("/join message_limit", ignorant, period=1)

        DechatTestcase.write_client_lines(creator, ignorant)

    def test_change_pass(self) -> None:
        """
        Change password during channel creation
        """

        creator = DechatTestcase.create_client()
        lucky = DechatTestcase.create_client()
        unlucky = DechatTestcase.create_client()

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
        execute_await("/join change_pass old_pass", unlucky)
        execute_await("/quit", unlucky)

        execute_await(
            "Hahaha look at that loser can't join the channel", lucky
        )

        DechatTestcase.write_client_lines(creator, lucky, unlucky)

    def test_owner_joins_pass(self) -> None:
        """
        Owner joins his own password protected channel
        """

        creator = DechatTestcase.create_client()
        observer = DechatTestcase.create_client()

        execute_await("/nick creator", creator)
        execute_await("/nick observer", observer)

        DechatTestcase.connect(creator, SERVERS[0])
        DechatTestcase.connect(observer, SERVERS[0])

        execute_await("/create owner_pass owner_pass", creator)
        execute_await("/join owner_pass owner_pass", observer)

        execute_await("/quit", creator)

        execute_await("/join owner_pass", creator)

        execute_await("I am in!", creator)

        DechatTestcase.write_client_lines(creator, observer)

    def test_info(self) -> None:
        """
        /info
        """
        client = DechatTestcase.create_client()

        execute_await("/nick creator", client)

        DechatTestcase.connect(client, SERVERS[0])

        execute_await("/info", client)

        DechatTestcase.write_client_lines(client)

    def test_motd(self) -> None:
        """
        /motd
        """
        client = DechatTestcase.create_client()

        execute_await("/nick creator", client)

        DechatTestcase.connect(client, SERVERS[0])

        execute_await("/motd", client)

        DechatTestcase.write_client_lines(client)

    def test_rules(self) -> None:
        """
        /rules
        """
        client = DechatTestcase.create_client()

        execute_await("/nick creator", client)

        DechatTestcase.connect(client, SERVERS[0])

        execute_await("/rules", client)

        DechatTestcase.write_client_lines(client)

    def test_help(self) -> None:
        """
        /help
        """
        client = DechatTestcase.create_client()

        execute_await("/nick creator", client)

        DechatTestcase.connect(client, SERVERS[0])

        execute_await("/help", client)

        DechatTestcase.write_client_lines(client)

    def test_invite(self) -> None:
        """
        Tests the /invite server function
        """
        inviter = DechatTestcase.create_client()
        invitee = DechatTestcase.create_client()

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
        await_response(invitee)

        DechatTestcase.write_client_lines(inviter, invitee)

    def test_invite_2(self) -> None:
        """
        An edge case for my implementation of /invite
        """
        inviter = DechatTestcase.create_client()
        invitee = DechatTestcase.create_client()

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

        DechatTestcase.write_client_lines(inviter, invitee)


if __name__ == "__main__":
    unittest.main() # run all tests
