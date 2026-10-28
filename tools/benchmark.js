'use strict';
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const { spawnSync } = require('node:child_process');
const root = path.resolve(__dirname, '..');
let samples = 7, baseline;
for (let i = 2; i < process.argv.length; i++) {
    if (process.argv[i] === '--samples') samples = Number(process.argv[++i]);
    else if (process.argv[i] === '--baseline') baseline = path.resolve(process.argv[++i]);
    else throw new Error('Opção desconhecida: ' + process.argv[i]);
}
if (!Number.isInteger(samples) || samples < 3 || samples > 100) throw new Error('--samples deve estar entre 3 e 100');
const compiler = process.env.ASSIS_BIN || path.join(root, 'bin', process.platform === 'win32' ? 'assis.exe' : 'assis');
const directory = fs.mkdtempSync(path.join(os.tmpdir(), 'assis-bench-'));
const output = path.join(root, 'benchmarks/resultados'); fs.mkdirSync(output, { recursive: true });
const version = require('../vscode-assisscript/package.json').version;
const variants = [{ name: `${version} otimizado`, compiler, flags: [] }, { name: `${version} sem otimização`, compiler, flags: ['--no-opt'] }];
if (baseline) variants.unshift({ name: 'anterior', compiler: baseline, flags: [], legacy: true });
function invoke(bin, args = []) {
    const begin = process.hrtime.bigint();
    const result = spawnSync(bin, args, { encoding: 'utf8', timeout: 60000, windowsHide: true });
    if (result.error || result.status !== 0) throw new Error(`${bin}: ${result.error || result.stderr || result.status}`);
    return { ms: Number(process.hrtime.bigint() - begin) / 1e6, stdout: result.stdout };
}
function stats(values) { const sorted = [...values].sort((a,b) => a-b); const mid = Math.floor(sorted.length / 2); return { medianMs: sorted.length % 2 ? sorted[mid] : (sorted[mid-1]+sorted[mid])/2, minMs: sorted[0], maxMs: sorted.at(-1), samplesMs: values }; }
const report = { generatedAt: new Date().toISOString(), platform: `${os.platform()} ${os.release()} ${os.arch()}`, cpu: os.cpus()[0].model, node: process.version, samples, warmups: 1, includesProcessStartup: true, variants: variants.map(v => ({ name: v.name, version: invoke(v.compiler, ['version']).stdout.trim() })), results: [] };
const cases = [
    { name: 'aritmetica', expected: '25750000000\n' },
    { name: 'hashmap', expected: '199998000000\n' },
    { name: 'array', expected: '499999500000\n' },
    { name: 'strings-prefixo', expected: '80\n' }
];
function textKernel(legacy) {
    // Frozen copies isolate the old checked indexing and new bounded byte loop.
    const declaration = legacy ? '' : 'let a: *byte = bytes(strings); let b: *byte = bytes(prefixo);';
    const compare = legacy ? 'strings[i] != prefixo[i]' : 'a[i] != b[i]';
    const value = 'a'.repeat(2000);
    return `fn prefixo(strings: text, prefixo: text): bool { let n: int = len(prefixo); if (n > len(strings)) { return false; } ${declaration} let i: int = 0; while(i < n) { if (${compare}) { return false; } i += 1; } return true; }
fn main(): int { let strings: text = "${value}"; let i: int = 0; let total: int = 0; while (i < 80) { if (prefixo(strings, strings)) { total += 1; } i += 1; } print(total); return 0; }`;
}
try {
    for (const entry of cases) for (const variant of variants) {
        const source = path.join(directory, entry.name + '.assis');
        fs.writeFileSync(source, entry.name === 'strings-prefixo' ? textKernel(variant.legacy) : fs.readFileSync(path.join(root, 'benchmarks', entry.name + '.assis')));
        let binary;
        const compileTimes = [];
        for (let i = 0; i < 3; i++) {
            binary = path.join(directory, `${entry.name}-${variants.indexOf(variant)}-${i}` + (process.platform === 'win32' ? '.exe' : ''));
            compileTimes.push(invoke(variant.compiler, ['build', source, '-o', binary, ...variant.flags]).ms);
        }
        const measure = () => { const r = invoke(binary); if (r.stdout !== entry.expected) throw new Error(`${entry.name}: resultado incorreto: ${r.stdout}`); return r.ms; };
        measure(); const times = Array.from({length: samples}, measure);
        const result = { case: entry.name, variant: variant.name, binaryBytes: fs.statSync(binary).size, compile: stats(compileTimes), execution: stats(times) };
        report.results.push(result); console.log(`${entry.name} | ${variant.name} | ${result.execution.medianMs.toFixed(2)} ms | ${result.binaryBytes} bytes`);
    }
    fs.writeFileSync(path.join(output, 'benchmark.json'), JSON.stringify(report, null, 2) + '\n');
    let markdown = `# Medições do AssisScript ${version}\n\nExecução: ${report.generatedAt}. ${report.platform}; ${report.cpu}; Node ${report.node}.\n\n${samples} amostras após 1 aquecimento; mediana, incluindo início do processo. Compilação medida em três amostras separadas. Cada saída foi validada.\n\n| Programa | Variante | Execução mediana (ms) | Mín–máx (ms) | Compilação mediana (ms) | Bytes |\n| --- | --- | ---: | ---: | ---: | ---: |\n`;
    for (const r of report.results) markdown += `| ${r.case} | ${r.variant} | ${r.execution.medianMs.toFixed(2)} | ${r.execution.minMs.toFixed(2)}–${r.execution.maxMs.toFixed(2)} | ${r.compile.medianMs.toFixed(2)} | ${r.binaryBytes} |\n`;
    markdown += '\nO caso strings-prefixo compara o laço da biblioteca anterior (indexação verificada) ao laço da biblioteca nova (bytes limitados por comprimento). As outras cargas usam o mesmo fonte em todas as variantes. Diferenças próximas ao custo de iniciar um processo não são conclusivas. Não há comparação com outras linguagens. Dados brutos: [benchmark.json](benchmark.json).\n';
    fs.writeFileSync(path.join(output, 'RELATORIO.md'), markdown);
    fs.writeFileSync(path.join(root, 'docs/RESULTADOS-DESEMPENHO.md'), markdown.replace('(benchmark.json)', '(DESEMPENHO.json)'));
    fs.writeFileSync(path.join(root, 'docs/DESEMPENHO.json'), JSON.stringify(report, null, 2) + '\n');
} finally { assertTemporary(); fs.rmSync(directory, {recursive: true, force: true, maxRetries: 10, retryDelay: 100}); }
function assertTemporary() { if (path.dirname(directory) !== path.resolve(os.tmpdir()) || !path.basename(directory).startsWith('assis-bench-')) throw new Error('Pasta temporária inesperada'); }
