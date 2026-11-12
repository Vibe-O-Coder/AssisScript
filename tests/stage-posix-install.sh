#!/bin/sh
# Match the distribution's sources and compiler without replacing tracked bin/.
set -eu
root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
compiler=$1
stage=$2
mkdir -p "$stage/bin"
cp "$compiler" "$stage/bin/assis"
for entry in assets benchmarks docs stdlib tools vscode-assisscript instalar.sh desinstalar.sh \
    README.md README.en.md README.es.md README.pt-BR.md LICENSE THIRD_PARTY_NOTICES.md; do
    ln -s "$root/$entry" "$stage/$entry"
done
# The installer enumerates nested examples with find, which skips symlink roots.
cp -R "$root/exemplos" "$stage/exemplos"
