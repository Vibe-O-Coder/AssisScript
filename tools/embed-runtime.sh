#!/bin/sh
set -eu
root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
mkdir -p "$root/build"
as --64 -I "$root/src" "$root/src/runtime.S" -o "$root/build/runtime.o"
if readelf -r "$root/build/runtime.o" | grep -q 'R_X86_64'; then
    echo 'Erro: o runtime contém relocations pendentes.' >&2
    exit 1
fi
objcopy -O binary --only-section=.text "$root/build/runtime.o" "$root/build/runtime.bin"
{
    echo '/* Gerado de runtime.S por tools/embed-runtime.sh. */'
    echo '#ifndef ASSIS_RUNTIME_BLOB_H'
    echo '#define ASSIS_RUNTIME_BLOB_H'
    echo 'static const unsigned char runtime_blob[] = {'
    od -An -v -t u1 "$root/build/runtime.bin" | awk '{ for(i=1;i<=NF;i++) printf "%s,", $i; print ""; }'
    echo '};'
    nm -n "$root/build/runtime.o" | awk '$3 ~ /^asrt_/ { name=$3; sub(/^asrt_/,"",name); printf "#define RT_%s 0x%s\n",name,$1; }'
    echo '#endif'
} > "$root/src/runtime_blob.h"
as --64 -I "$root/src" "$root/src/runtime_win.S" -o "$root/build/runtime_win.o"
if readelf -r "$root/build/runtime_win.o" | grep -q 'R_X86_64'; then
    echo 'Erro: o runtime Windows contém relocations pendentes.' >&2
    exit 1
fi
objcopy -O binary --only-section=.text "$root/build/runtime_win.o" "$root/build/runtime_win.bin"
{
    echo '/* Gerado de runtime_win.S por tools/embed-runtime.sh. */'
    echo '#ifndef ASSIS_RUNTIME_WIN_BLOB_H'
    echo '#define ASSIS_RUNTIME_WIN_BLOB_H'
    echo 'static const unsigned char runtime_win_blob[] = {'
    od -An -v -t u1 "$root/build/runtime_win.bin" | awk '{ for(i=1;i<=NF;i++) printf "%s,", $i; print ""; }'
    echo '};'
    nm -n "$root/build/runtime_win.o" | awk '$3 ~ /^asrt_/ && $3 !~ /^asrt_import_/ { name=$3; sub(/^asrt_/,"",name); printf "#define WRT_%s 0x%s\n",name,$1; }'
    echo 'static const struct { size_t offset; const char *name; } windows_import_patches[] = {'
    nm -n "$root/build/runtime_win.o" | awk '$3 ~ /^asrt_import_/ { name=$3; sub(/^asrt_import_/,"",name); sub(/_[0-9]+$/,"",name); printf "{0x%s, \"%s\"},\n",$1,name; }'
    echo '};'
    echo '#endif'
} > "$root/src/runtime_win_blob.h"
echo 'Runtimes Linux e Windows incorporados ao código-fonte.'
