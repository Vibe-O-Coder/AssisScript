/* OS adaptation for read-only local resource grants. The trusted AssisScript
 * loader owns manifest parsing, quotas, cancellation and publication. */
#define LOCAL_ROOT_BYTES 4096
#define LOCAL_KEY_BYTES 1024
#define LOCAL_FILE_BYTES 1048576
#define LOCAL_GRANTS 16

static int local_key(const uint8_t *key, int64_t length) {
    if (!key || length < 1 || length > LOCAL_KEY_BYTES) return 0;
    int segment = 0;
    for (int i = 0; i <= length; ++i) {
        int ch = i == length ? '/' : key[i];
        if (ch == '/') {
            /* Also excludes empty, dot and dot-dot segments. */
            if (!segment || segment > 255 || key[i - 1] == '.') return 0;
            segment = 0;
        } else {
            if (!((ch >= 'a' && ch <= 'z') || (ch >= 'A' && ch <= 'Z') ||
                  (ch >= '0' && ch <= '9') || ch == '.' || ch == '_' || ch == '-'))
                return 0;
            ++segment;
        }
    }
    return 1;
}

#ifdef _WIN32
#include <winternl.h>
#include <wchar.h>
typedef HANDLE LocalFileHandle;
#define LOCAL_INVALID INVALID_HANDLE_VALUE
#define LOCAL_MAX_COMPONENTS 64
typedef NTSTATUS (NTAPI *LocalNtCreateFile)(PHANDLE, ACCESS_MASK, POBJECT_ATTRIBUTES,
    PIO_STATUS_BLOCK, PLARGE_INTEGER, ULONG, ULONG, ULONG, ULONG, PVOID, ULONG);

static void local_release(LocalFileHandle handle) { CloseHandle(handle); }

static LocalNtCreateFile local_nt_create(void) {
    HMODULE module = GetModuleHandleW(L"ntdll.dll");
    FARPROC proc = module ? GetProcAddress(module, "NtCreateFile") : NULL;
    LocalNtCreateFile create = NULL;
    _Static_assert(sizeof(create) == sizeof(proc), "NT entry point size");
    memcpy(&create, &proc, sizeof(create));
    return create;
}

static int local_directory(LocalFileHandle handle, int directory) {
    FILE_ATTRIBUTE_TAG_INFO tags;
    if (GetFileType(handle) != FILE_TYPE_DISK ||
        !GetFileInformationByHandleEx(handle, FileAttributeTagInfo, &tags, sizeof(tags))) return 0;
    if (tags.FileAttributes & (FILE_ATTRIBUTE_REPARSE_POINT | FILE_ATTRIBUTE_DEVICE |
                               FILE_ATTRIBUTE_OFFLINE)) return 0;
    return !!(tags.FileAttributes & FILE_ATTRIBUTE_DIRECTORY) == directory;
}

static int local_spelling(LocalFileHandle handle, const WCHAR *expected) {
    WCHAR name[LOCAL_ROOT_BYTES + LOCAL_KEY_BYTES + 2];
    DWORD length = GetFinalPathNameByHandleW(handle, name, sizeof(name) / sizeof(*name),
                                            FILE_NAME_NORMALIZED | VOLUME_NAME_NONE);
    if (!length || length >= sizeof(name) / sizeof(*name)) return 0;
    WCHAR *leaf = wcsrchr(name, L'\\');
    return leaf && wcscmp(leaf + 1, expected) == 0;
}

/* Every component is opened beneath an already validated directory handle.
 * Keep its ancestors open without share-delete until the read finishes. */
