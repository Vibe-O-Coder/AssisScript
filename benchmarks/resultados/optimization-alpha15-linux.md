# Optimization regression measurements

Host: posix. Samples: 3. Entries: 20000. Interleaved samples, one warmup, independent output checks.

| Workload | Candidate median (ms) | Baseline median (ms) | Speedup |
| --- | ---: | ---: | ---: |
| hash_stride_1 | 3.787 | — | — |
| hash_stride_64 | 3.695 | — | — |
| hash_stride_4096 | 3.878 | — | — |
| hash_stride_65536 | 3.796 | — | — |
| large_zero_allocations | 3.104 | — | — |
| scalar_leaf_calls | 4.454 | — | — |
| fib35 | 39.487 | — | — |

Maximum strided/sequential ratio: 1.024. Gate: <=5.0.

Times include process startup. These workloads do not establish general production performance, keyed hash security or allocator concurrency. Raw samples, compiler versions and SHA-256 are in the adjacent JSON.
