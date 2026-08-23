# tests for the edge rules that turn embeddings into a semantic graph
#
# most of these run against hand built similarity matrices where the correct answer is
# known by inspection, rather than against the real embeddings, so a failure points at
# the rule and not at the model
import numpy as np
import pytest

from app.graph_builder import (
    KNNRule,
    ThresholdRule,
    all_pairs_distances,
    bridge_components,
    connected_components,
    cosine_matrix,
    to_adjacency_lists,
)


def sims_from(matrix):
    # builds a similarity matrix with the diagonal masked, as cosine_matrix would
    s = np.array(matrix, dtype=np.float32)
    np.fill_diagonal(s, -np.inf)
    return s


@pytest.fixture
def two_clusters():
    # words 0,1,2 are mutually close and 3,4,5 are mutually close, with a weak link
    # between the two groups at 0 <-> 3
    s = np.full((6, 6), 0.10, dtype=np.float32)
    for group in ([0, 1, 2], [3, 4, 5]):
        for a in group:
            for b in group:
                s[a, b] = 0.90
    s[0, 3] = s[3, 0] = 0.40
    np.fill_diagonal(s, -np.inf)
    return s


class TestCosineMatrix:
    def test_diagonal_is_masked(self):
        v = np.eye(4, dtype=np.float32)
        assert np.all(np.isneginf(np.diag(cosine_matrix(v))))

    def test_identical_vectors_score_one(self):
        v = np.array([[1.0, 0.0], [1.0, 0.0]], dtype=np.float32)
        assert cosine_matrix(v)[0, 1] == pytest.approx(1.0, abs=1e-5)

    def test_orthogonal_vectors_score_zero(self):
        v = np.array([[1.0, 0.0], [0.0, 1.0]], dtype=np.float32)
        assert cosine_matrix(v)[0, 1] == pytest.approx(0.0, abs=1e-5)

    def test_normalizes_unnormalized_input(self):
        # same directions as the unit case, just scaled, so results must match
        v = np.array([[3.0, 0.0], [5.0, 0.0]], dtype=np.float32)
        assert cosine_matrix(v)[0, 1] == pytest.approx(1.0, abs=1e-5)

    def test_output_is_symmetric(self):
        rng = np.random.default_rng(0)
        v = rng.normal(size=(8, 16)).astype(np.float32)
        s = cosine_matrix(v)
        off = ~np.eye(8, dtype=bool)
        assert np.allclose(s[off], s.T[off], atol=1e-6)


class TestThresholdRule:
    def test_connects_only_above_threshold(self, two_clusters):
        a = ThresholdRule(0.5).adjacency(two_clusters)
        assert a[0, 1] and a[3, 4]
        # the 0.40 cross link falls below the 0.5 bar
        assert not a[0, 3]

    def test_lower_threshold_admits_more_edges(self, two_clusters):
        strict = ThresholdRule(0.5).adjacency(two_clusters).sum()
        loose = ThresholdRule(0.3).adjacency(two_clusters).sum()
        assert loose > strict

    def test_no_self_edges(self, two_clusters):
        assert not ThresholdRule(0.0).adjacency(two_clusters).diagonal().any()

    def test_params_recorded(self):
        assert ThresholdRule(0.42).params() == {"threshold": 0.42}


class TestKNNRules:
    def test_union_gives_every_word_at_least_k_neighbours(self, two_clusters):
        # the guarantee that makes union forgiving: no word is ever a dead end
        a = KNNRule(k=2, mutual=False).adjacency(two_clusters)
        assert a.sum(axis=1).min() >= 2

    def test_mutual_is_a_subset_of_union(self, two_clusters):
        union = KNNRule(k=2, mutual=False, bridge=False).adjacency(two_clusters)
        mutual = KNNRule(k=2, mutual=True, bridge=False).adjacency(two_clusters)
        assert np.all(mutual <= union)

    def test_both_rules_are_symmetric(self, two_clusters):
        for mutual in (False, True):
            a = KNNRule(k=2, mutual=mutual).adjacency(two_clusters)
            assert np.array_equal(a, a.T)

    def test_no_self_edges(self, two_clusters):
        for mutual in (False, True):
            assert not KNNRule(k=3, mutual=mutual).adjacency(two_clusters).diagonal().any()

    def test_floor_blocks_weak_edges(self):
        # word 2 is far from everything, so with k=1 it would still pick up a neighbour
        s = sims_from([[0, 0.9, 0.1], [0.9, 0, 0.1], [0.1, 0.1, 0]])
        without = KNNRule(k=1, floor=0.0, bridge=False).adjacency(s)
        with_floor = KNNRule(k=1, floor=0.5, bridge=False).adjacency(s)
        assert without[2].any()
        assert not with_floor[2].any()

    def test_floor_applies_before_symmetry(self):
        # a weak edge must not sneak back in via the other endpoint's proposal
        s = sims_from([[0, 0.9, 0.2], [0.9, 0, 0.15], [0.2, 0.15, 0]])
        a = KNNRule(k=2, floor=0.5, mutual=False, bridge=False).adjacency(s)
        assert not a[0, 2] and not a[2, 0]

    def test_k_larger_than_vocabulary_is_clamped(self):
        s = sims_from([[0, 0.5], [0.5, 0]])
        a = KNNRule(k=99, bridge=False).adjacency(s)
        assert a[0, 1] and a.shape == (2, 2)

    def test_k_must_be_positive(self):
        with pytest.raises(ValueError):
            KNNRule(k=0)

    def test_mutual_prunes_hub_edges(self):
        # node 0 is everyone's nearest neighbour but reciprocates with only one of them,
        # which is exactly the hub pattern a global threshold cannot express
        n = 6
        s = np.full((n, n), 0.1, dtype=np.float32)
        for i in range(1, n):
            s[0, i] = s[i, 0] = 0.8
        s[0, 1] = s[1, 0] = 0.95
        np.fill_diagonal(s, -np.inf)

        union = KNNRule(k=1, mutual=False, bridge=False).adjacency(s)
        mutual = KNNRule(k=1, mutual=True, bridge=False).adjacency(s)
        assert union[0].sum() == n - 1
        assert mutual[0].sum() == 1

    def test_name_reflects_mode(self):
        assert KNNRule(mutual=False).name == "union_knn"
        assert KNNRule(mutual=True).name == "mutual_knn"


