# Optimization regression measurements

Host: posix. Samples: 7. Entries: 20000. Interleaved samples, one warmup, independent output checks.

| Workload | Candidate median (ms) | Baseline median (ms) | Speedup |
| --- | ---: | ---: | ---: |
| hash_stride_1 | 11.453 | 11.435 | 1.00x |
| hash_stride_64 | 10.018 | 9.811 | 0.98x |
| hash_stride_4096 | 10.720 | 10.364 | 0.97x |
| hash_stride_65536 | 10.747 | 10.530 | 0.98x |
| large_zero_allocations | 6.868 | 7.247 | 1.06x |
| scalar_leaf_calls | 18.826 | 18.159 | 0.96x |
| fib35 | 111.390 | 111.795 | 1.00x |

Maximum strided/sequential ratio: 0.938. Gate: <=5.0.

Times include process startup. These workloads do not establish general production performance, keyed hash security or allocator concurrency. Raw samples, compiler versions and SHA-256 are in the adjacent JSON.
