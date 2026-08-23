# edge rules for building the semantic graph from word embeddings
#
# the original game connected two words whenever cosine similarity cleared a single
# global threshold of 0.45. that is the wrong tool for this job: similarity
# distributions differ per word, so hub words clear the bar against hundreds of others
# while specific words clear it against almost none. breadth first search then routes
# nearly every path through the same few hubs
#
# it is worse with qwen3 embeddings, whose similarities are compressed high. measured
# on this vocabulary, genuinely unrelated pairs still score 0.43 to 0.64, so any fixed
# cutoff in that band is arbitrary
#
# the fix is to rank rather than threshold. every rule here reduces to the same thing,
# a boolean adjacency matrix built from a similarity matrix, so they can be scored
# head to head by the eval harness with identical downstream code
from typing import Dict, List, Optional

import numpy as np

# similarity assigned to the diagonal so a word is never its own neighbour
_SELF = -np.inf


def cosine_matrix(vectors: np.ndarray) -> np.ndarray:
    # pairwise cosine similarity for l2 normalized vectors, which is just the dot
    # product. the diagonal is masked out so self similarity never counts as an edge
    v = np.asarray(vectors, dtype=np.float32)
    norms = np.linalg.norm(v, axis=1, keepdims=True)
    if not np.allclose(norms, 1.0, atol=1e-3):
        v = v / np.maximum(norms, 1e-12)
    # the accelerate blas backend on macos sets spurious divide, invalid and overflow
    # flags during this matmul even though every output value is finite and inside the
    # valid cosine range (verified across 256, 1024 and 4096 dimensions, zero nan).
    # the flags are suppressed for this one line only, and the explicit check below is
    # what actually guards correctness, so a genuine numerical problem still surfaces
    with np.errstate(all="ignore"):
        sims = (v @ v.T).astype(np.float32)

    if not np.isfinite(sims).all():
        raise ValueError("similarity matrix contains non-finite values")

    np.fill_diagonal(sims, _SELF)
    return sims


def connected_components(adjacency: np.ndarray) -> np.ndarray:
    # labels each node with its component id using iterative breadth first search
    # written against numpy rather than scipy so the backend keeps numpy as its only
    # runtime dependency
    n = adjacency.shape[0]
    labels = np.full(n, -1, dtype=np.int32)
    current = 0

    for start in range(n):
        if labels[start] != -1:
            continue
        frontier = [start]
        labels[start] = current
        while frontier:
            node = frontier.pop()
            for neighbour in np.flatnonzero(adjacency[node]):
                if labels[neighbour] == -1:
                    labels[neighbour] = current
                    frontier.append(neighbour)
        current += 1

    return labels


def bridge_components(adjacency: np.ndarray, sims: np.ndarray) -> int:
    # connects disconnected components by repeatedly adding the single highest
    # similarity edge that crosses a component boundary, until the graph is connected
    #
    # this matters because a stranded word is unreachable, so any puzzle involving it
    # is unsolvable. each iteration adds exactly one edge and merges two components
    # returns the number of bridge edges added
    added = 0
    labels = connected_components(adjacency)

    while labels.max() > 0:
        # mask similarity to cross component pairs only, then take the global best
        cross = labels[:, None] != labels[None, :]
        candidates = np.where(cross, sims, _SELF)
        i, j = np.unravel_index(np.argmax(candidates), candidates.shape)

        if not np.isfinite(candidates[i, j]):
            # no finite cross component similarity left, nothing sensible to join
            break

        adjacency[i, j] = adjacency[j, i] = True
        added += 1
        labels = connected_components(adjacency)

    return added


class EdgeRule:
    # base class, subclasses turn a similarity matrix into a boolean adjacency matrix
    name = "base"

    def adjacency(self, sims: np.ndarray) -> np.ndarray:
        raise NotImplementedError

    def params(self) -> Dict[str, object]:
        raise NotImplementedError

    def describe(self) -> str:
        parts = ", ".join(f"{k}={v}" for k, v in self.params().items())
        return f"{self.name}({parts})"


