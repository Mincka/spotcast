"""Main module for private_session class testing."""

from types import MappingProxyType
from unittest.mock import MagicMock, patch

from custom_components.spotcast.sessions.connection_session import (
    HomeAssistant,
    ConfigEntry,
    RetrySupervisor,
)
from custom_components.spotcast.sessions.private_session import (
    PrivateSession,
)

PARENT_MODULE = "custom_components.spotcast.sessions.connection_session"
TEST_MODULE = "custom_components.spotcast.sessions.private_session"


def get_mocked_session() -> tuple[PrivateSession, dict[str, MagicMock]]:

    with patch(f"{PARENT_MODULE}.RetrySupervisor") as mock_supervisor:

        mock_supervisor.return_value = MagicMock(spec=RetrySupervisor)
        mock_supervisor.return_value.SUPERVISED_EXCEPTIONS = (
            RetrySupervisor.SUPERVISED_EXCEPTIONS
        )

        mocks = {
            "hass": MagicMock(spec=HomeAssistant),
            "entry": MagicMock(spec=ConfigEntry),
            "supervisor": mock_supervisor.return_value,
        }

        mocks["entry"].data = MappingProxyType({
            "internal_api": {
                "sp_dc": "foo",
                "sp_key": "bar",
            }
        })

        session = PrivateSession(mocks["hass"], mocks["entry"])

        return session, mocks
