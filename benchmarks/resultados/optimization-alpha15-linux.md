# Optimization regression measurements

Host: posix. Samples: 5. Entries: 20000. Interleaved samples, one warmup, independent output checks.

| Workload | Candidate median (ms) | Baseline median (ms) | Speedup |
| --- | ---: | ---: | ---: |
| hash_stride_1 | 9.267 | 10.103 | 1.09x |
| hash_stride_64 | 9.433 | 9.396 | 1.00x |
| hash_stride_4096 | 9.774 | 9.643 | 0.99x |
| hash_stride_65536 | 9.346 | 9.454 | 1.01x |
| large_zero_allocations | 6.005 | 5.959 | 0.99x |
| scalar_leaf_calls | 17.305 | 17.313 | 1.00x |
| fib35 | 96.549 | 96.924 | 1.00x |

Maximum strided/sequential ratio: 1.055. Gate: <=5.0.

Times include process startup. These workloads do not establish general production performance, keyed hash security or allocator concurrency. Raw samples, compiler versions and SHA-256 are in the adjacent JSON.
