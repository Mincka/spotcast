"""Module to test the async_step_desktop_api_auto step"""

from unittest import IsolatedAsyncioTestCase
from unittest.mock import MagicMock, AsyncMock, patch

from custom_components.spotcast.config_flow_classes.config_flow_handler \
    import (
        SpotcastFlowHandler,
        RelayedOAuth2ImplementationWithPcke,
    )


class TestAutoExternalStep(IsolatedAsyncioTestCase):

    @patch.object(
        SpotcastFlowHandler,
        "_get_pcke_impl",
        new_callable=MagicMock,
    )
    @patch.object(
        SpotcastFlowHandler,
        "async_external_step",
        new_callable=MagicMock,
    )
    async def asyncSetUp(self, mock_external: MagicMock, mock_pcke: MagicMock):

        mock_pcke.return_value = MagicMock(
            spec=RelayedOAuth2ImplementationWithPcke,
        )
        mock_pcke.return_value.async_generate_authorize_url = AsyncMock(
            return_value="https://foo.bar"
        )

        self.mocks = {
            "external": mock_external,
            "pcke": mock_pcke.return_value,
        }

        self.handler = SpotcastFlowHandler()
        self.handler.flow_id = "12345"

        self.result = await self.handler.async_step_desktop_api_auto()

    def test_external_step_called(self):
        try:
            self.mocks["external"].assert_called_with(
                step_id="desktop_api",
                url="https://foo.bar",
                description_placeholders={
                    "release_url": "https://github.com/Mincka/spotcast/blob/main/docs/config/spotcast_configuration.md",
                },
            )
        except AssertionError as exc:
            self.fail(exc)

        self.assertIs(self.result, self.mocks["external"].return_value)
