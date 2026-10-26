# Optimization regression measurements

Host: posix. Samples: 7. Entries: 20000. Interleaved samples, one warmup, independent output checks.

| Workload | Candidate median (ms) | Baseline median (ms) | Speedup |
| --- | ---: | ---: | ---: |
| hash_stride_1 | 11.832 | 7.758 | 0.66x |
| hash_stride_64 | 10.312 | 26.885 | 2.61x |
| hash_stride_4096 | 10.111 | 1016.975 | 100.58x |
| hash_stride_65536 | 10.101 | 12212.168 | 1209.00x |
| large_zero_allocations | 5.784 | 1689.771 | 292.15x |
| scalar_leaf_calls | 16.866 | 40.754 | 2.42x |
| fib35 | 128.535 | 114.641 | 0.89x |

Maximum strided/sequential ratio: 0.872. Gate: <=5.0.

Times include process startup. These workloads do not establish general production performance, keyed hash security or allocator concurrency. Raw samples, compiler versions and SHA-256 are in the adjacent JSON.

## Additional investigation: fib(37)

Twenty-one interleaved samples after the noisy fib(35) observation. Original fib(35) samples remain above and in JSON. Separate workload, not a replacement for those samples.

candidate: median 227.105 ms; range 222.903–284.242 ms.

baseline: median 255.452 ms; range 251.276–343.376 ms.

Source, expected output, binary hashes and every additional sample are in JSON. No isolated causal attribution or universal speedup is claimed.
