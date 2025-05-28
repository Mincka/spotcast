"""Manager for retry behavior after internal server errors.

Classes:
    - RetrySupervisor
"""

from time import time
from logging import getLogger, ERROR, DEBUG
from urllib3.exceptions import ReadTimeoutError
from aiohttp.client_exceptions import ClientOSError, ClientConnectorError

from requests.exceptions import ReadTimeout, ConnectionError

from custom_components.spotcast.sessions.exceptions import (
    InternalServerError,
    UpstreamServerNotready,
)

LOGGER = getLogger(__name__)


class RetrySupervisor:
    """Manager for retries to the upstreams server in case of errors."""

    SUPERVISED_EXCEPTIONS = (
        ReadTimeout,
        ReadTimeoutError,
        InternalServerError,
        UpstreamServerNotready,
        ClientConnectorError,
        ClientOSError,
        ConnectionError,
    )

    def __init__(self) -> None:
        """Manager for retries to the upstreams server in case of errors."""
        self._is_healthy = True
        self._next_retry = 0.0
        self.communication_counter = 0

    @property
    def is_healthy(self) -> bool:
        """Returns the health state of the session."""
        return self._is_healthy

    @is_healthy.setter
    def is_healthy(self, value: bool) -> None:
        """Sets the health state of the session."""
        self._is_healthy = value

        if self._is_healthy:
            self._next_retry = 0
            self.communication_counter = 0
        else:
            self.failed()

    @property
    def next_retry(self) -> float:
        """Return the time stamp when to try again."""
        return self._next_retry

    @property
    def is_ready(self) -> bool:
        """Returns True if connection can be reattempted."""
        return time() > self.next_retry

    def failed(self) -> None:
        """Updates the next_retry time because the connection failed."""
        self._next_retry = time() + 30

    def log_message(self, msg: str) -> None:
        """Logs a message to the logger.

        Sends as an Error level on the first and debug on subsequent messages
        """
        level = DEBUG if self.communication_counter > 0 else ERROR
        LOGGER.log(level, msg)
        self.communication_counter += 1
