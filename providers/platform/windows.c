/* Trusted native shell only. No AssisScript pointers, callbacks or page code
   are retained. Build/test diagnostics are excluded from production DLLs. */
#define WIN32_LEAN_AND_MEAN
#define _WIN32_WINNT 0x0A00
#include <windows.h>
#include <windowsx.h>
#include <limits.h>
#include <stddef.h>
#include <stdlib.h>
#include <string.h>
#include "assis_platform_v1.h"

#define WINDOWS 32
#define EVENTS 256
#define PIXELS_PER_WINDOW (4u * 1024u * 1024u)
#define PIXELS_TOTAL (16u * 1024u * 1024u)
#define GENERATIONS UINT64_C(0x0000ffffffffffff)
typedef struct {int64_t kind, a, b, request;} Event;
typedef struct {
    HDC dc, mask_dc;
    HBITMAP bitmap, mask_bitmap;
    HGDIOBJ old_bitmap, old_mask;
    uint32_t *pixels, *mask;
    int width, height;
} Surface;
typedef struct {
    int active, failure;
    int64_t token, instance, request;
    uint64_t generation;
    HWND hwnd;
    Surface surface;
    Event events[EVENTS];
    unsigned count;
} Window;
static Window windows[WINDOWS];
static volatile LONG owner;
static int64_t last_instance;
static size_t total_pixels;
static ATOM window_class;
static HINSTANCE module;
static const wchar_t class_name[] = L"AssisPlatformV1";
#ifdef ASSISP_TESTING
static int64_t fail_after = -1;
static int checkpoints;
static int unavailable;
static int fail_destroy;
#endif

