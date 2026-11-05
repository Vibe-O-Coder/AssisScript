/* Font/raster adaptation with a bounded exact short-text metric cache.
   Layout, semantic eligibility, line breaking,
   command order, clipping rectangles and names are supplied by AssisScript. */
#define FRAME_METRIC_SLOTS 512
#define FRAME_METRIC_BYTES 256
typedef struct {
    uint8_t text[FRAME_METRIC_BYTES];
    int length, size, weight;
    int64_t value;
} FrameMetric;
static FrameMetric frame_metrics[FRAME_METRIC_SLOTS];
static unsigned frame_metric_count, frame_metric_next;
static int64_t frame_metric_hits, frame_metric_misses;
static void frame_metrics_reset(void) {
    memset(frame_metrics, 0, sizeof(frame_metrics));
    frame_metric_count = frame_metric_next = 0;
    frame_metric_hits = frame_metric_misses = 0;
}
static HFONT frame_font(int size, int weight) {
    if (size < 1 || size > 256 || weight < 100 || weight > 900) return NULL;
    LOGFONTW font;
    if (!GetObjectW(GetStockObject(DEFAULT_GUI_FONT), sizeof(font), &font)) return NULL;
    font.lfHeight = -size; font.lfWidth = 0; font.lfWeight = weight;
    return resource_allowed() ? CreateFontIndirectW(&font) : NULL;
}
int64_t assisp_frame_version(void) {return on_owner() ? 1 : -5;}
int64_t assisp_frame_clock(void) {
    if (!on_owner()) return -5;
    LARGE_INTEGER counter, frequency;
    if (!QueryPerformanceCounter(&counter) || !QueryPerformanceFrequency(&frequency) ||
        counter.QuadPart < 0 || frequency.QuadPart <= 0 || frequency.QuadPart > INT64_MAX / 1000 ||
        counter.QuadPart / frequency.QuadPart > INT64_MAX / 1000) return -6;
    return (counter.QuadPart / frequency.QuadPart) * 1000 +
        ((counter.QuadPart % frequency.QuadPart) * 1000) / frequency.QuadPart;
}
int64_t assisp_frame_current(int64_t token) {
    Window *w = NULL; int code = access_window(token, &w);
    return code ? code : w->access ? w->access->document : 0;
}
int64_t assisp_frame_measure(const uint8_t *text, int64_t length, int32_t size, int32_t weight) {
    if (!on_owner()) return -5;
    if (size < 1 || size > 256 || weight < 100 || weight > 900 || length < 0 || length > 4096 || (!text && length)) return -1;
    int cacheable = length <= FRAME_METRIC_BYTES;
#ifdef ASSISP_TESTING
    /* Fault campaigns exercise real allocation boundaries, even for warm keys. */
    if (fail_after >= 0) cacheable = 0;
#endif
    if (cacheable) for (unsigned i = 0; i < frame_metric_count; i++) {
        FrameMetric *m = &frame_metrics[i];
        if (m->length == length && m->size == size && m->weight == weight &&
            (!length || !memcmp(m->text, text, (size_t)length))) {
            if (frame_metric_hits < INT64_MAX) frame_metric_hits++;
            return m->value;
        }
    }
    if (frame_metric_misses < INT64_MAX) frame_metric_misses++;
    wchar_t *wide = NULL; int count = 0; int code = wide_text(text, length, 4096, &wide, &count);
    if (code) return code;
    HFONT font = frame_font(size, weight); HDC dc = font && resource_allowed() ? CreateCompatibleDC(NULL) : NULL;
    if (!dc) {if (font) DeleteObject(font); free(wide); return -4;}
    HGDIOBJ previous = SelectObject(dc, font); SIZE extent = {0}; TEXTMETRICW metrics = {0};
    if (!previous || previous == HGDI_ERROR || !GetTextExtentPoint32W(dc, wide, count, &extent) ||
        !GetTextMetricsW(dc, &metrics)) code = -6;
    if (previous && previous != HGDI_ERROR) SelectObject(dc, previous);
    DeleteDC(dc); DeleteObject(font); free(wide);
    int64_t value = ((int64_t)metrics.tmHeight << 32) | (uint32_t)extent.cx;
    if (!code && cacheable) {
        FrameMetric *m = &frame_metrics[frame_metric_next];
        memset(m, 0, sizeof(*m));
        if (length) memcpy(m->text, text, (size_t)length);
        m->length = (int)length; m->size = size; m->weight = weight; m->value = value;
        frame_metric_next = (frame_metric_next + 1) % FRAME_METRIC_SLOTS;
        if (frame_metric_count < FRAME_METRIC_SLOTS) frame_metric_count++;
    }
    return code ? code : value;
}
static int32_t frame_commit(int64_t token, int64_t projection, uint32_t background,
        const int64_t *commands, int64_t count, const uint8_t *text, int64_t length,
        const int64_t *access, int64_t items, const uint8_t *names, int64_t names_length, int catalog) {
    Window *w = NULL; int code = access_window(token, &w); if (code) return code;
    if (projection <= 0 || (w->access && projection <= w->access->document)) return -2;
    if (count < 0 || count > 33028 || (!commands && count) || length < 0 || length > 2097216 || (!text && length)) return -1;
    /* Bound area before any draw; no command can make raster work unbounded. */
    uint64_t area = 0, bytes = 0;
    for (int64_t i = 0; i < count; i++) {
        const int64_t *r = commands + i * 14;
        if (r[0] < 0 || r[0] > 1 || r[1] < -16777216 || r[1] > 16777216 || r[2] < -16777216 || r[2] > 16777216 ||
            r[3] < 0 || r[3] > 16777216 || r[4] < 0 || r[4] > 16777216 ||
            r[5] < 0 || r[5] > w->surface.width || r[6] < 0 || r[6] > w->surface.height ||
            r[7] < 0 || r[7] > w->surface.width-r[5] || r[8] < 0 || r[8] > w->surface.height-r[6] ||
            r[9] < 0 || r[9] > UINT32_MAX) return -1;
        if (r[0] == 1 && (r[10] < 1 || r[10] > 256 || r[11] < 100 || r[11] > 900 ||
            r[12] < 0 || r[13] < 0 || r[13] > 4096 || r[12] > length || r[13] > length-r[12])) return -1;
        area += (uint64_t)r[7] * (uint64_t)r[8];
        if (r[0] == 1) bytes += (uint64_t)r[13];
        if (area > UINT64_C(67108864) || bytes > UINT64_C(2097216)) return -4;
    }
    Surface next = {0}; code = make_surface(&next, w->surface.width, w->surface.height, 0);
    if (code) return code;
    size_t pixels = (size_t)next.width * next.height;
    for (size_t i = 0; i < pixels; i++) next.pixels[i] = over(background, 0xff000000u, 255);
    for (int64_t i = 0; i < count && !code; i++) {
        const int64_t *r = commands + i * 14;
        int64_t left = r[5], top = r[6], right = left+r[7], bottom = top+r[8];
        if (r[0] == 0) {
            if (r[1] > left) left = r[1];
            if (r[2] > top) top = r[2];
            if (r[1]+r[3] < right) right = r[1]+r[3];
            if (r[2]+r[4] < bottom) bottom = r[2]+r[4];
            for (int64_t y = top; y < bottom; y++) for (int64_t x = left; x < right; x++) {
                size_t at = (size_t)y*next.width+(size_t)x; next.pixels[at] = over((uint32_t)r[9], next.pixels[at], 255);
            }
        } else {
            wchar_t *wide = NULL; int units = 0; code = wide_text(text ? text+r[12] : NULL, r[13], 4096, &wide, &units);
            if (code) break;
            HFONT font = frame_font((int)r[10], (int)r[11]);
            if (!font) {free(wide); code = -4; break;}
            GdiFlush();
            for (int64_t y = top; y < bottom; y++) memset(next.mask+(size_t)y*next.width+left, 0, (size_t)(right-left)*sizeof(uint32_t));
            HGDIOBJ previous = SelectObject(next.mask_dc, font);
            RECT clip = {(LONG)left,(LONG)top,(LONG)right,(LONG)bottom};
            if (!previous || previous == HGDI_ERROR || SetTextColor(next.mask_dc, RGB(255,255,255)) == CLR_INVALID ||
                !SetBkMode(next.mask_dc, TRANSPARENT) || !ExtTextOutW(next.mask_dc, (int)r[1], (int)r[2], ETO_CLIPPED, &clip, wide, (UINT)units, NULL)) code = -6;
            if (previous && previous != HGDI_ERROR) SelectObject(next.mask_dc, previous);
            DeleteObject(font); free(wide); GdiFlush();
            if (code) break;
            for (int64_t y = top; y < bottom; y++) for (int64_t x = left; x < right; x++) {
                size_t at = (size_t)y*next.width+(size_t)x; uint32_t mask = next.mask[at];
                unsigned coverage = ((mask&255u)+((mask>>8)&255u)+((mask>>16)&255u)+1)/3;
                if (coverage) next.pixels[at] = over((uint32_t)r[9],next.pixels[at],coverage);
            }
        }
    }
    if (!code) code = accessibility_commit(token, projection, access, items, names, names_length, catalog);
    if (code) {free_surface(&next); return code;}
    /* No fallible operation follows the accessible commit; physical presentation
       is separate. Calls run on one owner thread, without user callbacks. */
    Surface old = w->surface; w->surface = next; free_surface(&old); return 0;
}

int64_t assisp_frame_catalog_version(void) {return on_owner() ? 1 : -5;}
int32_t assisp_frame_commit(int64_t token, int64_t projection, uint32_t background,
        const int64_t *commands, int64_t count, const uint8_t *text, int64_t length,
        const int64_t *access, int64_t items, const uint8_t *names, int64_t names_length) {
    return frame_commit(token, projection, background, commands, count, text, length, access, items, names, names_length, 0);
}
int32_t assisp_frame_catalog_commit(int64_t token, int64_t projection, uint32_t background,
        const int64_t *commands, int64_t count, const uint8_t *text, int64_t length,
        const int64_t *access, int64_t items, const uint8_t *names, int64_t names_length) {
    return frame_commit(token, projection, background, commands, count, text, length, access, items, names, names_length, 1);
}
