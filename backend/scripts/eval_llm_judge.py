#!/usr/bin/env python3
# llm-as-judge eval for the semantic graph
#
# cosine similarity and graph statistics cannot tell you whether an edge actually reads
# as sensible to a person. a graph can score perfectly on connectivity and hub flatness
# while still linking 'glaze' to 'philosophy'. this asks claude to judge the edges the
# way a player would
# the methodology that makes this a measurement rather than a vibe check is the blind
# control group. we sample edges from the graph and an equal number of random
# non-edges, shuffle them together, and send them unlabelled. if the judge rates edges
# and non-edges the same, the graph carries no signal, no matter how good its absolute
# numbers look. the separation between the two is the actual result
#
# dev only, never runs in production or ci. needs ANTHROPIC_API_KEY
#
# usage:
#   python scripts/eval_llm_judge.py --dry-run          print prompts, call nothing
#   python scripts/eval_llm_judge.py --pairs 100
from __future__ import annotations

import argparse
import json
import logging
import os
import random
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
from pydantic import BaseModel, Field

BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))

from app.graph_builder import KNNRule, cosine_matrix  # noqa: E402

DATA_DIR = BACKEND / "data"
EVAL_DIR = BACKEND / "evals"
VECTORS = DATA_DIR / "embeddings_full.npz"

MODEL = "claude-opus-5"
PAIRS_PER_REQUEST = 25

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)-7s %(message)s",
                    datefmt="%H:%M:%S")
log = logging.getLogger("judge")


class PairVerdict(BaseModel):
    word_a: str
    word_b: str
    strength: int = Field(ge=1, le=5,
                          description="1 = no sensible connection, 5 = obviously connected")
    reason: str = Field(description="at most 12 words")


class PairBatch(BaseModel):
    verdicts: List[PairVerdict]


class PathVerdict(BaseModel):
    path: List[str]
    sensible: bool = Field(description="true if every consecutive step is a fair link")
    weakest_step: str = Field(description="the least defensible step, as 'a -> b'")
    reason: str = Field(description="at most 20 words")


class PathBatch(BaseModel):
    verdicts: List[PathVerdict]


PAIR_SYSTEM = (
    "You are judging word pairs for a word association game. Players connect two words "
    "through a chain of related words, so the bar is 'would a reasonable player accept "
    "this link', not 'are these synonyms'. Words related by theme, category, cause, "
    "or common association all count. Rate each pair 1 to 5. Be discriminating: some "
    "of these pairs are deliberately random and should score 1."
)

PATH_SYSTEM = (
    "You are judging solution paths for a word association game. A path is sensible "
    "only if EVERY consecutive step is a link a reasonable player would accept. "
    "Theme, category, cause and common association all count as valid links; strict "
    "synonymy is not required. One bad step makes the whole path not sensible."
)


def load_graph(dim: int, k: int) -> Tuple[np.ndarray, List[str]]:
    data = np.load(VECTORS, allow_pickle=True)
    vectors = data["vectors"].astype(np.float32)[:, :dim]
    words = list(data["words"])
    sims = cosine_matrix(vectors)
    return KNNRule(k=k, mutual=False).adjacency(sims), words


def sample_pairs(adjacency: np.ndarray, words: List[str], n: int,
                 rng: random.Random) -> List[Dict]:
    # equal numbers of real edges and random non-edges, tagged so we can score them
    # afterwards, but the tag is never shown to the judge
    edges = list(zip(*np.where(np.triu(adjacency))))
    rng.shuffle(edges)
    samples = [{"a": words[i], "b": words[j], "is_edge": True} for i, j in edges[:n]]

    seen = set()
    while len(samples) < 2 * n:
        i, j = rng.randrange(len(words)), rng.randrange(len(words))
        if i == j or adjacency[i, j] or (i, j) in seen:
            continue
        seen.add((i, j))
        samples.append({"a": words[i], "b": words[j], "is_edge": False})

    rng.shuffle(samples)
    return samples


