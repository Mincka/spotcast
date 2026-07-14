"""Module to test the system_health_info function"""

import inspect

from unittest import IsolatedAsyncioTestCase
from unittest.mock import MagicMock, AsyncMock, patch

from custom_components.spotcast.system_health import (
    system_health_info,
    HomeAssistant,
    __version__,
    SpotifyAccount,
)

TEST_MODULE = "custom_components.spotcast.system_health"


class TestHealthyAccount(IsolatedAsyncioTestCase):

    @patch(f"{TEST_MODULE}.async_check_can_reach_url")
    async def asyncSetUp(self, mock_url_check: AsyncMock):

        self.mocks = {
            "hass": MagicMock(spec=HomeAssistant),
            "account": MagicMock(spec=SpotifyAccount),
            "url_check": mock_url_check,
        }

        self.mocks["hass"].data = {
            "spotcast": {
                "1234": {
                    "account": self.mocks["account"]
                }
            }
        }

        self.mocks["account"].health_status = {
            "public": True,
            "private": True,
        }

        self.mocks["account"].id = "dummy"
        self.mocks["account"].is_default = True

        self.result = await system_health_info(self.mocks["hass"])

    def test_results_contain_current_version(self):
        self.assertIn("Version", self.result)
        self.assertEqual(self.result["Version"], __version__)

    def test_results_set_user_as_default(self):
        self.assertIn("Account 1 Is Default", self.result)
        self.assertTrue(self.result["Account 1 Is Default"])

    def test_no_account_identifier_leaked(self):
        """System health ends up in public bug reports: the Spotify
        account id must not appear in it."""
        self.assertNotIn("dummy", str(self.result).lower())

    def test_device_registration_check_uses_full_url(self):
        url = self.mocks["url_check"].call_args_list[1][0][1]
        self.assertTrue(url.startswith("https://"))


class TestUnHealthyAccount(IsolatedAsyncioTestCase):

    @patch(f"{TEST_MODULE}.async_check_can_reach_url")
    async def asyncSetUp(self, mock_url_check: AsyncMock):

        self.mocks = {
            "hass": MagicMock(spec=HomeAssistant),
            "account": MagicMock(spec=SpotifyAccount),
            "url_check": mock_url_check,
        }

        self.mocks["hass"].data = {
            "spotcast": {
                "1234": {
                    "account": self.mocks["account"]
                }
            }
        }

        self.mocks["account"].health_status = {
            "public": False,
            "private": False,
        }

        self.mocks["account"].id = "dummy"
        self.mocks["account"].is_default = True

        self.result = await system_health_info(self.mocks["hass"])

    def test_proper_failed_check_object(self):
        self.assertEqual(
            self.result["Account 1 Public Token"],
            {"type": "failed", "error": "unhealthy"},
        )
