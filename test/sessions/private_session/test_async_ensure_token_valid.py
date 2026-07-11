"""Module to test the async_ensure_token_valid method of the
PrivateSession"""

from time import time
from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock

from custom_components.spotcast.sessions.exceptions import (
    InternalServerError,
    UpstreamServerNotready,
)

from test.sessions.private_session import get_mocked_session


class TestSupervisorNotReady(IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.session, self.mocks = get_mocked_session()
        self.mocks["supervisor"].is_ready = False

    async def test_raises_upstream_server_not_ready(self):
        with self.assertRaises(UpstreamServerNotready):
            await self.session.async_ensure_token_valid()


class TestTokenStillValid(IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.session, self.mocks = get_mocked_session()
        self.mocks["supervisor"].is_ready = True
        self.session._expires_at = time() + 3600
        self.session.async_refresh_token = AsyncMock()
        await self.session.async_ensure_token_valid()

    async def test_no_refresh_attempted(self):
        try:
            self.session.async_refresh_token.assert_not_called()
        except AssertionError as exc:
            self.fail(exc)


class TestExpiredTokenRefreshed(IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.session, self.mocks = get_mocked_session()
        self.mocks["supervisor"].is_ready = True
        self.session._expires_at = 0
        self.session.async_refresh_token = AsyncMock()
        await self.session.async_ensure_token_valid()

    async def test_refresh_attempted(self):
        try:
            self.session.async_refresh_token.assert_called_once()
        except AssertionError as exc:
            self.fail(exc)

    async def test_supervisor_marked_healthy(self):
        self.assertTrue(self.mocks["supervisor"]._is_healthy)


class TestSupervisedFailure(IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.session, self.mocks = get_mocked_session()
        self.mocks["supervisor"].is_ready = True
        self.session._expires_at = 0
        self.session.async_refresh_token = AsyncMock(
            side_effect=InternalServerError(503, "spotify is down")
        )

    async def test_raises_upstream_server_not_ready(self):
        with self.assertRaises(UpstreamServerNotready):
            await self.session.async_ensure_token_valid()

    async def test_supervisor_marked_unhealthy(self):
        with self.assertRaises(UpstreamServerNotready):
            await self.session.async_ensure_token_valid()

        self.assertFalse(self.mocks["supervisor"]._is_healthy)
