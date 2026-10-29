# Backend comparison — alpha.15

3 interleaved samples, one warmup, 2000000 base iterations. Times include process startup.

| Workload | Candidate median (ms) | Reference median (ms) | Speedup |
| --- | ---: | ---: | ---: |
| disjoint_loops | 30.319 | 72.174 | 2.380x |
| stencil_offsets | 57.619 | 158.160 | 2.745x |
| reverse_traversal | 27.607 | 57.444 | 2.081x |
| scalar_leaf | 24.424 | 76.898 | 3.148x |
| float_values | 61.992 | 61.444 | 0.991x |

Exact compiler/program hashes, output references, compile times, sizes and raw samples are in the adjacent JSON.
These bounded workloads do not establish general performance or production readiness. No bounds check is removed without an induction proof.
