"""Module to test the send_message_callback function"""

from unittest import TestCase
from unittest.mock import MagicMock, patch

from custom_components.spotcast.chromecast.spotify_controller import (
    SpotifyController,
    SpotifyAccount,
    Chromecast,
)

TEST_MODULE = "custom_components.spotcast.chromecast.spotify_controller."


class TestMessageSending(TestCase):

    @patch.object(SpotifyController, "send_message")
    def setUp(self, mock_send: MagicMock):
        mock_account = MagicMock(spec=SpotifyAccount)
        self.mock_send = mock_send
        self.dummy_message = {
            "foo": "bar"
        }

        self.controller = SpotifyController(mock_account)
        self.controller._current_message = self.dummy_message

        self.controller._send_message_callback(self)

    def test_correct_message_sent(self):
        try:
            self.mock_send.assert_called_with(self.dummy_message)
        except AssertionError:
            self.fail("sent message was not expected dummy message")

    def test_current_message_reset(self):
        self.assertIsNone(self.controller._current_message)


class TestGroupSettleDelay(TestCase):

    @patch(TEST_MODULE + "time.sleep")
    @patch.object(SpotifyController, "send_message")
    def test_group_waits_before_send(
            self,
            mock_send: MagicMock,
            mock_sleep: MagicMock,
    ):
        controller = SpotifyController(MagicMock(spec=SpotifyAccount))
        controller._current_message = {"foo": "bar"}
        controller.current_device = MagicMock(spec=Chromecast)
        controller.current_device.is_group = True

        controller._send_message_callback(self)

        mock_sleep.assert_called_once()
        mock_send.assert_called_once_with({"foo": "bar"})

    @patch(TEST_MODULE + "time.sleep")
    @patch.object(SpotifyController, "send_message")
    def test_single_device_does_not_wait(
            self,
            mock_send: MagicMock,
            mock_sleep: MagicMock,
    ):
        controller = SpotifyController(MagicMock(spec=SpotifyAccount))
        controller._current_message = {"foo": "bar"}
        controller.current_device = MagicMock(spec=Chromecast)
        controller.current_device.is_group = False

        controller._send_message_callback(self)

        mock_sleep.assert_not_called()
        mock_send.assert_called_once_with({"foo": "bar"})
