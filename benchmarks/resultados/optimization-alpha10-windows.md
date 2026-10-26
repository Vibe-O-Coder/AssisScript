# Optimization regression measurements

Host: nt. Samples: 7. Entries: 20000. Interleaved samples, one warmup, independent output checks.

| Workload | Candidate median (ms) | Baseline median (ms) | Speedup |
| --- | ---: | ---: | ---: |
| hash_stride_1 | 22.730 | 20.519 | 0.90x |
| hash_stride_64 | 23.723 | 40.004 | 1.69x |
| hash_stride_4096 | 25.254 | 1163.191 | 46.06x |
| hash_stride_65536 | 24.632 | 17592.305 | 714.20x |
| large_zero_allocations | 22.249 | 778.538 | 34.99x |
| scalar_leaf_calls | 36.720 | 58.412 | 1.59x |
| fib35 | 116.896 | 136.820 | 1.17x |

Maximum strided/sequential ratio: 1.111. Gate: <=5.0.

Times include process startup. These workloads do not establish general production performance, keyed hash security or allocator concurrency. Raw samples, compiler versions and SHA-256 are in the adjacent JSON.