static LocalFileHandle local_child(LocalNtCreateFile create, LocalFileHandle directory, WCHAR *component,
                               int folder, int exact) {
    size_t count = wcslen(component);
    if (!count || count > 255 || component[count - 1] == L'.' ||
        component[count - 1] == L' ') return LOCAL_INVALID;
    UNICODE_STRING name = {(USHORT)(count * sizeof(WCHAR)),
                           (USHORT)(count * sizeof(WCHAR)), component};
    OBJECT_ATTRIBUTES attrs;
    InitializeObjectAttributes(&attrs, &name, OBJ_CASE_INSENSITIVE | OBJ_DONT_REPARSE,
                               directory, NULL);
    IO_STATUS_BLOCK io;
    LocalFileHandle handle = LOCAL_INVALID;
    ACCESS_MASK access = FILE_READ_ATTRIBUTES | SYNCHRONIZE |
                         (folder ? FILE_TRAVERSE : FILE_READ_DATA);
    ULONG share = FILE_SHARE_READ | (folder ? FILE_SHARE_WRITE : 0);
    ULONG options = FILE_OPEN_REPARSE_POINT | FILE_SYNCHRONOUS_IO_NONALERT |
                    (folder ? 0 : FILE_NON_DIRECTORY_FILE);
    if (create(&handle, access, &attrs, &io, NULL, 0, share, FILE_OPEN, options, NULL, 0) < 0)
        return LOCAL_INVALID;
    if (!local_directory(handle, folder) || (exact && !local_spelling(handle, component))) {
        local_release(handle);
        return LOCAL_INVALID;
    }
    return handle;
}

static LocalFileHandle local_walk(LocalNtCreateFile create, LocalFileHandle root, WCHAR *path,
                              int folder, int exact, LocalFileHandle *parents, int *count) {
    LocalFileHandle parent = root;
    for (;;) {
        WCHAR *separator = wcschr(path, L'\\');
        if (!separator) return local_child(create, parent, path, folder, exact);
        if (*count == LOCAL_MAX_COMPONENTS) return LOCAL_INVALID;
        *separator = 0;
        LocalFileHandle child = local_child(create, parent, path, 1, exact);
        if (child == LOCAL_INVALID) return LOCAL_INVALID;
        parents[(*count)++] = child;
        parent = child;
        path = separator + 1;
    }
}

static int64_t local_root(const uint8_t *path, int64_t length, LocalFileHandle *result) {
    WCHAR wide[LOCAL_ROOT_BYTES + 1];
    int count = MultiByteToWideChar(CP_UTF8, MB_ERR_INVALID_CHARS, (const char *)path,
                                    (int)length, wide, LOCAL_ROOT_BYTES);
    if (count < 3) return -1;
    wide[count] = 0;
    for (int i = 0; i < count; ++i) {
        if (wide[i] == L'/') wide[i] = L'\\';
        if (i >= 3 && wcschr(L":*?\"<>|", wide[i])) return -1;
    }
    WCHAR drive = wide[0];
    if (!((drive >= L'A' && drive <= L'Z') || (drive >= L'a' && drive <= L'z')) ||
        wide[1] != L':' || wide[2] != L'\\') return -1;
    if (count > 3 && wide[count - 1] == L'\\') wide[--count] = 0;
    WCHAR volume[4] = {drive, L':', L'\\', 0};
    if (GetDriveTypeW(volume) != DRIVE_FIXED) return -10;
    LocalNtCreateFile create = local_nt_create();
    if (!create) return -10;
    LocalFileHandle root = CreateFileW(volume, FILE_TRAVERSE | FILE_READ_ATTRIBUTES,
        FILE_SHARE_READ | FILE_SHARE_WRITE, NULL, OPEN_EXISTING,
        FILE_FLAG_BACKUP_SEMANTICS | FILE_FLAG_OPEN_REPARSE_POINT, NULL);
    if (root == LOCAL_INVALID) return -6;
    if (!local_directory(root, 1)) {
        local_release(root);
        return -6;
    }
    if (count == 3) {
        *result = root;
        return 0;
    }
    LocalFileHandle parents[LOCAL_MAX_COMPONENTS];
    int opened = 0;
    *result = local_walk(create, root, wide + 3, 1, 0, parents, &opened);
    while (opened) local_release(parents[--opened]);
    local_release(root);
    return *result == LOCAL_INVALID ? -6 : 0;
}

