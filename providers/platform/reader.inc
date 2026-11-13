/* OS adapter only: AssisScript supplies roles/names/states/geometry/actions.
   MSAA simple children form a document/semantic-block projection, not a DOM.
   COM calls are marshalled to the provider's owner thread by Oleacc. */
struct Access {
    IAccessible iface;
    LONG references;
    int64_t token, document, count, length;
    int64_t *words;
    uint8_t *names;
};
static int64_t system_rgba(int index) {
    COLORREF c = GetSysColor(index);
    return (int64_t)((uint32_t)GetRValue(c) << 24 | (uint32_t)GetGValue(c) << 16 |
        (uint32_t)GetBValue(c) << 8 | 255u);
}
int32_t assisp_preferences(int64_t token, int64_t *words, int64_t capacity) {
    if (words && capacity >= 10) memset(words, 0, 10 * sizeof(int64_t));
    if (!on_owner()) return -5;
    if (!words || capacity < 10) return -1;
    Window *w = NULL; int code = access_window(token, &w); if (code) return code;
    HIGHCONTRASTW contrast = {0}; contrast.cbSize = sizeof(contrast);
    BOOL animation = FALSE;
    if (!SystemParametersInfoW(SPI_GETHIGHCONTRAST, sizeof(contrast), &contrast, 0) ||
        !SystemParametersInfoW(SPI_GETCLIENTAREAANIMATION, 0, &animation, 0)) return -6;
    int64_t result[10] = {1, (contrast.dwFlags & HCF_HIGHCONTRASTON) != 0, !animation,
        system_rgba(COLOR_WINDOW), system_rgba(COLOR_WINDOWTEXT), system_rgba(COLOR_BTNFACE),
        system_rgba(COLOR_BTNTEXT), system_rgba(COLOR_GRAYTEXT), system_rgba(COLOR_HIGHLIGHT),
        system_rgba(COLOR_HIGHLIGHTTEXT)};
    memcpy(words, result, sizeof(result)); w->preferences = 1;
    return 0;
}
#ifdef ASSISP_TESTING
static LONG access_objects;
#endif
static Access *as_access(IAccessible *iface) {return (Access *)iface;}
static HRESULT access_live(IAccessible *iface, Window **out) {
    if (!on_owner()) {return RPC_E_WRONG_THREAD;}
    Access *a = as_access(iface); Window *w = lookup(a->token);
    if (!w || w->access != a) {return CO_E_OBJNOTCONNECTED;}
    *out = w; return S_OK;
}
static int child_index(Access *a, VARIANT child, int64_t *index) {
    if (V_VT(&child) != VT_I4 || V_I4(&child) < 0 || V_I4(&child) >= a->count) {return 0;}
    *index = V_I4(&child); return 1;
}
/* A failed/too-small reflow can leave a larger retained snapshot. Native
   accessibility still clips to the actual surface, exactly as GDI does. */
