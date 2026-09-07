"""Module to test the add_user_error_handler"""

from unittest import TestCase
from unittest.mock import MagicMock, patch

from custom_components.spotcast.chromecast.spotify_controller import (
    SpotifyController,
    SpotifyAccount,
    CastMessage,
)

TEST_MODULE = "custom_components.spotcast.chromecast.spotify_controller"


class TestTransferErrorHandling(TestCase):

    @patch(f"{TEST_MODULE}.threading.Event")
    def setUp(self, mock_event: MagicMock):

        mock_account = MagicMock(spec=SpotifyAccount)
        self.controller = SpotifyController(mock_account)

        # The handler records the refusal rather than raising it, since it
        # runs on a thread where a raise would be logged and dropped.
        self.controller._transfer_error_handler(
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


class TestTransferErrorRecordOrdering(TestCase):
    """`launch_error` must be readable as soon as the flag is set

    The waiting thread polls `credential_error` every second rather
    than only waking on `waiting.set()`, so a poll landing between
    the two assignments would report the generic message and drop
    what the device actually said.
    """

    @patch(f"{TEST_MODULE}.threading.Event")
    def test_detail_is_recorded_before_the_flag_is_raised(
            self,
            mock_event: MagicMock,  # pylint: disable=W0613
    ):
        controller = SpotifyController(MagicMock(spec=SpotifyAccount))
        observed = []

        with patch.object(
                SpotifyController,
                "_describe",
                side_effect=lambda *_: observed.append(
                    controller.credential_error
                ) or "detail",
        ):
            controller._transfer_error_handler(
                MagicMock(spec=CastMessage),
                {},
            )

        self.assertEqual(observed, [False])
