"""Module to test the async_remove_config_entry_device function"""

from unittest import IsolatedAsyncioTestCase
from unittest.mock import MagicMock

from homeassistant.helpers.device_registry import DeviceEntry

from custom_components.spotcast import (
    async_remove_config_entry_device,
    HomeAssistant,
    ConfigEntry,
    DOMAIN,
)
from custom_components.spotcast.spotify import SpotifyAccount


def build_mocks(active_ids: list[str], identifiers: set) -> dict:
    mocks = {
        "hass": MagicMock(spec=HomeAssistant),
        "entry": MagicMock(spec=ConfigEntry),
        "account": MagicMock(spec=SpotifyAccount),
        "device": MagicMock(spec=DeviceEntry),
    }
    mocks["entry"].entry_id = "12345"
    mocks["account"].devices = [{"id": x} for x in active_ids]
    mocks["device"].identifiers = identifiers
    mocks["hass"].data = {
        DOMAIN: {"12345": {"account": mocks["account"]}}
    }
    return mocks


class TestStaleDeviceRemoval(IsolatedAsyncioTestCase):

    async def test_absent_device_can_be_removed(self):
        mocks = build_mocks(["foo"], {(DOMAIN, "bar")})
        result = await async_remove_config_entry_device(
            mocks["hass"], mocks["entry"], mocks["device"],
        )
        self.assertTrue(result)


class TestActiveDeviceRemoval(IsolatedAsyncioTestCase):

    async def test_active_device_cannot_be_removed(self):
        mocks = build_mocks(["foo"], {(DOMAIN, "foo")})
        result = await async_remove_config_entry_device(
            mocks["hass"], mocks["entry"], mocks["device"],
        )
        self.assertFalse(result)


class TestUnloadedAccountRemoval(IsolatedAsyncioTestCase):

    async def test_removal_allowed_without_account(self):
        mocks = build_mocks(["foo"], {(DOMAIN, "foo")})
        mocks["hass"].data = {}
        result = await async_remove_config_entry_device(
            mocks["hass"], mocks["entry"], mocks["device"],
        )
        self.assertTrue(result)