static int access_rect(Window *w, const int64_t *r, RECT *out) {
    out->left = (LONG)r[2]; out->top = (LONG)r[3];
    int64_t right = r[2] + r[4], bottom = r[3] + r[5];
    out->right = (LONG)(right < w->surface.width ? right : w->surface.width);
    out->bottom = (LONG)(bottom < w->surface.height ? bottom : w->surface.height);
    return !(r[1] & 4) && out->left < out->right && out->top < out->bottom;
}
static HRESULT STDMETHODCALLTYPE ac_query(IAccessible *self, REFIID iid, void **out) {
    if (!out) {return E_POINTER;} *out = NULL;
    if (IsEqualIID(iid, &IID_IUnknown) || IsEqualIID(iid, &IID_IDispatch) || IsEqualIID(iid, &IID_IAccessible)) {
        *out = self; InterlockedIncrement(&as_access(self)->references); return S_OK;
    }return E_NOINTERFACE;
}
static ULONG STDMETHODCALLTYPE ac_add(IAccessible *self) {return (ULONG)InterlockedIncrement(&as_access(self)->references);}
static ULONG STDMETHODCALLTYPE ac_release(IAccessible *self) {
    Access *a = as_access(self); LONG refs = InterlockedDecrement(&a->references);
    if (!refs) {
#ifdef ASSISP_TESTING
        InterlockedDecrement(&access_objects);
#endif
        free(a->words); free(a->names); free(a);
    }return (ULONG)refs;
}
static HRESULT STDMETHODCALLTYPE ac_type_count(IAccessible *self, UINT *out) {
    (void)self; if (!out) {return E_POINTER;} *out = 1; return S_OK;
}
static HRESULT STDMETHODCALLTYPE ac_type(IAccessible *self, UINT index, LCID locale, ITypeInfo **out) {
    (void)self; if (!out) {return E_POINTER;} *out = NULL; if (index) {return DISP_E_BADINDEX;}
    ITypeLib *lib = NULL; HRESULT hr = LoadRegTypeLib(&LIBID_Accessibility, 1, 1, locale, &lib);
    if (SUCCEEDED(hr)) {hr = ITypeLib_GetTypeInfoOfGuid(lib, &IID_IAccessible, out); ITypeLib_Release(lib);}return hr;
}
static HRESULT STDMETHODCALLTYPE ac_ids(IAccessible *self, REFIID iid, LPOLESTR *names, UINT count, LCID locale, DISPID *ids) {
    (void)iid; ITypeInfo *info = NULL; HRESULT hr = ac_type(self, 0, locale, &info);
    if (SUCCEEDED(hr)) {hr = DispGetIDsOfNames(info, names, count, ids); ITypeInfo_Release(info);}return hr;
}
static HRESULT STDMETHODCALLTYPE ac_invoke(IAccessible *self, DISPID id, REFIID iid, LCID locale, WORD flags,
        DISPPARAMS *params, VARIANT *result, EXCEPINFO *exception, UINT *error) {
    (void)iid; ITypeInfo *info = NULL; HRESULT hr = ac_type(self, 0, locale, &info);
    if (SUCCEEDED(hr)) {hr = DispInvoke(self, info, id, flags, params, result, exception, error); ITypeInfo_Release(info);}return hr;
}
static HRESULT STDMETHODCALLTYPE ac_parent(IAccessible *self, IDispatch **out) {
    if (!out) {return E_POINTER;} *out = NULL; Window *w = NULL; HRESULT hr = access_live(self, &w);
    if (FAILED(hr)) {return hr;} IAccessible *parent = NULL;
    hr = CreateStdAccessibleObject(w->hwnd, OBJID_WINDOW, &IID_IAccessible, (void **)&parent);
    if (SUCCEEDED(hr)) {*out = (IDispatch *)parent;} return hr;
}
static HRESULT STDMETHODCALLTYPE ac_count(IAccessible *self, LONG *out) {
    if (!out) {return E_POINTER;} *out = 0; Window *w = NULL; HRESULT hr = access_live(self, &w);
    if (SUCCEEDED(hr)) {*out = (LONG)(as_access(self)->count - 1);} return hr;
}
static HRESULT STDMETHODCALLTYPE ac_child(IAccessible *self, VARIANT child, IDispatch **out) {
    if (!out) {return E_POINTER;} *out = NULL; Window *w = NULL; HRESULT hr = access_live(self, &w);
    if (FAILED(hr)) {return hr;} int64_t index;
    if (!child_index(as_access(self), child, &index) || !index) {return E_INVALIDARG;}
    return S_FALSE; /* simple element; caller uses this interface + child ID */
}
static HRESULT STDMETHODCALLTYPE ac_name(IAccessible *self, VARIANT child, BSTR *out) {
    if (!out) {return E_POINTER;} *out = NULL; Window *w = NULL; HRESULT hr = access_live(self, &w);
    if (FAILED(hr)) {return hr;} Access *a = as_access(self); int64_t index;
    if (!child_index(a, child, &index)) {return E_INVALIDARG;}
    int64_t *r = a->words + index * 8; wchar_t *wide = NULL; int count = 0;
    int code = wide_text(a->names + r[6], r[7], 1048576, &wide, &count);
    if (code) {return code == -4 ? E_OUTOFMEMORY : E_INVALIDARG;}
    *out = SysAllocStringLen(wide, (UINT)count); free(wide); return *out ? S_OK : E_OUTOFMEMORY;
}
static HRESULT STDMETHODCALLTYPE ac_no_string(IAccessible *self, VARIANT child, BSTR *out) {
    if (!out) {return E_POINTER;} *out = NULL; Window *w = NULL; HRESULT hr = access_live(self, &w);
    if (FAILED(hr)) {return hr;} int64_t index;
    return child_index(as_access(self), child, &index) ? S_FALSE : E_INVALIDARG;
}
static int edit_role(int64_t role) {return role == 24 || role == 25;}
static HRESULT STDMETHODCALLTYPE ac_value(IAccessible *self, VARIANT child, BSTR *out) {
    HRESULT hr = ac_no_string(self, child, out); if (FAILED(hr)) return hr;
    Access *a = as_access(self); int64_t index;
    if (!child_index(a, child, &index)) return E_INVALIDARG;
    const int64_t *r = a->words + index * 8;
    if (!edit_role(r[0])) return S_FALSE;
    const uint8_t *value = a->names + r[6] + r[7];
    int64_t length = value[0] | ((int64_t)value[1] << 8);
    wchar_t *wide = NULL; int count = 0;
    int code = wide_text(value + 2, length, 1024, &wide, &count);
    if (code) return code == -4 ? E_OUTOFMEMORY : E_INVALIDARG;
    *out = SysAllocStringLen(wide, (UINT)count);
    free(wide);
    return *out ? S_OK : E_OUTOFMEMORY;
}
static HRESULT STDMETHODCALLTYPE ac_description(IAccessible *self, VARIANT child, BSTR *out) {
    HRESULT hr = ac_no_string(self, child, out); if (FAILED(hr)) {return hr;}
    int64_t index; Access *a = as_access(self); if (!child_index(a, child, &index)) {return E_INVALIDARG;}
    int64_t role = a->words[index * 8];
    const wchar_t *description = role == 8 ? L"heading" : role == 12 ? L"main" :
        role == 13 ? L"section" : role == 14 ? L"header" : role == 15 ? L"footer" : role == 16 ? L"navigation" : NULL;
    if (!description) {return S_FALSE;}
    *out = SysAllocString(description); return *out ? S_OK : E_OUTOFMEMORY;
}
static int action_role(int64_t role) {
    return role == 9 || role == 17 || role == 21;
}
static HRESULT STDMETHODCALLTYPE ac_role(IAccessible *self, VARIANT child, VARIANT *out) {
    if (!out) {return E_POINTER;} VariantInit(out); Window *w = NULL; HRESULT hr = access_live(self, &w);
    if (FAILED(hr)) {return hr;} int64_t index; Access *a = as_access(self);
    if (!child_index(a, child, &index)) {return E_INVALIDARG;}
    V_VT(out) = VT_I4; int64_t role = a->words[index * 8];
    V_I4(out) = role == 1 ? ROLE_SYSTEM_DOCUMENT : role == 9 ? ROLE_SYSTEM_PUSHBUTTON :
        role == 17 ? ROLE_SYSTEM_LINK : role == 18 ? ROLE_SYSTEM_LIST : role == 19 ? ROLE_SYSTEM_LISTITEM :
        role == 21 ? ROLE_SYSTEM_CHECKBUTTON : edit_role(role) ? ROLE_SYSTEM_TEXT :
        ((role >= 12 && role <= 16) || role == 22) ? ROLE_SYSTEM_GROUPING : ROLE_SYSTEM_STATICTEXT; return S_OK;
}
static HRESULT STDMETHODCALLTYPE ac_state(IAccessible *self, VARIANT child, VARIANT *out) {
    if (!out) {return E_POINTER;} VariantInit(out); Window *w = NULL; HRESULT hr = access_live(self, &w);
    if (FAILED(hr)) {return hr;} int64_t index; Access *a = as_access(self);
    if (!child_index(a, child, &index)) {return E_INVALIDARG;}
    int64_t *r = a->words + index * 8; LONG flags = r[0] == 21 || edit_role(r[0]) ? 0 : STATE_SYSTEM_READONLY;
    if (r[1] & 1) flags |= STATE_SYSTEM_UNAVAILABLE;
    if ((action_role(r[0]) || edit_role(r[0])) && !(r[1] & 1)) flags |= STATE_SYSTEM_FOCUSABLE;
    if (r[0] == 21 && (r[1] & 8)) flags |= STATE_SYSTEM_CHECKED;
    if ((r[1] & 2) && GetFocus() == w->hwnd) flags |= STATE_SYSTEM_FOCUSED;
    RECT rect; if (!access_rect(w, r, &rect)) flags |= STATE_SYSTEM_OFFSCREEN;
    V_VT(out) = VT_I4; V_I4(out) = flags; return S_OK;
}
static HRESULT STDMETHODCALLTYPE ac_help_topic(IAccessible *self, BSTR *file, VARIANT child, LONG *topic) {
    if (!file || !topic) {return E_POINTER;} *topic = 0; return ac_no_string(self, child, file);
}
static HRESULT STDMETHODCALLTYPE ac_focus(IAccessible *self, VARIANT *out) {
    if (!out) {return E_POINTER;} VariantInit(out); Window *w = NULL; HRESULT hr = access_live(self, &w);
    if (FAILED(hr)) {return hr;} if (GetFocus() != w->hwnd) {return S_FALSE;} Access *a = as_access(self);
    V_VT(out) = VT_I4; V_I4(out) = CHILDID_SELF;
    for (int64_t i = 1; i < a->count; i++) if (a->words[i * 8 + 1] & 2) {V_I4(out) = (LONG)i; break;}
    return S_OK;
}
static HRESULT STDMETHODCALLTYPE ac_selection(IAccessible *self, VARIANT *out) {
    if (!out) {return E_POINTER;} VariantInit(out); Window *w = NULL; HRESULT hr = access_live(self, &w);
    return FAILED(hr) ? hr : S_FALSE; /* MSAA has no text range interface. */
}
static HRESULT STDMETHODCALLTYPE ac_action_name(IAccessible *self, VARIANT child, BSTR *out) {
    HRESULT hr = ac_no_string(self, child, out); if (FAILED(hr)) {return hr;}
    int64_t index; Access *a = as_access(self); if (!child_index(a, child, &index)) {return E_INVALIDARG;}
    const int64_t *r = a->words + index * 8;
    if (!action_role(r[0]) || (r[1] & 1)) {return S_FALSE;}
    const wchar_t *name = r[0] == 17 ? L"Open" : r[0] == 21 ? (r[1] & 8 ? L"Uncheck" : L"Check") : L"Press";
    *out = SysAllocString(name); return *out ? S_OK : E_OUTOFMEMORY;
}
static HRESULT STDMETHODCALLTYPE ac_select(IAccessible *self, LONG flags, VARIANT child) {
    (void)flags; Window *w = NULL; HRESULT hr = access_live(self, &w); if (FAILED(hr)) {return hr;}
    int64_t index; return child_index(as_access(self), child, &index) ? E_NOTIMPL : E_INVALIDARG;
}
static HRESULT STDMETHODCALLTYPE ac_location(IAccessible *self, LONG *x, LONG *y, LONG *width, LONG *height, VARIANT child) {
    if (!x || !y || !width || !height) {return E_POINTER;} *x = *y = *width = *height = 0;
    Window *w = NULL; HRESULT hr = access_live(self, &w); if (FAILED(hr)) {return hr;}
    int64_t index; Access *a = as_access(self); if (!child_index(a, child, &index)) {return E_INVALIDARG;}
    int64_t *r = a->words + index * 8; RECT rect;
    if (!access_rect(w, r, &rect)) {return S_FALSE;}
    POINT point = {rect.left, rect.top};
    if (!ClientToScreen(w->hwnd, &point)) {return E_FAIL;}
    *x = point.x; *y = point.y; *width = rect.right-rect.left; *height = rect.bottom-rect.top; return S_OK;
}
static HRESULT STDMETHODCALLTYPE ac_navigate(IAccessible *self, LONG direction, VARIANT child, VARIANT *out) {
    if (!out) {return E_POINTER;} VariantInit(out); Window *w = NULL; HRESULT hr = access_live(self, &w);
    if (FAILED(hr)) {return hr;} Access *a = as_access(self); int64_t index;
    if (!child_index(a, child, &index)) {return E_INVALIDARG;}
    int64_t target = -1;
    if (!index && a->count > 1 && direction == NAVDIR_FIRSTCHILD) target = 1;
    if (!index && a->count > 1 && direction == NAVDIR_LASTCHILD) target = a->count - 1;
    if (index > 0 && direction == NAVDIR_NEXT && index + 1 < a->count) target = index + 1;
    if (index > 1 && direction == NAVDIR_PREVIOUS) target = index - 1;
    if (target < 0) {return S_FALSE;} V_VT(out) = VT_I4; V_I4(out) = (LONG)target; return S_OK;
}
static HRESULT STDMETHODCALLTYPE ac_hit(IAccessible *self, LONG x, LONG y, VARIANT *out) {
    if (!out) {return E_POINTER;} VariantInit(out); Window *w = NULL; HRESULT hr = access_live(self, &w);
    if (FAILED(hr)) {return hr;} POINT point = {x,y}; if (!ScreenToClient(w->hwnd, &point)) {return E_FAIL;}
    Access *a = as_access(self); int64_t *root = a->words; RECT root_rect;
    if (!access_rect(w, root, &root_rect) || !PtInRect(&root_rect, point)) {return S_FALSE;}
    V_VT(out) = VT_I4; V_I4(out) = CHILDID_SELF;
    for (int64_t i = a->count - 1; i >= 1; i--) {
        int64_t *r = a->words + i * 8; RECT rect;
        if (access_rect(w, r, &rect) && PtInRect(&rect, point)) {
            V_I4(out) = (LONG)i; break;
        }
    }return S_OK;
}
static HRESULT STDMETHODCALLTYPE ac_action(IAccessible *self, VARIANT child) {
    Window *w = NULL; HRESULT hr = access_live(self, &w); if (FAILED(hr)) {return hr;}
    Access *a = as_access(self); int64_t index; if (!child_index(a, child, &index)) {return E_INVALIDARG;}
    if (!action_role(a->words[index * 8]) || (a->words[index * 8 + 1] & 1)) {return E_ACCESSDENIED;}
    enqueue(w, 11, a->document, index); return w->failure ? E_FAIL : S_OK;
}
static HRESULT STDMETHODCALLTYPE ac_put(IAccessible *self, VARIANT child, BSTR value) {
    (void)value; Window *w = NULL; HRESULT hr = access_live(self, &w); if (FAILED(hr)) {return hr;}
    int64_t index; return child_index(as_access(self), child, &index) ? E_ACCESSDENIED : E_INVALIDARG;
}
static IAccessibleVtbl accessible_vtable = {
    ac_query, ac_add, ac_release, ac_type_count, ac_type, ac_ids, ac_invoke,
    ac_parent, ac_count, ac_child, ac_name, ac_value, ac_description, ac_role, ac_state,
    ac_no_string, ac_help_topic, ac_no_string, ac_focus, ac_selection, ac_action_name,
    ac_select, ac_location, ac_navigate, ac_hit, ac_action, ac_put, ac_put
};
static LRESULT accessible_object(Window *w, WPARAM wp) {
    return LresultFromObject(&IID_IAccessible, wp, (IUnknown *)&w->access->iface);
}
static void accessibility_close(Window *w) {
    if (w->access) {Access *old = w->access; w->access = NULL; ac_release(&old->iface); OleUninitialize();}
}
int64_t assisp_reader_version(void) {return on_owner() ? 1 : -5;}
int64_t assisp_measure_scaled(const uint8_t *text, int64_t length, int32_t scale) {
    if (!on_owner()) {return -5;} if (scale != 1000 && scale != 2000) {return -1;}
    if (scale == 1000) {return assisp_measure_utf8(text, length);}
    wchar_t *wide = NULL; int count = 0; int code = wide_text(text, length, 4096, &wide, &count); if (code) {return code;}
    HFONT font = reader_font(scale); HDC dc = font && resource_allowed() ? CreateCompatibleDC(NULL) : NULL;
    if (!dc) {if (font) DeleteObject(font); free(wide); return -4;}
    HGDIOBJ previous = SelectObject(dc, font); SIZE extent = {0};
    if (!previous || previous == HGDI_ERROR || !GetTextExtentPoint32W(dc, wide, count, &extent)) code = -6;
    if (previous && previous != HGDI_ERROR) SelectObject(dc, previous);
    DeleteDC(dc); DeleteObject(font); free(wide);
    return code ? code : ((int64_t)extent.cy << 32) | (uint32_t)extent.cx;
}
int32_t assisp_text_scaled(int64_t token, int32_t x, int32_t y, const uint8_t *text, int64_t length, uint32_t rgba, int32_t scale) {
    return draw_scaled(token, x, y, text, length, rgba, scale);
}
int32_t assisp_clipboard_utf8(int64_t token, const uint8_t *text, int64_t length) {
    Window *w = NULL; int code = access_window(token, &w); if (code) {return code;}
    if (length < 0 || length > 1048576 || (!text && length) || (length && memchr(text, 0, (size_t)length))) {return -1;}
    wchar_t *wide = NULL; int count = 0; code = wide_text(text, length, 1048576, &wide, &count); if (code) {return code;}
    size_t extra = 0; for (int i = 0; i < count; i++) if (wide[i] == L'\n' && (!i || wide[i-1] != L'\r')) extra++;
    HGLOBAL memory = resource_allowed() ? GlobalAlloc(GMEM_MOVEABLE, ((size_t)count + extra + 1) * sizeof(wchar_t)) : NULL;
    if (!memory) {free(wide); return -4;} wchar_t *target = GlobalLock(memory);
    if (!target) {free(wide); GlobalFree(memory); return -4;} size_t at = 0;
    for (int i = 0; i < count; i++) {if (wide[i] == L'\n' && (!i || wide[i-1] != L'\r')) target[at++] = L'\r'; target[at++] = wide[i];}
    target[at] = 0; GlobalUnlock(memory); free(wide);
    if (!OpenClipboard(w->hwnd)) {GlobalFree(memory); return -6;}
    int success = EmptyClipboard() && SetClipboardData(CF_UNICODETEXT, memory) != NULL;
    CloseClipboard(); if (!success) {GlobalFree(memory); return -6;} return 0;
}
int32_t assisp_clipboard_read_utf8(int64_t token, int64_t document, uint8_t *output, int64_t capacity) {
    Window *w = NULL;
    int code = access_window(token, &w);
    if (code) return code;
    if (!output || capacity < 1 || capacity > 1024 || document <= 0) return -1;
    if (!w->text_input || w->text_document != document) return -2;
    if (!OpenClipboard(w->hwnd)) return -6;

    int result = 0;
    if (IsClipboardFormatAvailable(CF_UNICODETEXT)) {
        HGLOBAL memory = GetClipboardData(CF_UNICODETEXT);
        const WCHAR *wide = memory ? GlobalLock(memory) : NULL;
        if (!wide) {
            result = -6;
        } else {
            size_t units = GlobalSize(memory) / sizeof(*wide);
            size_t limit = units < (size_t)capacity + 1 ? units : (size_t)capacity + 1;
            size_t count = 0;
            while (count < limit && wide[count]) count++;
            if (count == limit) result = count > (size_t)capacity ? -4 : -1;
            else if (count) {
                int bytes = WideCharToMultiByte(CP_UTF8, WC_ERR_INVALID_CHARS, wide, (int)count, NULL, 0, NULL, NULL);
                if (!bytes) result = -1;
                else if (bytes > capacity) result = -4;
                else {
                    int written = WideCharToMultiByte(CP_UTF8, WC_ERR_INVALID_CHARS, wide, (int)count, (char *)output, bytes, NULL, NULL);
                    result = written == bytes ? bytes : -1;
                }
            }
            GlobalUnlock(memory);
        }
    }
    if (!CloseClipboard()) return -6;
    return result;
}
static int32_t accessibility_commit(int64_t token, int64_t document, const int64_t *words, int64_t count, const uint8_t *names, int64_t length, int projection_kind) {
    Window *w = NULL; int code = access_window(token, &w); if (code) {return code;}
    if (document <= 0 || !words || count < 1 || count > 32769 || length < 0 || length > 1048608 || (!names && length)) {return -1;}
    if (w->access && document < w->access->document) {return -2;}
    // Validate every range before allocating/copying; slices must be UTF-8 boundaries.
    int focused = 0;
    int64_t expected_name = 0;
    for (int64_t i = 0; i < count; i++) {
        const int64_t *r = words + i * 8;
        int allowed = i ? r[0] == 6 || r[0] == 8 || r[0] == 9 ||
            (projection_kind >= 1 && r[0] >= 12 && r[0] <= 19) ||
            (projection_kind >= 2 && r[0] >= 20 && r[0] <= 22) ||
            (projection_kind == 3 && edit_role(r[0])) : r[0] == 1;
        int mask = projection_kind >= 2 && r[0] == 21 ? 15 : 7;
        if (!allowed || r[1] < 0 || r[1] > mask ||
            r[2] < 0 || r[2] > 16384 || r[3] < 0 || r[3] > 16384 || r[4] < 0 || r[4] > 16384 || r[5] < 0 || r[5] > 16384 ||
            r[6] < 0 || r[7] < 0 || r[7] > 1048576 || r[6] > length || r[7] > length - r[6]) return -1;
        if (projection_kind == 3) {
            if (r[6] != expected_name || (r[7] && !MultiByteToWideChar(CP_UTF8, MB_ERR_INVALID_CHARS,
                    (const char *)names+r[6], (int)r[7], NULL, 0))) return -1;
            expected_name = r[6] + r[7];
            if (edit_role(r[0])) {
                if (length - expected_name < 2) return -1;
                int size = names[expected_name] | (names[expected_name+1] << 8);
                expected_name += 2;
                if (size > 1024 || size > length - expected_name ||
                    (size && (memchr(names+expected_name, 0, (size_t)size) ||
                    !MultiByteToWideChar(CP_UTF8, MB_ERR_INVALID_CHARS, (const char *)names+expected_name, size, NULL, 0)))) return -1;
                expected_name += size;
            }
        } else if ((r[6] < length && names[r[6]] >= 128 && names[r[6]] < 192) ||
                   (r[6]+r[7] < length && names[r[6]+r[7]] >= 128 && names[r[6]+r[7]] < 192)) return -1;
        if (r[1] & 2) {if ((!action_role(r[0]) && !edit_role(r[0])) || (r[1] & 1) || focused++) return -1;}
    }
    if (projection_kind == 3) {
        if (expected_name != length) return -1;
    } else if (length && !MultiByteToWideChar(CP_UTF8, MB_ERR_INVALID_CHARS, (const char *)names, (int)length, NULL, 0)) return -1;
    Access *old = w->access;
    if (old && old->document == document) {
        if (count != old->count || length != old->length || (length && memcmp(names, old->names, (size_t)length))) {return -1;}
        for (int64_t i = 0; i < count; i++) if (words[i*8] != old->words[i*8] ||
            words[i*8+6] != old->words[i*8+6] || words[i*8+7] != old->words[i*8+7]) return -1;
    }
    int64_t *copied = resource_allowed() ? malloc((size_t)count * 8 * sizeof(int64_t)) : NULL;
    uint8_t *labels = copied && resource_allowed() ? malloc((size_t)length + 1) : NULL;
    if (!copied || !labels) {free(copied); free(labels); return -4;}
    memcpy(copied, words, (size_t)count * 8 * sizeof(int64_t)); if (length) memcpy(labels, names, (size_t)length); labels[length] = 0;
    Access *a = old;
    int new_document = !old || old->document != document; LONG focused_before = 0, focused_after = 0;
    if (old) for (int64_t i = 1; i < old->count; i++) if (old->words[i*8+1] & 2) focused_before = (LONG)i;
    if (new_document) {
        a = resource_allowed() ? calloc(1, sizeof(*a)) : NULL;
        if (!a) {free(copied); free(labels); return -4;}
        a->iface.lpVtbl = &accessible_vtable; a->references = 1; a->token = token; a->document = document;
        if (!old && FAILED(OleInitialize(NULL))) {free(copied); free(labels); free(a); return -6;}
#ifdef ASSISP_TESTING
        InterlockedIncrement(&access_objects);
#endif
    }
    int64_t *previous_words = new_document ? NULL : a->words; uint8_t *previous_names = new_document ? NULL : a->names;
    a->words = copied; a->names = labels; a->count = count; a->length = length; w->access = a;
    free(previous_words); free(previous_names); if (new_document && old) ac_release(&old->iface);
    for (int64_t i = 1; i < count; i++) if (words[i*8+1] & 2) focused_after = (LONG)i;
    if (new_document) NotifyWinEvent(EVENT_OBJECT_REORDER, w->hwnd, OBJID_CLIENT, CHILDID_SELF);
    else NotifyWinEvent(EVENT_OBJECT_LOCATIONCHANGE, w->hwnd, OBJID_CLIENT, CHILDID_SELF);
    if (focused_before != focused_after || new_document) NotifyWinEvent(EVENT_OBJECT_FOCUS, w->hwnd, OBJID_CLIENT, focused_after);
    return 0;
}

int32_t assisp_accessibility(int64_t token, int64_t document, const int64_t *words, int64_t count, const uint8_t *names, int64_t length) {
    return accessibility_commit(token, document, words, count, names, length, 0);
}
