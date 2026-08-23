"""Module to test the shared rate limit guard"""

from unittest import TestCase
from unittest.mock import patch

from custom_components.spotcast.spotify.rate_limit import (
    RateLimitGuard,
    RateLimitedError,
    DEFAULT_RETRY_AFTER,
)

TEST_MODULE = "custom_components.spotcast.spotify.rate_limit"


class TestRegisterWithHeader(TestCase):

    @patch(f"{TEST_MODULE}.time", return_value=1000.0)
    def setUp(self, mock_time):
        self.guard = RateLimitGuard()
        self.result = self.guard.register("2484")

    def test_retry_at_set_from_header(self):
        self.assertEqual(self.guard.retry_at, 3484.0)

    def test_retry_at_returned(self):
        self.assertEqual(self.result, 3484.0)

    @patch(f"{TEST_MODULE}.time", return_value=1000.0)
    def test_guard_is_limited(self, mock_time):
        self.assertTrue(self.guard.is_limited)

    @patch(f"{TEST_MODULE}.time", return_value=1000.0)
    def test_seconds_remaining(self, mock_time):
        self.assertEqual(self.guard.seconds_remaining, 2485)


class TestRegisterWithoutHeader(TestCase):

    @patch(f"{TEST_MODULE}.time", return_value=1000.0)
    def test_default_window_used(self, mock_time):
        guard = RateLimitGuard()
        guard.register(None)
        self.assertEqual(guard.retry_at, 1000.0 + DEFAULT_RETRY_AFTER)

    @patch(f"{TEST_MODULE}.time", return_value=1000.0)
    def test_garbage_header_uses_default(self, mock_time):
        guard = RateLimitGuard()
        guard.register("Wed, 21 Oct 2015 07:28:00 GMT")
        self.assertEqual(guard.retry_at, 1000.0 + DEFAULT_RETRY_AFTER)

    @patch(f"{TEST_MODULE}.time", return_value=1000.0)
    def test_negative_header_clamped(self, mock_time):
        guard = RateLimitGuard()
        guard.register("-5")
        self.assertEqual(guard.retry_at, 1000.0)


class TestRegisterNeverShortens(TestCase):

    @patch(f"{TEST_MODULE}.time", return_value=1000.0)
    def test_later_window_kept(self, mock_time):
        guard = RateLimitGuard()
        guard.register("600")
        guard.register("60")
        self.assertEqual(guard.retry_at, 1600.0)

    @patch(f"{TEST_MODULE}.time", return_value=1000.0)
    def test_longer_window_extends(self, mock_time):
        guard = RateLimitGuard()
        guard.register("60")
        guard.register("600")
        self.assertEqual(guard.retry_at, 1600.0)


class TestCheck(TestCase):

    def setUp(self):
        self.guard = RateLimitGuard()

    @patch(f"{TEST_MODULE}.time", return_value=1000.0)
    def test_passes_when_not_limited(self, mock_time):
        try:
            self.guard.check()
        except RateLimitedError:
            self.fail()

    @patch(f"{TEST_MODULE}.time", return_value=1000.0)
    def test_raises_while_limited(self, mock_time):
        self.guard.register("60")

        with self.assertRaises(RateLimitedError) as ctx:
            self.guard.check()

        self.assertEqual(ctx.exception.retry_at, 1060.0)
        self.assertEqual(ctx.exception.http_status, 429)

    @patch(f"{TEST_MODULE}.time")
    def test_passes_after_window(self, mock_time):
        mock_time.return_value = 1000.0
        self.guard.register("60")

        mock_time.return_value = 1061.0

        try:
            self.guard.check()
        except RateLimitedError:
            self.fail()

        self.assertFalse(self.guard.is_limited)

    @patch(f"{TEST_MODULE}.time", return_value=1000.0)
    def test_clear_lifts_the_limit(self, mock_time):
        self.guard.register("60")
        self.guard.clear()

        self.assertFalse(self.guard.is_limited)
        self.assertEqual(self.guard.retry_at, 0.0)


class TestLogging(TestCase):

    @patch(f"{TEST_MODULE}.time", return_value=1000.0)
    def test_warning_only_once_per_window(self, mock_time):
        guard = RateLimitGuard()

        with self.assertLogs(TEST_MODULE, level="DEBUG") as logs:
            guard.register("60")
            guard.register("60")
            guard.register("60")

        levels = [record.levelname for record in logs.records]
        self.assertEqual(levels.count("WARNING"), 1)
        self.assertEqual(levels.count("DEBUG"), 2)

    @patch(f"{TEST_MODULE}.time")
    def test_warning_again_after_window_expired(self, mock_time):
        guard = RateLimitGuard()

        mock_time.return_value = 1000.0
        guard.register("60")

        mock_time.return_value = 1061.0
        guard.check()

        with self.assertLogs(TEST_MODULE, level="WARNING") as logs:
            guard.register("60")

        self.assertEqual(len(logs.records), 1)
