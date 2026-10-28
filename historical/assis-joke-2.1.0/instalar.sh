#!/bin/sh
# Instala o binário pronto. Não compila nem baixa dependências.
set -eu
root=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
prefix="${HOME:?HOME não definido}/.local"
change_path=yes
while [ "$#" -gt 0 ]; do
    case "$1" in
        --prefix) [ "$#" -ge 2 ] || { echo 'Use --prefix PASTA' >&2; exit 2; }; prefix=$2; shift 2 ;;
        --no-path) change_path=no; shift ;;
        --help|-h) echo 'Uso: sh instalar.sh [--prefix PASTA] [--no-path]'; exit 0 ;;
        *) echo "Opção desconhecida: $1" >&2; exit 2 ;;
    esac
done
case "$(uname -s):$(uname -m)" in
    Linux:x86_64) ;;
    *) echo 'Este instalador .sh é para Linux x86_64. No Windows x64, use instalar-windows.cmd.' >&2; exit 1 ;;
esac
[ -f "$root/bin/assis" ] || { echo 'bin/assis não encontrado. Extraia o pacote completo.' >&2; exit 1; }
[ -n "$prefix" ] || { echo 'O prefixo não pode ser vazio.' >&2; exit 2; }
mkdir -p "$prefix"
prefix=$(CDPATH= cd -- "$prefix" && pwd -P)
mkdir -p "$prefix/bin" "$prefix/share/assisscript/exemplos" "$prefix/share/assisscript/docs"
cp "$root/bin/assis" "$prefix/bin/assis"
chmod 755 "$prefix/bin/assis"
cp "$root/README.md" "$prefix/share/assisscript/README.md"
cp "$root/exemplos/"*.assis "$prefix/share/assisscript/exemplos/"
cp "$root/docs/GRAMATICA.ebnf" "$prefix/share/assisscript/docs/GRAMATICA.ebnf"
cp "$root/docs/"*.md "$prefix/share/assisscript/docs/"
printf '%s\n' 'AssisScript 2.1.0' > "$prefix/share/assisscript/INSTALADO"

default_prefix=$(CDPATH= cd -- "$HOME" && pwd -P)/.local
if [ "$change_path" = yes ] && [ "$prefix" = "$default_prefix" ]; then
    for profile in "$HOME/.profile" "$HOME/.bashrc" "$HOME/.zshrc"; do
        [ "$profile" != "$HOME/.zshrc" ] || [ -f "$profile" ] || continue
        if ! grep -Fq '# >>> AssisScript PATH >>>' "$profile" 2>/dev/null; then
            cat >> "$profile" <<'PATH_BLOCK'

# >>> AssisScript PATH >>>
case ":$PATH:" in
    *":$HOME/.local/bin:"*) ;;
    *) export PATH="$HOME/.local/bin:$PATH" ;;
esac
# <<< AssisScript PATH <<<
PATH_BLOCK
        fi
    done
    printf 'ASSIS: instalado em %s/bin/assis\n' "$prefix"
    printf '%s\n' 'Abra um novo terminal ou execute: . "$HOME/.profile"' 'Depois: assis version'
else
    printf 'ASSIS: instalado em %s/bin/assis\n' "$prefix"
    printf 'Inclua %s/bin no PATH ou use o caminho completo.\n' "$prefix"
fi