def sample_paths(adjacency: np.ndarray, words: List[str], n: int,
                 rng: random.Random) -> List[List[str]]:
    from collections import deque

    neighbours = [np.flatnonzero(adjacency[i]) for i in range(len(words))]
    paths = []
    attempts = 0
    while len(paths) < n and attempts < n * 60:
        attempts += 1
        src, dst = rng.randrange(len(words)), rng.randrange(len(words))
        if src == dst:
            continue
        prev = {src: None}
        queue = deque([src])
        while queue and dst not in prev:
            node = queue.popleft()
            for nb in neighbours[node]:
                if nb not in prev:
                    prev[nb] = node
                    queue.append(nb)
        if dst not in prev:
            continue
        chain, node = [], dst
        while node is not None:
            chain.append(words[node])
            node = prev[node]
        chain.reverse()
        if 3 <= len(chain) <= 7:
            paths.append(chain)
    return paths


def render_pair_prompt(batch: List[Dict]) -> str:
    listing = "\n".join(f"{i + 1}. {p['a']} / {p['b']}" for i, p in enumerate(batch))
    return f"Rate each pair from 1 to 5.\n\n{listing}"


def render_path_prompt(batch: List[List[str]]) -> str:
    listing = "\n".join(f"{i + 1}. {' -> '.join(p)}" for i, p in enumerate(batch))
    return f"Judge each path.\n\n{listing}"


def call(client, system: str, prompt: str, schema):
    response = client.messages.parse(
        model=MODEL,
        max_tokens=8000,
        system=system,
        thinking={"type": "adaptive"},
        messages=[{"role": "user", "content": prompt}],
        output_format=schema,
    )
    return response.parsed_output


def chunk(items: List, size: int) -> List[List]:
    return [items[i:i + size] for i in range(0, len(items), size)]


def judge_pairs(client, samples: List[Dict], workers: int) -> List[Dict]:
    batches = chunk(samples, PAIRS_PER_REQUEST)
    log.info("Judging %d pairs in %d requests", len(samples), len(batches))

    lookup = {(s["a"], s["b"]): s for s in samples}
    scored: List[Dict] = []

    def run(batch):
        return call(client, PAIR_SYSTEM, render_pair_prompt(batch), PairBatch)

    with ThreadPoolExecutor(max_workers=workers) as pool:
        for result in pool.map(run, batches):
            for verdict in result.verdicts:
                source = (lookup.get((verdict.word_a, verdict.word_b))
                          or lookup.get((verdict.word_b, verdict.word_a)))
                if source is None:
                    continue
                scored.append({"a": verdict.word_a, "b": verdict.word_b,
                               "is_edge": source["is_edge"],
                               "strength": verdict.strength, "reason": verdict.reason})
    return scored


def judge_paths(client, paths: List[List[str]], workers: int) -> List[Dict]:
    batches = chunk(paths, 10)
    log.info("Judging %d paths in %d requests", len(paths), len(batches))
    out: List[Dict] = []

    def run(batch):
        return call(client, PATH_SYSTEM, render_path_prompt(batch), PathBatch)

    with ThreadPoolExecutor(max_workers=workers) as pool:
        for result in pool.map(run, batches):
            out.extend(v.model_dump() for v in result.verdicts)
    return out


def summarize(pairs: List[Dict], paths: List[Dict]) -> Dict:
    edge = [p["strength"] for p in pairs if p["is_edge"]]
    control = [p["strength"] for p in pairs if not p["is_edge"]]

    summary = {
        "edges_judged": len(edge),
        "controls_judged": len(control),
        "edge_mean": float(np.mean(edge)) if edge else 0.0,
        "control_mean": float(np.mean(control)) if control else 0.0,
        "separation": float(np.mean(edge) - np.mean(control)) if edge and control else 0.0,
        # an edge scoring 1 or 2 is one a player would reject, which is the number that
        # actually matters for whether the game feels fair
        "edge_reject_rate": float(np.mean([s <= 2 for s in edge])) if edge else 0.0,
        "control_reject_rate": float(np.mean([s <= 2 for s in control])) if control else 0.0,
        "paths_judged": len(paths),
        "path_sensible_rate": float(np.mean([p["sensible"] for p in paths])) if paths else 0.0,
    }
    summary["worst_edges"] = sorted(
        [p for p in pairs if p["is_edge"]], key=lambda p: p["strength"]
    )[:15]
    return summary


