"""Module to test the async_cleanup_entities method."""

from unittest import IsolatedAsyncioTestCase
from unittest.mock import MagicMock, patch, AsyncMock

from custom_components.spotcast.sensor.spotify_current_audio_features import (
    CurrentTrackKeySensor
)
from custom_components.spotcast import (
    async_cleanup_entities,
    HomeAssistant,
    ConfigEntry,
)


class TestEntityMissing(IsolatedAsyncioTestCase):

    @patch(
        "custom_components.spotcast.entity_registry",
        new_callable=MagicMock,
    )
    async def asyncSetUp(self, mock_registry: MagicMock):

        self.mocks: dict[str, MagicMock] = {
            "hass": MagicMock(spec=HomeAssistant),
            "entry": MagicMock(spec=ConfigEntry),
            "sensor": MagicMock(spec=CurrentTrackKeySensor),
            "registry": mock_registry.async_get.return_value,
        }

        self.mocks["sensor"].entity_id = "foo"
        self.mocks["registry"].async_get.return_value = None

        self.result = await async_cleanup_entities(
            self.mocks["hass"],
            self.mocks["entry"],
            [self.mocks["sensor"]],
        )

    def test_result_returned(self):
        self.assertEqual(self.result, 0)

    def test_entity_not_removed(self):
        self.mocks["registry"].async_remove.assert_not_called()


class TestEntityFromDifferentConfig(IsolatedAsyncioTestCase):

    @patch(
        "custom_components.spotcast.entity_registry",
        new_callable=MagicMock,
    )
    async def asyncSetUp(self, mock_registry: MagicMock):

        self.mocks: dict[str, MagicMock] = {
            "hass": MagicMock(spec=HomeAssistant),
            "entry": MagicMock(spec=ConfigEntry),
            "sensor": MagicMock(spec=CurrentTrackKeySensor),
            "registry": mock_registry.async_get.return_value,
        }

        self.mocks["sensor"].entity_id = "foo"
        self.mocks["entry"].entry_id = "baz"
        self.mocks["registry"].async_get.return_value.config_entry_id = "bar"

        self.result = await async_cleanup_entities(
            self.mocks["hass"],
            self.mocks["entry"],
            [self.mocks["sensor"]],
        )

    def test_result_returned(self):
        self.assertEqual(self.result, 0)

    def test_entity_not_removed(self):
        self.mocks["registry"].async_remove.assert_not_called()


class TestDeprecatedEntry(IsolatedAsyncioTestCase):

    @patch(
        "custom_components.spotcast.entity_registry",
        new_callable=MagicMock,
    )
    async def asyncSetUp(self, mock_registry: MagicMock):

        self.mocks: dict[str, MagicMock] = {
            "hass": MagicMock(spec=HomeAssistant),
            "entry": MagicMock(spec=ConfigEntry),
            "sensor": MagicMock(spec=CurrentTrackKeySensor),
            "registry": mock_registry.async_get.return_value,
        }

        self.mocks["sensor"].entity_id = "foo"
        self.mocks["entry"].entry_id = "bar"
        self.mocks["registry"].async_get.return_value.config_entry_id = "bar"
        self.mocks["registry"].async_get.return_value.entity_id = "foo"

        self.result = await async_cleanup_entities(
            self.mocks["hass"],
            self.mocks["entry"],
            [self.mocks["sensor"]],
        )

    def test_result_returned(self):
        self.assertEqual(self.result, 1)

    def test_entity_not_removed(self):
        self.mocks["registry"].async_remove.assert_called_with("foo")
