#!/bin/sh
set -eu
root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
assis=${ASSIS_BIN:-"$root/bin/assis"}
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT HUP INT TERM
count=0
expect() {
    wanted=$1; shift
    set +e
    "$@" > "$tmp/out" 2> "$tmp/err"
    actual=$?
    set -e
    [ "$actual" = "$wanted" ] || { cat "$tmp/err" >&2; echo "Status $actual, esperado $wanted: $*" >&2; exit 1; }
    count=$((count+1))
}
expect 0 "$assis" check --legacy "$root/stdlib/math.assis" --library
printf 'import "b";\n' > "$tmp/a.assis"
printf 'import "a";\n' > "$tmp/b.assis"
expect 1 "$assis" check --legacy "$tmp/a.assis" --diagnostics=json
grep -Fq 'ciclo de importação' "$tmp/err"
printf 'fn AssisAssis(): int { return 21; }\n' > "$tmp/lib.assis"
printf 'import "lib"; fn main(): int { return AssisAssis(); }\n' > "$tmp/main.assis"
expect 0 "$assis" build --legacy "$tmp/main.assis" -o "$tmp/programa"
expect 21 "$tmp/programa"
cp "$tmp/programa" "$tmp/original"
printf 'fn AssisAssis(): int { return true; }\n' > "$tmp/lib.assis"
expect 1 "$assis" build --legacy "$tmp/main.assis" -o "$tmp/programa" --diagnostics=json
cmp "$tmp/programa" "$tmp/original"
grep -Fq "$tmp/lib.assis" "$tmp/err"
printf 'fn AssisAssis(): int {\n return 1 / 0;\n}\n' > "$tmp/lib.assis"
expect 70 "$assis" run --legacy "$tmp/main.assis"
grep -Fq "$tmp/lib.assis:2: divisão por zero" "$tmp/err"
printf 'fn AssisAssis(): int { return 42; }\n' > "$tmp/snapshot.assis"
expect 0 "$assis" check --legacy "$tmp/main.assis" --overlay "$tmp/lib.assis" "$tmp/snapshot.assis"
printf 'fn main(): int { return true; }\n' > "$tmp/stdin.assis"
expect 1 "$assis" check --legacy "$tmp/main.assis" --stdin --diagnostics=json < "$tmp/stdin.assis"
expect 0 "$assis" run --legacy "$root/exemplos/08_modulos.assis"
mkdir "$tmp/install"
HOME="$tmp/install" sh "$root/instalar.sh" > "$tmp/install-out"
expect 0 "$tmp/install/.local/bin/assis" run --legacy "$tmp/install/.local/share/assisscript/exemplos/08_modulos.assis"
expect 0 "$tmp/install/.local/bin/assis" run "$tmp/install/.local/share/assisscript/exemplos/20_valores_e_resultados.assis" --safe --debug
expect 0 "$tmp/install/.local/bin/assis" run "$tmp/install/.local/share/assisscript/exemplos/25_recursos_e_unicode.assis" --safe --debug
cmp "$root/docs/PROGRESSO.json" "$tmp/install/.local/share/assisscript/docs/PROGRESSO.json"
printf '%s\n' pessoal > "$tmp/install/.local/share/assisscript/docs/pessoal.txt"
HOME="$tmp/install" sh "$root/desinstalar.sh" > "$tmp/remove-out"
[ -f "$tmp/install/.local/share/assisscript/docs/pessoal.txt" ]
for marker in 'AssisScript 2.2.0' 'AssisScript 3.2.0' 'AssisScript 3.3.0-alpha.1' 'AssisScript 3.3.0-alpha.2' 'AssisScript 3.3.0-alpha.3' 'AssisScript 3.3.0-alpha.4' 'AssisScript 3.3.0-alpha.5' 'AssisScript 3.3.0-alpha.6' 'AssisScript 3.3.0-alpha.7' 'AssisScript 3.3.0-alpha.8' 'AssisScript 3.3.0-alpha.9' 'AssisScript 3.3.0-alpha.10' 'AssisScript 3.3.0-alpha.11' 'AssisScript 3.3.0-alpha.12' 'AssisScript 3.3.0-alpha.13'; do
    prefix="$tmp/marker"
    mkdir -p "$prefix/bin" "$prefix/share/assisscript"
    printf '%s\n' "$marker" > "$prefix/share/assisscript/INSTALADO"
    touch "$prefix/bin/assis" "$prefix/pessoal.txt"
    expect 0 sh "$root/desinstalar.sh" --prefix "$prefix"
    [ -f "$prefix/pessoal.txt" ] && [ ! -f "$prefix/bin/assis" ]
done
mkdir -p "$tmp/marker/bin" "$tmp/marker/share/assisscript"
printf '%s\n' 'OutroProjeto 3.3.0' > "$tmp/marker/share/assisscript/INSTALADO"
touch "$tmp/marker/bin/assis"
expect 1 sh "$root/desinstalar.sh" --prefix "$tmp/marker"
[ -f "$tmp/marker/bin/assis" ]
echo "ASSIS: $count testes adicionais de módulos aprovados em Linux."