static int on_owner(void) {
    LONG current = (LONG)GetCurrentThreadId();
    return InterlockedCompareExchange(&owner, current, 0) == 0 || owner == current;
}
static int resource_allowed(void) {
#ifdef ASSISP_TESTING
    checkpoints++;
    if (fail_after == 0) return 0;
    if (fail_after > 0) fail_after--;
#endif
    return 1;
}
static Window *lookup(int64_t token) {
    uint64_t bits = (uint64_t)token;
    unsigned index = (unsigned)(bits & 255u);
    if ((bits >> 56) != 0x51 || !index || index > WINDOWS) return NULL;
    Window *w = &windows[index - 1];
    return w->active && w->token == token ? w : NULL;
}
static void free_surface(Surface *s) {
    if (s->dc && s->old_bitmap) SelectObject(s->dc, s->old_bitmap);
    if (s->mask_dc && s->old_mask) SelectObject(s->mask_dc, s->old_mask);
    if (s->bitmap) DeleteObject(s->bitmap);
    if (s->mask_bitmap) DeleteObject(s->mask_bitmap);
    if (s->dc) DeleteDC(s->dc);
    if (s->mask_dc) DeleteDC(s->mask_dc);
    memset(s, 0, sizeof(*s));
}
/* Construct before replacing: OOM leaves the old surface intact. */
static int make_surface(Surface *out, int width, int height, size_t replaced) {
    Surface s = {0};
    if (width < 1 || height < 1 || width > 16384 || height > 16384) return -1;
    size_t count = (size_t)width * (size_t)height;
    if (count > PIXELS_PER_WINDOW || count > PIXELS_TOTAL - (total_pixels - replaced)) return -4;
    BITMAPINFO info = {0};
    info.bmiHeader.biSize = sizeof(BITMAPINFOHEADER);
    info.bmiHeader.biWidth = width; info.bmiHeader.biHeight = -height;
    info.bmiHeader.biPlanes = 1; info.bmiHeader.biBitCount = 32;
    info.bmiHeader.biCompression = BI_RGB;
    if (!resource_allowed() || !(s.dc = CreateCompatibleDC(NULL))) goto oom;
    if (!resource_allowed() || !(s.mask_dc = CreateCompatibleDC(NULL))) goto oom;
    if (!resource_allowed() || !(s.bitmap = CreateDIBSection(s.dc, &info, DIB_RGB_COLORS, (void **)&s.pixels, NULL, 0))) goto oom;
    if (!resource_allowed() || !(s.mask_bitmap = CreateDIBSection(s.mask_dc, &info, DIB_RGB_COLORS, (void **)&s.mask, NULL, 0))) goto oom;
    s.old_bitmap = SelectObject(s.dc, s.bitmap);
    s.old_mask = SelectObject(s.mask_dc, s.mask_bitmap);
    if (!s.old_bitmap || s.old_bitmap == HGDI_ERROR || !s.old_mask || s.old_mask == HGDI_ERROR) goto oom;
    s.width = width; s.height = height;
    for (size_t i = 0; i < count; i++) s.pixels[i] = 0xff000000u;
    *out = s; return 0;
oom:
    free_surface(&s); return -4;
}
static int wide_text(const uint8_t *bytes, int64_t length, int64_t maximum, wchar_t **out, int *count) {
    *out = NULL; *count = 0;
    if (length < 0 || length > maximum || (!bytes && length)) return -1;
    int n = length ? MultiByteToWideChar(CP_UTF8, MB_ERR_INVALID_CHARS, (const char *)bytes, (int)length, NULL, 0) : 0;
    if (length && !n) return -1;
    if (!resource_allowed() || !(*out = calloc((size_t)n + 1, sizeof(wchar_t)))) return -4;
    if (n && MultiByteToWideChar(CP_UTF8, MB_ERR_INVALID_CHARS, (const char *)bytes, (int)length, *out, n) != n) {
        free(*out); *out = NULL; return -1;
    }
    *count = n; return 0;
}
static void enqueue(Window *w, int64_t kind, int64_t a, int64_t b) {
    if (!w->active || w->failure) return;
    /* Coalesce only adjacent motion/resize events, preserving key/close order. */
    if ((kind == 2 || kind == 4) && w->count && w->events[w->count - 1].kind == kind) {
        w->events[w->count - 1].a = a; w->events[w->count - 1].b = b; return;
    }
    if (w->count == EVENTS || w->request == INT64_MAX) {
        w->failure = -6; w->count = 0;
        if (w->hwnd) ShowWindow(w->hwnd, SW_HIDE);
        if (w->request == INT64_MAX && w->hwnd) DestroyWindow(w->hwnd);
        return;
    }
    w->events[w->count++] = (Event){kind, a, b, ++w->request};
}
static LRESULT CALLBACK procedure(HWND hwnd, UINT message, WPARAM wp, LPARAM lp) {
    Window *w = (Window *)GetWindowLongPtrW(hwnd, GWLP_USERDATA);
    if (message == WM_NCCREATE) {
        w = ((CREATESTRUCTW *)lp)->lpCreateParams;
        SetWindowLongPtrW(hwnd, GWLP_USERDATA, (LONG_PTR)w); w->hwnd = hwnd;
    }
    if (!w) return DefWindowProcW(hwnd, message, wp, lp);
    switch (message) {
    case WM_CLOSE: enqueue(w, 1, 0, 0); return 0;
    case WM_SIZE: {
        int width = LOWORD(lp), height = HIWORD(lp);
        if (wp == SIZE_MINIMIZED || !width || !height) return 0;
        if (width != w->surface.width || height != w->surface.height) {
            Surface next = {0}; size_t previous = (size_t)w->surface.width * w->surface.height;
            int code = make_surface(&next, width, height, previous);
            if (code) {w->failure = code; return 0;}
            free_surface(&w->surface); w->surface = next;
            total_pixels = total_pixels - previous + (size_t)width * height;
        }
        enqueue(w, 2, width, height); return 0;
    }
    case WM_KEYDOWN: case WM_KEYUP: enqueue(w, 3, (int64_t)wp, message == WM_KEYDOWN); return 0;
    case WM_MOUSEMOVE: enqueue(w, 4, GET_X_LPARAM(lp), GET_Y_LPARAM(lp)); return 0;
    case WM_SETFOCUS: case WM_KILLFOCUS: enqueue(w, 5, message == WM_SETFOCUS, 0); return 0;
    case WM_DPICHANGED: enqueue(w, 6, ((int64_t)HIWORD(wp) * 1000 + 48) / 96, 0); return 0;
    case WM_ERASEBKGND: return 1;
    case WM_PAINT: {
        PAINTSTRUCT paint; HDC dc = BeginPaint(hwnd, &paint);
        if (dc && w->surface.dc) BitBlt(dc, 0, 0, w->surface.width, w->surface.height, w->surface.dc, 0, 0, SRCCOPY);
        EndPaint(hwnd, &paint); return 0;
    }
    case WM_NCDESTROY: SetWindowLongPtrW(hwnd, GWLP_USERDATA, 0); w->hwnd = NULL; break;
    }
    return DefWindowProcW(hwnd, message, wp, lp);
}
static int initialize(void) {
    if (window_class) return 0;
    WNDCLASSEXW wc = {0};
    wc.cbSize = sizeof(wc); wc.lpfnWndProc = procedure; wc.hInstance = module;
    wc.lpszClassName = class_name; wc.hCursor = LoadCursorW(NULL, (LPCWSTR)IDC_ARROW);
    window_class = RegisterClassExW(&wc);
    return window_class ? 0 : -6;
}
static void unregister_if_idle(void) {
    for (unsigned i = 0; i < WINDOWS; i++) if (windows[i].active) return;
    if (window_class && UnregisterClassW(class_name, module)) window_class = 0;
}
BOOL WINAPI DllMain(HINSTANCE instance, DWORD reason, LPVOID reserved) {
    (void)reserved; if (reason == DLL_PROCESS_ATTACH) module = instance; return TRUE;
}
int64_t assisp_abi_version(void) {return on_owner() ? ASSISP_ABI : -5;}
int32_t assisp_open(int64_t instance, int32_t width, int32_t height, const uint8_t *title, int64_t title_len, int64_t *out_window) {
    if (out_window) *out_window = 0;
    if (!on_owner()) return -5;
    if (!out_window || instance <= last_instance || width < 1 || height < 1 || width > 16384 || height > 16384 ||
        title_len < 0 || title_len > 4096 || (!title && title_len) || (title_len && memchr(title, 0, (size_t)title_len))) return -1;
#ifdef ASSISP_TESTING
    if (unavailable) return -3;
#endif
    wchar_t *wide = NULL; int chars = 0;
    int code = wide_text(title, title_len, 4096, &wide, &chars); (void)chars;
    if (code) return code;
    Window *w = NULL; unsigned index;
    for (index = 0; index < WINDOWS; index++) if (!windows[index].active && windows[index].generation < GENERATIONS) {w = &windows[index]; break;}
    if (!w) {free(wide); return -4;}
    code = initialize(); if (code) {free(wide); return code;}
    Surface surface = {0}; code = make_surface(&surface, width, height, 0);
    if (code) {free(wide); unregister_if_idle(); return code;}
    uint64_t generation = w->generation + 1;
    memset(w, 0, sizeof(*w)); w->generation = generation; w->active = 1;
    w->instance = instance; w->token = (int64_t)(UINT64_C(0x5100000000000000) | generation << 8 | (index + 1));
    w->surface = surface; total_pixels += (size_t)width * height;
    DPI_AWARENESS_CONTEXT previous_dpi = SetThreadDpiAwarenessContext(DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2);
    RECT rect = {0, 0, width, height};
    if (!previous_dpi || !AdjustWindowRectExForDpi(&rect, WS_OVERLAPPEDWINDOW, FALSE, 0, GetDpiForSystem())) code = -6;
    HWND hwnd = !code && resource_allowed() ? CreateWindowExW(0, class_name, wide, WS_OVERLAPPEDWINDOW,
        CW_USEDEFAULT, CW_USEDEFAULT, rect.right - rect.left, rect.bottom - rect.top, NULL, NULL, module, w) : NULL;
    if (previous_dpi) SetThreadDpiAwarenessContext(previous_dpi);
    free(wide);
    if (!hwnd || w->failure) {
        code = w->failure ? w->failure : code ? code : -4;
        w->active = 0;
        if (w->hwnd) DestroyWindow(w->hwnd);
        total_pixels -= (size_t)w->surface.width * w->surface.height;
        free_surface(&w->surface); w->count = 0; unregister_if_idle(); return code;
    }
    last_instance = instance;
#ifndef ASSISP_TESTING
    ShowWindow(hwnd, SW_SHOWNORMAL);
#endif
    *out_window = w->token; return 0;
}
static int access_window(int64_t token, Window **out) {
    if (!on_owner()) return -5;
    *out = lookup(token); if (!*out) return -2;
    return (*out)->failure;
}
int32_t assisp_poll(int64_t token, int32_t timeout_ms, int64_t *words, int64_t capacity) {
    if (words && capacity >= 8) memset(words, 0, 8 * sizeof(int64_t));
    if (!on_owner()) return -5;
    if (!words || capacity < 8 || timeout_ms < 0 || timeout_ms > 50) return -1;
    Window *w = lookup(token); if (!w) return -2;
    ULONGLONG deadline = GetTickCount64() + (unsigned)timeout_ms;
    for (;;) {
        /* A finite batch prevents a native message flood starving the caller. */
        MSG message;
        for (int i = 0; i < 512 && PeekMessageW(&message, NULL, 0, 0, PM_REMOVE); i++) {
            if (message.message == WM_QUIT) {
                for (unsigned j = 0; j < WINDOWS; j++) enqueue(&windows[j], 1, 0, 0);
            } else {TranslateMessage(&message); DispatchMessageW(&message);}
        }
        if (w->failure) return w->failure;
        if (w->count) {
            Event e = w->events[0]; w->count--;
            memmove(w->events, w->events + 1, w->count * sizeof(Event));
            int64_t event[8] = {ASSISP_ABI, e.kind, token, w->instance, (int64_t)w->generation, e.a, e.b, e.request};
            memcpy(words, event, sizeof(event)); return 0;
        }
        ULONGLONG now = GetTickCount64(); if (now >= deadline) return 1;
        DWORD result = MsgWaitForMultipleObjectsEx(0, NULL, (DWORD)(deadline - now), QS_ALLINPUT, MWMO_INPUTAVAILABLE);
        if (result == WAIT_FAILED) return -6;
    }
}
static unsigned blend(unsigned source, unsigned destination, unsigned alpha) {
    return (source * alpha + destination * (255 - alpha) + 127) / 255;
}
static uint32_t over(uint32_t rgba, uint32_t bgra, unsigned coverage) {
    unsigned a = ((rgba & 255u) * coverage + 127) / 255;
    return 0xff000000u | blend(rgba >> 24, (bgra >> 16) & 255u, a) << 16 |
        blend((rgba >> 16) & 255u, (bgra >> 8) & 255u, a) << 8 | blend((rgba >> 8) & 255u, bgra & 255u, a);
}
int32_t assisp_clear(int64_t token, uint32_t rgba) {
    Window *w = NULL; int code = access_window(token, &w); if (code) return code;
    GdiFlush(); size_t count = (size_t)w->surface.width * w->surface.height;
    for (size_t i = 0; i < count; i++) w->surface.pixels[i] = over(rgba, w->surface.pixels[i], 255);
    return 0;
}
int32_t assisp_text_utf8(int64_t token, int32_t x, int32_t y, const uint8_t *text, int64_t length, uint32_t rgba) {
    Window *w = NULL; int code = access_window(token, &w); if (code) return code;
    wchar_t *wide = NULL; int count = 0; code = wide_text(text, length, 1048576, &wide, &count);
    if (code) return code;
    Surface *s = &w->surface; size_t pixels = (size_t)s->width * s->height;
    GdiFlush(); memset(s->mask, 0, pixels * sizeof(uint32_t));
    HGDIOBJ previous = SelectObject(s->mask_dc, GetStockObject(DEFAULT_GUI_FONT));
    SetTextColor(s->mask_dc, RGB(255, 255, 255)); SetBkMode(s->mask_dc, TRANSPARENT);
    int64_t cursor = x;
    for (int offset = 0; offset < count && cursor < s->width;) {
        int chunk = count - offset; if (chunk > 4096) chunk = 4096;
        if (offset + chunk < count && wide[offset + chunk - 1] >= 0xd800 && wide[offset + chunk - 1] <= 0xdbff) chunk--;
        SIZE extent;
        if (!GetTextExtentPoint32W(s->mask_dc, wide + offset, chunk, &extent) ||
            !TextOutW(s->mask_dc, (int)cursor, y, wide + offset, chunk)) {code = -6; break;}
        cursor += extent.cx; offset += chunk;
    }
    SelectObject(s->mask_dc, previous); free(wide); GdiFlush();
    if (code) return code;
    for (size_t i = 0; i < pixels; i++) {
        uint32_t mask = s->mask[i];
        unsigned coverage = ((mask & 255u) + ((mask >> 8) & 255u) + ((mask >> 16) & 255u) + 1) / 3;
        if (coverage) s->pixels[i] = over(rgba, s->pixels[i], coverage);
    }
    return 0;
}
int32_t assisp_present(int64_t token) {
    Window *w = NULL; int code = access_window(token, &w); if (code) return code;
    if (!InvalidateRect(w->hwnd, NULL, FALSE) || !UpdateWindow(w->hwnd)) return -6;
    return 0;
}
int32_t assisp_close(int64_t token) {
    if (!on_owner()) return -5;
    Window *w = lookup(token); if (!w) return -2;
    /* Revoke before DestroyWindow can send any synchronous native message. */
    w->active = 0; w->count = 0;
    if (w->hwnd) {
        int destroyed;
#ifdef ASSISP_TESTING
        destroyed = !fail_destroy && DestroyWindow(w->hwnd);
#else
        destroyed = DestroyWindow(w->hwnd);
#endif
        if (!destroyed) {w->active = 1; w->failure = -6; return -6;}
    }
    total_pixels -= (size_t)w->surface.width * w->surface.height;
    free_surface(&w->surface); w->failure = 0; w->token = 0; unregister_if_idle(); return 0;
}
#ifdef ASSISP_TESTING
ASSISP_API int64_t assisp_test_control(int64_t operation, int64_t value) {
    if (!on_owner()) return -5;
    if (operation == 0) {fail_after = value; checkpoints = 0; return 0;}
    if (operation == 1) return checkpoints;
    if (operation == 2) {unavailable = value != 0; return 0;}
    if (operation == 3) return (int64_t)total_pixels;
    if (operation == 7) {fail_destroy = value != 0; return 0;}
    Window *w = lookup(value); if (!w) return -2;
    if (operation == 4) return (int64_t)(uintptr_t)w->hwnd;
    if (operation == 5) {w->request = INT64_MAX; return 0;}
    if (operation == 6) {w->generation = GENERATIONS; return 0;}
    return -1;
}
ASSISP_API int64_t assisp_test_pixel(int64_t token, int32_t x, int32_t y) {
    if (!on_owner()) return -5;
    Window *w = lookup(token); if (!w) return -2;
    if (x < 0 || y < 0 || x >= w->surface.width || y >= w->surface.height) return -1;
    GdiFlush(); return w->surface.pixels[(size_t)y * w->surface.width + x];
}
#endif
