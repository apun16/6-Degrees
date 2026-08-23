# Embedding and graph evaluation

Vocabulary: **1761 words**  
Model: **Qwen/Qwen3-Embedding-8B** at 4096-d  

## Intrinsic benchmarks (Spearman vs human judgement)

`relatedness` sets are the ones aligned with this game about associations; SimLex deliberately penalises association and is shown as a contrast.

| Benchmark | Measures | sentence-transformers/all-MiniLM-L6-v2 | Qwen/Qwen3-Embedding-8B | Delta |
|---|---|---|---|---|
| SimLex-999 | similarity | 0.446 | 0.685 | +0.239 |
| WS-353-ALL | mixed | 0.729 | 0.783 | +0.054 |
| WS-353-SIM | similarity | 0.767 | 0.873 | +0.106 |
| WS-353-REL | relatedness | 0.652 | 0.710 | +0.058 |
| MEN-3k | relatedness | 0.735 | 0.852 | +0.117 |
| MTurk-771 | relatedness | 0.687 | 0.839 | +0.152 |
| RG-65 | similarity | 0.731 | 0.896 | +0.165 |

- Mean over **relatedness** sets: all-MiniLM-L6-v2 0.691, Qwen3-Embedding-8B 0.800  (delta +0.109)
- Mean over **similarity** sets: all-MiniLM-L6-v2 0.648, Qwen3-Embedding-8B 0.818  (delta +0.170)

### Matryoshka 

Mean Spearman over the relatedness benchmarks at each truncation. The graph sweep below cannot choose a dimension, since its metrics are structural and saturate; this measures semantics directly.

| dim | relatedness Spearman | vs best | artifact size |
|---|---|---|---|
| 256 | 0.7573 | -0.0430 | 0.9 MB |
| 512 | 0.7759 | -0.0244 | 1.8 MB |
| 1024 | 0.7893 | -0.0109 | 3.6 MB |
| 2048 | 0.7972 | -0.0031 | 7.2 MB |
| 4096 | 0.8002 | +0.0000 | 14.4 MB |

## Graph config

`playable` is the fraction of word pairs that form a legal puzzle (2 to 6 steps). `1-hop` pairs are already adjacent and therefore unusable. `gini` measures hub concentration, lower is flatter.

