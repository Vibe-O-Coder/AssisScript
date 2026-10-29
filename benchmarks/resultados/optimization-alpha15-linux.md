# Optimization regression measurements

Host: posix. Samples: 3. Entries: 20000. Interleaved samples, one warmup, independent output checks.

| Workload | Candidate median (ms) | Baseline median (ms) | Speedup |
| --- | ---: | ---: | ---: |
| hash_stride_1 | 28.805 | — | — |
| hash_stride_64 | 27.928 | — | — |
| hash_stride_4096 | 27.719 | — | — |
| hash_stride_65536 | 28.008 | — | — |
| large_zero_allocations | 9.612 | — | — |
| scalar_leaf_calls | 46.407 | — | — |
| fib35 | 255.966 | — | — |

Maximum strided/sequential ratio: 0.972. Gate: <=5.0.

Times include process startup. These workloads do not establish general production performance, keyed hash security or allocator concurrency. Raw samples, compiler versions and SHA-256 are in the adjacent JSON.
