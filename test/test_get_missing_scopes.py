"""Module to test the get_missing_scopes function and its enforcement
in async_setup_entry"""

from unittest import IsolatedAsyncioTestCase, TestCase
from unittest.mock import MagicMock

from custom_components.spotcast import (
    async_setup_entry,
    get_missing_scopes,
    HomeAssistant,
    ConfigEntry,
    ConfigEntryAuthFailed,
)
from custom_components.spotcast.spotify import SpotifyAccount


def entry_with_scope(scope) -> MagicMock:
    entry = MagicMock(spec=ConfigEntry)
    entry.entry_id = "foo"
    entry.options = {}
    token = {} if scope is None else {"scope": scope}
    entry.data = {"external_api": {"token": token}}
    return entry


class TestFullScopes(TestCase):

    def test_no_missing_scopes(self):
        entry = entry_with_scope(" ".join(SpotifyAccount.SCOPE))
        self.assertEqual(get_missing_scopes(entry), set())

    def test_comma_separated_scopes_accepted(self):
        entry = entry_with_scope(",".join(SpotifyAccount.SCOPE))
        self.assertEqual(get_missing_scopes(entry), set())


class TestMissingScopes(TestCase):

    def test_missing_scope_reported(self):
        granted = [s for s in SpotifyAccount.SCOPE if s != "user-library-modify"]
        entry = entry_with_scope(" ".join(granted))
        self.assertEqual(get_missing_scopes(entry), {"user-library-modify"})


class TestUnknownScopes(TestCase):

    def test_absent_scope_key_skips_validation(self):
        entry = entry_with_scope(None)
        self.assertEqual(get_missing_scopes(entry), set())

    def test_absent_external_api_skips_validation(self):
        entry = MagicMock(spec=ConfigEntry)
        entry.data = {}
        self.assertEqual(get_missing_scopes(entry), set())


class TestSetupAbortsOnMissingScopes(IsolatedAsyncioTestCase):

    async def test_auth_failed_raised(self):
        hass = MagicMock(spec=HomeAssistant)
        granted = [s for s in SpotifyAccount.SCOPE if s != "user-library-modify"]
        entry = entry_with_scope(" ".join(granted))

        with self.assertRaises(ConfigEntryAuthFailed):
            await async_setup_entry(hass, entry)
