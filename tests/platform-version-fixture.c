/* Loader/negotiation fixture only; no native product implementation. */
#include "../providers/platform/assis_platform_v1.h"
#ifndef FIXTURE_ABI
#define FIXTURE_ABI 65537
#endif
static int64_t calls;
int64_t assisp_abi_version(void) {return FIXTURE_ABI;}
int32_t assisp_open(int64_t i, int32_t w, int32_t h, const uint8_t *t, int64_t n, int64_t *out) {
    (void)i; (void)w; (void)h; (void)t; (void)n; calls++; *out = 0; return -3;
}
int32_t assisp_poll(int64_t t, int32_t m, int64_t *w, int64_t c) {(void)t;(void)m;(void)w;(void)c;return -3;}
int32_t assisp_clear(int64_t t, uint32_t c) {(void)t;(void)c;return -3;}
int32_t assisp_text_utf8(int64_t t,int32_t x,int32_t y,const uint8_t *b,int64_t n,uint32_t c) {
    (void)t;(void)x;(void)y;(void)b;(void)n;(void)c;return -3;
}
int32_t assisp_present(int64_t t) {(void)t;return -3;}
int32_t assisp_close(int64_t t) {(void)t;return -3;}
ASSISP_API int64_t assisp_test_calls(void) {return calls;}
