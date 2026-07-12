"""Module to test the async_get_internal_playlist_length function"""

from unittest import IsolatedAsyncioTestCase
from unittest.mock import MagicMock, AsyncMock, patch

from custom_components.spotcast.spotify.account import (
    SpotifyAccount,
    PublicSession,
    DesktopSession,
    HomeAssistant,
    Spotify,
    Store,
)

from test.spotify.account import TEST_MODULE


class TestDelegation(IsolatedAsyncioTestCase):

    @patch(
        f"{TEST_MODULE}.async_get_playlist_length",
        new_callable=AsyncMock,
    )
    @patch(f"{TEST_MODULE}.Store", spec=Store, new_callable=MagicMock)
    @patch(f"{TEST_MODULE}.Spotify", spec=Spotify, new_callable=MagicMock)
    async def asyncSetUp(
        self,
        mock_spotify: MagicMock,
        mock_store: MagicMock,
        mock_length: AsyncMock,
    ):

        mock_length.return_value = 50
        self.mock_length = mock_length

        self.account = SpotifyAccount(
            entry_id="12345",
            hass=MagicMock(spec=HomeAssistant),
            public_session=MagicMock(spec=PublicSession),
            private_session=MagicMock(spec=DesktopSession),
            is_default=True,
        )

        self.result = await self.account.async_get_internal_playlist_length(
            "spotify:playlist:foo"
        )

    def test_length_returned(self):
        self.assertEqual(self.result, 50)

    def test_helper_called_with_account_and_uri(self):
        try:
            self.mock_length.assert_called_once_with(
                self.account, "spotify:playlist:foo"
            )
        except AssertionError as exc:
            self.fail(exc)
