#!/usr/bin/env python3
# eval harness for the embedding upgrade and the semantic graph
#   --benchmarks  intrinsic word similarity correlation against human judgements.
#                 loads the embedding models, so it is slow, but it is what proves
#                 qwen3 is actually better than the minilm baseline rather than just
#                 newer
#   --sweep       graph health across matryoshka dimension, edge rule and k. reads the
#                 prebuilt vectors only, so it re-runs in seconds and is what picks the
#                 shipped configuration
# both write into evals/report.md
# a note on which benchmarks matter here. simlex-999 measures similarity
# and penalises association, so it scores cup/coffee low. ws-353-rel, men and mturk
# measure relatedness. this game is built on association, a player linking heart to
# love to family, so the relatedness sets are the aligned ones and simlex is reported
# as a contrast :)
from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))

from app.graph_builder import (  # noqa: E402
    KNNRule,
    ThresholdRule,
    all_pairs_distances,
    connected_components,
    cosine_matrix,
)

DATA_DIR = BACKEND / "data"
BENCH_DIR = DATA_DIR / "benchmarks"
EVAL_DIR = BACKEND / "evals"
VECTORS = DATA_DIR / "embeddings_full.npz"

BASELINE_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# name -> (filename, kind). kind records what the humans were asked to rate, which is
# the difference between a benchmark this game should chase and one it should not
BENCHMARKS = {
    "SimLex-999": ("SimLex-999.txt", "similarity"),
    "WS-353-ALL": ("EN-WS-353-ALL.txt", "mixed"),
    "WS-353-SIM": ("EN-WS-353-SIM.txt", "similarity"),
    "WS-353-REL": ("EN-WS-353-REL.txt", "relatedness"),
    "MEN-3k": ("EN-MEN-TR-3k.txt", "relatedness"),
    "MTurk-771": ("EN-MTurk-771.txt", "relatedness"),
    "RG-65": ("EN-RG-65.txt", "similarity"),
}

SWEEP_DIMS = [256, 512, 1024, 2048, 4096]

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)-7s %(message)s",
                    datefmt="%H:%M:%S")
log = logging.getLogger("eval")


# ---------------------------------------------------------------- statistics

def spearman(a: np.ndarray, b: np.ndarray) -> float:
    # rank correlation, implemented on numpy so the backend does not pick up scipy
    # just for one function. ties get average ranks, which is what makes this spearman
    # rather than a plain pearson on argsort positions
    def rank(x):
        order = np.argsort(x)
        ranks = np.empty(len(x), dtype=np.float64)
        ranks[order] = np.arange(len(x), dtype=np.float64)
        # average the ranks inside each group of equal values
        _, inverse, counts = np.unique(x, return_inverse=True, return_counts=True)
        sums = np.zeros(len(counts))
        np.add.at(sums, inverse, ranks)
        return (sums / counts)[inverse]

    ra, rb = rank(np.asarray(a, float)), rank(np.asarray(b, float))
    ra -= ra.mean()
    rb -= rb.mean()
    denom = np.sqrt((ra**2).sum() * (rb**2).sum())
    return float((ra @ rb) / denom) if denom else 0.0


def gini(values: np.ndarray) -> float:
    # inequality of the degree distribution: 0 means every word has the same number of
    # neighbours, higher means a few hub words dominate the graph
    x = np.sort(np.asarray(values, dtype=np.float64))
    n = len(x)
    total = x.sum()
    if n == 0 or total == 0:
        return 0.0
    return float((2 * np.arange(1, n + 1) - n - 1) @ x / (n * total))


# ---------------------------------------------------------------- benchmarks

def load_benchmark(filename: str) -> List[Tuple[str, str, float]]:
    path = BENCH_DIR / filename
    rows = []
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        parts = line.replace("\t", " ").split()
        if len(parts) < 3:
            continue
        # simlex ships a header row and extra columns; both are handled by simply
        # skipping anything whose third field is not a number
        try:
            score = float(parts[3]) if filename.startswith("SimLex") else float(parts[2])
        except (ValueError, IndexError):
            continue
        rows.append((parts[0].lower(), parts[1].lower(), score))
    return rows


