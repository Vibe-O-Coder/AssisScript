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
/* Additive viewer extension 1. Base ABI and old entry points are unchanged. */
ASSISP_API int64_t assisp_view_version(void);
/* Packed (height << 32) | width, or a negative status. DEFAULT_GUI_FONT. */
ASSISP_API int64_t assisp_measure_utf8(const uint8_t *text, int64_t length);
ASSISP_API int32_t assisp_rect(int64_t window, int32_t x, int32_t y,
    int32_t width, int32_t height, uint32_t rgba);
/* Additive reader extension 1. MSAA projection is copied transactionally. */
ASSISP_API int64_t assisp_reader_version(void);
/* Preferences extension 1: ten i64 words: version, highContrast, reducedMotion,
   background, text, button, buttonText, disabledText, selection, selectionText.
   Colors are opaque RGBA. Successful query subscribes this window to events
   12 (preferences changed) and 13 (visible,0); old callers never receive them. */
ASSISP_API int32_t assisp_preferences(int64_t window, int64_t *words, int64_t capacity);
ASSISP_API int64_t assisp_measure_scaled(const uint8_t *text, int64_t length, int32_t scale);
ASSISP_API int32_t assisp_text_scaled(int64_t window, int32_t x, int32_t y,
    const uint8_t *text, int64_t length, uint32_t rgba, int32_t scale);
ASSISP_API int32_t assisp_clipboard_utf8(int64_t window, const uint8_t *text, int64_t length);
/* count records of 8 i64: role, flags, x,y,width,height,name_offset,name_length.
   First is document; remaining are flat semantic blocks. Document instance
   is monotonically increasing per window. Flags disabled=1, focused=2,
   offscreen=4. No pointers to caller memory survive the call. */
ASSISP_API int32_t assisp_accessibility(int64_t window, int64_t document,
    const int64_t *words, int64_t count, const uint8_t *names, int64_t length);
/* Additive frame extension 1. Font size is integer pixels, weight 100..900. */
ASSISP_API int64_t assisp_frame_version(void);
ASSISP_API int64_t assisp_frame_current(int64_t window);
ASSISP_API int64_t assisp_frame_measure(const uint8_t *text, int64_t length, int32_t size, int32_t weight);
/* Raster commands: 14 i64 per record, documented in PERFIL-FRAME-LOCAL-V1.md.
   All commands and accessible projection commit together, or neither does.
   projection increases strictly for every publication on this window.
   Presentation to the physical desktop is a separate assisp_present call. */
ASSISP_API int32_t assisp_frame_commit(int64_t window, int64_t projection, uint32_t background,
    const int64_t *commands, int64_t count, const uint8_t *text, int64_t length,
    const int64_t *access, int64_t items, const uint8_t *names, int64_t names_length);
/* Catalog-reading extension 1: same records and limits, additional roles 12..19. */
ASSISP_API int64_t assisp_frame_catalog_version(void);
ASSISP_API int32_t assisp_frame_catalog_commit(int64_t window, int64_t projection, uint32_t background,
    const int64_t *commands, int64_t count, const uint8_t *text, int64_t length,
    const int64_t *access, int64_t items, const uint8_t *names, int64_t names_length);
#endif
