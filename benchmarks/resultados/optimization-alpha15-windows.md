# Optimization regression measurements

Host: nt. Samples: 5. Entries: 20000. Interleaved samples, one warmup, independent output checks.

| Workload | Candidate median (ms) | Baseline median (ms) | Speedup |
| --- | ---: | ---: | ---: |
| hash_stride_1 | 20.781 | 21.083 | 1.01x |
| hash_stride_64 | 21.742 | 21.109 | 0.97x |
| hash_stride_4096 | 21.986 | 22.331 | 1.02x |
| hash_stride_65536 | 21.557 | 21.369 | 0.99x |
| large_zero_allocations | 16.871 | 17.310 | 1.03x |
| scalar_leaf_calls | 29.861 | 29.826 | 1.00x |
| fib35 | 105.501 | 107.110 | 1.02x |

Maximum strided/sequential ratio: 1.058. Gate: <=5.0.

Times include process startup. These workloads do not establish general production performance, keyed hash security or allocator concurrency. Raw samples, compiler versions and SHA-256 are in the adjacent JSON.
