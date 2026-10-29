# Backend comparison — alpha.15

3 interleaved samples, one warmup, 2000000 base iterations. Times include process startup.

| Workload | Candidate median (ms) | Reference median (ms) | Speedup |
| --- | ---: | ---: | ---: |
| disjoint_loops | 9.646 | 33.344 | 3.457x |
| stencil_offsets | 27.133 | 105.353 | 3.883x |
| reverse_traversal | 8.205 | 23.757 | 2.896x |
| scalar_leaf | 7.325 | 38.432 | 5.247x |
| float_values | 44.998 | 44.224 | 0.983x |

Exact compiler/program hashes, output references, compile times, sizes and raw samples are in the adjacent JSON.
These bounded workloads do not establish general performance or production readiness. No bounds check is removed without an induction proof.
