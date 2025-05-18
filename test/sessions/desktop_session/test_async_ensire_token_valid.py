"""Module to test the async_ensure_token_valid function."""

from time import time
from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, MagicMock, patch

from aiohttp.client_exceptions import ClientOSError
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from custom_components.spotcast.sessions.retry_supervisor import RetrySupervisor
from custom_components.spotcast.sessions.desktop_session import (
    DesktopSession,
    UpstreamServerNotready,
)

from test.sessions.desktop_session import TEST_MODULE


class TestTokenExpired(IsolatedAsyncioTestCase):

    @patch(f"{TEST_MODULE}.time", new_callable=MagicMock)
    @patch.object(DesktopSession, "async_refresh_token")
    async def asyncSetUp(self, mock_refresh: AsyncMock, mock_time: MagicMock):

        self.mocks = {
            "hass": MagicMock(spec=HomeAssistant),
            "entry": MagicMock(spec=ConfigEntry),
            "supervisor": MagicMock(spec=RetrySupervisor),
            "refresh": mock_refresh,
            "time": mock_time,
        }

        self.mocks["update"] = (
            self.mocks["hass"]
            .config_entries
            .async_update_entry
        )

        self.mocks["time"].return_value = 500
        self.mocks["supervisor"].is_ready = True
        self.mocks["refresh"].return_value = {
            "access_token": "foo",
            "expires_in": 300,
            "refresh_token": "bar",
        }

        self.mocks["entry"].data = {
            "desktop_api": {
                "token": {
                    "access_token": "baz",
                    "expires_at": 0,
                    "refresh_token": "bar",
                }
            }
        }

        self.session = DesktopSession(self.mocks["hass"], self.mocks["entry"])
        self.session.supervisor = self.mocks["supervisor"]

        await self.session.async_ensure_token_valid()

    def test_new_data(self):
        try:
            self.mocks["update"].assert_called_with(
                self.session.entry,
                data={
                    "desktop_api": {
                        "token": {
                            "access_token": "foo",
                            "expires_at": 800,
                            "refresh_token": "bar",
                        }
                    }
                }
            )
        except AssertionError as exc:
            self.fail(exc)


class TestTokenNotExpired(IsolatedAsyncioTestCase):

    @patch(f"{TEST_MODULE}.time", new_callable=MagicMock)
    @patch.object(DesktopSession, "async_refresh_token")
    async def asyncSetUp(self, mock_refresh: AsyncMock, mock_time: MagicMock):

        self.mocks = {
            "hass": MagicMock(spec=HomeAssistant),
            "entry": MagicMock(spec=ConfigEntry),
            "supervisor": MagicMock(spec=RetrySupervisor),
            "refresh": mock_refresh,
            "time": mock_time,
        }

        self.mocks["update"] = (
            self.mocks["hass"]
            .config_entries
            .async_update_entry
        )

        self.mocks["time"].return_value = 500
        self.mocks["supervisor"].is_ready = True
        self.mocks["refresh"].return_value = {
            "access_token": "foo",
            "expires_in": 300,
            "refresh_token": "bar",
        }

        self.mocks["entry"].data = {
            "desktop_api": {
                "token": {
                    "access_token": "baz",
                    "expires_at": time()+9999,
                    "refresh_token": "bar",
                }
            }
        }

        self.session = DesktopSession(self.mocks["hass"], self.mocks["entry"])
        self.session.supervisor = self.mocks["supervisor"]

        await self.session.async_ensure_token_valid()

    def test_new_data(self):
        try:
            self.mocks["update"].assert_not_called()
        except AssertionError as exc:
            self.fail(exc)


class TestSupervisorNotReady(IsolatedAsyncioTestCase):

    @patch(f"{TEST_MODULE}.time", new_callable=MagicMock)
    @patch.object(DesktopSession, "async_refresh_token")
    async def test_error_raised(
        self,
        mock_refresh: AsyncMock,
        mock_time: MagicMock,
    ):

        self.mocks = {
            "hass": MagicMock(spec=HomeAssistant),
            "entry": MagicMock(spec=ConfigEntry),
            "supervisor": MagicMock(spec=RetrySupervisor),
            "refresh": mock_refresh,
            "time": mock_time,
        }

        self.mocks["update"] = (
            self.mocks["hass"]
            .config_entries
            .async_update_entry
        )

        self.mocks["time"].return_value = 500
        self.mocks["supervisor"].is_ready = False
        self.mocks["refresh"].return_value = {
            "access_token": "foo",
            "expires_in": 300,
            "refresh_token": "bar",
        }

        self.mocks["entry"].data = {
            "desktop_api": {
                "token": {
                    "access_token": "baz",
                    "expires_at": 0,
                    "refresh_token": "bar",
                }
            }
        }

        self.session = DesktopSession(self.mocks["hass"], self.mocks["entry"])
        self.session.supervisor = self.mocks["supervisor"]

        with self.assertRaises(UpstreamServerNotready):
            await self.session.async_ensure_token_valid()


class TestErrorWhileRefreshing(IsolatedAsyncioTestCase):

    @patch(f"{TEST_MODULE}.time", new_callable=MagicMock)
    @patch.object(DesktopSession, "async_refresh_token")
    async def test_error_raised(
        self,
        mock_refresh: AsyncMock,
        mock_time: MagicMock,
    ):

        self.mocks = {
            "hass": MagicMock(spec=HomeAssistant),
            "entry": MagicMock(spec=ConfigEntry),
            "supervisor": MagicMock(spec=RetrySupervisor),
            "refresh": mock_refresh,
            "time": mock_time,
        }

        self.mocks["update"] = (
            self.mocks["hass"]
            .config_entries
            .async_update_entry
        )

        self.mocks["time"].return_value = 500
        self.mocks["supervisor"].is_ready = True
        self.mocks["supervisor"].SUPERVISED_EXCEPTIONS = (
            RetrySupervisor.SUPERVISED_EXCEPTIONS
        )
        self.mocks["refresh"].side_effect = ClientOSError()

        self.mocks["entry"].data = {
            "desktop_api": {
                "token": {
                    "access_token": "baz",
                    "expires_at": 0,
                    "refresh_token": "bar",
                }
            }
        }

        self.session = DesktopSession(self.mocks["hass"], self.mocks["entry"])
        self.session.supervisor = self.mocks["supervisor"]

        with self.assertRaises(UpstreamServerNotready):
            await self.session.async_ensure_token_valid()
