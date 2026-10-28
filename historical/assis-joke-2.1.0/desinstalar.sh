#!/bin/sh
set -eu
prefix="${HOME:?HOME não definido}/.local"
while [ "$#" -gt 0 ]; do
    case "$1" in
        --prefix) [ "$#" -ge 2 ] || { echo 'Use --prefix PASTA' >&2; exit 2; }; prefix=$2; shift 2 ;;
        --help|-h) echo 'Uso: sh desinstalar.sh [--prefix PASTA]'; exit 0 ;;
        *) echo "Opção desconhecida: $1" >&2; exit 2 ;;
    esac
done
[ -n "$prefix" ] || { echo 'O prefixo não pode ser vazio.' >&2; exit 2; }
[ -d "$prefix" ] || { echo 'Instalação não encontrada.' >&2; exit 1; }
prefix=$(CDPATH= cd -- "$prefix" && pwd -P)
data="$prefix/share/assisscript"
[ -f "$data/INSTALADO" ] || { echo 'Instalação AssisScript não encontrada nesse prefixo.' >&2; exit 1; }
grep -Fxq 'AssisScript 2.1.0' "$data/INSTALADO" || { echo 'Marcador de instalação inválido.' >&2; exit 1; }
rm -f "$prefix/bin/assis"
rm -rf "$data"
default_prefix=$(CDPATH= cd -- "$HOME" && pwd -P)/.local
if [ "$prefix" = "$default_prefix" ]; then
    for profile in "$HOME/.profile" "$HOME/.bashrc" "$HOME/.zshrc"; do
        [ -f "$profile" ] || continue
        if grep -Fq '# >>> AssisScript PATH >>>' "$profile" && grep -Fq '# <<< AssisScript PATH <<<' "$profile"; then
            tmp=$(mktemp)
            sed '/^# >>> AssisScript PATH >>>$/,/^# <<< AssisScript PATH <<<$/{d;}' "$profile" > "$tmp"
            cat "$tmp" > "$profile"
            rm -f "$tmp"
        fi
    done
fi
echo 'ASSIS: compilador desinstalado. Seus projetos foram preservados.'