def benchmark_vocabulary() -> List[str]:
    words = set()
    for filename, _ in BENCHMARKS.values():
        for a, b, _ in load_benchmark(filename):
            words.update((a, b))
    return sorted(words)


def cache_path(model_name: str) -> Path:
    return BENCH_DIR / f"vectors_{model_name.split('/')[-1]}.npz"


def embed_with(model_name: str, words: List[str], instruction: Optional[str],
               batch_size: int) -> Dict[str, np.ndarray]:
    # cached to disk because re-encoding 2400 words with an 8b model to re-render a
    # table is a waste of four minutes, and the dimension curve below needs to reuse
    # exactly these vectors
    cache = cache_path(model_name)
    if cache.exists():
        stored = np.load(cache, allow_pickle=True)
        if list(stored["words"]) == words:
            log.info("Reusing cached vectors for %s", model_name)
            return {w: v for w, v in zip(words, stored["vectors"].astype(np.float32))}

    import torch
    from sentence_transformers import SentenceTransformer

    log.info("Loading %s ...", model_name)
    kwargs = {}
    if "Qwen3" in model_name:
        kwargs = {
            "model_kwargs": {"dtype": torch.float16, "low_cpu_mem_usage": True},
            "tokenizer_kwargs": {"padding_side": "left"},
        }
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    model = SentenceTransformer(model_name, device=device, **kwargs)
    model.max_seq_length = 32

    prompt = f"Instruct: {instruction}\nQuery:" if instruction else None
    t0 = time.time()
    vectors = model.encode(words, prompt=prompt, batch_size=batch_size,
                           convert_to_numpy=True, normalize_embeddings=True,
                           show_progress_bar=True)
    log.info("Encoded %d words in %.0fs", len(words), time.time() - t0)

    del model
    if device == "mps":
        try:
            torch.mps.empty_cache()
        except Exception:  # noqa: BLE001
            pass

    vectors = np.asarray(vectors, dtype=np.float32)
    BENCH_DIR.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(cache, vectors=vectors.astype(np.float16),
                        words=np.array(words, dtype=object))
    return {w: v for w, v in zip(words, vectors)}


def dimension_curve(vectors: Dict[str, np.ndarray]) -> List[Dict]:
    # the graph sweep cannot choose a matryoshka dimension: its metrics are structural
    # (connectivity, hub flatness, path length) and they saturate, scoring 256-d and
    # 4096-d identically. structure says nothing about whether the neighbours are the
    # semantically right ones
    #
    # this measures truncation directly instead, scoring the human judgement benchmarks
    # at each width. it is the evidence the composite objective cannot provide
    words = sorted(vectors)
    matrix = np.stack([vectors[w] for w in words])

    rows = []
    for dim in SWEEP_DIMS:
        sliced = matrix[:, :dim]
        sliced = sliced / np.maximum(np.linalg.norm(sliced, axis=1, keepdims=True), 1e-12)
        scored = score_benchmarks({w: v for w, v in zip(words, sliced)})
        related = [s["spearman"] for n, s in scored.items()
                   if BENCHMARKS[n][1] == "relatedness"]
        rows.append({
            "dim": dim,
            "relatedness_mean": float(np.mean(related)),
            "per_benchmark": {n: s["spearman"] for n, s in scored.items()},
        })
        log.info("dim=%-5d relatedness mean spearman = %.4f", dim, rows[-1]["relatedness_mean"])
    return rows


def score_benchmarks(vectors: Dict[str, np.ndarray]) -> Dict[str, Dict[str, float]]:
    results = {}
    for name, (filename, kind) in BENCHMARKS.items():
        pairs = load_benchmark(filename)
        predicted, gold = [], []
        for a, b, score in pairs:
            if a in vectors and b in vectors:
                predicted.append(float(vectors[a] @ vectors[b]))
                gold.append(score)
        results[name] = {
            "spearman": spearman(predicted, gold) if predicted else 0.0,
            "pairs": len(predicted),
            "total": len(pairs),
            "kind": kind,
        }
    return results


