"""Module to test the async_ensure_tokens_valid function"""

from types import MappingProxyType
from unittest import IsolatedAsyncioTestCase
from unittest.mock import MagicMock, patch, AsyncMock

from custom_components.spotcast.spotify.account import (
    SpotifyAccount,
    PublicSession,
    DesktopSession,
    HomeAssistant,
    ConfigEntry,
    Spotify,
    Store,
)

from test.spotify.account import TEST_MODULE


class TestUpdateRequired(IsolatedAsyncioTestCase):

    @patch(f"{TEST_MODULE}.Store", new_callable=MagicMock)
    @patch(f"{TEST_MODULE}.Spotify", new_callable=MagicMock)
    @patch.object(SpotifyAccount, "_async_refresh_single_token")
    @patch.object(SpotifyAccount, "async_profile")
    async def asyncSetUp(
        self,
        mock_profile: AsyncMock,
        mock_refresh: AsyncMock,
        mock_spotify: MagicMock,
        mock_store: MagicMock,
    ):

        mock_spotify.return_value = MagicMock(spec=Spotify)
        mock_store.return_value = MagicMock(spec=Store)

        self.mocks = {
            "hass": MagicMock(spec=HomeAssistant),
            "public_session": MagicMock(spec=PublicSession),
            "private_session": MagicMock(spec=DesktopSession),
            "entry": MagicMock(spec=ConfigEntry),
            "profile": mock_profile,
            "refresh": mock_refresh,
            "spotify": mock_spotify.return_value,
        }

        self.mocks["hass"].config_entries = MagicMock()
        self.mocks["hass"].config_entries.async_get_entry = MagicMock()
        self.mocks["hass"].config_entries.async_get_entry\
            .return_value = self.mocks["entry"]

        self.mocks["entry"].data = MappingProxyType({
            "desktop_api": {
                "token": {
                    "access_token": "foo",
                    "refresh_token": "bar",
                    "expires_at": 123,
                }
            },
            "external_api": {
                "token": {
                    "access_token": "baz",
                    "refresh_token": "boo",
                    "expires_at": 234,
                },
                "implementation": "far",
            }
        })

        self.mocks["refresh"].side_effect = [
            True,
            True,
        ]

        self.mocks["public_session"].data = {
            "token": {
                "access_token": "foo",
                "refresh_token": "world",
                "expires_at": 345,
            },
            "auth_implementation": "far"
        }

        self.mocks["private_session"].data = {
            "token": {
                "access_token": "hello",
                "refresh_token": "world",
                "expires_at": 345,
            }
        }

        self.mocks["public_session"].token = "foo"
        self.mocks["private_session"].token = "hello"

        self.mocks["hass"].config_entries.async_update_entry = MagicMock()
        self.mocks["update"] = (
            self.mocks["hass"].config_entries.async_update_entry
        )

        self.account = SpotifyAccount(
            entry_id="foo",
            hass=self.mocks["hass"],
            public_session=self.mocks["public_session"],
            private_session=self.mocks["private_session"],
        )

        await self.account.async_ensure_tokens_valid()

    def test_entry_updated(self):
        try:
            self.mocks["update"].assert_called_once_with(
                entry=self.mocks["entry"],
                data={
                    "external_api": {
                        "token": {
                            "access_token": "foo",
                            "refresh_token": "world",
                            "expires_at": 345,
                        },
                        "auth_implementation": "far",
                    },
                    "desktop_api": {
                        "token": {
                            "access_token": "hello",
                            "refresh_token": "world",
                            "expires_at": 345,
                        }
                    },
                }
            )
        except AssertionError as exc:
            self.fail(exc)
