"""Module to test that the translation files stay in sync.

`strings.json` is the source of truth Home Assistant validates through
hassfest, and `translations/en.json` must be a copy of it. Every other
language file must expose exactly the same keys with exactly the same
`{placeholder}` tokens: Home Assistant falls back to English for a
missing key, so a typo in a language file degrades silently, and a
placeholder that was renamed or dropped in translation renders the raw
token to the user. Nothing else in CI looks at the non-English files,
so these tests are the only gate.
"""

from json import loads
from pathlib import Path
from re import findall
from unittest import TestCase

REPOSITORY_ROOT = Path(__file__).resolve().parent.parent
INTEGRATION_DIR = REPOSITORY_ROOT / "custom_components" / "spotcast"
STRINGS_FILE = INTEGRATION_DIR / "strings.json"
TRANSLATIONS_DIR = INTEGRATION_DIR / "translations"
REFERENCE_FILE = TRANSLATIONS_DIR / "en.json"

PLACEHOLDER_PATTERN = r"\{[a-zA-Z_][a-zA-Z0-9_]*\}"


def read(path: Path) -> dict:
    """Returns the parsed content of a translation file."""
    return loads(path.read_text(encoding="utf-8"))


def flatten(content: dict, prefix: str = "") -> dict:
    """Returns the leaf strings of a translation file, keyed by their
    dotted path."""
    leaves = {}

    for key, value in content.items():
        path = f"{prefix}.{key}" if prefix else key

        if isinstance(value, dict):
            leaves.update(flatten(value, path))
        else:
            leaves[path] = value

    return leaves


def placeholders(value: str) -> set:
    """Returns the `{placeholder}` tokens found in a translated
    string."""
    return set(findall(PLACEHOLDER_PATTERN, value))


class TestTranslationsInSync(TestCase):

    def setUp(self):
        self.reference = flatten(read(REFERENCE_FILE))
        self.languages = sorted(
            path for path in TRANSLATIONS_DIR.glob("*.json")
            if path != REFERENCE_FILE
        )

    def test_english_translation_matches_strings(self):
        """hassfest validates `strings.json`; the English translation
        is what actually reaches the user. They must not diverge."""
        self.assertEqual(
            read(STRINGS_FILE),
            read(REFERENCE_FILE),
            "strings.json and translations/en.json must be identical",
        )

    def test_languages_are_present(self):
        """Guards the glob itself: an empty list would make every test
        below pass vacuously."""
        self.assertTrue(
            self.languages,
            f"no language files found in {TRANSLATIONS_DIR}",
        )

    def test_keys_match_reference(self):
        for path in self.languages:
            with self.subTest(language=path.stem):
                translation = flatten(read(path))

                missing = sorted(set(self.reference) - set(translation))
                extra = sorted(set(translation) - set(self.reference))

                self.assertFalse(
                    missing,
                    f"{path.name} is missing keys: {missing}",
                )
                self.assertFalse(
                    extra,
                    f"{path.name} has keys absent from en.json: {extra}",
                )

    def test_placeholders_match_reference(self):
        for path in self.languages:
            with self.subTest(language=path.stem):
                translation = flatten(read(path))

                for key, expected in self.reference.items():
                    if key not in translation:
                        continue

                    self.assertEqual(
                        placeholders(translation[key]),
                        placeholders(expected),
                        f"{path.name} placeholder mismatch at `{key}`",
                    )

    def test_no_empty_translations(self):
        for path in self.languages:
            with self.subTest(language=path.stem):
                blank = sorted(
                    key for key, value in flatten(read(path)).items()
                    if not value.strip()
                )

                self.assertFalse(
                    blank,
                    f"{path.name} has empty translations: {blank}",
                )