def run_benchmarks(batch_size: int) -> Dict[str, Dict]:
    words = benchmark_vocabulary()
    log.info("Benchmark vocabulary: %d unique words", len(words))

    meta = json.loads((DATA_DIR / "embeddings_full.meta.json").read_text())
    instruction = meta["instruction"]

    out = {}
    log.info("--- baseline: %s ---", BASELINE_MODEL)
    out[BASELINE_MODEL] = score_benchmarks(
        embed_with(BASELINE_MODEL, words, None, max(batch_size, 64))
    )
    log.info("--- upgrade: %s ---", meta["model"])
    upgrade_vectors = embed_with(meta["model"], words, instruction, batch_size)
    out[meta["model"]] = score_benchmarks(upgrade_vectors)

    log.info("--- matryoshka dimension curve ---")
    out["_dimension_curve"] = dimension_curve(upgrade_vectors)
    return out


# ---------------------------------------------------------------- graph sweep

def graph_metrics(adjacency: np.ndarray) -> Dict[str, float]:
    n = adjacency.shape[0]
    degrees = adjacency.sum(axis=1)
    distances = all_pairs_distances(adjacency)
    offdiag = distances[~np.eye(n, dtype=bool)]
    reachable = offdiag[offdiag != 255]

    return {
        "edges": int(adjacency.sum() // 2),
        "degree_median": float(np.median(degrees)),
        "degree_max": int(degrees.max()),
        "degree_min": int(degrees.min()),
        "gini": gini(degrees),
        "components": int(connected_components(adjacency).max() + 1),
        # the game rejects paths under 2 steps and caps them at 6, so these two are the
        # metrics that actually decide whether a puzzle is playable
        "one_hop": float(np.mean(offdiag == 1)),
        "playable": float(np.mean((offdiag >= 2) & (offdiag <= 6))),
        "median_hops": float(np.median(reachable)) if reachable.size else 0.0,
        "max_hops": int(reachable.max()) if reachable.size else 0,
    }


def objective(m: Dict[str, float]) -> float:
    # composite score used to pick the shipped configuration. weights are explicit and
    # deliberately few, so the choice can be argued with rather than taken on trust
    #
    #   playable    fraction of word pairs that make a legal puzzle, 2 to 6 steps
    #   one_hop     pairs already adjacent, unusable as puzzles, penalised
    #   gini        hub concentration, penalised
    #   difficulty  how close the median path is to 4 hops, which sits mid way in the
    #               6 step budget and leaves room for a player to beat the algorithm
    difficulty = 1.0 - min(abs(m["median_hops"] - 4.0) / 4.0, 1.0)
    connected = 1.0 if m["components"] == 1 else 0.0
    return (0.40 * m["playable"]
            + 0.25 * difficulty
            + 0.20 * connected
            + 0.10 * (1.0 - m["gini"])
            + 0.05 * (1.0 - m["one_hop"]))


def candidate_rules() -> List:
    rules = [ThresholdRule(t) for t in (0.45, 0.55, 0.65)]
    rules += [KNNRule(k=k, mutual=False) for k in (4, 6, 8, 10, 12, 15, 20)]
    rules += [KNNRule(k=k, mutual=True) for k in (6, 10, 15, 20)]
    return rules


def run_sweep(dims: List[int]) -> List[Dict]:
    data = np.load(VECTORS, allow_pickle=True)
    full = data["vectors"].astype(np.float32)
    log.info("Sweeping %d dimensions x %d rules", len(dims), len(candidate_rules()))

    rows = []
    for dim in dims:
        sims = cosine_matrix(full[:, :dim])
        for rule in candidate_rules():
            t0 = time.time()
            metrics = graph_metrics(rule.adjacency(sims))
            row = {"dim": dim, "rule": rule.name, "config": rule.describe(), **metrics}
            row["score"] = objective(metrics)
            rows.append(row)
            log.info("dim=%-5d %-34s playable=%.1f%% med=%.1f gini=%.2f score=%.3f (%.1fs)",
                     dim, rule.describe(), 100 * metrics["playable"],
                     metrics["median_hops"], metrics["gini"], row["score"],
                     time.time() - t0)
    return rows


# ---------------------------------------------------------------- reporting

QUALITY_RETENTION = 0.98


def select_configuration(bench: Optional[Dict], sweep: Optional[List[Dict]]) -> Optional[Dict]:
    # the two halves of the eval answer two different questions, and combining them by
    # taking a single argmax over the sweep would be wrong: the sweep's top rows are
    # tied to within 0.001 across every dimension, so the winner would be decided by
    # tie order rather than by evidence
    #
    #   edge rule   from the sweep, which discriminates it cleanly (0.982 vs 0.722)
    #   dimension   from the benchmark curve, which is the only measurement that can
    #               see a difference between 256-d and 4096-d
    if not sweep:
        return None

    # average each rule's score across dimensions so the choice is not an artifact of
    # whichever dimension happened to round up
    by_rule: Dict[str, List[float]] = {}
    for row in sweep:
        by_rule.setdefault(row["config"], []).append(row["score"])
    best_rule = max(by_rule, key=lambda c: float(np.mean(by_rule[c])))

    curve = (bench or {}).get("_dimension_curve")
    if curve:
        ceiling = max(r["relatedness_mean"] for r in curve)
        # smallest width that still retains most of the semantic quality, since every
        # doubling past that costs artifact size for a fraction of a correlation point
        viable = [r for r in curve
                  if r["relatedness_mean"] >= QUALITY_RETENTION * ceiling]
        chosen = min(viable, key=lambda r: r["dim"]) if viable else \
            max(curve, key=lambda r: r["relatedness_mean"])
        dim, retention = chosen["dim"], chosen["relatedness_mean"] / ceiling
        basis = (f"smallest width retaining >= {QUALITY_RETENTION:.0%} of peak "
                 f"relatedness (this one retains {retention:.1%})")
    else:
        dim = max(r["dim"] for r in sweep)
        basis = "no dimension curve available, defaulting to full width"

    row = next((r for r in sweep if r["config"] == best_rule and r["dim"] == dim), None)
    return {"rule": best_rule, "dim": dim, "dim_basis": basis,
            "rule_score": float(np.mean(by_rule[best_rule])),
            "metrics": row}


def render_report(bench: Optional[Dict], sweep: Optional[List[Dict]]) -> str:
    meta = json.loads((DATA_DIR / "embeddings_full.meta.json").read_text())
    out = ["# Embedding and graph evaluation", ""]
    out += [f"Vocabulary: **{meta['word_count']} words**  ",
            f"Model: **{meta['model']}** at {meta['dimension']}-d  ", ""]

    if bench:
        out += ["## Intrinsic benchmarks (Spearman vs human judgement)", "",
                "Higher is better. `relatedness` sets are the ones aligned with this "
                "game, which is about association rather than strict synonymy; "
                "SimLex deliberately penalises association and is shown as a contrast.",
                ""]
        models = [m for m in bench if not m.startswith("_")]
        out += ["| Benchmark | Measures | " + " | ".join(models) + " | Delta |",
                "|---|---|" + "---|" * (len(models) + 1)]
        for name, (_, kind) in BENCHMARKS.items():
            scores = [bench[m][name]["spearman"] for m in models]
            delta = scores[-1] - scores[0]
            cells = " | ".join(f"{s:.3f}" for s in scores)
            out.append(f"| {name} | {kind} | {cells} | {delta:+.3f} |")
        out.append("")

        for label, kinds in [("relatedness", {"relatedness"}), ("similarity", {"similarity"})]:
            means = [float(np.mean([bench[m][n]["spearman"]
                                    for n, (_, k) in BENCHMARKS.items() if k in kinds]))
                     for m in models]
            out.append(f"- Mean over **{label}** sets: " +
                       ", ".join(f"{m.split('/')[-1]} {s:.3f}" for m, s in zip(models, means)) +
                       f"  (delta {means[-1] - means[0]:+.3f})")
        out.append("")

        curve = bench.get("_dimension_curve")
        if curve:
            top = max(r["relatedness_mean"] for r in curve)
            out += ["### Matryoshka dimension", "",
                    "Mean Spearman over the relatedness benchmarks at each truncation. "
                    "The graph sweep below cannot choose a dimension, since its metrics "
                    "are structural and saturate; this measures semantics directly.", "",
                    "| dim | relatedness Spearman | vs best | artifact size |",
                    "|---|---|---|---|"]
            for r in curve:
                mb = 1761 * r["dim"] * 2 / 1e6
                out.append(f"| {r['dim']} | {r['relatedness_mean']:.4f} | "
                           f"{r['relatedness_mean'] - top:+.4f} | {mb:.1f} MB |")
            out.append("")

    if sweep:
        chosen = select_configuration(bench, sweep)
        best = next((r for r in sweep
                     if r["config"] == chosen["rule"] and r["dim"] == chosen["dim"]),
                    max(sweep, key=lambda r: r["score"])) if chosen else \
            max(sweep, key=lambda r: r["score"])
        out += ["## Graph configuration sweep", "",
                "`playable` is the fraction of word pairs that form a legal puzzle "
                "(2 to 6 steps). `1-hop` pairs are already adjacent and therefore "
                "unusable. `gini` measures hub concentration, lower is flatter.", "",
                "| dim | rule | edges | deg med | deg max | gini | comp | 1-hop | playable | med hops | score |",
                "|---|---|---|---|---|---|---|---|---|---|---|"]
        for r in sorted(sweep, key=lambda r: -r["score"]):
            marker = " **<-**" if r is best else ""
            out.append(
                f"| {r['dim']} | {r['config']} | {r['edges']} | {r['degree_median']:.0f} | "
                f"{r['degree_max']} | {r['gini']:.2f} | {r['components']} | "
                f"{r['one_hop']:.1%} | {r['playable']:.1%} | {r['median_hops']:.1f} | "
                f"{r['score']:.3f}{marker} |")
        if chosen:
            m = chosen["metrics"] or best
            out += ["", "## Selected configuration", "",
                    f"**`{chosen['rule']}` at {chosen['dim']}-d**", "",
                    f"- Edge rule chosen by the sweep, mean score {chosen['rule_score']:.3f} "
                    f"across dimensions.",
                    f"- Dimension chosen by the benchmark curve, not the sweep: "
                    f"{chosen['dim_basis']}. The sweep's top rows are tied to within "
                    f"0.001 across all five widths, so it cannot make this call.",
                    f"- Resulting graph: {m['edges']} edges, median degree "
                    f"{m['degree_median']:.0f}, gini {m['gini']:.2f}, "
                    f"{m['playable']:.1%} of pairs playable, median {m['median_hops']:.0f} hops.",
                    ""]

    return "\n".join(out) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description="evaluate embeddings and graph configurations")
    ap.add_argument("--benchmarks", action="store_true",
                    help="run intrinsic word similarity benchmarks (loads models, slow)")
    ap.add_argument("--sweep", action="store_true",
                    help="sweep graph configurations (fast, uses prebuilt vectors)")
    ap.add_argument("--dims", type=int, nargs="+", default=SWEEP_DIMS)
    ap.add_argument("--batch-size", type=int, default=16)
    ap.add_argument("--report-only", action="store_true",
                    help="re-render the report from cached results, computing nothing")
    args = ap.parse_args()

    if not args.benchmarks and not args.sweep and not args.report_only:
        args.benchmarks = args.sweep = True

    EVAL_DIR.mkdir(parents=True, exist_ok=True)
    results_path = EVAL_DIR / "results.json"
    existing = json.loads(results_path.read_text()) if results_path.exists() else {}

    if args.benchmarks and not args.report_only:
        existing["benchmarks"] = run_benchmarks(args.batch_size)
    if args.sweep and not args.report_only:
        existing["sweep"] = run_sweep(args.dims)

    results_path.write_text(json.dumps(existing, indent=2) + "\n")
    report = render_report(existing.get("benchmarks"), existing.get("sweep"))
    (EVAL_DIR / "report.md").write_text(report)

    log.info("Wrote %s and %s", results_path.name, "report.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
