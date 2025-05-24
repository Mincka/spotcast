"""Moduel to test the async_ensure_token_value property of the
ConnectionSession class"""

from time import time
from unittest import IsolatedAsyncioTestCase
from unittest.mock import MagicMock

from custom_components.spotcast.sessions.retry_supervisor import (
    RetrySupervisor,
)
from custom_components.spotcast.sessions.connection_session import (
    UpstreamServerNotready,
    TokenRefreshError,
    ClientResponseError,
)

from test.sessions.connection_session import get_mocked_session


class TestSuccessfullRefresh(IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.session, self.mocks = get_mocked_session()
        self.mocks["supervisor"].is_ready = True
        self.mocks["supervisor"].is_healthy = False
        self.result = await self.session.async_ensure_token_valid()

    def test_returns_true(self):
        self.assertTrue(self.result)

    def test_token_updated(self):
        self.assertEqual(self.session.access_token, "boo")
        self.assertEqual(self.session.refresh_token, "baz")
        self.assertEqual(self.session.expires_at, 234)

    def test_supervisor_resetted_to_healthy(self):
        self.assertTrue(self.session.supervisor.is_healthy)


class TestValidToken(IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.session, self.mocks = get_mocked_session()
        self.mocks["supervisor"].is_ready = True
        self.session.token["expires_at"] = time() + 9999
        self.result = await self.session.async_ensure_token_valid()

    def test_returns_true(self):
        self.assertFalse(self.result)


class TestSupervisorNotReady(IsolatedAsyncioTestCase):

    async def test_error_raised(self):
        self.session, self.mocks = get_mocked_session()
        self.mocks["supervisor"].is_ready = False

        with self.assertRaises(UpstreamServerNotready):
            await self.session.async_ensure_token_valid()


class TestSupervisedErrorRaised(IsolatedAsyncioTestCase):

    @staticmethod
    async def async_dummy_refresh():
        raise RetrySupervisor.SUPERVISED_EXCEPTIONS[0]()

    async def test_error_raised(self):
        self.session, self.mocks = get_mocked_session()
        self.mocks["supervisor"].is_ready = True
        self.mocks["supervisor"].is_healthy = True
        self.mocks["supervisor"].SUPERVISED_EXCEPTIONS = (
            RetrySupervisor.SUPERVISED_EXCEPTIONS
        )

        self.session.async_refresh_token = self.async_dummy_refresh

        with self.assertRaises(UpstreamServerNotready):
            await self.session.async_ensure_token_valid()

        self.assertFalse(self.session.is_healthy)


class TestTokenRefreshError(IsolatedAsyncioTestCase):

    @staticmethod
    async def async_dummy_refresh():
        raise ClientResponseError(MagicMock(), MagicMock(), status=400)

    async def test_error_raised(self):
        self.session, self.mocks = get_mocked_session()
        self.mocks["supervisor"].is_ready = True
        self.mocks["supervisor"].is_healthy = True
        self.mocks["supervisor"].SUPERVISED_EXCEPTIONS = (
            RetrySupervisor.SUPERVISED_EXCEPTIONS
        )

        self.session.async_refresh_token = self.async_dummy_refresh

        with self.assertRaises(TokenRefreshError):
            await self.session.async_ensure_token_valid()


class TestUnknownClientError(IsolatedAsyncioTestCase):

    @staticmethod
    async def async_dummy_refresh():
        raise ClientResponseError(MagicMock(), MagicMock(), status=418)

    async def test_error_raised(self):
        self.session, self.mocks = get_mocked_session()
        self.mocks["supervisor"].is_ready = True
        self.mocks["supervisor"].is_healthy = True
        self.mocks["supervisor"].SUPERVISED_EXCEPTIONS = (
            RetrySupervisor.SUPERVISED_EXCEPTIONS
        )

        self.session.async_refresh_token = self.async_dummy_refresh

        with self.assertRaises(ClientResponseError):
            await self.session.async_ensure_token_valid()
