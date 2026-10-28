# Optimization regression measurements

Host: nt. Samples: 7. Entries: 20000. Interleaved samples, one warmup, independent output checks.

| Workload | Candidate median (ms) | Baseline median (ms) | Speedup |
| --- | ---: | ---: | ---: |
| hash_stride_1 | 22.586 | 22.320 | 0.99x |
| hash_stride_64 | 22.843 | 23.569 | 1.03x |
| hash_stride_4096 | 21.647 | 21.886 | 1.01x |
| hash_stride_65536 | 23.700 | 25.905 | 1.09x |
| large_zero_allocations | 20.052 | 20.004 | 1.00x |
| scalar_leaf_calls | 35.355 | 34.303 | 0.97x |
| fib35 | 104.311 | 103.940 | 1.00x |

Maximum strided/sequential ratio: 1.049. Gate: <=5.0.

Times include process startup. These workloads do not establish general production performance, keyed hash security or allocator concurrency. Raw samples, compiler versions and SHA-256 are in the adjacent JSON.
