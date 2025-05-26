"""Module to test the async_step_desktop_api"""

from unittest import IsolatedAsyncioTestCase
from unittest.mock import MagicMock, AsyncMock, patch

from custom_components.spotcast.config_flow_classes\
    .config_flow_handler import (
        SpotcastFlowHandler,
    )


class TestDesktopApiIntegration(IsolatedAsyncioTestCase):

    @patch.object(
        SpotcastFlowHandler,
        "async_external_step_done",
        new_callable=MagicMock,
    )
    @patch.object(SpotcastFlowHandler, "async_get_desktop_token")
    async def asyncSetUp(
        self,
        mock_token: AsyncMock,
        mock_done: MagicMock,
    ):

        self.mocks = {
            "token": mock_token,
            "done": mock_done,
        }

        self.mocks["token"].return_value = {"foo": "bar"}

        self.handler = SpotcastFlowHandler()
        self.handler.data = {}

        self.result = await self.handler.async_step_desktop_api({
            "access_token": "foo",
            "refresh_token": "bar",
        })

    def test_returns_external_step_done(self):
        try:
            self.mocks["done"].assert_called_with(
                next_step_id="desktop_api_done",
            )
        except AssertionError as exc:
            self.fail(exc)

        self.assertIs(self.result, self.mocks["done"].return_value)

    def test_data_set_with_desktop_token(self):
        self.assertEqual(
            self.handler.data,
            {"desktop_api": {"token": {"foo": "bar"}}},
        )
