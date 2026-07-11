"""Module to test the async_update_options function"""

from datetime import timedelta
from unittest import IsolatedAsyncioTestCase
from unittest.mock import MagicMock, AsyncMock

from custom_components.spotcast import (
    async_update_options,
    HomeAssistant,
    ConfigEntry,
    SpotcastCoordinator,
)
from custom_components.spotcast.spotify import SpotifyAccount


class TestRefreshRateChanged(IsolatedAsyncioTestCase):

    async def asyncSetUp(self):

        self.mocks = {
            "hass": MagicMock(spec=HomeAssistant),
            "entry": MagicMock(spec=ConfigEntry),
            "account": MagicMock(spec=SpotifyAccount),
            "coordinator": MagicMock(spec=SpotcastCoordinator),
        }

        self.mocks["entry"].entry_id = "12345"
        self.mocks["entry"].options = {
            "is_default": True,
            "base_refresh_rate": 15,
        }

        self.mocks["account"].is_default = False
        self.mocks["account"].base_refresh_rate = 30
        self.mocks["coordinator"].update_interval = timedelta(seconds=30)
        self.mocks["coordinator"].async_request_refresh = AsyncMock()

        self.mocks["hass"].data = {
            "spotcast": {
                "12345": {
                    "account": self.mocks["account"],
                    "coordinator": self.mocks["coordinator"],
                }
            }
        }

        await async_update_options(self.mocks["hass"], self.mocks["entry"])

    def test_account_refresh_rate_updated(self):
        self.assertEqual(self.mocks["account"].base_refresh_rate, 15)

    def test_account_is_default_updated(self):
        self.assertTrue(self.mocks["account"].is_default)

    def test_coordinator_interval_updated(self):
        self.assertEqual(
            self.mocks["coordinator"].update_interval,
            timedelta(seconds=15),
        )

    def test_refresh_requested(self):
        try:
            self.mocks["coordinator"].async_request_refresh\
                .assert_awaited_once()
        except AssertionError:
            self.fail()


class TestRefreshRateUnchanged(IsolatedAsyncioTestCase):

    async def asyncSetUp(self):

        self.mocks = {
            "hass": MagicMock(spec=HomeAssistant),
            "entry": MagicMock(spec=ConfigEntry),
            "account": MagicMock(spec=SpotifyAccount),
            "coordinator": MagicMock(spec=SpotcastCoordinator),
        }

        self.mocks["entry"].entry_id = "12345"
        self.mocks["entry"].options = {
            "is_default": False,
            "base_refresh_rate": 30,
        }

        self.mocks["account"].is_default = False
        self.mocks["account"].base_refresh_rate = 30
        self.mocks["coordinator"].update_interval = timedelta(seconds=30)
        self.mocks["coordinator"].async_request_refresh = AsyncMock()

        self.mocks["hass"].data = {
            "spotcast": {
                "12345": {
                    "account": self.mocks["account"],
                    "coordinator": self.mocks["coordinator"],
                }
            }
        }

        await async_update_options(self.mocks["hass"], self.mocks["entry"])

    def test_no_refresh_requested(self):
        try:
            self.mocks["coordinator"].async_request_refresh\
                .assert_not_awaited()
        except AssertionError:
            self.fail()

    def test_listeners_notified(self):
        try:
            self.mocks["coordinator"].async_update_listeners\
                .assert_called_once()
        except AssertionError:
            self.fail()


class TestEntryNotLoaded(IsolatedAsyncioTestCase):

    async def test_no_error_raised(self):

        self.mocks = {
            "hass": MagicMock(spec=HomeAssistant),
            "entry": MagicMock(spec=ConfigEntry),
        }

        self.mocks["entry"].entry_id = "12345"
        self.mocks["entry"].options = {
            "is_default": False,
            "base_refresh_rate": 30,
        }

        self.mocks["hass"].data = {"spotcast": {}}

        await async_update_options(self.mocks["hass"], self.mocks["entry"])