def render_report(summary: Dict) -> str:
    out = ["# LLM judge evaluation", "",
           f"Judge: **{MODEL}**. Edges and random non-edges were shuffled together and "
           "sent unlabelled, so the judge could not tell them apart.", "",
           "| Metric | Real edges | Random control |", "|---|---|---|",
           f"| Pairs judged | {summary['edges_judged']} | {summary['controls_judged']} |",
           f"| Mean strength (1-5) | {summary['edge_mean']:.2f} | {summary['control_mean']:.2f} |",
           f"| Rejected (scored 1-2) | {summary['edge_reject_rate']:.1%} | {summary['control_reject_rate']:.1%} |",
           "",
           f"**Separation: {summary['separation']:+.2f}** strength points between real "
           "edges and random pairs. A separation near zero would mean the graph carries "
           "no more signal than chance.", "",
           f"Paths judged fully sensible: **{summary['path_sensible_rate']:.1%}** "
           f"of {summary['paths_judged']}.", ""]

    if summary["worst_edges"]:
        out += ["## Weakest edges the judge found", "",
                "These are real graph edges a player would likely reject.", "",
                "| Pair | Strength | Reason |", "|---|---|---|"]
        out += [f"| {e['a']} / {e['b']} | {e['strength']} | {e['reason']} |"
                for e in summary["worst_edges"]]
        out.append("")
    return "\n".join(out) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description="llm-as-judge eval for the semantic graph")
    ap.add_argument("--pairs", type=int, default=150,
                    help="real edges to sample; an equal number of controls is added")
    ap.add_argument("--paths", type=int, default=40)
    ap.add_argument("--dim", type=int, default=1024)
    ap.add_argument("--k", type=int, default=10)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--dry-run", action="store_true",
                    help="print the sampled prompts and exit without calling the api")
    args = ap.parse_args()

    rng = random.Random(args.seed)
    adjacency, words = load_graph(args.dim, args.k)
    samples = sample_pairs(adjacency, words, args.pairs, rng)
    paths = sample_paths(adjacency, words, args.paths, rng)

    if args.dry_run:
        print("=== pair prompt (first batch) ===")
        print(render_pair_prompt(samples[:PAIRS_PER_REQUEST]))
        print("\n=== path prompt (first batch) ===")
        print(render_path_prompt(paths[:10]))
        print(f"\n{len(samples)} pairs "
              f"({sum(s['is_edge'] for s in samples)} edges / "
              f"{sum(not s['is_edge'] for s in samples)} controls), {len(paths)} paths")
        return 0

    if not os.environ.get("ANTHROPIC_API_KEY"):
        log.error("ANTHROPIC_API_KEY is not set; use --dry-run to inspect prompts")
        return 1

    import anthropic

    client = anthropic.Anthropic()
    summary = summarize(judge_pairs(client, samples, args.workers),
                        judge_paths(client, paths, args.workers))

    EVAL_DIR.mkdir(parents=True, exist_ok=True)
    (EVAL_DIR / "llm_judge.json").write_text(json.dumps(summary, indent=2) + "\n")
    (EVAL_DIR / "llm_judge.md").write_text(render_report(summary))

    log.info("edge mean %.2f vs control %.2f (separation %+.2f)",
             summary["edge_mean"], summary["control_mean"], summary["separation"])
    log.info("Wrote evals/llm_judge.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
