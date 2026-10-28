# Optimization regression measurements

Host: posix. Samples: 7. Entries: 20000. Interleaved samples, one warmup, independent output checks.

| Workload | Candidate median (ms) | Baseline median (ms) | Speedup |
| --- | ---: | ---: | ---: |
| hash_stride_1 | 15.755 | 22.681 | 1.44x |
| hash_stride_64 | 14.398 | 13.963 | 0.97x |
| hash_stride_4096 | 16.928 | 17.540 | 1.04x |
| hash_stride_65536 | 12.265 | 13.250 | 1.08x |
| large_zero_allocations | 6.973 | 7.188 | 1.03x |
| scalar_leaf_calls | 19.214 | 18.815 | 0.98x |
| fib35 | 115.101 | 113.752 | 0.99x |

Maximum strided/sequential ratio: 1.074. Gate: <=5.0.

Times include process startup. These workloads do not establish general production performance, keyed hash security or allocator concurrency. Raw samples, compiler versions and SHA-256 are in the adjacent JSON.