| dim | rule | edges | deg med | deg max | gini | comp | 1-hop | playable | med hops | score |
|---|---|---|---|---|---|---|---|---|---|---|
| 1024 | union_knn(k=10, floor=0.0, bridge=True) | 11677 | 12 | 44 | 0.15 | 1 | 0.8% | 99.2% | 4.0 | 0.982 **<-** |
| 4096 | union_knn(k=10, floor=0.0, bridge=True) | 11622 | 12 | 46 | 0.15 | 1 | 0.7% | 99.2% | 4.0 | 0.982 |
| 2048 | union_knn(k=10, floor=0.0, bridge=True) | 11623 | 12 | 43 | 0.15 | 1 | 0.8% | 99.2% | 4.0 | 0.982 |
| 512 | union_knn(k=10, floor=0.0, bridge=True) | 11725 | 12 | 43 | 0.15 | 1 | 0.8% | 99.2% | 4.0 | 0.982 |
| 2048 | union_knn(k=12, floor=0.0, bridge=True) | 13883 | 14 | 50 | 0.14 | 1 | 0.9% | 99.1% | 4.0 | 0.982 |
| 4096 | union_knn(k=12, floor=0.0, bridge=True) | 13853 | 14 | 48 | 0.14 | 1 | 0.9% | 99.1% | 4.0 | 0.982 |
| 1024 | union_knn(k=12, floor=0.0, bridge=True) | 13934 | 14 | 51 | 0.14 | 1 | 0.9% | 99.1% | 4.0 | 0.982 |
| 256 | union_knn(k=10, floor=0.0, bridge=True) | 11771 | 12 | 50 | 0.15 | 1 | 0.8% | 99.2% | 4.0 | 0.982 |
| 256 | union_knn(k=12, floor=0.0, bridge=True) | 14069 | 15 | 53 | 0.14 | 1 | 0.9% | 99.1% | 4.0 | 0.981 |
| 512 | union_knn(k=12, floor=0.0, bridge=True) | 14023 | 14 | 46 | 0.15 | 1 | 0.9% | 99.1% | 4.0 | 0.981 |
| 4096 | union_knn(k=15, floor=0.0, bridge=True) | 17228 | 18 | 59 | 0.14 | 1 | 1.1% | 98.9% | 4.0 | 0.981 |
| 2048 | union_knn(k=15, floor=0.0, bridge=True) | 17275 | 18 | 57 | 0.14 | 1 | 1.1% | 98.9% | 4.0 | 0.981 |
| 1024 | union_knn(k=15, floor=0.0, bridge=True) | 17345 | 18 | 56 | 0.14 | 1 | 1.1% | 98.9% | 4.0 | 0.981 |
| 256 | union_knn(k=15, floor=0.0, bridge=True) | 17493 | 18 | 60 | 0.14 | 1 | 1.1% | 98.9% | 4.0 | 0.981 |
| 512 | union_knn(k=15, floor=0.0, bridge=True) | 17445 | 18 | 57 | 0.14 | 1 | 1.1% | 98.9% | 4.0 | 0.981 |
| 4096 | mutual_knn(k=20, floor=0.0, bridge=True) | 12402 | 15 | 20 | 0.17 | 1 | 0.8% | 99.0% | 4.0 | 0.978 |
| 2048 | mutual_knn(k=20, floor=0.0, bridge=True) | 12335 | 15 | 20 | 0.17 | 1 | 0.8% | 99.0% | 4.0 | 0.978 |
| 1024 | mutual_knn(k=20, floor=0.0, bridge=True) | 12285 | 15 | 20 | 0.18 | 1 | 0.8% | 99.0% | 4.0 | 0.978 |
| 256 | mutual_knn(k=20, floor=0.0, bridge=True) | 12026 | 14 | 20 | 0.18 | 1 | 0.8% | 99.0% | 4.0 | 0.977 |
| 512 | mutual_knn(k=20, floor=0.0, bridge=True) | 12143 | 14 | 20 | 0.19 | 1 | 0.8% | 98.9% | 4.0 | 0.977 |
| 1024 | union_knn(k=20, floor=0.0, bridge=True) | 22938 | 24 | 68 | 0.13 | 1 | 1.5% | 98.5% | 3.0 | 0.918 |
| 4096 | union_knn(k=20, floor=0.0, bridge=True) | 22819 | 23 | 69 | 0.13 | 1 | 1.5% | 98.5% | 3.0 | 0.918 |
| 2048 | union_knn(k=20, floor=0.0, bridge=True) | 22886 | 23 | 74 | 0.13 | 1 | 1.5% | 98.5% | 3.0 | 0.917 |
| 512 | union_knn(k=20, floor=0.0, bridge=True) | 23081 | 24 | 77 | 0.14 | 1 | 1.5% | 98.5% | 3.0 | 0.917 |
| 256 | union_knn(k=20, floor=0.0, bridge=True) | 23196 | 24 | 75 | 0.14 | 1 | 1.5% | 98.5% | 3.0 | 0.917 |
| 256 | union_knn(k=8, floor=0.0, bridge=True) | 9475 | 10 | 40 | 0.15 | 1 | 0.6% | 98.6% | 5.0 | 0.916 |
| 512 | union_knn(k=8, floor=0.0, bridge=True) | 9435 | 10 | 34 | 0.15 | 1 | 0.6% | 98.3% | 5.0 | 0.915 |
| 1024 | union_knn(k=8, floor=0.0, bridge=True) | 9402 | 10 | 38 | 0.15 | 1 | 0.6% | 98.0% | 5.0 | 0.914 |
| 4096 | union_knn(k=8, floor=0.0, bridge=True) | 9375 | 10 | 37 | 0.15 | 1 | 0.6% | 98.0% | 5.0 | 0.914 |
| 2048 | union_knn(k=8, floor=0.0, bridge=True) | 9378 | 10 | 37 | 0.15 | 1 | 0.6% | 97.7% | 5.0 | 0.913 |
| 2048 | mutual_knn(k=15, floor=0.0, bridge=True) | 9144 | 11 | 15 | 0.18 | 1 | 0.6% | 95.2% | 5.0 | 0.900 |
| 4096 | mutual_knn(k=15, floor=0.0, bridge=True) | 9191 | 11 | 15 | 0.18 | 1 | 0.6% | 95.1% | 5.0 | 0.899 |
| 1024 | mutual_knn(k=15, floor=0.0, bridge=True) | 9073 | 11 | 15 | 0.19 | 1 | 0.6% | 95.1% | 5.0 | 0.899 |
| 256 | mutual_knn(k=15, floor=0.0, bridge=True) | 8926 | 11 | 15 | 0.20 | 1 | 0.6% | 94.4% | 5.0 | 0.895 |
| 2048 | threshold(threshold=0.55) | 42451 | 44 | 190 | 0.31 | 1 | 2.7% | 97.3% | 3.0 | 0.894 |
| 4096 | threshold(threshold=0.55) | 43959 | 45 | 193 | 0.31 | 1 | 2.8% | 97.2% | 3.0 | 0.894 |
| 512 | mutual_knn(k=15, floor=0.0, bridge=True) | 8976 | 11 | 16 | 0.19 | 1 | 0.6% | 93.8% | 5.0 | 0.893 |
| 1024 | threshold(threshold=0.55) | 58010 | 61 | 258 | 0.31 | 1 | 3.7% | 96.3% | 3.0 | 0.889 |
| 512 | union_knn(k=6, floor=0.0, bridge=True) | 7150 | 7 | 27 | 0.16 | 1 | 0.5% | 88.7% | 5.0 | 0.876 |
| 256 | union_knn(k=6, floor=0.0, bridge=True) | 7169 | 7 | 30 | 0.16 | 1 | 0.5% | 88.5% | 5.0 | 0.875 |
| 1024 | union_knn(k=6, floor=0.0, bridge=True) | 7131 | 7 | 30 | 0.16 | 1 | 0.5% | 87.8% | 5.0 | 0.873 |
| 4096 | union_knn(k=6, floor=0.0, bridge=True) | 7108 | 7 | 31 | 0.16 | 1 | 0.5% | 87.6% | 5.0 | 0.872 |
| 2048 | union_knn(k=6, floor=0.0, bridge=True) | 7136 | 7 | 32 | 0.16 | 1 | 0.5% | 86.2% | 5.0 | 0.866 |
| 512 | threshold(threshold=0.55) | 72939 | 74 | 320 | 0.33 | 1 | 4.7% | 95.3% | 2.0 | 0.821 |
| 256 | threshold(threshold=0.55) | 109101 | 108 | 454 | 0.34 | 1 | 7.0% | 93.0% | 2.0 | 0.809 |
| 2048 | threshold(threshold=0.45) | 321217 | 337 | 1049 | 0.29 | 1 | 20.7% | 79.3% | 2.0 | 0.753 |
| 4096 | threshold(threshold=0.45) | 336652 | 352 | 1066 | 0.28 | 1 | 21.7% | 78.3% | 2.0 | 0.749 |
| 256 | threshold(threshold=0.65) | 16047 | 15 | 88 | 0.39 | 18 | 1.0% | 96.7% | 4.0 | 0.748 |
| 512 | threshold(threshold=0.65) | 11508 | 11 | 70 | 0.38 | 24 | 0.7% | 93.8% | 4.0 | 0.736 |
| 1024 | threshold(threshold=0.45) | 434111 | 477 | 1262 | 0.27 | 1 | 28.0% | 72.0% | 2.0 | 0.722 |
| 512 | threshold(threshold=0.45) | 488649 | 544 | 1309 | 0.25 | 1 | 31.5% | 68.5% | 2.0 | 0.708 |
| 2048 | mutual_knn(k=10, floor=0.0, bridge=True) | 5998 | 7 | 11 | 0.20 | 1 | 0.4% | 60.6% | 6.0 | 0.697 |
| 4096 | mutual_knn(k=10, floor=0.0, bridge=True) | 5998 | 7 | 11 | 0.20 | 1 | 0.4% | 59.8% | 6.0 | 0.694 |
| 1024 | mutual_knn(k=10, floor=0.0, bridge=True) | 5945 | 7 | 11 | 0.21 | 1 | 0.4% | 59.1% | 6.0 | 0.691 |
| 256 | mutual_knn(k=10, floor=0.0, bridge=True) | 5855 | 7 | 11 | 0.21 | 1 | 0.4% | 58.5% | 6.0 | 0.688 |
| 256 | threshold(threshold=0.45) | 569673 | 647 | 1387 | 0.23 | 1 | 36.8% | 63.2% | 2.0 | 0.686 |
| 512 | mutual_knn(k=10, floor=0.0, bridge=True) | 5899 | 7 | 11 | 0.21 | 1 | 0.4% | 56.7% | 6.0 | 0.681 |
| 1024 | threshold(threshold=0.65) | 9683 | 9 | 56 | 0.39 | 35 | 0.6% | 87.5% | 5.0 | 0.649 |
| 4096 | threshold(threshold=0.65) | 8113 | 8 | 49 | 0.39 | 49 | 0.5% | 76.5% | 5.0 | 0.604 |
| 2048 | threshold(threshold=0.65) | 7858 | 8 | 48 | 0.38 | 45 | 0.5% | 74.2% | 5.0 | 0.596 |
| 512 | union_knn(k=4, floor=0.0, bridge=True) | 4852 | 5 | 17 | 0.17 | 1 | 0.3% | 48.4% | 7.0 | 0.589 |
| 256 | union_knn(k=4, floor=0.0, bridge=True) | 4860 | 5 | 18 | 0.17 | 1 | 0.3% | 47.5% | 7.0 | 0.585 |
| 4096 | union_knn(k=4, floor=0.0, bridge=True) | 4842 | 5 | 20 | 0.17 | 1 | 0.3% | 46.6% | 7.0 | 0.582 |
| 1024 | union_knn(k=4, floor=0.0, bridge=True) | 4847 | 5 | 19 | 0.17 | 1 | 0.3% | 46.5% | 7.0 | 0.582 |
| 2048 | union_knn(k=4, floor=0.0, bridge=True) | 4815 | 5 | 20 | 0.17 | 1 | 0.3% | 45.9% | 7.0 | 0.579 |
| 4096 | mutual_knn(k=6, floor=0.0, bridge=True) | 3505 | 4 | 7 | 0.23 | 1 | 0.2% | 11.1% | 10.0 | 0.372 |
| 256 | mutual_knn(k=6, floor=0.0, bridge=True) | 3463 | 4 | 8 | 0.24 | 1 | 0.2% | 11.0% | 10.0 | 0.370 |
| 512 | mutual_knn(k=6, floor=0.0, bridge=True) | 3473 | 4 | 8 | 0.23 | 1 | 0.2% | 10.9% | 10.0 | 0.370 |
| 1024 | mutual_knn(k=6, floor=0.0, bridge=True) | 3494 | 4 | 9 | 0.23 | 1 | 0.2% | 10.8% | 10.0 | 0.370 |
| 2048 | mutual_knn(k=6, floor=0.0, bridge=True) | 3479 | 4 | 7 | 0.23 | 1 | 0.2% | 10.5% | 10.0 | 0.369 |

## Selected configuration

**`union_knn(k=10, floor=0.0, bridge=True)` at 1024-d**

- Edge rule chosen by the sweep, mean score 0.982 across dimensions.
- Dimension chosen by the benchmark curve, not the sweep: smallest width retaining >= 98% of peak relatedness (this one retains 98.6%). The sweep's top rows are tied to within 0.001 across all five widths, so it cannot make this call.
- Resulting graph: 11677 edges, median degree 12, gini 0.15, 99.2% of pairs playable, median 4 hops.

