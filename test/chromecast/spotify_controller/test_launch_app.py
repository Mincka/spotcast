"""Module to test the launch_app function"""

from unittest import TestCase
from unittest.mock import MagicMock, patch
from threading import Event

from pychromecast.error import RequestTimeout

from custom_components.spotcast.chromecast.spotify_controller import (
    SpotifyController,
    SpotifyAccount,
    Chromecast,
    AppLaunchError,
    CONNECT_TIMEOUT,
)

TEST_MODULE = "custom_components.spotcast.chromecast.spotify_controller."


class TestAppLaunch(TestCase):

    @patch.object(SpotifyController, "launch")
    def test_app_launch_returns(self, mock_launch: MagicMock):
        mock_account = MagicMock(spec=SpotifyAccount)
        self.controller = SpotifyController(mock_account)

        mock_launch.side_effect = self.set_is_launched

        mock_device = MagicMock(spec=Chromecast)

        try:
            self.controller.launch_app(mock_device, max_attempts=2)
        except AppLaunchError:
            self.fail("Failed to launch app")

    def set_is_launched(self, *_, **__):
        self.controller.is_launched = True


class TestGroupPayload(TestCase):

    @patch.object(SpotifyController, "launch")
    def test_group_flag_reflects_device(self, mock_launch: MagicMock):
        self.controller = SpotifyController(MagicMock(spec=SpotifyAccount))
        mock_launch.side_effect = self.set_is_launched

        mock_device = MagicMock(spec=Chromecast)
        mock_device.is_group = True

        self.controller.launch_app(mock_device, max_attempts=2)

        payload = self.controller._current_message["payload"]
        self.assertTrue(payload["deviceAPI_isGroup"])

    @patch.object(SpotifyController, "launch")
    def test_single_device_flag_reflects_device(
            self,
            mock_launch: MagicMock,
    ):
        self.controller = SpotifyController(MagicMock(spec=SpotifyAccount))
        mock_launch.side_effect = self.set_is_launched

        mock_device = MagicMock(spec=Chromecast)
        mock_device.is_group = False

        self.controller.launch_app(mock_device, max_attempts=2)

        payload = self.controller._current_message["payload"]
        self.assertFalse(payload["deviceAPI_isGroup"])

    def set_is_launched(self, *_, **__):
        self.controller.is_launched = True


class TestAppFailLaunch(TestCase):

    @patch(TEST_MODULE+"threading.Event", spec=Event)
    @patch.object(SpotifyController, "launch")
    def test_app_launch_fails(
            self,
            mock_launch: MagicMock,
            mock_event: MagicMock
    ):
        mock_account = MagicMock(spec=SpotifyAccount)
        self.controller = SpotifyController(mock_account)

        mock_event.wait.side_effect = [
            None,
            self.set_is_launched,
        ]

        mock_device = MagicMock(spec=Chromecast)

        with self.assertRaises(AppLaunchError):
            self.controller.launch_app(mock_device, max_attempts=2)

    def set_is_launched(self, *_, **__):
        self.controller.is_launched = True


class TestCredentialRefusal(TestCase):
    """A refusal reported by the device must reach the caller"""

    @patch.object(SpotifyController, "launch")
    def test_credential_error_is_raised_to_the_caller(
            self,
            mock_launch: MagicMock,
    ):
        controller = SpotifyController(MagicMock(spec=SpotifyAccount))

        def refuse(*_, **__):
            controller._add_user_error_handler(
                MagicMock(),
                {"payload": {"statusString": "ERROR-CANNOT-LOAD",
                             "spotifyError": 409}},
            )

        mock_launch.side_effect = refuse

        with self.assertRaises(AppLaunchError) as caught:
            controller.launch_app(MagicMock(spec=Chromecast), max_attempts=10)

        self.assertIn("ERROR-CANNOT-LOAD", str(caught.exception))

    @patch.object(SpotifyController, "launch")
    def test_an_unreachable_device_does_not_block(
            self,
            mock_launch: MagicMock,
    ):
        """An unreachable device fails the call rather than blocking it

        `Chromecast.wait(timeout=...)` raises `RequestTimeout` rather
        than returning, so that is what the device does here.
        """
        controller = SpotifyController(MagicMock(spec=SpotifyAccount))

        device = MagicMock(spec=Chromecast)
        device.wait.side_effect = RequestTimeout("wait", CONNECT_TIMEOUT)

        with self.assertRaises(AppLaunchError) as caught:
            controller.launch_app(device, max_attempts=2)

        self.assertIn("Could not connect", str(caught.exception))
        mock_launch.assert_not_called()
        device.wait.assert_called_once_with(timeout=CONNECT_TIMEOUT)
