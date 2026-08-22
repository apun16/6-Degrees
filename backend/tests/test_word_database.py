"""Tests for the vocabulary data file and WordDatabase loader.

The word list used to live as a Python literal inside word_database.py, where 14
missing trailing commas silently concatenated adjacent entries -- producing junk
words like 'replicateefficient' and 'raincoatfurniture' while dropping 21 real
words ('love', 'ocean', 'red', 'animal', ...) from the game entirely. The list now
lives in data/words.json; these tests keep that class of corruption from returning.
"""
import json
import tempfile
from pathlib import Path

import pytest

from app.word_database import DEFAULT_WORD_FILE, WordDatabase


# Compound words that legitimately decompose into two other vocabulary entries.
# Anything NOT in this set that decomposes is treated as corruption. Adding an
# entry here is a deliberate "yes, I looked at this and it is a real word" signal.
KNOWN_COMPOUNDS = {
    'birthday', 'butterfly', 'carpet', 'earphone', 'earring', 'firetruck',
    'football', 'footnote', 'framework', 'headphone', 'homework', 'keyboard',
    'microphone', 'microwave', 'necklace', 'notebook', 'pancake', 'raincoat',
    'runtime', 'sunday', 'sunflower', 'sunglasses', 'weekend',
    # Pre-existing authoring artifacts: these should arguably be two words each
    # ('half brother', 'table tennis'), but they predate the comma bug and are
    # allowlisted here rather than silently changed.
    'halfbrother', 'halfsister', 'tabletennis',
}

# Words the comma bug removed from the game; all must be present.
RESTORED_WORDS = [
    'animal', 'coldness', 'cough', 'efficient', 'furniture', 'game', 'glaze',
    'love', 'ocean', 'particle', 'proud', 'raincoat', 'red', 'rehearsal',
    'replicate', 'run', 'science', 'sow', 'thirst', 'training', 'wealth',
]

# The exact junk the comma bug produced; none may ever reappear.
JUNK_WORDS = [
    'coldnesskey', 'coughgame', 'fawngeography', 'glazelove', 'letterapple',
    'particleanimal', 'raincoatfurniture', 'rehearsalred', 'replicateefficient',
    'sowtime', 'staticproud', 'thirstrun', 'trainingscience', 'wealthocean',
]


@pytest.fixture(scope='module')
def word_data():
    return json.loads(DEFAULT_WORD_FILE.read_text(encoding='utf-8'))


@pytest.fixture(scope='module')
def db():
    return WordDatabase()


class TestWordFileIntegrity:
    def test_default_word_file_exists(self):
        assert DEFAULT_WORD_FILE.exists(), f"missing vocabulary file: {DEFAULT_WORD_FILE}"

    def test_flat_list_matches_categories(self, word_data):
        from_categories = {w for ws in word_data['categories'].values() for w in ws}
        assert set(word_data['words']) == from_categories

    def test_no_duplicates_across_categories(self, word_data):
        seen, dupes = set(), []
        for members in word_data['categories'].values():
            for w in members:
                (dupes.append(w) if w in seen else seen.add(w))
        assert dupes == [], f"words listed in more than one category: {sorted(set(dupes))}"

    def test_entries_are_normalized(self, word_data):
        """Lowercase, trimmed, letters only -- internal hyphens allowed ('t-shirt')."""
        def ok(w):
            return (w and w == w.strip().lower()
                    and w[0].isalpha() and w[-1].isalpha()
                    and all(c.isalpha() or c == '-' for c in w))

        bad = [w for w in word_data['words'] if not ok(w)]
        assert bad == [], f"malformed vocabulary entries: {bad}"

    def test_no_concatenation_artifacts(self, word_data):
        """A word that is exactly two other vocabulary words joined is the
        signature of a dropped comma. Real compounds are allowlisted above."""
        words = set(word_data['words'])
        suspects = []
        for w in words:
            if w in KNOWN_COMPOUNDS:
                continue
            for i in range(3, len(w) - 2):
                if w[:i] in words and w[i:] in words:
                    suspects.append(f"{w} = {w[:i]} + {w[i:]}")
                    break
        assert suspects == [], (
            "possible dropped-comma corruption; if these are real compound words, "
            f"add them to KNOWN_COMPOUNDS: {suspects}"
        )


class TestCommaBugRegression:
    @pytest.mark.parametrize('word', RESTORED_WORDS)
    def test_restored_word_present(self, db, word):
        assert db.word_exists(word)

    @pytest.mark.parametrize('word', JUNK_WORDS)
    def test_junk_word_absent(self, db, word):
        assert not db.word_exists(word)

    def test_hardcoded_fallback_pairs_all_exist(self, db):
        """game_service.get_random_word_pair falls back to these pairs; every
        word in them must actually be in the vocabulary or the fallback is dead."""
        pairs = [
            ('cat', 'dog'), ('cat', 'animal'), ('dog', 'pet'), ('bird', 'animal'),
            ('tree', 'plant'), ('flower', 'plant'), ('car', 'vehicle'),
            ('house', 'building'), ('book', 'read'), ('happy', 'joy'),
            ('sad', 'emotion'), ('red', 'color'),
        ]
        missing = sorted({w for pair in pairs for w in pair if not db.word_exists(w)})
        assert missing == [], f"fallback pairs reference missing words: {missing}"


class TestWordDatabase:
    def test_loads_default_file(self, db):
        assert db.get_word_count() > 1500
        assert len(db.get_categories()) == 29

    def test_lookup_is_case_and_whitespace_insensitive(self, db):
        assert db.word_exists('  OCEAN ')
        assert db.word_exists('Love')

    def test_unknown_word_rejected(self, db):
        assert not db.word_exists('zzzznotaword')

    def test_get_all_words_is_sorted(self, db):
        words = db.get_all_words()
        assert words == sorted(words)

    def test_round_trip_preserves_words_and_categories(self, db, tmp_path):
        path = tmp_path / 'roundtrip.json'
        db.save_to_file(str(path))
        reloaded = WordDatabase(str(path))
        assert reloaded.words == db.words
        assert reloaded.categories == db.categories

    def test_accepts_bare_list_format(self, tmp_path):
        path = tmp_path / 'bare.json'
        path.write_text(json.dumps(['Alpha', ' beta ', 'GAMMA']))
        loaded = WordDatabase(str(path))
        assert loaded.words == {'alpha', 'beta', 'gamma'}
        assert loaded.get_categories() == {}

    @pytest.mark.parametrize('payload', ['{"nope": 1}', '{"words": []}', '[]'])
    def test_invalid_file_raises_rather_than_falling_back(self, tmp_path, payload):
        """A missing or malformed word file must fail loudly. Silently falling
        back to a stub vocabulary would ship a broken game that looks healthy."""
        path = tmp_path / 'bad.json'
        path.write_text(payload)
        with pytest.raises(ValueError):
            WordDatabase(str(path))

    def test_missing_file_raises(self, tmp_path):
        with pytest.raises(OSError):
            WordDatabase(str(tmp_path / 'does_not_exist.json'))
