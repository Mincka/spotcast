"""Module to test the get_best_candidate_function"""

from unittest import TestCase
from unittest.mock import MagicMock

from custom_components.spotcast.services.play_from_search import (
    get_best_candidate
)


class TestCandidateBasedOnFit(TestCase):

    def setUp(self):

        self.search_result = {
            "artists": [
                {"name": "foo"}
            ],
            "albums": [
                {"name": "bar"}
            ]
        }

        self.result = get_best_candidate("foo", self.search_result)

    def test_proper_result_selected(self):
        self.assertEqual(self.result, "artists")


class TestCandidateBasedOnType(TestCase):

    def setUp(self):

        self.search_result = {
            "artists": [
                {"name": "foo"}
            ],
            "albums": [
                {"name": "foo"}
            ],
            "tracks": [
                {"name": "foo"}
            ]
        }

        self.result = get_best_candidate("foo", self.search_result)

    def test_proper_result_selected(self):
        self.assertEqual(self.result, "artists")


class TestNoResults(TestCase):

    def test_empty_search_result_returns_none(self):
        self.assertIsNone(get_best_candidate("foo", {}))

    def test_all_empty_categories_returns_none(self):
        self.assertIsNone(
            get_best_candidate("foo", {"artists": [], "albums": []})
        )
