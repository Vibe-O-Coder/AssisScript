# Backend comparison — alpha.15

7 interleaved samples, one warmup, 4000000 base iterations. Times include process startup.

| Workload | Candidate median (ms) | Alpha.14 median (ms) | Speedup |
| --- | ---: | ---: | ---: |
| disjoint_loops | 100.713 | 165.568 | 1.644x |
| stencil_offsets | 368.426 | 466.382 | 1.266x |
| reverse_traversal | 77.589 | 88.269 | 1.138x |
| scalar_leaf | 64.969 | 65.057 | 1.001x |
| float_values | 126.878 | 177.050 | 1.395x |

Exact compiler/program hashes, output references, compile times, sizes and raw samples are in the adjacent JSON.
These bounded workloads do not establish general performance or production readiness. No bounds check is removed without an induction proof.
