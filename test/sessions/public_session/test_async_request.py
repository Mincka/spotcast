"""Module to test the async_request of the PublicSession class"""

from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, patch

from custom_components.spotcast.sessions.public_session import (
    PublicSession,
)

from test.sessions.public_session import get_mocked_session, TEST_MODULE


class Test(IsolatedAsyncioTestCase):

    @patch(f"{TEST_MODULE}.async_oauth2_request")
    @patch.object(PublicSession, "async_ensure_token_valid")
    async def asyncSetUp(
            self,
            mock_ensure: AsyncMock,
            mock_request: AsyncMock,
    ):
        self.session, self.mocks = get_mocked_session()

        self.mocks["implementation"].async_refresh_token = AsyncMock()
        self.mocks["ensure"] = mock_ensure
        self.mocks["request"] = mock_request
        self.mocks["refresh"] = (
            self.mocks["implementation"].async_refresh_token
        )
        self.mocks["refresh"].return_value = {
            "foo": "bar"
        }
        self.result = await self.session.async_request(
            "POST",
            "google.ca",
            foo="bar",
        )

    def test_ensure_token_valid_called(self):
        try:
            self.mocks["ensure"].assert_called_once()
        except AssertionError as exc:
            self.fail(exc)

    def test_request_forwarded(self):
        try:
            self.mocks["request"].assert_called_with(
                self.mocks["hass"],
                self.session.token,
                "POST",
                "google.ca",
                foo="bar",
            )
        except AssertionError as exc:
            self.fail(exc)
