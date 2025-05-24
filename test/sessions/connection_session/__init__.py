"""Main module for connection_session class testing."""

from types import MappingProxyType
from unittest.mock import MagicMock, patch

from custom_components.spotcast.sessions.connection_session import (
    ConnectionSession,
    HomeAssistant,
    ConfigEntry,
    Lock,
    RetrySupervisor,
)


TEST_MODULE = "custom_components.spotcast.sessions.connection_session"


class DummySession(ConnectionSession):

    async def async_refresh_token(self):
        return {
            "access_token": "boo",
            "expires_at": 234,
            "refresh_token": "baz",
            "scope": "foo bar",
        }


def get_mocked_session() -> tuple[DummySession, dict[str, MagicMock]]:

    with (
        patch(f"{TEST_MODULE}.RetrySupervisor") as mock_supervisor,
        patch(f"{TEST_MODULE}.Lock") as mock_lock,
    ):

        mock_lock.return_value = MagicMock(spec=Lock)
        mock_supervisor.return_value = MagicMock(spec=RetrySupervisor)

        mocks = {
            "hass": MagicMock(spec=HomeAssistant),
            "entry": MagicMock(spec=ConfigEntry),
            "lock": mock_lock.return_value,
            "supervisor": mock_supervisor.return_value,
        }

        mocks["entry"].data = MappingProxyType({
            "dummy_api": {
                "token": {
                    "access_token": "foo",
                    "expires_at": 123,
                    "refresh_token": "bar",
                    "scope": "read write",
                }
            }
        })

        session = DummySession(mocks["hass"], mocks["entry"])

        return session, mocks
