import os
import json
from typing import List, Set, Optional
import logging

logger = logging.getLogger(__name__)

class WordDatabase:
    # manages database of valid words for the game and can 
    # load words from a file or use a default set
    
    def __init__(self, word_file: Optional[str] = None):
        # init word database
        # word_file: optional path to a JSON file containing word list

        self.words: Set[str] = set()
        self.word_file = word_file
        
        if word_file and os.path.exists(word_file):
            self.load_from_file(word_file)
        else:
            # init with a default set of common words
            self._initialize_default_words()
    
    def _initialize_default_words(self):
        # init with default set of common, semantically rich words
        default_words = [
            # Nature & Environment
            'ocean', 'wave', 'beach', 'sand', 'water', 'river', 'lake', 'mountain', 'forest', 'tree',
            'flower', 'grass', 'sun', 'moon', 'star', 'sky', 'cloud', 'rain', 'snow', 'wind',
            
            # Animals & Nature
            'animal', 'creature', 'beast', 'mammal', 'reptile', 'amphibian', 'insect', 'bird', 'fish', 
            'dog', 'cat', 'horse', 'cow', 'pig', 'sheep', 'goat', 'chicken', 'duck', 'goose',
            'lion', 'tiger', 'leopard', 'cheetah', 'panther', 'jaguar', 'elephant', 'rhino', 'hippo', 'giraffe',
            'zebra', 'monkey', 'ape', 'gorilla', 'chimpanzee', 'bear', 'panda', 'polar', 'grizzly', 'black',
            'wolf', 'fox', 'coyote', 'deer', 'moose', 'elk', 'rabbit', 'hare', 'squirrel', 'chipmunk',
            'mouse', 'rat', 'hamster', 'guinea', 'ferret', 'raccoon', 'skunk', 'opossum', 'badger', 'beaver',
            'whale', 'dolphin', 'shark', 'octopus', 'squid', 'crab', 'lobster', 'seal', 'walrus', 'otter',
            'eagle', 'hawk', 'falcon', 'owl', 'crow', 'raven', 'parrot', 'penguin', 'flamingo', 'swan',
            'snake', 'python', 'cobra', 'viper', 'lizard', 'gecko', 'iguana', 'turtle', 'tortoise', 'crocodile',
            'alligator', 'frog', 'toad', 'salamander', 'spider', 'scorpion', 'ant', 'bee', 'wasp', 'butterfly',
            'moth', 'dragonfly', 'grasshopper', 'cricket', 'beetle', 'ladybug', 'mosquito', 'fly', 'worm',
            'kitten', 'puppy', 'calf', 'foal', 'lamb', 'chick', 'duckling', 'gosling', 'fawn', 'cub',
            
            # Music & Sound
            'music', 'song', 'sound', 'voice', 'piano', 'guitar', 'violin', 'drum', 'note', 'melody',
            'rhythm', 'harmony', 'concert', 'orchestra', 'singer', 'composer', 'keyboard', 'key',
            'instrument', 'trumpet', 'flute', 'saxophone', 'cello', 'harp', 'banjo', 'accordion',
            
            # Colours
            'red', 'blue', 'green', 'yellow', 'orange', 'purple', 'pink', 'black', 'white', 'gray',
            'brown', 'gold', 'silver', 'color', 'colour', 'hue', 'shade', 'tint', 'tone',
            'paint', 'brush', 'canvas', 'art', 'picture',
            
            # Emotions
            'love', 'hate', 'joy', 'sadness', 'fear', 'anger', 'peace', 'war', 'hope', 'dream',
            'heart', 'soul', 'mind', 'spirit', 'emotion', 'feeling', 'thought', 'idea', 'concept',
            
            # Objects & Tools
            'key', 'door', 'window', 'house', 'home', 'room', 'chair', 'table', 'book', 'paper',
            'pen', 'pencil', 'computer', 'phone', 'car', 'bike', 'road', 'bridge', 'building',
            
            # Food
            'apple', 'bread', 'cake', 'chocolate', 'coffee', 'tea', 'fruit', 'vegetable', 'rice',
            'meat', 'fish', 'soup', 'salad', 'pizza', 'burger', 'sandwich', 'cheese', 'milk',
            
            # Actions & Movement
            'run', 'walk', 'jump', 'fly', 'swim', 'dance', 'sing', 'play', 'work', 'rest',
            'sleep', 'wake', 'eat', 'drink', 'read', 'write', 'speak', 'listen', 'see', 'watch',
            
            # Time & Space
            'time', 'day', 'night', 'morning', 'evening', 'week', 'month', 'year', 'season',
            'spring', 'summer', 'fall', 'winter', 'space', 'earth', 'planet', 'world', 'country',
            
            # Abstract Concepts
            'freedom', 'justice', 'truth', 'beauty', 'wisdom', 'knowledge', 'power', 'strength',
            'weakness', 'courage', 'honor', 'respect', 'trust', 'faith', 'belief', 'doubt',
            
            # Technology
            'computer', 'internet', 'network', 'data', 'information', 'code', 'program', 'software',
            'hardware', 'screen', 'keyboard', 'mouse', 'button', 'click', 'link', 'website',
            
            # Family & Relationships
            'family', 'parent', 'child', 'mother', 'father', 'brother', 'sister', 'friend', 'enemy',
            'neighbor', 'teacher', 'student', 'doctor', 'patient', 'person', 'people', 'human',
            
            # Body & Health
            'body', 'head', 'eye', 'ear', 'nose', 'mouth', 'hand', 'finger', 'foot', 'leg',
            'arm', 'heart', 'brain', 'blood', 'bone', 'muscle', 'skin', 'hair', 'tooth',
            
            # Sports & Games
            'game', 'sport', 'ball', 'team', 'player', 'coach', 'win', 'lose', 'score', 'goal',
            'race', 'competition', 'champion', 'victory', 'defeat', 'match', 'tournament',
            
            # Science & Learning
            'science', 'math', 'physics', 'chemistry', 'biology', 'history', 'language', 'word',
            'letter', 'number', 'equation', 'theory', 'experiment', 'research', 'study', 'learn',
            'school', 'university', 'college', 'education', 'class', 'lesson', 'test', 'exam',
            'teacher', 'professor', 'student', 'pupil', 'homework', 'assignment', 'grade', 'degree',
            
            # Writing & Office Supplies
            'pencil', 'pen', 'marker', 'crayon', 'chalk', 'eraser', 'sharpener', 'notebook',
            'journal', 'diary', 'notepad', 'sketchbook', 'folder', 'binder', 'stapler', 'clip',
            'tape', 'glue', 'scissors', 'ruler', 'calculator', 'desk', 'office', 'work',
            
            # More abstract connections
            'fire', 'flame', 'heat', 'light', 'dark', 'shadow', 'bright', 'dim', 'warm', 'cold',
            'hot', 'ice', 'freeze', 'melt', 'solid', 'liquid', 'gas', 'energy', 'force', 'motion',
            
            # Weather & Climate
            'weather', 'climate', 'temperature', 'humidity', 'storm', 'thunder', 'lightning',
            'hurricane', 'tornado', 'blizzard', 'drought', 'flood', 'fog', 'mist', 'dew',
            
            # Plants & Trees
            'plant', 'tree', 'leaf', 'branch', 'root', 'seed', 'sprout', 'bud', 'bloom',
            'rose', 'tulip', 'daisy', 'sunflower', 'lily', 'orchid', 'cactus', 'fern',
            'oak', 'pine', 'maple', 'birch', 'willow', 'palm', 'bamboo', 'ivy',
            
            # Vehicles & Transportation
            'vehicle', 'car', 'truck', 'bus', 'train', 'plane', 'airplane', 'helicopter',
            'boat', 'ship', 'yacht', 'submarine', 'bicycle', 'motorcycle', 'scooter', 'skateboard',
            'taxi', 'ambulance', 'firetruck', 'police', 'ambulance', 'van', 'suv', 'sedan',
            
            # Buildings & Architecture
            'building', 'house', 'home', 'apartment', 'condo', 'mansion', 'cottage', 'cabin',
            'castle', 'palace', 'tower', 'skyscraper', 'church', 'temple', 'mosque', 'synagogue',
            'school', 'hospital', 'library', 'museum', 'theater', 'stadium', 'arena', 'mall',
            
            # Clothing & Fashion
            'clothing', 'clothes', 'shirt', 'pants', 'dress', 'skirt', 'jacket', 'coat',
            'sweater', 'hoodie', 't-shirt', 'jeans', 'shorts', 'socks', 'shoes', 'boots',
            'sneakers', 'sandals', 'hat', 'cap', 'gloves', 'scarf', 'belt', 'tie',
            
            # Furniture & Home
            'furniture', 'chair', 'table', 'desk', 'sofa', 'couch', 'bed', 'mattress',
            'pillow', 'blanket', 'sheet', 'curtain', 'carpet', 'rug', 'lamp', 'light',
            'mirror', 'picture', 'frame', 'shelf', 'cabinet', 'drawer', 'door', 'window',
            
            # Kitchen & Cooking
            'kitchen', 'cook', 'cooking', 'recipe', 'ingredient', 'spice', 'salt', 'pepper',
            'knife', 'fork', 'spoon', 'plate', 'bowl', 'cup', 'glass', 'mug',
            'pot', 'pan', 'oven', 'stove', 'microwave', 'refrigerator', 'freezer', 'sink',
            
            # Technology & Electronics
            'technology', 'electronic', 'device', 'gadget', 'appliance', 'machine', 'robot',
            'phone', 'smartphone', 'tablet', 'laptop', 'computer', 'monitor', 'screen', 'display',
            'keyboard', 'mouse', 'printer', 'scanner', 'camera', 'television', 'tv', 'radio',
            
            # Sports & Recreation
            'sport', 'sports', 'athletic', 'exercise', 'fitness', 'workout', 'training', 'practice',
            'football', 'soccer', 'basketball', 'baseball', 'tennis', 'golf', 'swimming', 'running',
            'cycling', 'hiking', 'climbing', 'skiing', 'surfing', 'skating', 'dancing', 'yoga',
            
            # Entertainment & Media
            'entertainment', 'media', 'television', 'movie', 'film', 'cinema', 'theater', 'show',
            'music', 'song', 'album', 'artist', 'band', 'concert', 'performance', 'stage',
            'book', 'novel', 'story', 'tale', 'fiction', 'nonfiction', 'magazine', 'newspaper',
            
            # Nature & Geography
            'geography', 'landscape', 'terrain', 'valley', 'canyon', 'plateau', 'hill', 'cliff',
            'island', 'peninsula', 'coast', 'shore', 'harbor', 'bay', 'gulf', 'strait',
            'desert', 'jungle', 'tundra', 'prairie', 'meadow', 'field', 'farm', 'ranch',
            
            # Time & Calendar
            'calendar', 'date', 'holiday', 'birthday', 'anniversary', 'celebration', 'party', 'festival',
            'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday', 'weekend',
            'january', 'february', 'march', 'april', 'may', 'june', 'july', 'august',
            'september', 'october', 'november', 'december', 'today', 'tomorrow', 'yesterday',
            
            # Emotions & Feelings (expanded)
            'happiness', 'sadness', 'anger', 'fear', 'surprise', 'disgust', 'excitement', 'boredom',
            'anxiety', 'stress', 'relief', 'calm', 'peaceful', 'nervous', 'confident', 'shy',
            'proud', 'ashamed', 'embarrassed', 'guilty', 'innocent', 'jealous', 'envious', 'grateful',
            
            # Body Parts (expanded)
            'organ', 'lung', 'liver', 'kidney', 'stomach', 'intestine', 'throat', 'neck',
            'shoulder', 'elbow', 'wrist', 'ankle', 'knee', 'hip', 'back', 'chest',
            'stomach', 'belly', 'waist', 'thigh', 'calf', 'shin', 'toe', 'nail',
            
            # Food & Drinks (expanded)
            'beverage', 'drink', 'juice', 'soda', 'water', 'beer', 'wine', 'cocktail',
            'breakfast', 'lunch', 'dinner', 'snack', 'dessert', 'candy', 'sweet', 'sour',
            'spicy', 'salty', 'bitter', 'tasty', 'delicious', 'yummy', 'gross', 'disgusting',
            
            # Colors (expanded)
            'color', 'colour', 'hue', 'shade', 'tint', 'tone', 'bright', 'dark', 'light',
            'vibrant', 'dull', 'vivid', 'pale', 'rich', 'deep', 'pastel', 'neon',
            
            # Shapes & Forms
            'shape', 'form', 'circle', 'square', 'triangle', 'rectangle', 'oval', 'diamond',
            'sphere', 'cube', 'cylinder', 'cone', 'pyramid', 'round', 'flat', 'curved',
            'straight', 'zigzag', 'spiral', 'wavy', 'smooth', 'rough', 'sharp', 'blunt'
        ]
        
        self.words = {word.lower().strip() for word in default_words}
        logger.info(f"Initialized with {len(self.words)} default words")
    
    def load_from_file(self, file_path: str):
        # load words from a JSON file
        # file_path: path to JSON file containing word list
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    self.words = {word.lower().strip() for word in data}
                elif isinstance(data, dict) and 'words' in data:
                    self.words = {word.lower().strip() for word in data['words']}
                else:
                    raise ValueError("Invalid JSON format")
            
            logger.info(f"Loaded {len(self.words)} words from {file_path}")
        except Exception as e:
            logger.error(f"Error loading words from file: {e}")
            self._initialize_default_words()
    
    def save_to_file(self, file_path: str):
        # save words to a JSON file
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump({'words': sorted(list(self.words))}, f, indent=2)
            logger.info(f"Saved {len(self.words)} words to {file_path}")
        except Exception as e:
            logger.error(f"Error saving words to file: {e}")
    
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