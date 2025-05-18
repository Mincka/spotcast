"""Module to test the async_refresh_token function"""

from json import JSONDecodeError
from time import time
from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, MagicMock, patch

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from custom_components.spotcast.sessions.desktop_session import (
    DesktopSession,
    ClientError,
    SPOTIFY_CLIENT_ID,
)

from test.sessions.desktop_session import TEST_MODULE


class TestTokenRefreshes(IsolatedAsyncioTestCase):

    @patch(f"{TEST_MODULE}.async_get_clientsession", new_callable=MagicMock)
    async def asyncSetUp(self, mock_session: MagicMock):

        mock_session.return_value.post = AsyncMock()

        self.mocks: dict[str, AsyncMock | MagicMock] = {
            "hass": MagicMock(spec=HomeAssistant),
            "entry": MagicMock(spec=ConfigEntry),
            "session": mock_session.return_value,
            "post": mock_session.return_value.post,
        }

        self.mocks["post"].return_value = MagicMock()
        self.mocks["response"] = self.mocks["post"].return_value

        self.mocks["entry"].data = {
            "desktop_api": {
                "token": {
                    "access_token": "foo",
                    "refresh_token": "bar",
                }
            }
        }

        self.mocks["response"].status = 200
        self.mocks["response"].json = AsyncMock()
        self.mocks["response"].json.return_value = {
            "access_token": "foo",
            "refresh_token": "bar",
            "expires_in": 200,
        }

        self.session = DesktopSession(self.mocks["hass"], self.mocks["entry"])
        self.result = await self.session.async_refresh_token()

    def test_post_call(self):
        try:
            self.mocks["post"].assert_called_with(
                url="https://accounts.spotify.com/api/token",
                data={
                    "grant_type": "refresh_token",
                    "client_id": SPOTIFY_CLIENT_ID,
                    "refresh_token": "bar",
                }
            )
        except AssertionError as exc:
            self.fail(exc)

    def test_expires_at_created(self):
        self.assertIn("expires_at", self.result)
        self.assertNotEqual(self.result["expires_at"], 200)
        self.assertGreater(self.result["expires_at"], time())


class TestStandardError(IsolatedAsyncioTestCase):

    @patch(f"{TEST_MODULE}.async_get_clientsession", new_callable=MagicMock)
    async def test_error_raised(self, mock_session: MagicMock):

        mock_session.return_value.post = AsyncMock()

        self.mocks: dict[str, AsyncMock | MagicMock] = {
            "hass": MagicMock(spec=HomeAssistant),
            "entry": MagicMock(spec=ConfigEntry),
            "session": mock_session.return_value,
            "post": mock_session.return_value.post,
        }

        self.mocks["post"].return_value = MagicMock()
        self.mocks["response"] = self.mocks["post"].return_value

        self.mocks["entry"].data = {
            "desktop_api": {
                "token": {
                    "access_token": "foo",
                    "refresh_token": "bar",
                }
            }
        }

        self.mocks["response"].status = 403
        self.mocks["response"].json = AsyncMock()
        self.mocks["response"].json.return_value = {
            "error": "dummy",
            "error_description": "dummy error"
        }

        self.mocks["response"].raise_for_status.side_effect = ClientError()

        self.session = DesktopSession(self.mocks["hass"], self.mocks["entry"])

        with self.assertRaises(ClientError):
            await self.session.async_refresh_token()


class TestDecodingError(IsolatedAsyncioTestCase):

    @patch(f"{TEST_MODULE}.async_get_clientsession", new_callable=MagicMock)
    async def test_error_raised(self, mock_session: MagicMock):

        mock_session.return_value.post = AsyncMock()

        self.mocks: dict[str, AsyncMock | MagicMock] = {
            "hass": MagicMock(spec=HomeAssistant),
            "entry": MagicMock(spec=ConfigEntry),
            "session": mock_session.return_value,
            "post": mock_session.return_value.post,
        }

        self.mocks["post"].return_value = MagicMock()
        self.mocks["response"] = self.mocks["post"].return_value

        self.mocks["entry"].data = {
            "desktop_api": {
                "token": {
                    "access_token": "foo",
                    "refresh_token": "bar",
                }
            }
        }

        self.mocks["response"].status = 403
        self.mocks["response"].json = AsyncMock()
        self.mocks["response"].json.side_effect = JSONDecodeError(
            "foo", "bar", 1)
        self.mocks["response"].raise_for_status.side_effect = ClientError()

        self.session = DesktopSession(self.mocks["hass"], self.mocks["entry"])

        with self.assertRaises(ClientError):
            await self.session.async_refresh_token()
