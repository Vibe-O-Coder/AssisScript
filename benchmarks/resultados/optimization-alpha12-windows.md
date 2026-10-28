# Optimization regression measurements

Host: nt. Samples: 7. Entries: 20000. Interleaved samples, one warmup, independent output checks.

| Workload | Candidate median (ms) | Baseline median (ms) | Speedup |
| --- | ---: | ---: | ---: |
| hash_stride_1 | 39.453 | 46.494 | 1.18x |
| hash_stride_64 | 21.451 | 21.586 | 1.01x |
| hash_stride_4096 | 42.880 | 20.420 | 0.48x |
| hash_stride_65536 | 44.257 | 38.832 | 0.88x |
| large_zero_allocations | 50.451 | 35.252 | 0.70x |
| scalar_leaf_calls | 31.860 | 31.755 | 1.00x |
| fib35 | 125.208 | 132.431 | 1.06x |

Maximum strided/sequential ratio: 1.122. Gate: <=5.0.

Times include process startup. These workloads do not establish general production performance, keyed hash security or allocator concurrency. Raw samples, compiler versions and SHA-256 are in the adjacent JSON.
