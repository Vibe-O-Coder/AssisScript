'use strict';
const { test, after } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { spawnSync } = require('node:child_process');
const root = path.resolve(__dirname, '..');
const compiler = process.env.ASSIS_BIN || path.join(root, 'bin', process.platform === 'win32' ? 'assis.exe' : 'assis');
const temp = fs.mkdtempSync(path.join(os.tmpdir(), 'assis-desenvolvimento-ação-'));
after(() => fs.rmSync(temp, { recursive: true, force: true }));
function write(name, text) { const file = path.join(temp, name); fs.mkdirSync(path.dirname(file), { recursive: true }); fs.writeFileSync(file, text); return file; }
function run(args, options = {}) { if (["build","run","check","doc","test","lock","ir"].includes(args[0]) && !args.includes("--safe") && !args.includes("--legacy")) args = [...args, "--legacy"]; const r = spawnSync(compiler, args, { encoding: 'utf8', timeout: 15000, windowsHide: true, ...options }); assert.ifError(r.error); return r; }
function rejection(args, message, options) { const r = run([...args, '--diagnostics=json'], options); assert.equal(r.status, 1, r.stderr); const d = JSON.parse(r.stderr); assert.match(d.message, message); return d; }
test('compilação estática: build não executa e binário roda sozinho', () => {
    const source = write('estatico.assis', 'fn main(): int { print("PROGRAMA EXECUTADO"); return 7; }');
    const binary = path.join(temp, process.platform === 'win32' ? 'estatico.exe' : 'estatico');
    const r = run(['build', source, '-o', binary]); assert.equal(r.status, 0, r.stderr); assert.doesNotMatch(r.stdout, /PROGRAMA EXECUTADO/);
    const executable = spawnSync(binary, [], { encoding: 'utf8', env: { ...process.env, PATH: 'C:\\sem-ferramentas' } });
    assert.equal(executable.status, 7); assert.equal(executable.stdout, 'PROGRAMA EXECUTADO\n');
    fs.writeFileSync(source, 'fn main(): int { return true; }'); const original = fs.readFileSync(binary);
    rejection(['build', source, '-o', binary], /não é possível/); assert.deepEqual(fs.readFileSync(binary), original);
    const absent = path.join(temp, 'invalido'); rejection(['build', source, '-o', absent], /não é possível/); assert(!fs.existsSync(absent) && !fs.existsSync(absent + '.exe'));
});
test('comentários, delimitadores, strings, BOM e CRLF', () => {
    const source = write('comentarios.assis', '\ufeff// palavras livres\r\n/* externo /* interno */ */\r\nfn main():int { print("miyabi te to"); return 0; }');
    const r = run(['run', source]); assert.equal(r.status,0,r.stderr);assert.equal(r.stdout,'miyabi te to\n');
    rejection(['check',write('comentario-error.assis','/* sem fim')], /sem fechamento/);
});
test('módulos: importação transitiva, repetida e herança entre arquivos', () => {
    write('modulos/base.assis', 'class AssisAssis { fn AssisFodase(): int { return 21; } }');
    write('modulos/derivada.assis', 'import "base"; class AssisFodase extends AssisAssis { fn AssisFodase(): int { return 42; } }');
    const source = write('modulos/principal.assis', 'import "base.assis"; import "derivada.assis"; import "./base.assis"; fn main(): int { let FodaseAssis: AssisAssis = new AssisFodase(); print(FodaseAssis.AssisFodase()); free(FodaseAssis); return 0; }');
    const r = run(['run', source], { cwd: os.tmpdir() }); assert.equal(r.status, 0, r.stderr); assert.equal(r.stdout, '42\n');
    assert.equal(run(['check', path.join(temp, 'modulos/base.assis'), '--library']).status, 0);
    rejection(['build', path.join(temp, 'modulos/base.assis'), '-o', path.join(temp, 'sem-entrada')], /falta a entrada/);
});
test('errors de importação: ciclos, ausência, colisões e fronteiras de arquivo', () => {
    const a = write('ciclo/a.assis', 'import "b";'); write('ciclo/b.assis', 'import "a";');
    const cycle = rejection(['check', a], /ciclo de importação/); assert(cycle.file.endsWith('b.assis'));
    rejection(['check', write('ausente.assis', 'import "nao-existe";')], /módulo não encontrado/);
    rejection(['check', write('sem-codepoint.assis', 'import "std/strings"')], /esperado ;/);
    rejection(['check', write('caminho-nulo.assis', 'import "abc\\0";')], /byte nulo/);
    write('incompleto.assis', 'fn AssisAssis(): int { return 1;');
    const d = rejection(['check', write('fronteira.assis', 'import "incompleto"; }')], /esperad/); assert(d.file.endsWith('incompleto.assis'));
    write('duplicado-a.assis', 'fn AssisAssis(): int { return 1; }');
    write('duplicado-b.assis', 'fn AssisAssis(): int { return 2; }');
    rejection(['check', write('duplicado.assis', 'import "duplicado-a"; import "duplicado-b"; fn main(): int { return 0; }')], /função declarada duas vezes/);
});
test('diagnóstico do módulo aponta arquivo e linha corretos', () => {
    const lib = write('error-biblioteca.assis', '// biblioteca\nfn AssisAssis(): int {\n    return true;\n}');
    const d = rejection(['check', write('error-principal.assis', 'import "error-biblioteca"; fn main(): int { return 0; }')], /não é possível/);
    assert.equal(d.file, lib); assert.equal(d.line, 3); assert.equal(d.column, 5); assert.equal(d.code, 'A001');
});
test('stdin, overlays e colunas UTF-16 usam posições do editor', () => {
    const source = write('editor.assis', 'fn main(): int { return 0; }');
    const text = 'fn main(): int { print("😀 ação"); return true; }';
    const d = rejection(['check', source, '--stdin'], /não é possível/, { input: text }); assert.equal(d.column, text.indexOf('return true') + 1);
    assert.equal(fs.readFileSync(source, 'utf8'), 'fn main(): int { return 0; }');
    const dep = write('overlay-dep.assis', 'fn AssisAssis(): int { return 21; }');
    const snapshot = write('snapshot.assis', 'fn AssisAssis(): text { return "errado"; }');
    const main = write('overlay-main.assis', 'import "overlay-dep"; fn main(): int { return AssisAssis(); }');
    assert.equal(run(['check', main]).status, 0); rejection(['check', main, '--overlay', dep, snapshot], /não é possível/);
});
test('diretórios de bibliotecas via -I e ASSIS_PATH', () => {
    write('externa/pacote.assis', 'fn AssisAssis(): int { return 42; }');
    const source = write('projeto/main.assis', 'import "pacote"; fn main(): int { print(AssisAssis()); return 0; }');
    for (const r of [run(['run', source, '-I', path.join(temp, 'externa')]), run(['run', source], { env: { ...process.env, ASSIS_PATH: path.join(temp, 'externa') } })]) { assert.equal(r.status, 0, r.stderr); assert.equal(r.stdout, '42\n'); }
});
test('fontes importados e extensão exe final são protegidos contra sobrescrita', () => {
    const name = process.platform === 'win32' ? 'biblioteca.exe' : 'biblioteca';
    const lib = write(name, 'fn AssisAssis(): int { return 1; }'), original = fs.readFileSync(lib);
    const main = write('protege.assis', `import "${name}"; fn main(): int { return 0; }`);
    const output = process.platform === 'win32' ? lib.slice(0, -4) : lib;
    const r = run(['build', main, '-o', output]); assert.equal(r.status, 2, r.stderr); assert.deepEqual(fs.readFileSync(lib), original);
});
test('bibliotecas padrão: matemática, texto UTF-8 e memória', () => {
    const source = write('padrao.assis', `import "std/math"; import "std/strings"; import "std/memory";
fn main(): int {
    print(Assis_assis_fodase(-5, 2), Assis_fodase_assis(-5, 2), Assis_fodase_fodase(99, 0, 10), Assis_assis_assis(-42));
    print(Fodase_assis_fodase("ação", "aç"), Fodase_fodase_assis("ação", "ão"), Fodase_assis_fodase("a", "ab"), Fodase_fodase_assis("", ""));
    let AssisAssis: *byte = alloc<byte>(3); let AssisFodase: *byte = alloc<byte>(3);
    Assis_Assis_Fodase(AssisAssis, 3, byte(255)); Assis_Fodase_Assis(AssisFodase, AssisAssis, 3);
    print(AssisFodase[0], AssisFodase[2]); free(AssisAssis); free(AssisFodase); return 0;
}`);
    const r = run(['run', source]); assert.equal(r.status, 0, r.stderr); assert.equal(r.stdout, '-5 2 10 42\ntrue true false true\n255 255\n');
});
test('falhas de runtime em bibliotecas incluem arquivo e linha', () => {
    const lib = write('runtime-lib.assis', 'fn AssisAssis(): int {\n return 1 / 0;\n}');
    const main = write('runtime-main.assis', 'import "runtime-lib"; fn main(): int { return AssisAssis(); }');
    const r = run(['run', main]); assert.equal(r.status, 70, r.stderr); assert(r.stderr.includes(lib + ':2: divisão por zero'), r.stderr);
    fs.writeFileSync(lib, 'fn AssisAssis(): int {\n let AssisFodase: text = "abc"; return AssisFodase[8];\n}');
    const index = run(['run', main]); assert.equal(index.status, 70, index.stderr); assert(index.stderr.includes(lib + ':2: índice de texto'), index.stderr);
    fs.writeFileSync(lib, 'fn AssisAssis(): int {\n let AssisFodase: *byte = alloc<byte>(-1); return 0;\n}');
    const alloc = run(['run', main]); assert.equal(alloc.status, 70, alloc.stderr); assert(alloc.stderr.includes(lib + ':2: tamanho de alocação'), alloc.stderr);
});
