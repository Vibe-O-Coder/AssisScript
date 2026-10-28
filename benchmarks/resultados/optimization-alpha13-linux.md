# Optimization regression measurements

Host: posix. Samples: 7. Entries: 20000. Interleaved samples, one warmup, independent output checks.

| Workload | Candidate median (ms) | Baseline median (ms) | Speedup |
| --- | ---: | ---: | ---: |
| hash_stride_1 | 10.501 | 10.819 | 1.03x |
| hash_stride_64 | 11.334 | 10.865 | 0.96x |
| hash_stride_4096 | 10.260 | 10.293 | 1.00x |
| hash_stride_65536 | 10.763 | 11.067 | 1.03x |
| large_zero_allocations | 7.086 | 6.738 | 0.95x |
| scalar_leaf_calls | 18.869 | 18.692 | 0.99x |
| fib35 | 105.972 | 105.514 | 1.00x |

Maximum strided/sequential ratio: 1.079. Gate: <=5.0.

Times include process startup. These workloads do not establish general production performance, keyed hash security or allocator concurrency. Raw samples, compiler versions and SHA-256 are in the adjacent JSON.
