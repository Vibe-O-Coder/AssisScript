# Backend comparison — alpha.15

3 interleaved samples, one warmup, 2000000 base iterations. Times include process startup.

| Workload | Candidate median (ms) | Reference median (ms) | Speedup |
| --- | ---: | ---: | ---: |
| disjoint_loops | 76.120 | 161.661 | 2.124x |
| stencil_offsets | 220.222 | 740.545 | 3.363x |
| reverse_traversal | 53.791 | 109.338 | 2.033x |
| scalar_leaf | 49.559 | 143.350 | 2.892x |
| float_values | 66.638 | 107.719 | 1.616x |

Exact compiler/program hashes, output references, compile times, sizes and raw samples are in the adjacent JSON.
These bounded workloads do not establish general performance or production readiness. No bounds check is removed without an induction proof.