static int64_t local_read_file(LocalFileHandle file, uint8_t *buffer, int64_t capacity) {
    BY_HANDLE_FILE_INFORMATION info;
    if (!GetFileInformationByHandle(file, &info) || info.nNumberOfLinks != 1) return -6;
    if (info.nFileSizeHigh || info.nFileSizeLow > (uint64_t)capacity) return -3;
    DWORD total = 0;
    while (total < info.nFileSizeLow) {
        DWORD got;
        if (!ReadFile(file, buffer + total, info.nFileSizeLow - total, &got, NULL) || !got) return -6;
        total += got;
    }
    uint8_t extra;
    DWORD got;
    BY_HANDLE_FILE_INFORMATION after;
    if (!ReadFile(file, &extra, 1, &got, NULL) || got ||
        !GetFileInformationByHandle(file, &after) || after.nNumberOfLinks != 1 ||
        after.nFileSizeHigh || after.nFileSizeLow != total ||
        CompareFileTime(&info.ftLastWriteTime, &after.ftLastWriteTime) != 0) return -6;
    return total;
}

static int64_t local_read(LocalFileHandle root, const uint8_t *key, int64_t length,
                          uint8_t *buffer, int64_t capacity) {
    WCHAR wide[LOCAL_KEY_BYTES + 1];
    for (int i = 0; i < length; ++i) wide[i] = key[i] == '/' ? L'\\' : key[i];
    wide[length] = 0;
    LocalNtCreateFile create = local_nt_create();
    if (!create) return -10;
    LocalFileHandle parents[LOCAL_MAX_COMPONENTS];
    int opened = 0;
    LocalFileHandle file = local_walk(create, root, wide, 0, 1, parents, &opened);
    int64_t status = -6;
    if (file != LOCAL_INVALID) {
        status = local_read_file(file, buffer, capacity);
        local_release(file);
    }
    while (opened) local_release(parents[--opened]);
    return status;
}

#else
#include <sys/stat.h>
#include <sys/vfs.h>
#include <linux/magic.h>
#include <linux/openat2.h>
typedef int LocalFileHandle;
#define LOCAL_INVALID (-1)

static void local_release(LocalFileHandle handle) { close(handle); }

static int64_t local_os_error(void) { return errno == ENOSYS || errno == EINVAL ? -10 : -6; }

static int64_t local_root(const uint8_t *path, int64_t length, LocalFileHandle *result) {
    if (path[0] != '/') return -1;
    char name[LOCAL_ROOT_BYTES + 1];
    memcpy(name, path, (size_t)length);
    name[length] = 0;
    struct open_how how = {.flags = O_PATH | O_DIRECTORY | O_CLOEXEC,
                           .resolve = RESOLVE_NO_SYMLINKS};
    *result = (int)syscall(SYS_openat2, AT_FDCWD, name, &how, sizeof(how));
    return *result < 0 ? local_os_error() : 0;
}

static int local_same_file(const struct stat *before, const struct stat *after) {
    return S_ISREG(after->st_mode) && after->st_nlink == 1 &&
           before->st_dev == after->st_dev && before->st_ino == after->st_ino &&
           before->st_size == after->st_size &&
           before->st_mtim.tv_sec == after->st_mtim.tv_sec &&
           before->st_mtim.tv_nsec == after->st_mtim.tv_nsec &&
           before->st_ctim.tv_sec == after->st_ctim.tv_sec &&
           before->st_ctim.tv_nsec == after->st_ctim.tv_nsec;
}

/* Reopen the checked inode through the kernel's descriptor directory. Opening
 * an unclassified pathname for reading could touch a device or block on FIFO. */
static int local_open_pinned(LocalFileHandle node) {
    int proc = open("/proc/self/fd", O_PATH | O_DIRECTORY | O_CLOEXEC);
    if (proc < 0) return -1;
    struct statfs fs;
    int file = -1;
    if (fstatfs(proc, &fs) == 0 && fs.f_type == PROC_SUPER_MAGIC) {
        char name[32];
        snprintf(name, sizeof(name), "%d", node);
        file = openat(proc, name, O_RDONLY | O_CLOEXEC | O_NONBLOCK | O_NOCTTY);
    }
    close(proc);
    return file;
}

