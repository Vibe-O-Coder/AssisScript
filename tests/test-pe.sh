#!/bin/sh
# Validação do backend PE no Linux com stubs de APIs e ABI Microsoft.
set -eu
root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT HUP INT TERM
count=0
for fixture in "$root/tests/cases/"*.assis; do
    name=${fixture%.assis}
    "$root/bin/assis" build --legacy "$fixture" --target windows-x64 -o "$tmp/programa.exe" > "$tmp/build"
    set +e
    "$root/build/pe_probe" "$tmp/programa.exe" > "$tmp/out" 2> "$tmp/err"
    actual=$?
    set -e
    expected=$(cat "$name.status")
    [ "$actual" = "$expected" ] || { cat "$tmp/err" >&2; echo "Status inesperado em $fixture" >&2; exit 1; }
    diff -u "$name.stdout" "$tmp/out"
    diff -u "$name.stderr" "$tmp/err"
    count=$((count+1))
done
echo "ASSIS: $count casos PE32+ aprovados com base relocada e ABI Microsoft."
echo 'Este harness não substitui os testes em Windows real.'
