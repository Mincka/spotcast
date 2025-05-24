"""Module to test the constructor of the ConnectionSession class."""

from unittest import TestCase

from custom_components.spotcast.sessions.connection_session import (
    Lock,
    RetrySupervisor,
)

from test.sessions.connection_session import get_mocked_session


class DataRetention(TestCase):

    def setUp(self):

        self.session, self.mocks = get_mocked_session()

    def test_data_is_copy_of_entry_data(self):
        self.assertIsNot(self.session._entry_data, self.session.entry.data)
        self.assertEqual(self.session._entry_data, self.session.entry.data)

    def test_hass_retention(self):
        self.assertIs(self.session.hass, self.mocks["hass"])

    def test_entry_retention(self):
        self.assertIs(self.session.entry, self.mocks["entry"])

    def test_lock_created(self):
        self.assertIsInstance(self.session._token_lock, Lock)

    def test_retry_supervisor_created(self):
        self.assertIsInstance(self.session.supervisor, RetrySupervisor)
