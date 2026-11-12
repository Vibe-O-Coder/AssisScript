#ifndef ASSIS_WORKER_V1_H
#define ASSIS_WORKER_V1_H
#include <stdint.h>
#ifdef _WIN32
#define ASSW_API __declspec(dllexport)
#else
#define ASSW_API __attribute__((visibility("default")))
#endif
/* Main-thread only. Buffers are borrowed for this call, never retained.
 * 0 I/O backpressure, >0 bytes, -1 input, -2 stale, -3 unsupported,
 * -4 OS/resource, -5 EOF. Tokens are local identities, never capabilities.
 * Executable is a trusted host-supplied absolute path; no shell or page native code. */
ASSW_API int64_t assw_version(void);
ASSW_API int64_t assw_open(const uint8_t*,int64_t,int64_t,int64_t*);
/* Extension: fixed page-compile-worker argument, 16..512 MiB, 1..10 CPU s.
 * Windows limits committed private memory; Linux limits address space.
 * Windows also requires LPAC isolation, with no unrestricted fallback.
 * Does not authorize executing a downloaded compiler or native page binary. */
ASSW_API int64_t assw_compile_open(const uint8_t*,int64_t,int64_t,int64_t,int64_t*);
/* Six words: version=1, limit bytes, current RSS, peak RSS, private commit
 * (Windows) or virtual size (Linux), running=1/exited=2. Sample before close.
 * RSS is observed, not a hard working-set ceiling. Output zeroed on stale. */
ASSW_API int64_t assw_usage(int64_t,int64_t*,int64_t);
ASSW_API int64_t assw_send(int64_t,const uint8_t*,int64_t);
ASSW_API int64_t assw_receive(int64_t,uint8_t*,int64_t);
ASSW_API int64_t assw_close(int64_t);
ASSW_API int64_t assw_child_read(uint8_t*,int64_t);
ASSW_API int64_t assw_child_write(const uint8_t*,int64_t);
/* Enter/verify before reading input. 1 Linux x64 restriction or Windows
 * AppContainer token with zero capabilities; the trusted Windows launcher
 * separately requires LPAC, per-spawn SID and process mitigations.
 * 0 means an explicitly unrestricted Windows launch.
 * Linux failure is -4 and the worker must exit without reading page bytes. */
ASSW_API int64_t assw_restrict(void);

/* Trusted host only. Open an explicit absolute UTF-8 directory grant, then
 * read canonical relative resource keys using that live grant. Successful
 * root open returns a positive token, read returns its byte count (including
 * zero). -1 invalid input, -2 stale token, -3 limit, -6 denied/I/O/changed,
 * -10 unavailable, -11 wrong thread. Buffers are borrowed; ignore output
 * bytes on failure. Close revokes the grant. No grant is inherited or sent
 * to the page. Supported by the local file provider extension version 1. */
ASSW_API int64_t assw_local_version(void);
ASSW_API int64_t assw_local_open(const uint8_t*,int64_t);
ASSW_API int64_t assw_local_read(int64_t,const uint8_t*,int64_t,uint8_t*,int64_t);
ASSW_API int64_t assw_local_close(int64_t);
#endif
