# Optimization regression measurements

Host: nt. Samples: 3. Entries: 20000. Interleaved samples, one warmup, independent output checks.

| Workload | Candidate median (ms) | Baseline median (ms) | Speedup |
| --- | ---: | ---: | ---: |
| hash_stride_1 | 17.651 | — | — |
| hash_stride_64 | 17.191 | — | — |
| hash_stride_4096 | 17.058 | — | — |
| hash_stride_65536 | 17.248 | — | — |
| large_zero_allocations | 16.483 | — | — |
| scalar_leaf_calls | 19.475 | — | — |
| fib35 | 98.616 | — | — |

Maximum strided/sequential ratio: 0.977. Gate: <=5.0.

Times include process startup. These workloads do not establish general production performance, keyed hash security or allocator concurrency. Raw samples, compiler versions and SHA-256 are in the adjacent JSON.
