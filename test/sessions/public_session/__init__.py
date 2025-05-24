"""Main module for public_session class testing."""

from types import MappingProxyType
from unittest.mock import MagicMock, patch

from custom_components.spotcast.sessions.connection_session import (
    HomeAssistant,
    ConfigEntry,
    Lock,
    RetrySupervisor,
)
from custom_components.spotcast.sessions.public_session import (
    PublicSession,
    AbstractOAuth2Implementation,
)

PARENT_MODULE = "custom_components.spotcast.sessions.connection_session"
TEST_MODULE = "custom_components.spotcast.sessions.public_session"


def get_mocked_session() -> tuple[PublicSession, dict[str, MagicMock]]:

    with (
        patch(f"{PARENT_MODULE}.RetrySupervisor") as mock_supervisor,
        patch(f"{PARENT_MODULE}.Lock") as mock_lock,
    ):

        mock_lock.return_value = MagicMock(spec=Lock)
        mock_supervisor.return_value = MagicMock(spec=RetrySupervisor)

        mocks = {
            "hass": MagicMock(spec=HomeAssistant),
            "entry": MagicMock(spec=ConfigEntry),
            "implementation": MagicMock(spec=AbstractOAuth2Implementation),
            "lock": mock_lock.return_value,
            "supervisor": mock_supervisor.return_value,
        }

        mocks["entry"].data = MappingProxyType({
            "external_api": {
                "token": {
                    "access_token": "foo",
                    "expires_at": 123,
                    "refresh_token": "bar",
                    "scope": "read write",
                }
            }
        })

        session = PublicSession(
            mocks["hass"],
            mocks["entry"],
            mocks["implementation"],
        )

        return session, mocks
