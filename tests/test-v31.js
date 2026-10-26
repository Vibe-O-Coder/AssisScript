'use strict';
const { test, after } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { spawnSync } = require('node:child_process');
const root = path.resolve(__dirname, '..');
const compiler = process.env.ASSIS_BIN || path.join(root, 'bin', process.platform === 'win32' ? 'assis.exe' : 'assis');
const temp = fs.mkdtempSync(path.join(os.tmpdir(), 'assis-v31-'));
after(() => { assert(path.dirname(temp) === path.resolve(os.tmpdir()) && path.basename(temp).startsWith('assis-v31-')); fs.rmSync(temp, { recursive: true, force: true }); });
function run(args) { const r = spawnSync(compiler, args, { encoding: 'utf8', timeout: 30000, windowsHide: true }); assert.ifError(r.error); return r; }
function source(text) { const file = path.join(temp, 'main.assis'); fs.writeFileSync(file, text); return file; }
function execute(imports, body, expected = '') {
    const file = source(imports.map(lib => `#yuri <std/${lib}.assis>`).join('\n') + `\nassis assis_assis(): int { ${body}\nreturn 0; }`);
    if (process.env.ASSIS_FIXTURE_DIR) {
        const directory = path.resolve(process.env.ASSIS_FIXTURE_DIR); fs.mkdirSync(directory, {recursive:true});
        const name = String(execute.fixture = (execute.fixture || 0) + 1).padStart(3, '0');
        fs.writeFileSync(path.join(directory, name + '.assis'), fs.readFileSync(file)); fs.writeFileSync(path.join(directory, name + '.stdout'), expected);
    }
    for (const flags of [[], ['--no-opt']]) { const r = run(['run', file, ...flags]); assert.equal(r.status, 0, r.stderr); assert.equal(r.stdout, expected); }
}
test('decimal: limites, overflow, posição e formatação int64', () => {
    const valid = ['0', '-0', '+42', '-42', '9223372036854775807', '-9223372036854775808'];
    let body = valid.map(s => `{ let r: ResultadoInt = inteiro_de_texto("${s}"); assert(r.ok); assert(r.valor == ${BigInt(s)}); let t: Texto = texto_de_inteiro(r.valor); assert(t.visualizacao() == "${BigInt(s)}"); t.dispose(); free(t); free(r); }`).join('\n');
    for (const [s, code, position] of [['', 1, 0], ['+', 2, 1], ['12x', 2, 2], [' 1', 2, 0], ['9223372036854775808', 3, 18], ['-9223372036854775809', 3, 19]]) body += `{ let r: ResultadoInt = inteiro_de_texto("${s}"); assert(!r.ok && r.codigo == ${code} && r.posicao == ${position}); free(r); }`;
    execute(['conversoes'], body);
});
test('erros recuperáveis: soma, divisão, mapas e arrays preservam saída em falha', () => {
    execute(['erros'], `let a: ResultadoInt = somar_seguro(0x7fff_ffff_ffff_ffff, 1); assert(!a.ok && a.codigo == 3); free(a);
let b: ResultadoInt = somar_seguro(-0x8000_0000_0000_0000, -1); assert(!b.ok); free(b);
let c: ResultadoInt = dividir_seguro(1, 0); assert(!c.ok && c.codigo == 4); free(c);
let d: ResultadoInt = dividir_seguro(-0x8000_0000_0000_0000, -1); assert(!d.ok); free(d);
let e: ResultadoInt = somar_seguro(-40, 82); assert(e.ok && e.valor == 42); free(e);
let arr: Array<int> = [42]; let saida: int = 77;
assert(!arr.try_get(-1, &saida) && saida == 77); assert(!arr.try_get(1, &saida)); assert(!arr.try_pop(null) && len(arr) == 1);
assert(arr.try_get(0, &saida) && saida == 42); assert(arr.try_pop(&saida)); assert(!arr.try_pop(&saida) && saida == 42); free(arr);
let mapa: HashMap<text, int> = new HashMap<text, int>(); mapa.set("ação", 19);
assert(!mapa.try_get("ausente", &saida) && saida == 42); assert(!mapa.try_get("ação", null)); assert(mapa.try_get("ação", &saida) && saida == 19); free(mapa);`);
});
test('Texto: autoacréscimo com/sem realocação, vida própria, UTF-8 e KMP', () => {
    execute(['texto'], String.raw`let t: Texto = new Texto(); assert(t.visualizacao() == "");
t.adicionar("ação"); t.adicionar(t.visualizacao()); assert(t.visualizacao() == "açãoação");
t.adicionar("123456789012345678901234567890"); let antes: int = t.tamanho(); t.adicionar(t.visualizacao()); assert(t.tamanho() == antes * 2);
let copia: Texto = recortar_texto(t.visualizacao(), 0, 6); t.dispose(); assert(copia.visualizacao() == "ação"); free(t);
let limpo: Texto = aparar_texto(" \t ação \r\n"); assert(limpo.visualizacao() == "ação");
assert(encontrar_texto("ababababac", "ababac") == 4); assert(encontrar_texto("", "") == 0); assert(encontrar_texto("aaa", "b") == -1);
assert(comeca_com("ação", "aç") && termina_com("ação", "ão")); assert(contem("abc", ""));
copia.dispose(); copia.dispose(); free(copia); limpo.dispose(); free(limpo);`);
});
test('heapsort e busca: comparação com ordenação independente em entradas adversas', () => {
    let seed = 1234567; const next = () => (seed = (Math.imul(seed, 1664525) + 1013904223) | 0);
    const cases = [[], [1], [2, 1], [3, 1, 2], Array(50).fill(7), Array.from({length: 100}, (_, i) => 99 - i), Array.from({length: 250}, next)];
    let body = '';
    for (const values of cases) {
        const sorted = [...values].sort((a, b) => a - b);
        body += `{ let a: Array<int> = [${values}]; ordenar_inteiros(a); ${sorted.map((v,i) => `assert(a[${i}] == ${v});`).join('')} assert(busca_binaria(a, 0x7fff_ffff_ffff_ffff) == -1); assert(unicos_ordenados(a) == ${new Set(values).size}); free(a); }`;
    }
    execute(['algoritmos'], body);
});
test('CSV: campos vazios, CRLF, aspas escapadas, multilinha e erros recuperáveis', () => {
    execute(['csv'], String.raw`let d: DocumentoCSV = ler_csv("nome;valor\r\n\"ação; teste\";\"12\"\r\n\"a\"\"b\";\"x\ny\"\r\n;", byte(59));
assert(d.ok && len(d.linhas) == 4); assert(d.linhas[1][0] == "ação; teste"); assert(d.linhas[2][0] == "a\"b"); assert(d.linhas[2][1] == "x\ny"); assert(len(d.linhas[3]) == 2 && d.linhas[3][1] == ""); d.dispose(); d.dispose(); free(d);
let v: DocumentoCSV = ler_csv("", byte(44)); assert(v.ok && len(v.linhas) == 0); v.dispose(); free(v);
let r: DocumentoCSV = ler_csv("\"sem fim", byte(44)); assert(!r.ok && r.posicao == 8); r.dispose(); free(r);
let s: DocumentoCSV = ler_csv("\"a\"x", byte(44)); assert(!s.ok && s.posicao == 3); s.dispose(); free(s);
let u: DocumentoCSV = ler_csv("a\rb", byte(44)); assert(!u.ok && u.posicao == 1); u.dispose(); free(u);
let z: DocumentoCSV = ler_csv("a,b", byte(0)); assert(!z.ok); z.dispose(); free(z);`);
});
test('Base64 e hexadecimal: comparação com Buffer, todos os bytes e padding inválido', () => {
    let body = '';
    for (const bytes of [[], [0], [255,0], [77,97,110], Array.from({length: 256}, (_, i) => i)]) {
        const data = Buffer.from(bytes);
        body += `{ let a: Array<byte> = [${bytes.map(b => `byte(${b})`)}]; let b: Texto = base64_codificar(a); assert(b.visualizacao() == "${data.toString('base64')}"); let c: ResultadoBytes = base64_decodificar(b.visualizacao()); assert(c.ok && len(c.dados) == len(a)); let h: Texto = hexadecimal_codificar(a); assert(h.visualizacao() == "${data.toString('hex')}"); let x: ResultadoBytes = hexadecimal_decodificar(h.visualizacao()); assert(x.ok); let i: int = 0; while(i < len(a)) { assert(a[i] == c.dados[i] && a[i] == x.dados[i]); i += 1; } free(a); b.dispose(); free(b); c.dispose(); free(c); h.dispose(); free(h); x.dispose(); free(x); }`;
    }
    for (const bad of ['A', '====', 'A===', 'AA=A', 'AB==', 'AAB=', 'AA==AAAA', 'AA A']) body += `{ let r: ResultadoBytes = base64_decodificar("${bad}"); assert(!r.ok); r.dispose(); free(r); }`;
    for (const bad of ['0', 'xz', '0x00']) body += `{ let r: ResultadoBytes = hexadecimal_decodificar("${bad}"); assert(!r.ok); r.dispose(); free(r); }`;
    execute(['codificacao'], body);
});
test('otimizador: aritmética int64 confrontada com BigInt e ordem dos efeitos', () => {
    let body = 'let zero: int = 0; assert(!(false && (1 / zero == 0))); assert(true || (1 / zero == 0));';
    let seed = 19n; const next = () => { seed = BigInt.asUintN(64, seed * 6364136223846793005n + 1442695040888963407n); return BigInt.asIntN(64, seed); };
    for (let i = 0; i < 100; i++) {
        const a = next(), b = next();
        for (const [op, expected] of [['+', a+b], ['-', a-b], ['*', a*b], ['^', a^b]]) body += `assert((${a} ${op} (${b})) == ${BigInt.asIntN(64, expected)}); { let x: int = ${a}; let y: int = ${b}; assert((x ${op} y) == ${BigInt.asIntN(64, expected)}); }`;
        body += `{ let x: int = ${a}; assert(x * 8 == ${BigInt.asIntN(64, a * 8n)}); }`;
    }
    body += 'let n: int = 0; let p: *int = &n; n += 3; *p *= 8; assert(n == 24); let b: byte = byte(255); b += 2; assert(b == 1); assert((-0x8000_0000_0000_0000 / -1) == -0x8000_0000_0000_0000);';
    execute([], body);
    const file = source('assis alterar(p: *int): int { *p = 10; return 2; } assis assis_assis(): int { let n: int = 3; n += alterar(&n); assert(n == 5); return 0; }');
    for (const flags of [[], ['--no-opt']]) assert.equal(run(['run', file, ...flags]).status, 0);
});
test('diagnósticos incluem ajuda e intervalo UTF-16; ponteiros de texto exigem tipos corretos', () => {
    const r = run(['check', source('assis assis_assis(): int { let errado: int = true; return 0; }'), '--diagnostics=json']);
    assert.equal(r.status, 1); const d = JSON.parse(r.stderr); assert.equal(d.code, 'A001'); assert(d.endColumn > d.column); assert.match(d.hint, /tipos/); assert.equal(d.severity, 'error');
    for (const expr of ['text(1)', 'bytes(12)']) assert.equal(run(['check', source(`assis assis_assis(): int { ${expr}; return 0; }`)]).status, 1);
});
test('funções com quadro grande podem chamar antes de inicializar variáveis locais', () => {
    const declarations = Array.from({length: 6000}, (_, i) => `let local_${i}: int = ${i};`).join('\n');
    execute([], `print("pilha valida"); ${declarations} assert(local_5999 == 5999);`, 'pilha valida\n');
});
test('assert aceita mensagem e só a avalia na falha', () => {
    const file = source('assis mensagem(): text { print("efeito indevido"); return "contexto"; } assis assis_assis(): int { assert(true, mensagem()); return 0; }');
    const success = run(['run', file]); assert.equal(success.status, 0, success.stderr); assert.equal(success.stdout, '');
    const r = run(['run', source('assis assis_assis(): int { assert(false, "estoque insuficiente"); return 0; }')]);
    assert.equal(r.status, 70); assert.match(r.stderr, /estoque insuficiente/); assert.match(r.stderr, /assert/);
});
test('exemplos de aplicação produzem relatório e transporte binário corretos', () => {
    const sales = run(['run', path.join(root, 'exemplos/12_relatorio_vendas.assis')]); assert.equal(sales.status, 0, sales.stderr); assert.equal(sales.stdout, 'Cafe, centavos: 5000\nCha, centavos: 1700\nMenor venda: 1250\n');
    const binary = run(['run', path.join(root, 'exemplos/13_codificacao.assis')]); assert.equal(binary.status, 0, binary.stderr); assert.equal(binary.stdout, 'Base64: AAH+/w==\nHex: 0001feff\n');
});
test('instalação: núcleo obrigatório, seleção de opcionais e remoção isolada', {skip: process.platform !== 'win32'}, () => {
    const setup = path.join(root, 'bin/assis-setup.exe');
    function setupRun(args) { const r = spawnSync(setup, args, {encoding:'utf8', timeout:20000, windowsHide:true}); assert.ifError(r.error); return r; }
    for (const [name, flags, optional] of [['minimal', ['--minimal'], []], ['selected', ['--with', 'csv,algoritmos'], ['csv','algoritmos']], ['full', [], JSON.parse(fs.readFileSync(path.join(root,'stdlib/catalogo.json'))).libraries.filter(lib=>!lib.required).map(lib=>lib.name)], ['log', ['--with','log'], ['log','cli']]]) {
        const prefix = path.join(temp, 'instalacao-' + name);
        const result = setupRun(['install', '--prefix', prefix, '--no-path', '--no-associations', ...flags]); assert.equal(result.status, 0, result.stderr);
        const catalog = JSON.parse(fs.readFileSync(path.join(prefix, 'stdlib/catalogo.json')));
        for (const lib of catalog.libraries) {
            assert.equal(fs.existsSync(path.join(prefix, 'stdlib', lib.name + '.assis')), lib.required || optional.includes(lib.name), lib.name);
            assert(fs.existsSync(path.join(prefix, 'docs', lib.doc)));
        }
        const app = source('#yuri <std/conversoes.assis>\nassis assis_assis(): int { let r: ResultadoInt = inteiro_de_texto("42"); assert(r.ok && r.valor == 42); free(r); return 0; }');
        const checked = spawnSync(path.join(prefix, 'bin/assis.exe'), ['run', app], {encoding:'utf8', timeout:20000, windowsHide:true}); assert.ifError(checked.error); assert.equal(checked.status, 0, checked.stderr);
        fs.writeFileSync(path.join(prefix, 'pessoal.txt'), 'preservar');
        assert.equal(setupRun(['uninstall', '--prefix', prefix, '--no-path', '--no-associations']).status, 0);
        assert(fs.existsSync(path.join(prefix, 'pessoal.txt'))); assert(!fs.existsSync(path.join(prefix, 'stdlib')));
    }
    const invalid = path.join(temp, 'instalacao-invalida'); assert.notEqual(setupRun(['install', '--prefix', invalid, '--no-path', '--no-associations', '--with', 'nao-existe']).status, 0); assert(!fs.existsSync(invalid));
});
test('catálogo: cada biblioteca e documento existe e a análise de tipos passa', () => {
    const catalog = JSON.parse(fs.readFileSync(path.join(root, 'stdlib/catalogo.json')));
    assert.equal(catalog.libraries.filter(lib => lib.required).length, 5);
    for (const lib of catalog.libraries) { assert(fs.existsSync(path.join(root, 'docs', lib.doc))); const r = run(['check', path.join(root, 'stdlib', lib.name + '.assis'), '--library']); assert.equal(r.status, 0, r.stderr); }
});
