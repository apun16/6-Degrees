import json
from pathlib import Path
from typing import Dict, List, Set, Optional
import logging

logger = logging.getLogger(__name__)

# source of truth for the game vocabulary
DEFAULT_WORD_FILE = Path(__file__).resolve().parent.parent / "data" / "words.json"

class WordDatabase:
    # manages the database of valid words for the game, loaded from a JSON
    # word file (data/words.json by default)
    
    def __init__(self, word_file: Optional[str] = None):
        # init word database
        # word_file: path to a JSON word list; defaults to the packaged data/words.json

        self.words: Set[str] = set()
        self.categories: Dict[str, List[str]] = {}
        self.word_file = word_file or str(DEFAULT_WORD_FILE)

        self.load_from_file(self.word_file)

    def load_from_file(self, file_path: str):
        # load words from a JSON file
        # accepts either a bare list, or an object with a "words" key and
        # optional "categories" mapping used for stratified sampling and evals
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if isinstance(data, list):
            words = data
            categories = {}
        elif isinstance(data, dict) and 'words' in data:
            words = data['words']
            categories = data.get('categories', {})
        else:
            raise ValueError(
                f"Invalid word file {file_path}: expected a list or an object with a 'words' key"
            )

        self.words = {word.lower().strip() for word in words}
        self.categories = {
            name: [w.lower().strip() for w in members]
            for name, members in categories.items()
        }

        if not self.words:
            raise ValueError(f"Word file {file_path} contained no words")

        logger.info(
            f"Loaded {len(self.words)} words in {len(self.categories)} categories "
            f"from {file_path}"
        )

    def get_categories(self) -> Dict[str, List[str]]:
        # get the category -> words mapping (empty if the word file had none)
        return self.categories

    def save_to_file(self, file_path: str):
        # save words to a JSON file, round-tripping categories so this never
        # silently discards the grouping that load_from_file read in
        payload = {'words': sorted(self.words)}
        if self.categories:
            payload['categories'] = self.categories
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved {len(self.words)} words to {file_path}")
    
    def add_word(self, word: str) -> bool:
        # Add a word to the database
        # returns True if word was added, False if it already existed
        word_lower = word.lower().strip()
        if word_lower not in self.words:
            self.words.add(word_lower)
            return True
        return False
    
    def word_exists(self, word: str) -> bool:
        # check if a word exists in the database.
        # returns True if word exists, False otherwise
        return word.lower().strip() in self.words
    
    def get_all_words(self) -> List[str]:
        # get all words in the database as a sorted list
        return sorted(list(self.words))
    
    def get_random_words(self, count: int) -> List[str]:
        # get a random sample of words from the database
        # returns a list of random words
        import random
        words_list = list(self.words)
        return random.sample(words_list, min(count, len(words_list)))
    
    def get_word_count(self) -> int:
        # get the total number of words in the database
        return len(self.words)