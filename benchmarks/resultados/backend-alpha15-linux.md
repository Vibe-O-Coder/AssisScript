# Backend comparison — alpha.15

3 interleaved samples, one warmup, 2000000 base iterations. Times include process startup.

| Workload | Candidate median (ms) | Reference median (ms) | Speedup |
| --- | ---: | ---: | ---: |
| disjoint_loops | 92.626 | 224.426 | 2.423x |
| stencil_offsets | 353.885 | 1267.579 | 3.582x |
| reverse_traversal | 78.965 | 149.631 | 1.895x |
| scalar_leaf | 58.568 | 246.465 | 4.208x |
| float_values | 64.622 | 126.543 | 1.958x |

Exact compiler/program hashes, output references, compile times, sizes and raw samples are in the adjacent JSON.
These bounded workloads do not establish general performance or production readiness. No bounds check is removed without an induction proof.
