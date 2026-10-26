# Optimization regression measurements

Host: posix. Samples: 7. Entries: 20000. Interleaved samples, one warmup, independent output checks.

| Workload | Candidate median (ms) | Baseline median (ms) | Speedup |
| --- | ---: | ---: | ---: |
| hash_stride_1 | 11.311 | 7.907 | 0.70x |
| hash_stride_64 | 11.535 | 28.108 | 2.44x |
| hash_stride_4096 | 11.358 | 1114.473 | 98.12x |
| hash_stride_65536 | 10.047 | 15597.580 | 1552.46x |
| large_zero_allocations | 6.227 | 1761.276 | 282.86x |
| scalar_leaf_calls | 20.573 | 51.622 | 2.51x |
| fib35 | 104.467 | 112.820 | 1.08x |

Maximum strided/sequential ratio: 1.020. Gate: <=5.0.

Times include process startup. These workloads do not establish general production performance, keyed hash security or allocator concurrency. Raw samples, compiler versions and SHA-256 are in the adjacent JSON.
