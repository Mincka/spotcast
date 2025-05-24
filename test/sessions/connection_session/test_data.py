"""Moduel to test the data property of the ConnectionSession class"""

from unittest import TestCase

from test.sessions.connection_session import get_mocked_session


class TestDataGetter(TestCase):

    def setUp(self):
        self.session, self.mocks = get_mocked_session()

    def test_data_value(self):
        self.assertEqual(
            self.session.data,
            {
                "token": {
                    "access_token": "foo",
                    "expires_at": 123,
                    "refresh_token": "bar",
                    "scope": "read write",
                }
            }
        )


class TestDataSetter(TestCase):

    def setUp(self):
        self.session, self.mocks = get_mocked_session()
        self.new_data = {
            "token": {
                "access_token": "baz",
                "expires_at": 123,
                "refresh_token": "bar",
                "scope": "read write",
            }
        }

        self.session.data = self.new_data

    def test_data_value(self):
        self.assertEqual(self.session.data, self.new_data)
