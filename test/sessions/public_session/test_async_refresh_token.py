"""Module to test the constructor of the PublicSession class"""

from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock

from test.sessions.public_session import get_mocked_session


class TestCallForwarded(IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.session, self.mocks = get_mocked_session()

        self.mocks["implementation"].async_refresh_token = AsyncMock()
        self.mocks["refresh"] = (
            self.mocks["implementation"].async_refresh_token
        )
        self.mocks["refresh"].return_value = {
            "foo": "bar"
        }
        self.result = await self.session.async_refresh_token()

    def test_refresh_method_called(self):
        try:
            self.mocks["refresh"].assert_called_once()
        except AssertionError as exc:
            self.fail(exc)

    def test_data_returned(self):
        self.assertEqual(self.result, {"foo": "bar"})
