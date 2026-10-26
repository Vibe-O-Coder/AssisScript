'use strict';
const { test, after } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { spawnSync } = require('node:child_process');
const root = path.resolve(__dirname, '..');
const compiler = process.env.ASSIS_BIN || path.join(root, 'bin', process.platform === 'win32' ? 'assis.exe' : 'assis');
const temp = fs.mkdtempSync(path.join(os.tmpdir(), 'assis-v3-'));
after(() => { assert(path.dirname(temp) === path.resolve(os.tmpdir()) && path.basename(temp).startsWith('assis-v3-')); fs.rmSync(temp, { recursive: true, force: true }); });
function write(name, source) { const file = path.join(temp, name); fs.mkdirSync(path.dirname(file), { recursive: true }); fs.writeFileSync(file, source); return file; }
function run(args, options = {}) { const r = spawnSync(compiler, args, { encoding: 'utf8', timeout: 20000, windowsHide: true, ...options }); assert.ifError(r.error); return r; }
function execute(source, expected) { const r = run(['run', write('main.assis', source)]); assert.equal(r.status, 0, r.stderr); if (expected !== undefined) assert.equal(r.stdout, expected); }
function reject(source, message) { const r = run(['check', write('invalid.assis', source), '--diagnostics=json']); assert.equal(r.status, 1, r.stderr); assert.match(JSON.parse(r.stderr).message, message); }
const main = body => `assis assis_assis(): int { ${body} return 0; }`;

