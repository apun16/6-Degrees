# tests for the eval harness itself
#
# an eval that is silently wrong is worse than no eval, because it launders a bad
# configuration into a decision that looks evidence backed. these cover the statistics
# and the selection logic against cases where the answer is known
import numpy as np
import pytest

from scripts.eval_embeddings import (
    BENCHMARKS,
    gini,
    load_benchmark,
    objective,
    select_configuration,
    spearman,
)


class TestSpearman:
    def test_perfect_correlation(self):
        assert spearman([1, 2, 3, 4, 5], [1, 2, 3, 4, 5]) == pytest.approx(1.0)

    def test_perfect_anticorrelation(self):
        assert spearman([1, 2, 3, 4, 5], [5, 4, 3, 2, 1]) == pytest.approx(-1.0)

    def test_is_rank_based_not_value_based(self):
        # a monotone but wildly nonlinear transform must not change the result, which
        # is the whole reason spearman is used here rather than pearson
        x = [1, 2, 3, 4, 5]
        assert spearman(x, [1, 100, 10_000, 1e6, 1e8]) == pytest.approx(1.0)

    def test_handles_ties_with_average_ranks(self):
        assert spearman([1, 2, 2, 3], [1, 2, 2, 3]) == pytest.approx(1.0)

    def test_constant_input_returns_zero_not_nan(self):
        result = spearman([1, 1, 1, 1], [1, 2, 3, 4])
        assert result == 0.0 and not np.isnan(result)

    def test_matches_a_known_value(self):
        # hand computed: ranks 0,1,2,3 against 0,2,1,3 gives rho = 0.8
        assert spearman([1, 2, 3, 4], [1, 3, 2, 4]) == pytest.approx(0.8)


class TestGini:
    def test_uniform_distribution_is_zero(self):
        assert gini(np.array([5, 5, 5, 5])) == pytest.approx(0.0)

    def test_concentrated_distribution_is_high(self):
        assert gini(np.array([0, 0, 0, 100])) > 0.7

    def test_all_zero_returns_zero_not_nan(self):
        assert gini(np.array([0, 0, 0])) == 0.0

    def test_more_unequal_scores_higher(self):
        assert gini(np.array([1, 2, 3, 4])) < gini(np.array([1, 1, 1, 40]))


class TestBenchmarkParsing:
    @pytest.mark.parametrize("name,expected", [
        ("SimLex-999", 999), ("WS-353-ALL", 353), ("WS-353-SIM", 203),
        ("WS-353-REL", 252), ("MEN-3k", 3000), ("MTurk-771", 771), ("RG-65", 65),
    ])
    def test_row_counts_match_published_sizes(self, name, expected):
        # a parser that silently drops rows would quietly change every score
        assert len(load_benchmark(BENCHMARKS[name][0])) == expected

    def test_simlex_header_is_skipped(self):
        rows = load_benchmark(BENCHMARKS["SimLex-999"][0])
        assert all(isinstance(score, float) for _, _, score in rows)
        assert ("word1", "word2") not in [(a, b) for a, b, _ in rows]

    def test_words_are_lowercased(self):
        for a, b, _ in load_benchmark(BENCHMARKS["MEN-3k"][0]):
            assert a == a.lower() and b == b.lower()

    def test_scores_vary(self):
        scores = [s for _, _, s in load_benchmark(BENCHMARKS["WS-353-ALL"][0])]
        assert min(scores) != max(scores)


class TestObjective:
    def base(self, **over):
        m = {"playable": 0.99, "median_hops": 4.0, "components": 1,
             "gini": 0.15, "one_hop": 0.01}
        m.update(over)
        return m

    def test_ideal_graph_scores_near_one(self):
        assert objective(self.base()) > 0.95

    def test_disconnected_graph_is_penalised(self):
        assert objective(self.base(components=7)) < objective(self.base())

    def test_unplayable_graph_scores_low(self):
        assert objective(self.base(playable=0.10, median_hops=10.0)) < 0.5

    def test_hub_heavy_graph_is_penalised(self):
        assert objective(self.base(gini=0.60)) < objective(self.base(gini=0.10))

    def test_trivial_two_hop_graph_beaten_by_four_hop(self):
        # the current production behaviour: everything two hops apart is not a puzzle
        assert objective(self.base(median_hops=2.0)) < objective(self.base(median_hops=4.0))


class TestSelectConfiguration:
    def sweep_rows(self):
        # rule A is clearly better, and is tied across every dimension, which is the
        # exact situation that makes an argmax over score pick a dimension by accident
        rows = []
        for dim in (256, 512, 1024, 2048, 4096):
            rows.append({"config": "ruleA", "dim": dim, "score": 0.98, "edges": 100,
                         "degree_median": 12, "gini": 0.15, "playable": 0.99,
                         "median_hops": 4.0})
            rows.append({"config": "ruleB", "dim": dim, "score": 0.72, "edges": 900,
                         "degree_median": 400, "gini": 0.30, "playable": 0.72,
                         "median_hops": 2.0})
        return rows

    def curve(self):
        return [{"dim": 256, "relatedness_mean": 0.757},
                {"dim": 512, "relatedness_mean": 0.776},
                {"dim": 1024, "relatedness_mean": 0.789},
                {"dim": 2048, "relatedness_mean": 0.797},
                {"dim": 4096, "relatedness_mean": 0.800}]

    def test_picks_the_better_rule(self):
        chosen = select_configuration({"_dimension_curve": self.curve()}, self.sweep_rows())
        assert chosen["rule"] == "ruleA"

    def test_dimension_comes_from_the_curve_not_the_tie(self):
        # 1024 retains 98.6% of peak, 512 only 97.0%, so 1024 is the smallest viable
        chosen = select_configuration({"_dimension_curve": self.curve()}, self.sweep_rows())
        assert chosen["dim"] == 1024

    def test_stricter_retention_demands_a_wider_vector(self):
        import scripts.eval_embeddings as ev
        original = ev.QUALITY_RETENTION
        ev.QUALITY_RETENTION = 0.999
        try:
            chosen = select_configuration({"_dimension_curve": self.curve()}, self.sweep_rows())
            assert chosen["dim"] == 4096
        finally:
            ev.QUALITY_RETENTION = original

    def test_falls_back_when_no_curve_is_available(self):
        chosen = select_configuration({}, self.sweep_rows())
        assert chosen["rule"] == "ruleA"
        assert chosen["dim"] == 4096

    def test_returns_none_without_a_sweep(self):
        assert select_configuration({}, []) is None
