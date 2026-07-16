"""Module to test that the option definitions stay in sync.

Entry options are defined in four places that must agree:
`const.DEFAULT_OPTIONS`, the options flow defaults, the options flow
schema and the `OptionData` typed dict. A key added to one but not the
others has already caused a setup crash once (v6.5.3-beta.2 splatted
an option the account constructor did not know). These tests fail the
build when the definitions drift.
"""

from unittest import TestCase

from custom_components.spotcast.const import DEFAULT_OPTIONS
from custom_components.spotcast.config_flow_classes.options_flow_handler \
    import (
        DEFAULT_OPTIONS as FLOW_DEFAULT_OPTIONS,
        SpotcastOptionsFlowHandler,
    )
from custom_components.spotcast.entry_data import OptionData


class TestOptionDefinitionsInSync(TestCase):

    def test_flow_defaults_match_const_defaults(self):
        self.assertEqual(dict(FLOW_DEFAULT_OPTIONS), dict(DEFAULT_OPTIONS))

    def test_option_data_fields_match_defaults(self):
        self.assertEqual(
            set(OptionData.__annotations__),
            set(DEFAULT_OPTIONS),
        )

    def test_flow_schema_covers_all_options(self):
        """The options form must expose every option. `is_default` is
        exposed through the `set_default` action field."""
        schema = SpotcastOptionsFlowHandler.SCHEMAS["init"].schema
        schema_keys = {str(key) for key in schema}

        expected = (set(DEFAULT_OPTIONS) - {"is_default"}) | {"set_default"}

        self.assertEqual(schema_keys, expected)
