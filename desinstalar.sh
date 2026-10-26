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
grep -Eq '^AssisScript [0-9]+\.[0-9]+\.[0-9]+(-[0-9A-Za-z][0-9A-Za-z.-]*)?$' "$data/INSTALADO" || { echo 'Marcador de instalação inválido.' >&2; exit 1; }
if [ -f "$data/INSTALADOS.txt" ]; then
    data=$(CDPATH= cd -- "$data" && pwd -P)
    while IFS= read -r entry; do
        case "$entry" in ''|/*|*\\*|..|../*|*/../*|*/..) echo 'Manifesto de instalação inválido.' >&2; exit 1 ;; esac
        parent=$(dirname -- "$data/$entry")
        if [ -d "$parent" ]; then
            parent=$(CDPATH= cd -- "$parent" && pwd -P)
            case "$parent" in "$data"|"$data/"*) ;; *) echo 'Diretório externo no manifesto; remoção interrompida.' >&2; exit 1 ;; esac
        fi
    done < "$data/INSTALADOS.txt"
    rm -f "$prefix/bin/assis"
    while IFS= read -r entry; do rm -f -- "$data/$entry"; done < "$data/INSTALADOS.txt"
    rm -f "$data/INSTALADOS.txt"
    find "$data" -depth -type d -exec rmdir -- {} \; 2>/dev/null || true
else
    # Compatibility with old distributions that did not track installed paths.
    rm -f "$prefix/bin/assis"
    rm -rf "$data"
fi
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
