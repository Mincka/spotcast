"""Moduel to test the token property of the ConnectionSession class"""

from unittest import TestCase

from test.sessions.connection_session import get_mocked_session


class TestTokenGetter(TestCase):

    def setUp(self):
        self.session, self.mocks = get_mocked_session()

    def test_data_value(self):
        self.assertEqual(
            self.session.token,
            {
                "access_token": "foo",
                "expires_at": 123,
                "refresh_token": "bar",
                "scope": "read write",
            }
        )


class TestDataSetter(TestCase):

    def setUp(self):
        self.session, self.mocks = get_mocked_session()
        self.new_data = {
            "access_token": "baz",
            "expires_at": 123,
            "refresh_token": "bar",
            "scope": "read write",
        }

        self.session.token = self.new_data

    def test_data_value(self):
        self.assertEqual(self.session.token, self.new_data)