static int64_t local_read_file(int file, const struct stat *expected, uint8_t *buffer) {
    struct stat observed;
    if (fstat(file, &observed) != 0 || !local_same_file(expected, &observed)) return -6;
    size_t total = 0;
    while (total < (size_t)expected->st_size) {
        ssize_t got = read(file, buffer + total, (size_t)expected->st_size - total);
        if (got < 0 && errno == EINTR) continue;
        if (got <= 0) return -6;
        total += (size_t)got;
    }
    uint8_t extra;
    ssize_t got;
    do { got = read(file, &extra, 1); } while (got < 0 && errno == EINTR);
    if (got != 0 || fstat(file, &observed) != 0 || !local_same_file(expected, &observed)) return -6;
    return (int64_t)total;
}

static int64_t local_read(LocalFileHandle root, const uint8_t *key, int64_t length,
                          uint8_t *buffer, int64_t capacity) {
    char name[LOCAL_KEY_BYTES + 1];
    memcpy(name, key, (size_t)length);
    name[length] = 0;
    struct open_how how = {.flags = O_PATH | O_CLOEXEC,
                           .resolve = RESOLVE_BENEATH | RESOLVE_NO_SYMLINKS | RESOLVE_NO_XDEV};
    int node = (int)syscall(SYS_openat2, root, name, &how, sizeof(how));
    if (node < 0) return local_os_error();
    int64_t status = -6;
    struct stat info;
    if (fstat(node, &info) == 0 && S_ISREG(info.st_mode) && info.st_nlink == 1) {
        if (info.st_size < 0 || info.st_size > capacity) status = -3;
        else {
            int file = local_open_pinned(node);
            if (file >= 0) {
                status = local_read_file(file, &info, buffer);
                close(file);
            }
        }
    }
    close(node);
    return status;
}
#endif

typedef struct { int64_t token; LocalFileHandle root; } LocalGrant;
static LocalGrant local_grants[LOCAL_GRANTS];
static int64_t local_sequence;

static LocalGrant *local_grant(int64_t token) {
    if (token <= 0) return NULL;
    for (int i = 0; i < LOCAL_GRANTS; ++i)
        if (local_grants[i].token == token) return &local_grants[i];
    return NULL;
}

int64_t assw_local_version(void) { return owner_thread() ? 1 : -11; }

int64_t assw_local_open(const uint8_t *path, int64_t length) {
    if (!owner_thread()) return -11;
    if (!path || length < 1 || length > LOCAL_ROOT_BYTES || memchr(path, 0, (size_t)length))
        return -1;
    for (int i = 0; i < LOCAL_GRANTS; ++i) {
        if (local_grants[i].token) continue;
        if (local_sequence == INT64_MAX) return -3;
        LocalFileHandle root = LOCAL_INVALID;
        int64_t status = local_root(path, length, &root);
        if (status != 0) return status;
        local_grants[i] = (LocalGrant){++local_sequence, root};
        return local_grants[i].token;
    }
    return -3;
}

int64_t assw_local_read(int64_t token, const uint8_t *key, int64_t length,
                        uint8_t *buffer, int64_t capacity) {
    if (!owner_thread()) return -11;
    LocalGrant *grant = local_grant(token);
    if (!grant) return -2;
    if (!local_key(key, length) || capacity < 0 || capacity > LOCAL_FILE_BYTES ||
        (capacity && !buffer)) return -1;
    return local_read(grant->root, key, length, buffer, capacity);
}

int64_t assw_local_close(int64_t token) {
    if (!owner_thread()) return -11;
    LocalGrant *grant = local_grant(token);
    if (!grant) return -2;
    local_release(grant->root);
    grant->token = 0;
    return 0;
}
