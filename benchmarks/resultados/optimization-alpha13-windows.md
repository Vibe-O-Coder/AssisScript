# Optimization regression measurements

Host: nt. Samples: 7. Entries: 20000. Interleaved samples, one warmup, independent output checks.

| Workload | Candidate median (ms) | Baseline median (ms) | Speedup |
| --- | ---: | ---: | ---: |
| hash_stride_1 | 23.763 | 22.422 | 0.94x |
| hash_stride_64 | 21.640 | 21.239 | 0.98x |
| hash_stride_4096 | 21.360 | 21.383 | 1.00x |
| hash_stride_65536 | 21.498 | 22.343 | 1.04x |
| large_zero_allocations | 17.511 | 17.277 | 0.99x |
| scalar_leaf_calls | 33.102 | 33.180 | 1.00x |
| fib35 | 119.043 | 122.536 | 1.03x |

Maximum strided/sequential ratio: 0.911. Gate: <=5.0.

Times include process startup. These workloads do not establish general production performance, keyed hash security or allocator concurrency. Raw samples, compiler versions and SHA-256 are in the adjacent JSON.
