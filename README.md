# Six-Degrees

TO DO LIST

- [X] init frontend + backend
- [X] create intial landing page
    - [X] add network design to landing page
    - [X] functional play button linked to game page
    - [X] example connections that periodically flip through
- [X] create game page
    - [X] navbar -> refresh option + ? information page
    - [X] footer -> links to github + @2026 + objective
    - [X] implement info page + refresh 
    - [X] word input page + hint & submit button
    - [ ] N/A - try implementing dynamic hints -> share next word after their last correct one or hints if the target next word is part of a semantic cluster (ex: Animals, Colours, etc)
    - [X] add word progress animation where they can see how many words they have submitted + the path laid out
    - [X] semi transparent dot design patern in the background
- [X] implement game logic
    - [X] rules on information page
    - [X] scoring that depend on beating algorithm with points given accordingly
- [X] NLP: Semantic connection of words -> graph model (word: node, edge: implicit: etc)
    - [X] BFS implemented to find optimal path between 2 words
    - [X] implement cosine similarity to measure how related words are
    - [X] connect words by meaning -> words embeded in vectors + store this meaning
- [ ] Implement frontend testing using Jest
    - [ ] Game State test
    - [ ] API test
    - [ ] Score Render test
    - [ ] Path Input Validation test (etc...)
- [ ] Implement backend testing using PyTest
    - [ ] embedding generated test
    - [ ] semantic simulated test
    - [ ] semantic neighbour test
    - [ ] bfs test
    - [ ] player path test
    - [ ] scoring test
    - [ ] api/route test (etc...)
- [X] Share button to send result + play game link via Messages, Notes, etc
- [ ] GitHub Actions is okay with full codebase
- [ ] Update README.md with finalized design choice + overview
- [ ] clear documentation/comments
- [X] deploy on vercel + vercel page analytics to see how people are playing :)
- [ ] continue optimizing algo + UI + get feedback from others to make it more enjoyable (maybe a leaderboard???)

TECH STACK/TOOLS: TypeScript + JavaScript, Python, CSS, Flask, Next.js, Framer Motion, Sentence Transformers, Github Actions (CI/CD Pipelines), pytest + jest
