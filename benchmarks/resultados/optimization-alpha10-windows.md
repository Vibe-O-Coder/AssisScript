# Optimization regression measurements

Host: nt. Samples: 7. Entries: 20000. Interleaved samples, one warmup, independent output checks.

| Workload | Candidate median (ms) | Baseline median (ms) | Speedup |
| --- | ---: | ---: | ---: |
| hash_stride_1 | 22.924 | 20.511 | 0.89x |
| hash_stride_64 | 23.029 | 40.143 | 1.74x |
| hash_stride_4096 | 23.153 | 1052.660 | 45.46x |
| hash_stride_65536 | 23.357 | 12327.735 | 527.80x |
| large_zero_allocations | 19.677 | 635.099 | 32.28x |
| scalar_leaf_calls | 34.050 | 52.033 | 1.53x |
| fib35 | 104.603 | 120.625 | 1.15x |

Maximum strided/sequential ratio: 1.019. Gate: <=5.0.

Times include process startup. These workloads do not establish general production performance, keyed hash security or allocator concurrency. Raw samples, compiler versions and SHA-256 are in the adjacent JSON.