class TestConnectedComponents:
    def test_single_component(self):
        a = np.array([[0, 1, 0], [1, 0, 1], [0, 1, 0]], dtype=bool)
        assert connected_components(a).max() == 0

    def test_isolated_node_is_its_own_component(self):
        a = np.array([[0, 1, 0], [1, 0, 0], [0, 0, 0]], dtype=bool)
        assert connected_components(a).max() == 1

    def test_two_disjoint_pairs(self):
        a = np.zeros((4, 4), dtype=bool)
        a[0, 1] = a[1, 0] = a[2, 3] = a[3, 2] = True
        labels = connected_components(a)
        assert labels[0] == labels[1]
        assert labels[2] == labels[3]
        assert labels[0] != labels[2]


class TestBridging:
    def test_bridging_produces_one_component(self):
        # two pairs with no edges between them
        s = sims_from([[0, .9, .3, .2], [.9, 0, .1, .1], [.3, .1, 0, .9], [.2, .1, .9, 0]])
        a = np.zeros((4, 4), dtype=bool)
        a[0, 1] = a[1, 0] = a[2, 3] = a[3, 2] = True
        added = bridge_components(a, s)
        assert added == 1
        assert connected_components(a).max() == 0

    def test_bridge_uses_the_strongest_cross_edge(self):
        s = sims_from([[0, .9, .3, .2], [.9, 0, .1, .1], [.3, .1, 0, .9], [.2, .1, .9, 0]])
        a = np.zeros((4, 4), dtype=bool)
        a[0, 1] = a[1, 0] = a[2, 3] = a[3, 2] = True
        bridge_components(a, s)
        # 0-2 at 0.3 is the best available crossing
        assert a[0, 2] and a[2, 0]

    def test_already_connected_graph_is_untouched(self):
        s = sims_from([[0, .9], [.9, 0]])
        a = np.array([[False, True], [True, False]])
        assert bridge_components(a, s) == 0

    def test_mutual_knn_with_bridging_is_connected(self, two_clusters):
        rule = KNNRule(k=1, mutual=True, bridge=True)
        a = rule.adjacency(two_clusters)
        assert connected_components(a).max() == 0
        assert rule.bridges_added >= 1

    def test_bridging_can_be_disabled(self, two_clusters):
        rule = KNNRule(k=1, mutual=True, bridge=False)
        rule.adjacency(two_clusters)
        assert rule.bridges_added == 0


class TestAdjacencyLists:
    def test_round_trips_words(self):
        a = np.zeros((3, 3), dtype=bool)
        a[0, 1] = a[1, 0] = True
        lists = to_adjacency_lists(a, ["cat", "dog", "rock"])
        assert lists == {"cat": ["dog"], "dog": ["cat"], "rock": []}

    def test_neighbours_are_sorted(self):
        a = np.ones((3, 3), dtype=bool)
        np.fill_diagonal(a, False)
        assert to_adjacency_lists(a, ["c", "a", "b"])["c"] == ["a", "b"]


class TestAllPairsDistances:
    def test_distance_to_self_is_zero(self):
        a = np.array([[0, 1], [1, 0]], dtype=bool)
        assert np.all(np.diag(all_pairs_distances(a)) == 0)

    def test_path_lengths_on_a_chain(self):
        # 0 - 1 - 2 - 3
        n = 4
        a = np.zeros((n, n), dtype=bool)
        for i in range(n - 1):
            a[i, i + 1] = a[i + 1, i] = True
        d = all_pairs_distances(a)
        assert d[0, 1] == 1 and d[0, 2] == 2 and d[0, 3] == 3

    def test_unreachable_nodes_get_the_sentinel(self):
        a = np.zeros((3, 3), dtype=bool)
        a[0, 1] = a[1, 0] = True
        d = all_pairs_distances(a)
        assert d[0, 2] == 255 and d[2, 0] == 255

    def test_matrix_is_symmetric(self):
        rng = np.random.default_rng(1)
        a = rng.random((12, 12)) > 0.7
        a = a | a.T
        np.fill_diagonal(a, False)
        d = all_pairs_distances(a)
        assert np.array_equal(d, d.T)

    def test_agrees_with_a_naive_bfs(self):
        rng = np.random.default_rng(2)
        n = 20
        a = rng.random((n, n)) > 0.75
        a = a | a.T
        np.fill_diagonal(a, False)
        fast = all_pairs_distances(a)

        from collections import deque
        for src in range(n):
            seen = {src: 0}
            q = deque([src])
            while q:
                node = q.popleft()
                for nb in np.flatnonzero(a[node]):
                    if nb not in seen:
                        seen[nb] = seen[node] + 1
                        q.append(nb)
            for dst in range(n):
                assert fast[src, dst] == seen.get(dst, 255)
