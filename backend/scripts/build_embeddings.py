#!/usr/bin/env python3
# offline script: embeds the game vocabulary with qwen3-embedding and saves the vectors
# this runs on a dev machine, never in production
#
# the game vocabulary is fixed and closed (validate_word rejects anything outside
# data/words.json) so the backend never needs to embed at request time. that is what
# lets us use an 8b model here and ship nothing but a numpy array
#
# we encode once at the model's native 4096 dimensions and save that. qwen3-embedding
# supports matryoshka truncation anywhere in 32..4096, and truncating is just a slice
# plus renormalize, so the eval sweep can try every candidate dimension without paying
# for a re-encode. the shipped truncated artifact is derived from this file later
#
# usage:
#   python scripts/build_embeddings.py                 8b, falls back to 4b
#   python scripts/build_embeddings.py --model 4B      force the 4b model
#   python scripts/build_embeddings.py --limit 32      smoke test, writes nothing
from __future__ import annotations

import argparse
import json
import logging
import platform
import sys
import time
from pathlib import Path
from typing import List, Optional, Tuple

import numpy as np

BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))

DATA_DIR = BACKEND / "data"
WORDS_FILE = DATA_DIR / "words.json"
OUT_FILE = DATA_DIR / "embeddings_full.npz"

# tried in order, first one that loads and encodes wins
# the 8b is roughly 16gb in fp16 which is tight on 24gb of unified memory, so the 4b
# is a real fallback and not just belt and braces
MODEL_CANDIDATES = {
    "8B": "Qwen/Qwen3-Embedding-8B",
    "4B": "Qwen/Qwen3-Embedding-4B",
    "0.6B": "Qwen/Qwen3-Embedding-0.6B",
}
DEFAULT_ORDER = ["8B", "4B"]

# qwen3-embedding is instruction aware and the model card notes that omitting the
# instruction costs 1 to 5 percent. this task description is tuned for the game: we
# want words related by theme and association, not just synonyms
INSTRUCTION = (
    "Given a word, retrieve other words that are related to it by meaning, "
    "theme, category, or common association"
)

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s  %(levelname)-7s %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("build_embeddings")


def load_vocabulary(limit: Optional[int] = None) -> List[str]:
    # reads the vocabulary in a deterministic sorted order
    # order matters because it defines the row index of every vector, and vocab.json
    # maps words to those indices. sorting keeps rebuilds reproducible
    data = json.loads(WORDS_FILE.read_text(encoding="utf-8"))
    words = sorted({w.lower().strip() for w in data["words"]})
    if limit:
        words = words[:limit]
    log.info("Loaded %d words from %s", len(words), WORDS_FILE.name)
    return words


def pick_device() -> str:
    import torch

    if torch.backends.mps.is_available():
        return "mps"
    if torch.cuda.is_available():
        return "cuda"
    return "cpu"


def is_memory_error(exc: BaseException) -> bool:
    # mps and cuda oom surfaces as several unrelated exception types and messages
    text = f"{type(exc).__name__}: {exc}".lower()
    needles = (
        "out of memory", "oom", "cannot allocate", "insufficient memory",
        "mps backend out of memory", "invalid buffer size", "failed to allocate",
    )
    return isinstance(exc, (MemoryError, RuntimeError)) and any(n in text for n in needles)


def load_model(repo_id: str, device: str):
    import torch
    from sentence_transformers import SentenceTransformer

    log.info("Loading %s onto %s (fp16)...", repo_id, device)
    t0 = time.time()
    model = SentenceTransformer(
        repo_id,
        device=device,
        model_kwargs={
            # dtype supersedes the deprecated torch_dtype in transformers 4.56+
            "dtype": torch.float16,
            # stream weights shard by shard instead of materializing the whole model
            # in cpu ram first, which is essential for the 8b on 24gb
            "low_cpu_mem_usage": True,
        },
        # qwen3-embedding pools the last token, so padding must be on the left or the
        # pooled vector gets read off a pad token
        tokenizer_kwargs={"padding_side": "left"},
    )
    # single words, so the 32k default just wastes memory
    model.max_seq_length = 32
    log.info("Loaded in %.1fs | embedding dim = %d",
             time.time() - t0, model.get_sentence_embedding_dimension())
    return model


def encode_words(model, words: List[str], batch_size: int) -> np.ndarray:
    # we pass normalize_embeddings=False, but qwen3-embedding ships a normalize module
    # in its sentence-transformers pipeline so output comes back l2 normalized anyway.
    # that is harmless for matryoshka: truncating a normalized vector and renormalizing
    # is identical to truncating the raw vector and normalizing, because the full
    # vector norm is a scalar that renormalizing divides back out (max abs diff 3e-08)
    prompt = f"Instruct: {INSTRUCTION}\nQuery:"
    t0 = time.time()
    vectors = model.encode(
        words,
        prompt=prompt,
        batch_size=batch_size,
        convert_to_numpy=True,
        normalize_embeddings=False,
        show_progress_bar=True,
    )
    log.info("Encoded %d words in %.1fs (%.1f words/s)",
             len(words), time.time() - t0, len(words) / max(time.time() - t0, 1e-6))
    return np.asarray(vectors, dtype=np.float32)