class ThresholdRule(EdgeRule):
    # the original behaviour, kept as the baseline the other rules have to beat
    name = "threshold"

    def __init__(self, threshold: float = 0.45):
        self.threshold = threshold

    def adjacency(self, sims: np.ndarray) -> np.ndarray:
        return sims >= self.threshold

    def params(self) -> Dict[str, object]:
        return {"threshold": self.threshold}


class KNNRule(EdgeRule):
    # rank based edges. each word proposes its k nearest neighbours, then the proposals
    # are combined either way:
    #
    #   union   edge if either endpoint proposed the other. every word keeps at least k
    #           neighbours so nothing is stranded and no path dead ends. more forgiving,
    #           which suits a game where a player's intuitive move should be accepted
    #
    #   mutual  edge only if both endpoints proposed each other. much higher precision
    #           and it flattens hubs, but it is sparse enough to strand words, so
    #           bridging is applied afterwards to keep the graph connected
    #
    # floor is an absolute similarity ceiling on nonsense: a word in a sparse region of
    # the space still has a nearest neighbour, but that neighbour may be unrelated
    def __init__(self, k: int = 10, floor: float = 0.0, mutual: bool = False,
                 bridge: bool = True):
        if k < 1:
            raise ValueError("k must be at least 1")
        self.k = k
        self.floor = floor
        self.mutual = mutual
        self.bridge = bridge
        self.bridges_added: Optional[int] = None

    @property
    def name(self) -> str:  # type: ignore[override]
        return "mutual_knn" if self.mutual else "union_knn"

    def adjacency(self, sims: np.ndarray) -> np.ndarray:
        n = sims.shape[0]
        k = min(self.k, n - 1)

        # argpartition is o(n) per row against argsort's o(n log n), and we do not care
        # about the ordering within the top k, only membership
        top = np.argpartition(-sims, kth=k - 1, axis=1)[:, :k]

        proposals = np.zeros((n, n), dtype=bool)
        rows = np.repeat(np.arange(n), k)
        proposals[rows, top.ravel()] = True

        # the floor applies to proposals, before the symmetry step, so a weak edge
        # cannot sneak back in through the other endpoint
        if self.floor > 0:
            proposals &= sims >= self.floor

        adjacency = (proposals & proposals.T) if self.mutual else (proposals | proposals.T)
        np.fill_diagonal(adjacency, False)

        self.bridges_added = 0
        if self.bridge:
            self.bridges_added = bridge_components(adjacency, sims)

        return adjacency

    def params(self) -> Dict[str, object]:
        return {"k": self.k, "floor": self.floor, "bridge": self.bridge}


def to_adjacency_lists(adjacency: np.ndarray, words: List[str]) -> Dict[str, List[str]]:
    # converts the boolean matrix into the word keyed lists that get shipped as json
    return {
        word: sorted(words[j] for j in np.flatnonzero(adjacency[i]))
        for i, word in enumerate(words)
    }


def all_pairs_distances(adjacency: np.ndarray, unreachable: int = 255) -> np.ndarray:
    # breadth first search from every node, giving hop counts between all word pairs
    #
    # shipping this turns optimal path length into an o(1) lookup instead of a graph
    # traversal per request, and lets puzzle selection sample directly at a target
    # difficulty rather than retrying random pairs until one lands in range
    n = adjacency.shape[0]
    if unreachable > np.iinfo(np.uint8).max:
        raise ValueError("unreachable sentinel must fit in uint8")

    neighbours = [np.flatnonzero(adjacency[i]) for i in range(n)]
    distances = np.full((n, n), unreachable, dtype=np.uint8)

    for source in range(n):
        distances[source, source] = 0
        frontier = np.array([source])
        depth = 0
        while frontier.size:
            depth += 1
            if depth >= unreachable:
                break
            nxt = np.unique(np.concatenate([neighbours[v] for v in frontier])) \
                if frontier.size else np.empty(0, dtype=int)
            nxt = nxt[distances[source, nxt] == unreachable]
            if nxt.size == 0:
                break
            distances[source, nxt] = depth
            frontier = nxt

    return distances
