"""Module to test the release method of the chromecast_player. It must
stop the socket client thread without blocking or raising (see #80)."""

import socket
from unittest import TestCase
from unittest.mock import MagicMock
from uuid import uuid4

from pychromecast.models import CastInfo, HostServiceInfo

from custom_components.spotcast.media_player.chromecast_player import (
    Chromecast,
)


def unused_port() -> int:
    """Returns a local port nothing listens on"""
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


class TestReleaseStopsSocketThread(TestCase):
    """Runs the real socket client against a closed port, where it
    retries forever until stopped, like a leaked client does."""

    def setUp(self):
        cast_info = CastInfo(
            {HostServiceInfo("127.0.0.1", unused_port())},
            uuid4(),
            None,
            "Bathroom",
            None,
            "cast",
            None,
            None,
        )
        self.device = Chromecast(cast_info, zconf=MagicMock(), retry_wait=0.1)
        self.device.start()
        self.addCleanup(self.device.socket_client.disconnect)

    def test_thread_stops(self):
        self.device.release()
        self.device.socket_client.join(timeout=5)
        self.assertFalse(self.device.socket_client.is_alive())

    def test_release_twice_does_not_raise(self):
        self.device.release()
        self.device.release()


class TestReleaseDoesNotJoin(TestCase):

    def test_socket_client_disconnect_called_without_join(self):
        device = MagicMock(spec=Chromecast)
        device.socket_client = MagicMock()

        Chromecast.release(device)

        device.socket_client.disconnect.assert_called_once_with()
        device.join.assert_not_called()
        device.disconnect.assert_not_called()
