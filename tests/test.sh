#!/bin/sh
# Testes nativos: nenhum Python, compilador C ou assembler é chamado.
set -eu
root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
assis=${ASSIS_BIN:-"$root/bin/assis"}
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT HUP INT TERM
count=0
fail() { printf 'FALHA: %s\n' "$*" >&2; exit 1; }
expect_status() {
    expected=$1; shift
    set +e
    "$@" > "$tmp/out" 2> "$tmp/err"
    actual=$?
    set -e
    [ "$actual" = "$expected" ] || { cat "$tmp/err" >&2; fail "status $actual, esperado $expected: $*"; }
    count=$((count+1))
}

for fixture in "$root/tests/cases/"*.assis; do
    name=${fixture%.assis}
    "$assis" build "$fixture" -o "$tmp/programa" > "$tmp/build" 2> "$tmp/build-error" || { cat "$tmp/build-error" >&2; fail "$fixture não compilou"; }
    set +e
    "$tmp/programa" > "$tmp/out" 2> "$tmp/err"
    actual=$?
    set -e
    expected=$(cat "$name.status")
    [ "$actual" = "$expected" ] || fail "status de $fixture: $actual, esperado $expected"
    diff -u "$name.stdout" "$tmp/out" || fail "saída de $fixture"
    diff -u "$name.stderr" "$tmp/err" || fail "diagnóstico de $fixture"
    count=$((count+1))
done
for fixture in "$root/tests/rejections/"*.assis; do
    expect_status 1 "$assis" check "$fixture"
    grep -Fq -f "${fixture%.assis}.message" "$tmp/err" || fail "diagnóstico de $fixture"
done

expect_status 0 "$assis" version
grep -Fq '3.3.0-alpha.10' "$tmp/out" || fail 'versão'
expect_status 0 "$assis" doctor
expect_status 0 "$assis" help
expect_status 2 "$assis" comando-inexistente
expect_status 2 "$assis" check "$tmp/inexistente.assis"
expect_status 0 "$assis" tokens "$root/exemplos/01_ola.assis"
grep -Fq 'FODASE' "$tmp/out" || fail 'tokens'

cp "$root/exemplos/01_ola.assis" "$tmp/fonte com espaço.assis"
cp "$tmp/fonte com espaço.assis" "$tmp/backup"
expect_status 2 "$assis" build "$tmp/fonte com espaço.assis" -o "$tmp/fonte com espaço.assis"
cmp "$tmp/backup" "$tmp/fonte com espaço.assis" || fail 'proteção do fonte'
ln "$tmp/fonte com espaço.assis" "$tmp/alias.assis"
expect_status 2 "$assis" build "$tmp/fonte com espaço.assis" -o "$tmp/alias.assis"
expect_status 2 "$assis" build "$tmp/fonte com espaço.assis" -o "$assis"
expect_status 0 "$assis" build "$tmp/fonte com espaço.assis" -o "$tmp/binário com espaço"
expect_status 0 "$tmp/binário com espaço"

printf '%s\n' 'assis assis_assis(): FODase { ASSis (aSsIs) {} }' > "$tmp/laco.assis"
expect_status 124 "$assis" run "$tmp/laco.assis" --timeout 0.02
expect_status 2 "$assis" run "$tmp/laco.assis" --timeout -1
expect_status 2 "$assis" run "$tmp/laco.assis" --timeout nan

# Prova operacional: não há ferramenta auxiliar no PATH.
PATH=/assisscript-sem-ferramentas "$assis" build "$root/exemplos/03_polimorfismo.assis" -o "$tmp/sem-dependencias" > "$tmp/build"
PATH=/assisscript-sem-ferramentas "$tmp/sem-dependencias" > "$tmp/out"
printf 'Base: 14\nDerivada via base: 42\n' > "$tmp/expected"
diff -u "$tmp/expected" "$tmp/out" || fail 'compilação sem PATH'
count=$((count+1))
PATH=/assisscript-sem-ferramentas "$assis" run "$root/exemplos/03_polimorfismo.assis" > "$tmp/out"
diff -u "$tmp/expected" "$tmp/out" || fail 'run sem PATH'
count=$((count+1))

expect_status 0 "$assis" new "$tmp/projeto com espaço"
(cd "$tmp/projeto com espaço" && "$assis" run) > "$tmp/out"
grep -Fq 'Assis, mundo. Fodase. 42' "$tmp/out" || fail 'projeto novo'
expect_status 2 "$assis" new "$tmp/projeto com espaço"
count=$((count+1))

# HOME isolado: não altera os arquivos de configuração de quem executa os testes.
mkdir "$tmp/home"
HOME="$tmp/home" sh "$root/instalar.sh" > "$tmp/install"
[ -f "$tmp/home/.local/share/assisscript/docs/LINGUAGEM.md" ] || fail 'manual instalado'
count=$((count+1))
HOME="$tmp/home" PATH=/usr/bin:/bin /bin/sh -c '. "$HOME/.profile"; assis version' > "$tmp/out"
grep -Fq '3.3.0-alpha.10' "$tmp/out" || fail 'comando instalado no PATH'
HOME="$tmp/home" sh "$root/instalar.sh" > "$tmp/install"
[ "$(grep -Fc '# >>> AssisScript PATH >>>' "$tmp/home/.profile")" = 1 ] || fail 'PATH duplicado na reinstalação'
HOME="$tmp/home" sh "$root/desinstalar.sh" > "$tmp/uninstall"
[ ! -e "$tmp/home/.local/bin/assis" ] || fail 'desinstalação do binário'
if grep -Fq 'AssisScript PATH' "$tmp/home/.profile"; then fail 'desinstalação do PATH'; fi
count=$((count+3))

HOME="$tmp/home" sh "$root/instalar.sh" --prefix "$tmp/prefixo com espaço" --no-path > "$tmp/install"
expect_status 0 "$tmp/prefixo com espaço/bin/assis" version
HOME="$tmp/home" sh "$root/desinstalar.sh" --prefix "$tmp/prefixo com espaço" > "$tmp/uninstall"
[ ! -e "$tmp/prefixo com espaço/bin/assis" ] || fail 'desinstalação customizada'
count=$((count+1))

if command -v readelf >/dev/null 2>&1; then
    if readelf -l "$assis" | grep -q INTERP; then fail 'o compilador distribuído depende de loader dinâmico'; fi
    if readelf -l "$tmp/sem-dependencias" | grep -q INTERP; then fail 'o programa depende de loader dinâmico'; fi
    count=$((count+2))
fi
printf 'ASSIS: %s testes nativos aprovados, incluindo 256 operações aritméticas.\n' "$count"
