"""Moduel to test the is_healthy property of the ConnectionSession class"""

from unittest import TestCase

from test.sessions.connection_session import get_mocked_session


class Test_isHealthy(TestCase):

    def setUp(self):
        self.session, self.mocks = get_mocked_session()
        self.session.supervisor.is_healthy = True

    def test_returns_supervisors_status(self):
        self.assertEqual(
            self.session.is_healthy,
            self.session.supervisor.is_healthy,
        )
