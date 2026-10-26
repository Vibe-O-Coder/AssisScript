#!/bin/sh
# Instala o binário pronto. Não compila nem baixa dependências.
set -eu
root=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
prefix="${HOME:?HOME não definido}/.local"
change_path=yes
. "$root/stdlib/catalogo.sh"
optional=$ASSIS_OPTIONAL
selected=no
while [ "$#" -gt 0 ]; do
    case "$1" in
        --prefix) [ "$#" -ge 2 ] || { echo 'Use --prefix PASTA' >&2; exit 2; }; prefix=$2; shift 2 ;;
        --no-path) change_path=no; shift ;;
        --minimal) [ "$selected" = yes ] || optional=''; selected=yes; shift ;;
        --with)
            [ "$#" -ge 2 ] && [ -n "$2" ] || { echo '--with exige LISTA' >&2; exit 2; }
            [ "$selected" = yes ] || optional=''; selected=yes
            case "$2" in ,*|*,|*,,*) echo 'Lista de bibliotecas inválida' >&2; exit 2 ;; esac
            saved_ifs=$IFS; IFS=,; set -f
            for lib in $2; do case " $ASSIS_OPTIONAL " in *" $lib "*) optional="$optional $lib" ;; *) echo "Biblioteca desconhecida: $lib" >&2; exit 2 ;; esac; done
            set +f; IFS=$saved_ifs; shift 2 ;;
        --help|-h) echo 'Uso: sh instalar.sh [--prefix PASTA] [--no-path] [--minimal | --with LISTA]'; exit 0 ;;
        *) echo "Opção desconhecida: $1" >&2; exit 2 ;;
    esac
done
changed=yes
while [ "$changed" = yes ]; do
    changed=no
    for rule in $ASSIS_DEPENDENCIES; do
        owner=${rule%%:*}; dependency=${rule#*:}
        case " $optional " in *" $owner "*) case " $optional " in *" $dependency "*) ;; *) optional="$optional $dependency"; changed=yes ;; esac ;; esac
    done
done
case "$(uname -s):$(uname -m)" in
    Linux:x86_64) ;;
    *) echo 'Este instalador .sh é para Linux x86_64. No Windows x64, use instalar-windows.cmd.' >&2; exit 1 ;;
esac
[ -f "$root/bin/assis" ] || { echo 'bin/assis não encontrado. Extraia o pacote completo.' >&2; exit 1; }
[ -n "$prefix" ] || { echo 'O prefixo não pode ser vazio.' >&2; exit 2; }
mkdir -p "$prefix"
prefix=$(CDPATH= cd -- "$prefix" && pwd -P)
mkdir -p "$prefix/bin" "$prefix/share/assisscript/exemplos" "$prefix/share/assisscript/docs" "$prefix/share/assisscript/stdlib"
mkdir -p "$prefix/share/assisscript/assets"
cp "$root/bin/assis" "$prefix/bin/assis"
chmod 755 "$prefix/bin/assis"
cp "$root/README.md" "$prefix/share/assisscript/README.md"
cp "$root/README.en.md" "$root/README.pt-BR.md" "$root/README.es.md" "$root/LICENSE" "$root/THIRD_PARTY_NOTICES.md" "$prefix/share/assisscript/"
cp "$root/exemplos/"*.assis "$prefix/share/assisscript/exemplos/"
cp -R "$root/exemplos/." "$prefix/share/assisscript/exemplos/"
cp "$root/exemplos/"*.pillow "$prefix/share/assisscript/exemplos/"
cp "$root/assets/"*.ico "$prefix/share/assisscript/assets/"
mkdir -p "$prefix/share/assisscript/benchmarks/resultados"
cp "$root/benchmarks/resultados/"*.md "$root/benchmarks/resultados/"*.json "$prefix/share/assisscript/benchmarks/resultados/"
for lib in $ASSIS_REQUIRED $optional; do cp "$root/stdlib/$lib.assis" "$prefix/share/assisscript/stdlib/"; done
mkdir -p "$prefix/share/assisscript/tools" "$prefix/share/assisscript/vscode-assisscript/src"
cp "$root/tools/assis-lsp.js" "$prefix/share/assisscript/tools/"
cp "$root/vscode-assisscript/src/language.js" "$root/vscode-assisscript/src/reference.json" "$prefix/share/assisscript/vscode-assisscript/src/"
cp "$root/vscode-assisscript/package.json" "$prefix/share/assisscript/vscode-assisscript/"
cp "$root/stdlib/catalogo.sh" "$prefix/share/assisscript/stdlib/"
cp "$root/stdlib/catalogo.json" "$prefix/share/assisscript/stdlib/"
cp "$root/docs/GRAMATICA.ebnf" "$prefix/share/assisscript/docs/GRAMATICA.ebnf"
cp "$root/docs/"*.md "$prefix/share/assisscript/docs/"
cp "$root/docs/"*.json "$prefix/share/assisscript/docs/"
cp "$root/docs/LICENSE" "$prefix/share/assisscript/docs/"
mkdir -p "$prefix/share/assisscript/docs/third-party"
cp "$root/docs/third-party/"*.txt "$prefix/share/assisscript/docs/third-party/"
printf 'AssisScript %s\n' "$ASSIS_VERSION" > "$prefix/share/assisscript/INSTALADO"
manifest="$prefix/share/assisscript/INSTALADOS.txt"
{
    printf '%s\n' README.md README.en.md README.pt-BR.md README.es.md LICENSE THIRD_PARTY_NOTICES.md docs/LICENSE stdlib/catalogo.json stdlib/catalogo.sh INSTALADO tools/assis-lsp.js vscode-assisscript/src/language.js vscode-assisscript/src/reference.json vscode-assisscript/package.json
    for notice in "$root/docs/third-party/"*.txt; do printf '%s\n' "${notice#"$root/"}"; done
    find "$root/exemplos" -type f | while IFS= read -r example; do printf '%s\n' "${example#"$root/"}"; done
    for lib in $ASSIS_REQUIRED $optional; do printf 'stdlib/%s.assis\n' "$lib"; done
    for file in "$root/docs/"*.md "$root/docs/"*.json "$root/docs/"*.ebnf "$root/exemplos/"*.assis "$root/exemplos/"*.pillow "$root/exemplos/bibliotecas/"*.assis "$root/assets/"*.ico "$root/benchmarks/resultados/"*.md "$root/benchmarks/resultados/"*.json; do
        [ -f "$file" ] || continue
        printf '%s\n' "${file#"$root/"}"
    done
} > "$manifest"

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
