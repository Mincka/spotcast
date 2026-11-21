"""Module to test the description placeholders of the Add application
credentials dialog"""

from json import loads
from pathlib import Path
from re import findall
from unittest import IsolatedAsyncioTestCase
from unittest.mock import MagicMock, patch

from homeassistant.helpers.network import NoURLAvailableError

from custom_components.spotcast.application_credentials import (
    DASHBOARD_URL,
    SETUP_GUIDE_URL,
    UNKNOWN_HOST_REDIRECT_URI,
    async_get_description_placeholders,
)

TEST_MODULE = "custom_components.spotcast.application_credentials"
STRINGS_FILE = (
    Path(__file__).resolve().parent.parent
    / "custom_components"
    / "spotcast"
    / "strings.json"
)
MY_REDIRECT_URI = "https://my.home-assistant.io/redirect/oauth"


class TestMyHomeAssistantLoaded(IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        hass = MagicMock()
        hass.config.components = {"my", "spotify"}
        self.result = await async_get_description_placeholders(hass)

    def test_redirect_uri_is_my_home_assistant(self):
        self.assertEqual(self.result["redirect_uri"], MY_REDIRECT_URI)

    def test_dashboard_url(self):
        self.assertEqual(self.result["dashboard_url"], DASHBOARD_URL)

    def test_setup_guide_points_to_step_1(self):
        self.assertEqual(self.result["setup_guide_url"], SETUP_GUIDE_URL)
        self.assertTrue(
            SETUP_GUIDE_URL.endswith("#1-create-a-spotify-application")
        )


class TestWithoutMyHomeAssistant(IsolatedAsyncioTestCase):

    @patch(f"{TEST_MODULE}.get_url", return_value="http://ha.local:8123")
    async def asyncSetUp(self, mock_get_url: MagicMock):
        self.mock_get_url = mock_get_url
        hass = MagicMock()
        hass.config.components = {"spotify"}
        self.result = await async_get_description_placeholders(hass)

    def test_redirect_uri_is_the_instance_callback(self):
        self.assertEqual(
            self.result["redirect_uri"],
            "http://ha.local:8123/auth/external/callback",
        )


class TestWithoutAnyKnownUrl(IsolatedAsyncioTestCase):

    @patch(f"{TEST_MODULE}.get_url", side_effect=NoURLAvailableError)
    async def asyncSetUp(self, _):
        hass = MagicMock()
        hass.config.components = {"spotify"}
        self.result = await async_get_description_placeholders(hass)

    def test_redirect_uri_falls_back_to_a_template(self):
        self.assertEqual(
            self.result["redirect_uri"],
            UNKNOWN_HOST_REDIRECT_URI,
        )
        self.assertTrue(
            UNKNOWN_HOST_REDIRECT_URI.endswith("/auth/external/callback")
        )


class TestPlaceholdersMatchTheDescription(IsolatedAsyncioTestCase):
    """A placeholder the description uses but the platform does not
    provide renders as a raw `{token}` in the dialog."""

    async def asyncSetUp(self):
        hass = MagicMock()
        hass.config.components = {"my"}
        self.result = await async_get_description_placeholders(hass)

        strings = loads(STRINGS_FILE.read_text(encoding="utf-8"))
        description = strings["application_credentials"]["description"]
        self.used = set(findall(r"\{([a-zA-Z_][a-zA-Z0-9_]*)\}", description))

    def test_same_placeholders(self):
        self.assertEqual(self.used, set(self.result))
