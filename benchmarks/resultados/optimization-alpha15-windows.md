# Optimization regression measurements

Host: nt. Samples: 3. Entries: 20000. Interleaved samples, one warmup, independent output checks.

| Workload | Candidate median (ms) | Baseline median (ms) | Speedup |
| --- | ---: | ---: | ---: |
| hash_stride_1 | 24.029 | — | — |
| hash_stride_64 | 30.157 | — | — |
| hash_stride_4096 | 26.407 | — | — |
| hash_stride_65536 | 27.419 | — | — |
| large_zero_allocations | 23.589 | — | — |
| scalar_leaf_calls | 43.095 | — | — |
| fib35 | 142.781 | — | — |

Maximum strided/sequential ratio: 1.255. Gate: <=5.0.

Times include process startup. These workloads do not establish general production performance, keyed hash security or allocator concurrency. Raw samples, compiler versions and SHA-256 are in the adjacent JSON.
