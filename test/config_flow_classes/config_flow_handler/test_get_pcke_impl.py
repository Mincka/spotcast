"""Module to test the get_pcke_impl function."""

from unittest import TestCase
from unittest.mock import MagicMock, patch

from homeassistant.core import HomeAssistant

from custom_components.spotcast.config_flow_classes\
    .config_flow_handler import (
        SpotcastFlowHandler,
        RelayedOAuth2ImplementationWithPcke,
        SPOTIFY_CLIENT_ID,
        SPOTIFY_AUTHORIZE_URL,
        SPOTIFY_TOKEN_URL,
    )

from test.config_flow_classes.config_flow_handler import TEST_MODULE


class TestImplementationExist(TestCase):

    @patch(f"{TEST_MODULE}.RelayedOAuth2ImplementationWithPcke")
    def setUp(self, mock_impl_init: MagicMock):

        self.mocks = {
            "hass": MagicMock(spec=HomeAssistant),
            "impl": MagicMock(spec=RelayedOAuth2ImplementationWithPcke),
            "impl_init": mock_impl_init,
        }

        self.handler = SpotcastFlowHandler()
        self.handler._pcke_impl = self.mocks["impl"]

        self.result = self.handler._get_pcke_impl()

    def test_impl_constructor_not_called(self):
        try:
            self.mocks["impl_init"].assert_not_called()
        except AssertionError as exc:
            self.fail(exc)

    def test_same_implementation_returned(self):
        self.assertIs(self.result, self.mocks["impl"])


class TestImplementationAbsent(TestCase):

    @patch(f"{TEST_MODULE}.RelayedOAuth2ImplementationWithPcke")
    def setUp(self, mock_impl_init: MagicMock):

        self.mocks = {
            "hass": MagicMock(spec=HomeAssistant),
            "impl": MagicMock(spec=RelayedOAuth2ImplementationWithPcke),
            "impl_init": mock_impl_init,
        }

        self.handler = SpotcastFlowHandler()
        self.handler.hass = self.mocks["hass"]

        self.result = self.handler._get_pcke_impl()

    def test_impl_constructor_not_called(self):
        try:
            self.mocks["impl_init"].assert_called_with(
                hass=self.mocks["hass"],
                domain="spotcast-desktop",
                client_id=SPOTIFY_CLIENT_ID,
                authorize_url=SPOTIFY_AUTHORIZE_URL,
                token_url=SPOTIFY_TOKEN_URL,
            )
        except AssertionError as exc:
            self.fail(exc)
