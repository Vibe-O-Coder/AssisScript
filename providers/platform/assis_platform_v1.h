#ifndef ASSIS_PLATFORM_V1_H
#define ASSIS_PLATFORM_V1_H
#include <stdint.h>
#ifdef _WIN32
#define ASSISP_API __declspec(dllexport)
#else
#define ASSISP_API
#endif
#define ASSISP_ABI INT64_C(0x00010000)
/* All buffers are borrowed only for this call. Tokens are never pointers. */
ASSISP_API int64_t assisp_abi_version(void);
ASSISP_API int32_t assisp_open(int64_t instance, int32_t width, int32_t height,
    const uint8_t *title, int64_t title_len, int64_t *out_window);
ASSISP_API int32_t assisp_poll(int64_t window, int32_t timeout_ms,
    int64_t *event_words, int64_t word_capacity);
ASSISP_API int32_t assisp_clear(int64_t window, uint32_t rgba);
ASSISP_API int32_t assisp_text_utf8(int64_t window, int32_t x, int32_t y,
    const uint8_t *text, int64_t length, uint32_t rgba);
ASSISP_API int32_t assisp_present(int64_t window);
ASSISP_API int32_t assisp_close(int64_t window);
#endif
