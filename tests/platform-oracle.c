/* Independent C caller: compiled by GCC, not the AssisScript compiler. */
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include "../providers/platform/assis_platform_v1.h"

#define LOAD(name) __typeof__(&name) p_##name; do { FARPROC proc = GetProcAddress(library, #name); \
    if (!proc) {return 90;} memcpy(&p_##name, &proc, sizeof(proc)); } while (0)
int main(int argc, char **argv) {
    if (argc != 2) return 91;
    HMODULE library = LoadLibraryA(argv[1]); if (!library) return 92;
    LOAD(assisp_abi_version); LOAD(assisp_open); LOAD(assisp_poll);
    LOAD(assisp_clear); LOAD(assisp_text_utf8); LOAD(assisp_present); LOAD(assisp_close);
    int64_t token = 0, words[10] = {0};
    const uint8_t title[] = "Assis ABI \xc3\xa7";
    const uint8_t text[] = {'A', 0, 'B', ' ', 0xc3, 0xa7};
    printf("%lld\n", (long long)p_assisp_abi_version());
    int code = p_assisp_open(1, 320, 160, title, sizeof(title) - 1, &token);
    printf("%d %d\n", code, token != 0); if (code) return 93;
    printf("%d %d %d\n", p_assisp_clear(token, UINT32_C(0x244866ff)),
        p_assisp_text_utf8(token, 4, 4, text, sizeof(text), UINT32_C(0xf0f0f080)), p_assisp_present(token));
    /* The two canaries detect an ABI buffer overwrite. */
    words[8] = 123; words[9] = 456;
    do { code = p_assisp_poll(token, 0, words, 8);
        if (code == 0 && (words[0] != ASSISP_ABI || words[2] != token || words[3] != 1 || words[4] <= 0 || words[7] <= 0)) return 94;
    } while (code == 0);
    if (code != 1 || words[8] != 123 || words[9] != 456) return 95;
    for (int i = 0; i < 8; i++) if (words[i]) return 96;
    printf("%d\n", code);
    printf("%d\n", p_assisp_close(token));
    printf("%d %d\n", p_assisp_close(token), p_assisp_clear(token, 0));
    FreeLibrary(library); return 0;
}
