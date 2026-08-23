"""Integration wide backoff for the Spotify Web API rate limit.

Spotify enforces its rate limit per client id, not per account. Every
account configured in spotcast shares the same client id, so a 429
received by one account applies to all of them. The guard keeps a
single `retry_at` timestamp that every spotipy client consults before
sending a request, so the other accounts stop hammering the API (and
extending the penalty) until the window expires.

Classes:
    - RateLimitGuard

Constants:
    - DEFAULT_RETRY_AFTER(int): fallback window, in seconds, when the
        429 carries no usable `Retry-After` header
    - RATE_LIMIT_GUARD(RateLimitGuard): the shared guard instance
"""

from datetime import datetime
from logging import getLogger, DEBUG, WARNING
from threading import Lock
from time import time

from custom_components.spotcast.spotify.exceptions import RateLimitedError

LOGGER = getLogger(__name__)

DEFAULT_RETRY_AFTER = 30


class RateLimitGuard:
    """Shared state for an active Spotify rate limit.

    Thread safe: spotipy calls run in Home Assistant executor threads.

    Properties:
        - retry_at(float): epoch timestamp when calls may resume. 0
            when no rate limit is active
        - is_limited(bool): True while a rate limit is active
        - seconds_remaining(int): seconds until the limit expires

    Methods:
        - register
        - check
        - clear
    """

    def __init__(self):
        """Shared state for an active Spotify rate limit."""
        self._lock = Lock()
        self._retry_at = 0.0
        self._announced = False

    @property
    def retry_at(self) -> float:
        """Returns the epoch timestamp when calls may resume."""
        return self._retry_at

    @property
    def is_limited(self) -> bool:
        """Returns True while a rate limit is active."""
        return time() < self._retry_at

    @property
    def seconds_remaining(self) -> int:
        """Returns the number of seconds until the limit expires."""
        return max(0, int(self._retry_at - time()) + 1)

    @property
    def resume_time(self) -> str:
        """Returns the local time at which calls resume, for messages."""
        return datetime.fromtimestamp(self._retry_at).strftime("%H:%M:%S")

    def register(self, retry_after: str | int | None) -> float:
        """Records a 429 received from Spotify.

        Args:
            - retry_after(str | int | None): the value of the
                `Retry-After` header of the 429 response, in seconds.
                Falls back to `DEFAULT_RETRY_AFTER` when missing or
                not a number.

        Returns:
            - float: the epoch timestamp when calls may resume
        """
        seconds = self._parse_retry_after(retry_after)

        with self._lock:
            retry_at = time() + seconds

            # a longer window already registered wins: the api does
            # not shorten a penalty because we asked again
            if retry_at > self._retry_at:
                self._retry_at = retry_at

            level = DEBUG if self._announced else WARNING
            self._announced = True

        LOGGER.log(
            level,
            "Spotify rate limit reached for this client id. Pausing all "
            "Spotify API calls for %d s (until %s)",
            self.seconds_remaining,
            self.resume_time,
        )

        return self._retry_at

    def check(self):
        """Raises if a rate limit is currently active.

        Raises:
            - RateLimitedError: raised while the rate limit is active
        """
        with self._lock:
            if time() < self._retry_at:
                raise RateLimitedError(self._retry_at)

            # the window expired: the next 429 is a new event worth a
            # warning again
            self._announced = False

    def clear(self):
        """Clears the active rate limit."""
        with self._lock:
            self._retry_at = 0.0
            self._announced = False

    @staticmethod
    def _parse_retry_after(retry_after: str | int | None) -> int:
        """Returns the number of seconds to wait from a `Retry-After`
        value, falling back to the default when unusable."""
        try:
            seconds = int(str(retry_after).strip())
        except (TypeError, ValueError):
            LOGGER.debug(
                "Unusable Retry-After value `%s`. Using the default of "
                "%d s",
                retry_after,
                DEFAULT_RETRY_AFTER,
            )
            return DEFAULT_RETRY_AFTER

        return max(0, seconds)


RATE_LIMIT_GUARD = RateLimitGuard()