test('nomes livres, palavras legíveis e métodos preservam herança virtual', () => {
    execute(`ASSIS Pessoa { let idade: int; assis assis_fodase(valor: int): void { self.idade = valor; } assis ler(): int { return self.idade; } }
ASSIS Especial extends Pessoa { assis ler(): int { return self.idade * 2; } }
${main('let pessoa_42: Pessoa = new Especial(21); print(pessoa_42.ler()); free(pessoa_42);')}`, '42\n');
});
test('array cresce, insere, remove, inverte e preserva tipo e tamanho', () => {
    execute(main(`let a: Array<int> = []; let i: int = 0;
while (i < 1000) { a.push(i); i += 1; }
a.insert(0, -1); a.insert(len(a), 1000); assert(a.remove(0) == -1); assert(a.pop() == 1000);
a[2] *= 3; a.set(3, 90); a.reverse(); assert(a.get(996) == 90); assert(a[997] == 6);
assert(a.contains(90)); assert(!a.contains(-100)); print(len(a), a[0], a[999]);
a.clear(); assert(len(a) == 0); a.reserve(2000); a.push(42); a.dispose(); a.dispose(); a.push(7); print(a[0]); free(a);`), '1000 999 0\n7\n');
});
test('literais e argumentos aninhados, ponteiros, byte, bool e text', () => {
    execute(`assis soma(a: Array<int>): int { let v: int = a[0] + a[1]; free(a); return v; }
assis criar(): Array<int> { return [8, 9]; }
${main(`let m: Array<Array<int>> = [[1, 2], [], [3]]; m[1].push(4); assert(m[1][0] == 4);
let b: Array<byte> = [byte(255)]; b[0] += 2; assert(b[0] == byte(1));
let flags: Array<bool> = [true, false]; flags[1] = true; assert(flags[0] && flags[1]);
let texts: Array<text> = ["ação", ""]; assert(texts.contains("ação"));
let x: int = 5; let pointers: Array<*int> = [&x]; *pointers[0] += 2;
let returned: Array<int> = criar(); print(soma([20, 22]), returned.pop(), x);
free(returned); free(pointers); free(texts); free(flags); free(b); free(m[0]); free(m[1]); free(m[2]); free(m);`)}`, '42 9 7\n');
});
test('hashmap trata colisões, tombstones, crescimento, substituição e chave mínima', () => {
    execute(main(`let map: HashMap<int, int> = new HashMap<int, int>(); let i: int = 0;
while (i < 1500) { map.set(i * 64, i); i += 1; }
i = 0; while (i < 1500) { assert(map.get(i * 64) == i); if (i % 2 == 0) { assert(map.remove(i * 64)); } i += 1; }
assert(len(map) == 750); i = 0; while (i < 1500) { map.set(i * 64, i + 1); i += 1; }
assert(len(map) == 1500); map.set(-1, 7); map.set(-0x8000000000000000, 8); assert(map.get(0) == 1);
print(map.get(-1), map.get(-0x8000000000000000), len(map)); assert(!map.remove(-999));
map.clear(); assert(len(map) == 0); assert(!map.has(0)); map.set(0, 42); assert(map.get(0) == 42); map.dispose(); map.set(1, 2); free(map);`), '7 8 1502\n');
});
test('hashmap UTF-8, string vazia, chaves e valores são arrays independentes', () => {
    execute(main(`let map: HashMap<text, text> = new HashMap<text, text>(); map.set("ação", "certo"); map.set("", "vazio");
assert(map.has("ação")); assert(map.get_or("ausente", "fallback") == "fallback"); map.set("ação", "novo");
let keys: Array<text> = map.keys(); let values: Array<text> = map.values(); let i: int = 0;
while (i < len(keys)) { assert(map.get(keys[i]) == values[i]); i += 1; }
assert(keys.contains("")); assert(values.contains("novo")); assert(len(map) == 2); free(map); print(len(keys), len(values)); free(keys); free(values);`), '2 2\n');
});
test('hashmap bool/byte e coleções como valores', () => {
    execute(main(`let map: HashMap<bool, byte> = new HashMap<bool, byte>(); map.set(true, byte(255)); map.set(false, byte(3)); assert(map.get(true) == 255);
let nested: Array<HashMap<text, Array<int>>> = []; let entries: HashMap<text, Array<int>> = new HashMap<text, Array<int>>();
entries.set("teste", [42]); nested.push(entries); assert(nested[0].get("teste")[0] == 42);
free(entries.get("teste")); free(entries); free(nested); free(map);`));
});
test('struct possui tipo nominal, construtor de campos e referências compartilhadas', () => {
    execute(`struct Pessoa { let nome: text; let idade: int; let flags: Array<bool>; }
${main(`let p: Pessoa = new Pessoa(); assert(p.nome == ""); assert(p.idade == 0); assert(p.flags == null); free(p);
let q: Pessoa = new Pessoa("Miyabi", 24, [true]); let alias: Pessoa = q; alias.idade += 1; print(q.nome, q.idade); free(q.flags); free(q);`)}`, 'Miyabi 25\n');
    reject('struct A { let x: int; } struct B { let x: int; } ' + main('let a: A = new B(1);'), /não é possível/);
    reject('struct A { let x: int; } ' + main('let a: A = new A(true);'), /não é possível/);
    reject('struct A extends B {}', /não admite herança/);
    reject('struct A { assis metodo(): void {} }', /somente campos/);
    reject('struct A {} ASSIS B extends A {}', /não pode ser classe base/);
});
test('erros de tipos e especializações são rejeitados antes de gerar binário', () => {
    const cases = [
        ['let a: Array<int> = [true];', /não é possível/],
        ['let a: Array<int> = []; a.push("texto");', /não é possível/],
        ['let a: Array<void> = [];', /não aceitam void/],
        ['let a: HashMap<Array<int>, int> = null;', /chave de HashMap/],
        ['let a: Array<TipoAusente> = null;', /tipo desconhecido/],
        ['let a: Array<int> = []; let b: Array<byte> = a;', /não é possível/],
        ['let m: HashMap<text, int> = new HashMap<text, int>(); m.set(1, 42);', /não é possível/],
        ['let a: Array<int> = new Array<int>(1);', /inicializador/],
        ['print([1, 2]);', /contexto Array/],
        ['let __assis_reservado: int = 0;', /reservado/],
        ['let buffer: *void = alloc<void>(1);', /só pode ser retorno/]
    ];
    for (const [body, message] of cases) reject(main(body), message);
});
test('falhas de execução têm status 70: limites, mapa ausente, pop e overflow', () => {
    for (const body of [
        'let a: Array<int> = [1]; print(a[-1]);',
        'let a: Array<int> = [1]; a[1] = 2;',
        'let a: Array<int> = [1]; a[1] += 2;',
        'let a: Array<int> = []; a.pop();',
        'let a: Array<int> = []; a.insert(-1, 3);',
        'let a: Array<int> = []; a.reserve(-1);',
        'let m: HashMap<text, int> = new HashMap<text, int>(); m.get("ausente");',
        'let p: *int = alloc<int>(-1);',
        'let p: *int = alloc<int>(0x2000000000000000);',
        'assert(false);'
    ]) {
        const r = run(['run', write('runtime.assis', main(body))]); assert.equal(r.status, 70, r.stderr); assert.match(r.stderr, /FODASE R001/);
    }
});
test('ordem de avaliação em indexação composta e argumentos de coleção', () => {
    execute(`ASSIS Contador { let n: int; assis tick(): int { self.n += 1; return self.n - 1; } }
${main(`let c: Contador = new Contador(); let a: Array<int> = [10, 20]; a[c.tick()] += c.tick(); assert(c.n == 2); assert(a[0] == 11); free(a); free(c);`)}`);
});
test('#yuri e #body resolvem fontes transitivos e pacotes pontuados', () => {
    write('pkg/lib/calculos.assis', '/// Retorna o dobro.\nassis dobro(valor: int): int { return valor * 2; }');
    write('pkg/meu/pacote.pillow', '#yuri <../lib/calculos.assis>\n');
    write('pkg/src.pillow', '#body meu.pacote.pillow\n#yuri <lib/calculos.assis>\n');
    const file = write('pkg/main.assis', '#body src.pillow\n#yuri <lib/calculos.assis>\n' + main('print(dobro(21));'));
    const r = run(['run', file], { cwd: os.tmpdir() }); assert.equal(r.status, 0, r.stderr); assert.equal(r.stdout, '42\n');
    assert.equal(run(['check', path.join(temp, 'pkg/src.pillow'), '--library']).status, 0);
    const original = fs.readFileSync(path.join(temp, 'pkg/src.pillow'));
    const protectedOutput = run(['build', file, '-o', path.join(temp, 'pkg/src.pillow')]); assert.equal(protectedOutput.status, 2); assert.deepEqual(fs.readFileSync(path.join(temp, 'pkg/src.pillow')), original);
});
test('diretivas malformadas, pacotes com código e ciclos são diagnosticados', () => {
    for (const [source, message] of [
        ['#yuri <std/texto>', /extensão .assis/], ['#yuri "std/texto.assis"', /exige </],
        ['#yuri <std/texto.assis', /fechamento/], ['#body src.txt', /extensão .pillow/],
        ['#body', /extensão .pillow/], ['#outra', /desconhecida/],
        ['#yuri <std/texto.assis> assis f(): int { return 0; }', /linha própria/]
    ]) reject(source, message);
    const code = write('bad.pillow', 'assis algo(): int { return 0; }'); const bad = run(['check', code, '--library']); assert.equal(bad.status, 1); assert.match(bad.stderr, /somente #yuri e #body/);
    const a = write('a.pillow', '#body b.pillow\n'); write('b.pillow', '#body a.pillow\n');
    const r = run(['check', a, '--library']); assert.equal(r.status, 1); assert.match(r.stderr, /ciclo de importação/);
});
test('bibliotecas legíveis e projeto novo são executáveis sem ferramentas externas', () => {
    execute('#yuri <std/matematica.assis>\n#yuri <std/texto.assis>\n#yuri <std/memoria.assis>\n' + main(`assert(minimo(2, 3) == 2); assert(maximo(2, 3) == 3); assert(limitar(99, 0, 10) == 10); assert(absoluto(-42) == 42);
assert(comeca_com("ação", "aç")); assert(termina_com("ação", "ão")); assert(contem("ação", "çã")); assert(!contem("ação", "xyz"));
let a: *byte = alloc<byte>(4); let b: *byte = alloc<byte>(4); preencher(a, 4, byte(255)); copiar(b, a, 4); assert(b[3] == 255); free(a); free(b);`));
    const folder = path.join(temp, 'novo-projeto'); assert.equal(run(['new', folder]).status, 0);
    const r = run(['run'], { cwd: folder, env: { ...process.env, PATH: '' } }); assert.equal(r.status, 0, r.stderr); assert.equal(r.stdout, 'Assis, mundo. Fodase. 42\n');
    assert(fs.existsSync(path.join(folder, 'src.pillow')));
});
test('PE contém grupo de ícone e imagens válidas da segunda imagem', () => {
    const input = write('icone.assis', main('print(42);')), output = path.join(temp, 'icone.exe');
    assert.equal(run(['build', input, '--target', 'windows-x64', '-o', output]).status, 0);
    const pe = fs.readFileSync(output), offset = pe.readUInt32LE(0x3c), optional = offset + 24;
    const rva = pe.readUInt32LE(optional + 112 + 2*8), size = pe.readUInt32LE(optional + 116 + 2*8); assert(size > 1000);
    const sections = optional + pe.readUInt16LE(offset + 20); let resource;
    for (let i = 0; i < pe.readUInt16LE(offset + 6); i++) { const s = sections + i*40; if (pe.toString('ascii', s, s+5) === '.rsrc') resource = pe.readUInt32LE(s+20) + rva - pe.readUInt32LE(s+12); }
    assert(resource); assert.equal(pe.readUInt16LE(resource+14), 2);
    const original = fs.readFileSync(path.join(root, 'assets/compiled.ico')), count = original.readUInt16LE(4);
    for (let i = 0; i < count; i++) { const e = 6+i*16, payload = original.subarray(original.readUInt32LE(e+12), original.readUInt32LE(e+12)+original.readUInt32LE(e+8)); assert(pe.includes(payload)); }
    assert.equal(pe.readUInt32LE(resource+16), 3); assert.equal(pe.readUInt32LE(resource+24), 14);
});
