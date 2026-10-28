'use strict';
const { test, after } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const vm = require('node:vm');
const { EventEmitter } = require('node:events');
const language = require('../src/language');
const extensionPath = path.resolve(__dirname, '..');
const temp = fs.mkdtempSync(path.join(os.tmpdir(), 'assis-extension-'));
after(() => { assert(path.dirname(temp) === path.resolve(os.tmpdir()) && path.basename(temp).startsWith('assis-extension-')); fs.rmSync(temp, { recursive: true, force: true }); });
const disposable = () => ({ dispose() {} });
function uri(file) { return { scheme: 'file', fsPath: file, toString() { return 'file:///' + file; } }; }
function doc(file, text, languageId = 'assisscript', isDirty = false) {
    return { uri: uri(file), languageId, isDirty, isClosed: false, getText: range => range ? text.slice(range.start, range.end) : text,
        offsetAt: value => value, positionAt: value => value,
        getWordRangeAtPosition(offset) { let start = offset, end = offset; while (start && /\w/.test(text[start - 1])) start--; while (/\w/.test(text[end] || '')) end++; return { start, end }; } };
}
function harness(documents, settings = {}) {
    const commands = new Map(), providers = {}, diagnostics = new Map(), calls = [], events = {};
    const watch = { ...disposable(), onDidChange: disposable, onDidCreate: disposable, onDidDelete: disposable };
    const workspace = {
        textDocuments: documents, isTrusted: true, workspaceFolders: [], getWorkspaceFolder: () => ({ uri: uri(temp) }),
        getConfiguration: () => ({ get(name, fallback) { return ({ validationDelay: 100000, ...settings })[name] ?? fallback; } }),
        createFileSystemWatcher: () => watch,
        onDidOpenTextDocument: callback => { events.open = callback; return disposable(); },
        onDidChangeTextDocument: callback => { events.change = callback; return disposable(); },
        onDidSaveTextDocument: disposable, onDidCloseTextDocument: disposable, onDidChangeConfiguration: disposable, onDidGrantWorkspaceTrust: disposable
    };
    class Range { constructor(...values) { this.values = values; } isEqual(other) { return JSON.stringify(this.values) === JSON.stringify(other.values); } }
    class MarkdownString { constructor() { this.value = ''; } appendCodeblock(value) { this.value += value; } appendMarkdown(value) { this.value += value; } }
    const vscode = {
        workspace, Uri: { file: uri }, Range, MarkdownString,
        Position: class { constructor(line, character) { this.line = line; this.character = character; } },
        Diagnostic: class { constructor(range, message, severity) { Object.assign(this, { range, message, severity }); } },
        DiagnosticSeverity: { Error: 0, Warning: 1 },
        Hover: class { constructor(content) { this.contents = content; } },
        window: { activeTextEditor: { document: documents[0] }, createOutputChannel: () => ({ ...disposable(), appendLine() {}, show() {} }), showInformationMessage() {}, showWarningMessage() {} },
        languages: {
            createDiagnosticCollection: () => ({ ...disposable(), clear: () => diagnostics.clear(), set: (uri, items) => diagnostics.set(uri.fsPath, items) }),
            ...Object.fromEntries(['CompletionItem', 'Hover', 'Definition', 'SignatureHelp', 'DocumentSymbol'].map(name => [`register${name}Provider`, (selector, provider) => { providers[name] = provider; return disposable(); }]))
        },
        commands: { registerCommand: (name, action) => { commands.set(name, action); return disposable(); }, executeCommand: (name, target) => calls.push({ command: name, target }) },
        tasks: { registerTaskProvider: disposable }, CompletionItemKind: {}, SymbolKind: {}, ConfigurationTarget: { Global: 1 }
    };
    let interrupted = false;
    const spawn = (bin, args) => {
        const child = new EventEmitter(); child.stdout = new EventEmitter(); child.stderr = new EventEmitter(); child.stdin = new EventEmitter();
        child.stdout.setEncoding = child.stderr.setEncoding = () => {}; child.kill = () => { child.killed = true; };
        child.stdin.end = () => queueMicrotask(() => {
            const overlays = [];
            for (let i = 0; i < args.length; i++) if (args[i] === '--overlay') overlays.push({ file: args[i + 1], content: fs.readFileSync(args[i + 2], 'utf8') });
            calls.push({ bin, args, overlays });
            events.change({ contentChanges: [] });
            if (settings.interruptOnce && !interrupted) { interrupted = true; events.change({ contentChanges: [{ text: 'updated' }] }); }
            if (!child.killed) child.stderr.emit('data', JSON.stringify({ file: documents[0].uri.fsPath, line: 1, column: 1, endColumn: 6, code: 'A001', message: 'Erro do compilador.', hint: 'Confira os tipos.' }) + '\n');
            child.emit('close', child.killed ? null : 1);
        });
        return child;
    };
    const context = { extensionPath, subscriptions: [] };
    const sandbox = { require(name) { if (name === 'vscode') return vscode; if (name === 'node:child_process') return { spawn }; if (name === './language') return language; return require(name); }, module: { exports: {} }, setTimeout, clearTimeout, queueMicrotask, process };
    vm.runInNewContext(fs.readFileSync(path.join(extensionPath, 'src/extension.js'), 'utf8'), sandbox);
    sandbox.module.exports.activate(context);
    return { commands, providers, diagnostics, calls, dispose() { for (const item of context.subscriptions) item.dispose(); } };
}
test('comando check inclui pacotes e bibliotecas não salvos e publica o diagnóstico', async () => {
    const entry = doc(path.join(temp, 'assis.assis'), 'import "src.pillow";\nfn main(): int { return 0; }');
    const packageDoc = doc(path.join(temp, 'src.pillow'), 'import "lib.assis";\n', 'assisscript-package', true);
    const lib = doc(path.join(temp, 'lib.assis'), 'fn dobro(value: int): int { return value * 2; }', 'assisscript', true);
    const h = harness([entry, packageDoc, lib]);
    try {
        await h.commands.get('assisscript.check')();
        const runs = h.calls.filter(c => c.bin); assert.equal(runs.length, 1);
        assert.equal(runs[0].overlays.length, 2); assert(runs[0].overlays.some(o => o.file.endsWith('.pillow') && o.content.includes('import')));
        assert.equal(h.diagnostics.get(entry.uri.fsPath)[0].code, 'A001');
        assert.match(h.diagnostics.get(entry.uri.fsPath)[0].message, /Ajuda: Confira os tipos/);
        assert.equal(h.diagnostics.get(entry.uri.fsPath)[0].range.values[3], 5);
    } finally { h.dispose(); }
});

