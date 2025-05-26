"""Module to test the async_get_desktop_token function"""

from unittest import IsolatedAsyncioTestCase
from unittest.mock import MagicMock, AsyncMock, patch

from custom_components.spotcast.config_flow_classes\
    .config_flow_handler import (
        SpotcastFlowHandler,
    )


class TestFunctionRelayToImplementation(IsolatedAsyncioTestCase):

    @patch.object(
        SpotcastFlowHandler,
        "_get_pcke_impl",
        new_callable=MagicMock,
    )
    async def asyncSetUp(self, mock_impl: MagicMock,):

        self.mocks = {
            "impl": mock_impl.return_value,

        }

        self.mocks["impl"].async_resolve_external_data = AsyncMock()
        self.mocks["impl"].async_resolve_external_data.return_value = {
            "foo": "bar"
        }

        self.handler = SpotcastFlowHandler()
        self.result = await self.handler.async_get_desktop_token(
            {"bar": "foo"},
        )

    def test_external_data_passed_to_implementation(self):
        try:
            self.mocks["impl"].async_resolve_extern_data.async_called_with(
                {"bar": "foo"},
            )
        except AssertionError as exc:
            self.fail(exc)

    def test_data_returned(self):
        self.assertEqual(self.result, {"foo": "bar"})
