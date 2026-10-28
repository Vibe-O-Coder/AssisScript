# Backend comparison — alpha.15

7 interleaved samples, one warmup, 4000000 base iterations. Times include process startup.

| Workload | Candidate median (ms) | Alpha.14 median (ms) | Speedup |
| --- | ---: | ---: | ---: |
| disjoint_loops | 94.394 | 165.439 | 1.753x |
| stencil_offsets | 390.562 | 468.263 | 1.199x |
| reverse_traversal | 75.920 | 76.572 | 1.009x |
| scalar_leaf | 55.003 | 53.921 | 0.980x |
| float_values | 123.117 | 165.740 | 1.346x |

Exact compiler/program hashes, output references, compile times, sizes and raw samples are in the adjacent JSON.
These bounded workloads do not establish general performance or production readiness. No bounds check is removed without an induction proof.