test('catálogo abre manual individual offline de cada biblioteca', async () => {
    const entry = doc(path.join(temp, 'assis.assis'), 'fn main(): int { return 0; }');
    const h = harness([entry]);
    try {
        const catalog = JSON.parse(fs.readFileSync(path.resolve(extensionPath, '../stdlib/catalogo.json'), 'utf8'));
        for (const library of catalog.libraries) {
            await h.commands.get('assisscript.libraries')(library.name);
            assert(h.calls.some(c => c.command === 'markdown.showPreview' && c.target.fsPath.endsWith(library.doc) && fs.existsSync(c.target.fsPath)));
        }
    } finally { h.dispose(); }
});

test('diagnóstico de dependência usa entrada e lockfile do projeto', async () => {
    const entry=path.join(temp,'assis.assis'),manifest=path.join(temp,'assis.pkg'),vendor=path.join(temp,'vendor-editor');fs.mkdirSync(vendor,{recursive:true});
    const library=path.join(vendor,'api.assis'),text='namespace dep;public pure fn f():int{return 42;}';
    fs.writeFileSync(manifest,'package app 1.0.0\ndep dep 1.0.0 vendor-editor\n');fs.writeFileSync(path.join(vendor,'assis.pkg'),'package dep 1.0.0\n');fs.writeFileSync(library,text);fs.writeFileSync(entry,'import "pkg/dep/api.assis";\nfn main():int{return 0;}');
    const h=harness([doc(library,text,'assisscript',true)]);
    try{await h.commands.get('assisscript.check')();const run=h.calls.find(c=>c.bin);assert.equal(run.args[1],entry);assert(!run.args.includes('--stdin'));assert(!run.args.includes('--library'));assert(run.overlays.some(o=>o.file===library&&o.content===text));}
    finally{h.dispose();fs.unlinkSync(manifest);}
});
test('verificação manual repete quando uma edição real interrompe o processo', async () => {
    const entry = doc(path.join(temp, 'assis.assis'), 'fn main(): int { return 0; }');
    const h = harness([entry], { interruptOnce: true });
    try { await h.commands.get('assisscript.check')(); assert.equal(h.calls.filter(c => c.bin).length, 2); assert.equal(h.diagnostics.get(entry.uri.fsPath)[0].code, 'A001'); }
    finally { h.dispose(); }
});
test('provedor de hover mostra assinatura concreta e abre o manual offline', async () => {
    const source = 'fn main(): int { let a: Array<int> = []; a.push(42); free(a); return 0; }';
    const entry = doc(path.join(temp, 'assis.assis'), source), h = harness([entry]);
    try {
        const hover = h.providers.Hover.provideHover(entry, source.indexOf('.push') + 2);
        assert.match(hover.contents.value, /value: int/); assert.match(hover.contents.value, /amortizado/);
        await h.commands.get('assisscript.documentation')();
        assert(h.calls.some(c => c.command === 'markdown.showPreview' && fs.existsSync(c.target.fsPath)));
        assert(h.commands.has('assisscript.icons'));
    } finally { h.dispose(); }
});
