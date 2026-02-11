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
            # Verbs
            'create', 'build', 'destroy', 'analyze', 'compute', 'generate', 'evaluate', 'optimize',
            'calculate', 'design', 'construct', 'organize', 'communicate', 'collaborate',
            'innovate', 'investigate', 'develop', 'implement', 'execute', 'perform',
            'achieve', 'improve', 'expand', 'reduce', 'increase', 'decrease',
            'transform', 'adapt', 'evolve', 'predict', 'classify', 'cluster',
            'model', 'train', 'learn', 'reason', 'solve', 'explore',
            'discover', 'invent', 'engineer', 'architect', 'program', 'debug', 'deploy',
            'test', 'validate', 'verify', 'monitor', 'maintain', 'repair', 'upgrade',
            'download', 'upload', 'install', 'configure', 'customize', 'integrate',
            'automate', 'synchronize', 'backup', 'restore', 'encrypt', 'decrypt',
            'compress', 'decompress', 'convert', 'format', 'parse', 'render',
            'search', 'filter', 'sort', 'index', 'query', 'retrieve', 'store',
            'edit', 'modify', 'update', 'delete', 'insert', 'append', 'merge',
            'split', 'join', 'compare', 'contrast', 'match', 'replace', 'substitute',
            'extract', 'import', 'export', 'transfer', 'migrate', 'clone', 'replicate'

            # Adjectives
            'efficient', 'powerful', 'intelligent', 'creative', 'dynamic', 'complex',
            'simple', 'scalable', 'adaptive', 'resilient', 'strategic', 'innovative',
            'logical', 'critical', 'analytical', 'systematic', 'robust', 
            'flexible', 'agile', 'secure', 'reliable', 'automated',
            'digital', 'virtual', 'real', 'natural', 'organic', 'synthetic',
            'fast', 'slow', 'large', 'small', 'big', 'tiny', 'huge', 'micro',
            'modern', 'ancient', 'new', 'old', 'young', 'fresh', 'stale',
            'clean', 'dirty', 'clear', 'cloudy', 'bright', 'dark', 'light', 'heavy',
            'smooth', 'rough', 'soft', 'hard', 'solid', 'liquid', 'gaseous',
            'hot', 'cold', 'warm', 'cool', 'frozen', 'boiling', 'melted',
            'public', 'private', 'personal', 'professional', 'commercial',
            'local', 'global', 'national', 'international', 'internal', 'external',
            'active', 'passive', 'positive', 'negative', 'neutral', 'static'
            'proud', 'ashamed', 'embarrassed', 'guilty', 'innocent', 'jealous', 'envious', 'grateful',

            # Abstract Concepts
            'freedom', 'justice', 'truth', 'beauty', 'wisdom', 'knowledge', 'power', 'strength',
            'weakness', 'courage', 'honor', 'respect', 'trust', 'faith', 'belief', 'doubt',
            'identity', 'purpose', 'meaning', 'consciousness', 'awareness',
            'existence', 'reality', 'perception', 'intention', 'motivation',
            'discipline', 'ambition', 'curiosity', 'creativity',
            'insight', 'intuition', 'perspective', 'mindset',
            'focus', 'clarity', 'wisdom', 'knowledge', 'understanding',
            'concept', 'theory', 'hypothesis', 'principle', 'philosophy', 'logic',
            'ethics', 'morality', 'virtue', 'vice', 'sin', 'redemption',
            'destiny', 'fate', 'fortune', 'luck', 'chance', 'probability',
            'chaos', 'order', 'balance', 'harmony', 'conflict', 'peace',
            'growth', 'decay', 'birth', 'death', 'life', 'time', 'eternity',
            'infinity', 'limit', 'boundary', 'edge', 'center', 'core', 'essence',

            # Financial & Economic
            'capital', 'asset', 'liability', 'equity', 'revenue', 'profit',
            'loss', 'margin', 'investment', 'portfolio', 'market',
            'inflation', 'deflation', 'interest', 'bond', 'stock',
            'derivative', 'option', 'hedge', 'risk', 'return',
            'valuation', 'liquidity', 'volatility', 'dividend',
            'cashflow', 'expense', 'cost', 'overhead',
            'depreciation', 'amortization', 'inventory', 'audit',
            'ledger', 'fiscal', 'tax', 'tariff', 'subsidy', 'trader', 'broker', 'exchange', 'index', 'benchmark',
            'spread', 'yield', 'alpha', 'beta', 'arbitrage',
            'short', 'long', 'position', 'futures', 'swap',
            'commodity', 'currency', 'forex', 'derivatives',
            'securities', 'treasury', 'diversification', 'allocation', 'rebalancing',
            'hedging', 'speculation', 'momentum', 'growth',
            'value', 'indexing', 'passive', 'active',
            'gdp', 'recession', 'expansion', 'contraction',
            'unemployment', 'productivity', 'consumption',
            'supply', 'demand', 'scarcity', 'surplus',
            'deficit', 'monetary', 'fiscal', 'stimulus',
            'bank', 'lender', 'borrower', 'loan', 'mortgage',
            'fintech', 'blockchain', 'cryptocurrency', 'token',
            'stablecoin', 'defi', 'debt', 'leverage',
            'capitalization', 'shareholder', 'stakeholder', 'ownership',
            'merger', 'acquisition', 'buyout', 'ipo', 'spinoff',
            'restructuring', 'bankruptcy', 'insolvency', 'credit', 'debit', 'savings', 'wealth'

            # Nature & Environment
            'ocean', 'wave', 'beach', 'sand', 'water', 'river', 'lake', 'mountain', 'forest', 'tree',
            'flower', 'grass', 'sun', 'moon', 'star', 'sky', 'cloud', 'rain', 'snow', 'wind',
            'earth', 'ground', 'soil', 'rock', 'stone', 'pebble', 'sand', 'dust', 'dirt', 'mud',
            'hill', 'valley', 'canyon', 'cliff', 'cave', 'island', 'peninsula', 'coast', 'shore',
            'desert', 'jungle', 'swamp', 'marsh', 'wetland', 'tundra', 'prairie', 'savanna',
            'volcano', 'earthquake', 'tsunami', 'avalanche', 'landslide', 'erosion', 'weathering',
            'season', 'spring', 'summer', 'autumn', 'winter', 'climate', 'weather', 'temperature',
            'humidity', 'pressure', 'atmosphere', 'ozone', 'ecosystem', 'habitat', 'biosphere',
            'biodiversity', 'conservation', 'pollution', 'recycling', 'sustainability', 'renewable',
            'solar', 'wind', 'hydro', 'geothermal', 'biomass', 'fossil', 'fuel', 'coal', 'oil', 'gas',
            'mineral', 'metal', 'crystal', 'gem', 'diamond', 'gold', 'silver', 'copper', 'iron',
            'oxygen', 'nitrogen', 'carbon', 'hydrogen', 'helium', 'molecule', 'atom', 'particle'
            
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
            'kitten', 'puppy', 'calf', 'foal', 'lamb', 'chick', 'duckling', 'gosling', 'fawn', 'cub', 'fawn'
            'geography', 'landscape', 'terrain', 'valley', 'canyon', 'plateau', 'hill', 'cliff',
            'island', 'peninsula', 'coast', 'shore', 'harbor', 'bay', 'gulf', 'strait',
            'desert', 'jungle', 'tundra', 'prairie', 'meadow', 'field', 'farm', 'ranch',
            

            # Music & Sound
            'music', 'song', 'sound', 'voice', 'piano', 'guitar', 'violin', 'drum', 'note', 'melody',
            'rhythm', 'harmony', 'concert', 'orchestra', 'singer', 'composer', 'keyboard', 'key',
            'instrument', 'trumpet', 'flute', 'saxophone', 'cello', 'harp', 'banjo', 'accordion',
            'bass', 'percussion', 'synthesizer', 'microphone', 'speaker', 'headphone', 'earphone',
            'album', 'track', 'record', 'single', 'playlist', 'genre', 'style', 'tempo', 'beat',
            'chord', 'scale', 'octave', 'pitch', 'tone', 'timbre', 'volume', 'loudness', 'silence',
            'echo', 'reverb', 'distortion', 'feedback', 'noise', 'static', 'hiss', 'hum', 'buzz',
            'acoustic', 'electric', 'digital', 'analog', 'live', 'studio', 'remix', 'cover',
            'opera', 'symphony', 'jazz', 'blues', 'rock', 'pop', 'classical', 'folk', 'country',
            'hiphop', 'rap', 'electronic', 'dance', 'reggae', 'metal', 'punk', 'soul', 'funk',
            'choir', 'band', 'ensemble', 'solo', 'duet', 'trio', 'quartet', 'audition', 'rehearsal'
            
            # Colours
            'red', 'blue', 'green', 'yellow', 'orange', 'purple', 'pink', 'black', 'white', 'gray',
            'brown', 'gold', 'silver', 'color', 'colour', 'hue', 'shade', 'tint', 'tone',
            'paint', 'brush', 'canvas', 'art', 'picture', 'crimson', 'maroon', 'scarlet', 'ruby',
            'navy', 'azure', 'cyan', 'teal', 'turquoise', 'lime', 'olive', 'emerald', 'jade',
            'amber', 'coral', 'peach', 'magenta', 'violet', 'indigo', 'lavender', 'plum',
            'beige', 'cream', 'ivory', 'tan', 'bronze', 'copper', 'charcoal', 'slate', 'ivory',
            'pastel', 'neon', 'fluorescent', 'matte', 'glossy', 'metallic', 'iridescent',
            'transparent', 'opaque', 'translucent', 'pigment', 'dye', 'stain', 'varnish', 'glaze'
            
            # Emotions
            'love', 'hate', 'joy', 'sadness', 'fear', 'anger', 'peace', 'war', 'hope', 'dream',
            'heart', 'soul', 'mind', 'spirit', 'emotion', 'feeling', 'thought', 'idea', 'concept',
            'happiness', 'excitement', 'enthusiasm', 'passion', 'desire', 'longing', 'nostalgia',
            'melancholy', 'grief', 'sorrow', 'despair', 'loneliness', 'boredom', 'apathy',
            'anxiety', 'worry', 'stress', 'tension', 'panic', 'terror', 'horror', 'dread',
            'frustration', 'irritation', 'rage', 'fury', 'resentment', 'bitterness', 'envy',
            'jealousy', 'shame', 'guilt', 'embarrassment', 'humiliation', 'pride', 'confidence',
            'satisfaction', 'contentment', 'gratitude', 'relief', 'comfort', 'calm', 'serenity',
            'surprise', 'shock', 'amazement', 'wonder', 'awe', 'curiosity', 'interest',
            'sympathy', 'empathy', 'compassion', 'affection', 'tenderness', 'warmth', 'coldness'
            
            # Objects & Tools
            'key', 'door', 'window', 'house', 'home', 'room', 'chair', 'table', 'book', 'paper',
            'pen', 'pencil', 'computer', 'phone', 'car', 'bike', 'road', 'bridge', 'building',
            'tool', 'hammer', 'screwdriver', 'wrench', 'pliers', 'saw', 'drill', 'nail', 'screw',
            'knife', 'scissors', 'blade', 'axe', 'shovel', 'rake', 'hoe', 'ladder', 'rope',
            'chain', 'lock', 'clock', 'watch', 'calendar', 'map', 'compass', 'telescope',
            'microscope', 'binoculars', 'camera', 'lens', 'flashlight', 'torch', 'lantern',
            'candle', 'lamp', 'bulb', 'battery', 'charger', 'cable', 'wire', 'cord', 'plug',
            'switch', 'button', 'remote', 'controller', 'screen', 'monitor', 'display',
            'keyboard', 'mouse', 'printer', 'scanner', 'speaker', 'microphone', 'headset',
            'bag', 'box', 'container', 'bottle', 'jar', 'can', 'package', 'envelope', 'letter'
            
            # Food
            'apple', 'bread', 'cake', 'chocolate', 'coffee', 'tea', 'fruit', 'vegetable', 'rice',
            'meat', 'fish', 'soup', 'salad', 'pizza', 'burger', 'sandwich', 'cheese', 'milk', 'food',
            'water', 'juice', 'soda', 'beer', 'wine', 'milk', 'egg', 'butter', 'sugar', 'salt',
            'pepper', 'spice', 'herb', 'oil', 'vinegar', 'sauce', 'dressing', 'honey', 'jam',
            'pasta', 'noodle', 'bread', 'toast', 'cereal', 'oatmeal', 'pancake', 'waffle',
            'bacon', 'sausage', 'ham', 'beef', 'pork', 'lamb', 'chicken', 'turkey', 'duck',
            'carrot', 'potato', 'tomato', 'onion', 'garlic', 'lettuce', 'cabbage', 'broccoli',
            'spinach', 'pepper', 'cucumber', 'corn', 'bean', 'pea', 'lentil', 'nut', 'seed',
            'flour', 'dough', 'yeast', 'baking', 'cooking', 'recipe', 'meal', 'breakfast',
            'lunch', 'dinner', 'snack', 'dessert', 'appetizer', 'beverage', 'drink', 'thirst'
            
            # Actions & Movement
            'run', 'walk', 'jump', 'fly', 'swim', 'dance', 'sing', 'play', 'work', 'rest',
            'sleep', 'wake', 'eat', 'drink', 'read', 'write', 'speak', 'listen', 'see', 'watch',
            'move', 'stop', 'start', 'begin', 'end', 'finish', 'continue', 'pause', 'resume',
            'turn', 'rotate', 'spin', 'twist', 'bend', 'stretch', 'reach', 'grab', 'hold',
            'push', 'pull', 'lift', 'drop', 'throw', 'catch', 'kick', 'punch', 'hit', 'strike',
            'climb', 'crawl', 'creep', 'slide', 'glide', 'float', 'sink', 'dive', 'surface',
            'accelerate', 'decelerate', 'speed', 'slow', 'hurry', 'rush', 'delay', 'wait',
            'approach', 'retreat', 'advance', 'withdraw', 'enter', 'exit', 'arrive', 'depart',
            'follow', 'lead', 'chase', 'escape', 'pursue', 'flee', 'hide', 'seek', 'find',
            'search', 'hunt', 'gather', 'collect', 'pick', 'pluck', 'harvest', 'plant', 'sow'
            
            # Time & Space
            'time', 'day', 'night', 'morning', 'evening', 'week', 'month', 'year', 'season',
            'spring', 'summer', 'fall', 'winter', 'space', 'earth', 'planet', 'world', 'country',
            
            # Technology
            'computer', 'internet', 'network', 'data', 'information', 'code', 'program', 'software',
            'hardware', 'screen', 'keyboard', 'mouse', 'button', 'click', 'link', 'website',
            'server', 'client', 'database', 'cloud', 'storage', 'memory', 'processor', 'cpu',
            'gpu', 'chip', 'circuit', 'board', 'component', 'device', 'gadget', 'machine',
            'robot', 'automation', 'algorithm', 'function', 'method', 'class', 'object', 'variable',
            'array', 'string', 'integer', 'boolean', 'loop', 'condition', 'statement', 'syntax',
            'compiler', 'interpreter', 'runtime', 'environment', 'framework', 'library', 'api',
            'interface', 'protocol', 'packet', 'bandwidth', 'latency', 'throughput', 'firewall',
            'security', 'encryption', 'password', 'authentication', 'authorization', 'token',
            
            # Family & Relationships
            'family', 'parent', 'child', 'mother', 'father', 'brother', 'sister', 'friend', 'enemy',
            'neighbor', 'teacher', 'student', 'doctor', 'patient', 'person', 'people', 'human',
            'baby', 'infant', 'toddler', 'teenager', 'adult', 'senior', 'elder', 'ancestor',
            'descendant', 'relative', 'cousin', 'uncle', 'aunt', 'niece', 'nephew', 'grandparent',
            'grandmother', 'grandfather', 'grandchild', 'grandson', 'granddaughter', 'spouse',
            'husband', 'wife', 'partner', 'couple', 'marriage', 'wedding', 'divorce', 'single',
            'orphan', 'widow', 'widower', 'stepparent', 'stepchild', 'halfbrother', 'halfsister',
            'twin', 'sibling', 'offspring', 'heir', 'predecessor', 'successor', 'mentor', 'protege',
            
            # Body & Health
            'body', 'head', 'eye', 'ear', 'nose', 'mouth', 'hand', 'finger', 'foot', 'leg',
            'arm', 'heart', 'brain', 'blood', 'bone', 'muscle', 'skin', 'hair', 'tooth',
            'organ', 'lung', 'liver', 'kidney', 'stomach', 'intestine', 'throat', 'neck',
            'shoulder', 'elbow', 'wrist', 'ankle', 'knee', 'hip', 'back', 'chest',
            'waist', 'thigh', 'calf', 'toe', 'nail', 'vein', 'artery', 'nerve', 'cell',
            'health', 'fitness', 'exercise', 'workout', 'diet', 'nutrition', 'calorie',
            'protein', 'carbohydrate', 'fat', 'vitamin', 'mineral', 'fiber', 'sugar',
            'disease', 'illness', 'sickness', 'infection', 'virus', 'bacteria', 'fungus',
            'medicine', 'drug', 'pill', 'tablet', 'capsule', 'syrup', 'vaccine', 'antibiotic',
            'doctor', 'nurse', 'hospital', 'clinic', 'pharmacy', 'surgery', 'operation',
            'therapy', 'treatment', 'diagnosis', 'symptom', 'pain', 'ache', 'fever', 'cough'
                    
            # Sports & Games
            'game', 'sport', 'ball', 'team', 'player', 'coach', 'win', 'lose', 'score', 'goal',
            'race', 'competition', 'champion', 'victory', 'defeat', 'match', 'tournament',
            'football', 'soccer', 'basketball', 'baseball', 'tennis', 'golf', 'swimming', 'running',
            'cycling', 'hiking', 'climbing', 'skiing', 'surfing', 'skating', 'dancing', 'yoga',
            'hockey', 'volleyball', 'badminton', 'tabletennis', 'cricket', 'rugby', 'boxing',
            'wrestling', 'gymnastics', 'athletics', 'track', 'field', 'marathon', 'sprint',
            'relay', 'medal', 'trophy', 'prize', 'award', 'record', 'statistics', 'league',
            'division', 'conference', 'playoff', 'finals', 'semifinal', 'quarterfinal', 'round',
            'inning', 'period', 'quarter', 'half', 'timeout', 'overtime', 'draw', 'tie',
            'umpire', 'referee', 'judge', 'spectator', 'fan', 'crowd', 'stadium', 'arena',
            'court', 'field', 'pitch', 'track', 'course', 'pool', 'gym', 'fitness', 'training'
            
            # Science & Learning
            'science', 'math', 'physics', 'chemistry', 'biology', 'history', 'language', 'word',
            'letter', 'number', 'equation', 'theory', 'experiment', 'research', 'study', 'learn',
            'school', 'university', 'college', 'education', 'class', 'lesson', 'test', 'exam',
            'teacher', 'professor', 'student', 'pupil', 'homework', 'assignment', 'grade', 'degree',
            'astronomy', 'geology', 'geography', 'psychology', 'sociology', 'anthropology',
            'economics', 'politics', 'law', 'literature', 'art', 'music', 'philosophy', 'religion',
            'hypothesis', 'observation', 'measurement', 'calculation', 'analysis', 'conclusion',
            'evidence', 'proof', 'theorem', 'law', 'principle', 'formula', 'function', 'graph',
            'chart', 'diagram', 'table', 'data', 'statistics', 'probability', 'average', 'mean',
            'median', 'mode', 'range', 'deviation', 'variance', 'correlation', 'causation',
            
            # Writing & Office Supplies
            'pencil', 'pen', 'marker', 'crayon', 'chalk', 'eraser', 'sharpener', 'notebook',
            'journal', 'diary', 'notepad', 'sketchbook', 'folder', 'binder', 'stapler', 'clip',
            'tape', 'glue', 'scissors', 'ruler', 'calculator', 'desk', 'office', 'work',
            'paper', 'document', 'file', 'form', 'application', 'report', 'memo', 'letter',
            'envelope', 'stamp', 'postcard', 'card', 'invitation', 'certificate', 'diploma',
            'contract', 'agreement', 'proposal', 'resume', 'cv', 'portfolio', 'manuscript',
            'draft', 'outline', 'summary', 'abstract', 'index', 'glossary', 'bibliography',
            'reference', 'citation', 'footnote', 'header', 'footer', 'margin', 'page',
            
            # Weather & Climate
            'weather', 'climate', 'temperature', 'humidity', 'storm', 'thunder', 'lightning',
            'hurricane', 'tornado', 'blizzard', 'drought', 'flood', 'fog', 'mist', 'dew',
            'fire', 'flame', 'heat', 'light', 'dark', 'shadow', 'bright', 'dim', 'warm', 'cold',
            'hot', 'ice', 'freeze', 'melt', 'solid', 'liquid', 'gas', 'energy', 'force', 'motion',
            'rain', 'snow', 'sleet', 'hail', 'drizzle', 'shower', 'downpour', 'monsoon',
            'wind', 'breeze', 'gale', 'gust', 'cyclone', 'typhoon', 'storm',
    
            # Plants & Trees
            'plant', 'tree', 'leaf', 'branch', 'root', 'seed', 'sprout', 'bud', 'bloom',
            'rose', 'tulip', 'daisy', 'sunflower', 'lily', 'orchid', 'cactus', 'fern',
            'oak', 'pine', 'maple', 'birch', 'willow', 'palm', 'bamboo', 'ivy',
            'flower', 'petal', 'stem', 'trunk', 'bark', 'wood', 'timber', 'lumber',
            'fruit', 'apple', 'orange', 'banana', 'grape', 'berry', 'cherry', 'peach',
            'vegetable', 'carrot', 'potato', 'tomato', 'onion', 'lettuce', 'cabbage',
            'grass', 'lawn', 'meadow', 'pasture', 'weed', 'herb', 'spice', 'mint',
            'photosynthesis', 'chlorophyll', 'oxygen', 'carbon', 'nitrogen', 'soil',
                    
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
            'suit', 'uniform', 'costume', 'outfit', 'attire', 'apparel', 'garment', 'fabric',
            'cotton', 'wool', 'silk', 'linen', 'polyester', 'nylon', 'leather', 'denim',
            'lace', 'velvet', 'satin', 'corduroy', 'flannel', 'fleece', 'spandex', 'lycra',
            'button', 'zipper', 'pocket', 'collar', 'sleeve', 'cuff', 'hem', 'seam', 'stitch',
            'size', 'fit', 'tailor', 'alter', 'sew', 'knit', 'weave', 'dye', 'pattern', 'print',
            'fashion', 'style', 'trend', 'vintage', 'classic', 'casual', 'formal', 'elegant',
            'accessory', 'jewelry', 'watch', 'ring', 'necklace', 'bracelet', 'earring', 'glasses',
            'sunglasses', 'bag', 'purse', 'wallet', 'backpack', 'luggage', 'umbrella', 'raincoat'
            
            # Furniture & Home
            'furniture', 'chair', 'table', 'desk', 'sofa', 'couch', 'bed', 'mattress',
            'pillow', 'blanket', 'sheet', 'curtain', 'carpet', 'rug', 'lamp', 'light',
            'mirror', 'picture', 'frame', 'shelf', 'cabinet', 'drawer', 'door', 'window',
            
            # Kitchen & Cooking
            'kitchen', 'cook', 'cooking', 'recipe', 'ingredient', 'spice', 'salt', 'pepper',
            'knife', 'fork', 'spoon', 'plate', 'bowl', 'cup', 'glass', 'mug',
            'pot', 'pan', 'oven', 'stove', 'microwave', 'refrigerator', 'freezer', 'sink',
            
            # Entertainment & Media
            'entertainment', 'media', 'television', 'movie', 'film', 'cinema', 'theater', 'show',
            'music', 'song', 'album', 'artist', 'band', 'concert', 'performance', 'stage',
            'book', 'novel', 'story', 'tale', 'fiction', 'nonfiction', 'magazine', 'newspaper',
            
            # Time & Calendar
            'calendar', 'date', 'holiday', 'birthday', 'anniversary', 'celebration', 'party', 'festival',
            'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday', 'weekend',
            'january', 'february', 'march', 'april', 'may', 'june', 'july', 'august',
            'september', 'october', 'november', 'december', 'today', 'tomorrow', 'yesterday',
                        
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