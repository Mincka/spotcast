"""Module to test the async_step_desktop_api"""

from unittest import IsolatedAsyncioTestCase
from unittest.mock import MagicMock, AsyncMock, patch

from custom_components.spotcast.config_flow_classes.config_flow_handler import (
    SpotcastFlowHandler,
)

from test.config_flow_classes.config_flow_handler import TEST_MODULE


class TestDesktopApiIntegration(IsolatedAsyncioTestCase):

    @patch.object(SpotcastFlowHandler, "async_oauth_create_entry")
    async def asyncSetUp(self, mock_create: MagicMock):

        self.mocks = {
            "create": mock_create,
        }

        self.handler = SpotcastFlowHandler()

        await self.handler.async_step_desktop_api({
            "access_token": "foo",
            "refresh_token": "bar",
        })

    def test_create_entry_args(self):
        try:
            self.mocks["create"].assert_called_with({
                "desktop_api": {
                    "token": {
                        "access_token": "foo",
                        "token_type": "bearer",
                        "expires_at": 0,
                        "refresh_token": "bar",
                        "scope": "",
                    }
                },
                "name": "",
                "version": "2.1",
            })
        except AssertionError as exc:
            self.fail(exc)
