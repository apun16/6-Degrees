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
    - [ ] implement info page + refresh 
    - [ ] word input page + hint & submit button
    - [ ] try implementing dynamic hints -> share next word after their last correct one or hints if the target next word is part of a semantic cluster (ex: Animals, Colours, etc)
    - [ ] add word progress animation where they can see how many words they have submitted + the path laid out
    - [ ] semi transparent dot design patern in the background
- [ ] implement game logic
    - [ ] rules on information page
    - [ ] scoring that depend on beating algorithm with points given accordingly
- [ ] NLP: Semantic connection of words -> graph model (word: node, edge: implicit: etc)
    - [ ] BFS implemented to find optimal path between 2 words
    - [ ] implement cosine similarity to measure how related words are
    - [ ] connect words by meaning -> words embeded in vectors + store this meaning
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
- [ ] Share button to send result + play game link via Messages, Notes, etc
- [ ] GitHub Actions is okay with full codebase
- [ ] Update README.md with finalized design choice + overview
- [ ] clear documentation/comments
- [ ] deploy on vercel + vercel page analytics to see how people are playing :)
- [ ] continue optimizing algo + UI + get feedback from others to make it more enjoyable (maybe a leaderboard???)

TECH STACK/TOOLS: TypeScript + JavaScript, Python, CSS, Flask, Next.js, Framer Motion, Sentence Transformers, Github Actions (CI/CD Pipelines), pytest + jest