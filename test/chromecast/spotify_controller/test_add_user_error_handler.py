"""Module to test the add_user_error_handler"""

from unittest import TestCase
from unittest.mock import MagicMock, patch

from custom_components.spotcast.chromecast.spotify_controller import (
    SpotifyController,
    SpotifyAccount,
    CastMessage,
    AppLaunchError,
)

TEST_MODULE = "custom_components.spotcast.chromecast.spotify_controller"


class TestAddUserErrorHandling(TestCase):

    @patch(f"{TEST_MODULE}.threading.Event")
    def setUp(self, mock_event: MagicMock):

        mock_account = MagicMock(spec=SpotifyAccount)
        self.controller = SpotifyController(mock_account)

        # The handler records the refusal rather than raising it, since it
        # runs on a thread where a raise would be logged and dropped.
        self.controller._add_user_error_handler(
            MagicMock(spec=CastMessage),
            {
                "payload": {
                    "status": 108,
                    "statusString": "ERROR-CANNOT-LOAD",
                    "spotifyError": 409,
                }
            }
        )

    def test_device_removed(self):
        self.assertIsNone(self.controller.current_device)

    def test_credential_error_set(self):
        try:
            self.controller.waiting.set.assert_called()
        except AssertionError:
            self.fail()

    def test_credentials_error_set(self):
        self.assertTrue(self.controller.credential_error)

    def test_records_what_the_device_said(self):
        self.assertIn("ERROR-CANNOT-LOAD", self.controller.launch_error)
        self.assertIn("409", self.controller.launch_error)