def build(order: List[str], batch_size: int, limit: Optional[int]) -> Tuple[str, np.ndarray, List[str]]:
    # tries each model in turn, falling back on oom or download failure
    words = load_vocabulary(limit)
    device = pick_device()
    log.info("Device: %s | %s %s", device, platform.system(), platform.machine())

    errors = []
    for tier in order:
        repo_id = MODEL_CANDIDATES[tier]
        model = None
        try:
            model = load_model(repo_id, device)
            vectors = encode_words(model, words, batch_size)
            return repo_id, vectors, words
        except BaseException as exc:  # noqa: BLE001 - we genuinely want to retry on anything
            kind = "out of memory" if is_memory_error(exc) else type(exc).__name__
            log.warning("%s failed (%s): %s", repo_id, kind, exc)
            errors.append(f"{repo_id}: {kind}: {exc}")
            if tier is not order[-1]:
                log.warning("Falling back to the next model...")
        finally:
            if model is not None:
                del model
            _free_memory(device)

    raise RuntimeError("Every candidate model failed:\n  " + "\n  ".join(errors))


def _free_memory(device: str) -> None:
    # best effort cleanup between model attempts
    # this runs in a finally block so it must never raise: an exception here would
    # propagate out of build() and abort the fallback to the next model, masking the
    # real failure with a cleanup error
    import gc

    try:
        import torch

        gc.collect()
        if device == "mps":
            torch.mps.empty_cache()
        elif device == "cuda":
            torch.cuda.empty_cache()
    except Exception as exc:  # noqa: BLE001
        log.debug("cache cleanup failed (ignored): %s", exc)


def save(repo_id: str, vectors: np.ndarray, words: List[str], elapsed: float) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    # a silently broken encode usually shows up as zero or non finite rows
    if not np.isfinite(vectors).all():
        raise ValueError("encoder produced non-finite values")
    norms = np.linalg.norm(vectors, axis=1)
    if (norms == 0).any():
        raise ValueError(f"{int((norms == 0).sum())} zero vectors in output")

    np.savez_compressed(
        OUT_FILE,
        vectors=vectors.astype(np.float16),
        words=np.array(words, dtype=object),
    )

    meta = {
        "model": repo_id,
        "dimension": int(vectors.shape[1]),
        "word_count": len(words),
        "instruction": INSTRUCTION,
        # derived from the data rather than asserted, because the model's pipeline
        # normalizes regardless of what we request and recording our intent would lie
        "normalized": bool(np.allclose(norms, 1.0, atol=1e-3)),
        "dtype": "float16",
        "build_seconds": round(elapsed, 1),
        "note": (
            "Full-dimension vectors at the model's native width. To produce the "
            "shipped artifact, slice to the target Matryoshka dimension and "
            "renormalize, no re-encode needed."
        ),
    }
    (DATA_DIR / "embeddings_full.meta.json").write_text(
        json.dumps(meta, indent=2) + "\n"
    )

    size_mb = OUT_FILE.stat().st_size / 1e6
    log.info("Wrote %s  (%s, %.1f MB)", OUT_FILE.name, str(vectors.shape), size_mb)
    log.info("norm: min=%.3f mean=%.3f max=%.3f", norms.min(), norms.mean(), norms.max())


def main() -> int:
    ap = argparse.ArgumentParser(
        description="embed the game vocabulary with qwen3-embedding"
    )
    ap.add_argument("--model", choices=[*MODEL_CANDIDATES, "auto"], default="auto",
                    help="model tier, auto tries 8B then falls back to 4B")
    ap.add_argument("--batch-size", type=int, default=16)
    ap.add_argument("--limit", type=int, default=None,
                    help="only embed the first N words, for a smoke test")
    args = ap.parse_args()

    order = DEFAULT_ORDER if args.model == "auto" else [args.model]

    t0 = time.time()
    try:
        repo_id, vectors, words = build(order, args.batch_size, args.limit)
    except RuntimeError as exc:
        log.error("%s", exc)
        return 1

    if args.limit:
        log.info("Smoke test only (--limit %d); not writing artifacts.", args.limit)
        log.info("Shape would be %s from %s", vectors.shape, repo_id)
        return 0

    save(repo_id, vectors, words, time.time() - t0)
    log.info("Done in %.1fs using %s", time.time() - t0, repo_id)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
