#!/usr/bin/env node
'use strict';
// LSP 3.17 over stdio. Only the protocol is written to stdout.
const fs = require('node:fs');
const fsp = fs.promises;
const os = require('node:os');
const path = require('node:path');
const { fileURLToPath, pathToFileURL } = require('node:url');
const { spawn } = require('node:child_process');
const language = require(fs.existsSync(path.resolve(__dirname, '../vscode-assisscript/src/language.js')) ? '../vscode-assisscript/src/language' : '../src/language');
const packageInfo = require(fs.existsSync(path.resolve(__dirname, '../vscode-assisscript/package.json')) ? '../vscode-assisscript/package.json' : '../package.json');
let input = Buffer.alloc(0), root = process.cwd(), options = {}, shutdown = false;
const documents = new Map(), pending = new Map(), generations = new Map(), timers = new Map(), children = new Set(), published = new Set();
const MAX = 16 * 1024 * 1024;
const send = object => { const body = Buffer.from(JSON.stringify(object)); process.stdout.write(`Content-Length: ${body.length}\r\n\r\n`); process.stdout.write(body); };
const notify = (method, params) => send({ jsonrpc: '2.0', method, params });
const offset = (text, position) => { const lines = text.split('\n'); let n = 0; for (let i = 0; i < Math.min(position.line, lines.length - 1); i++) n += lines[i].length + 1; return Math.min(text.length, n + Math.min(position.character, lines[Math.min(position.line, lines.length - 1)].length)); };
const position = (text, n) => { const lines = text.slice(0, n).split('\n'); return { line: lines.length - 1, character: lines.at(-1).length }; };
const range = (model, symbol) => ({ start: position(model.text, symbol.start), end: position(model.text, symbol.end) });
function compiler() { const name=process.platform === 'win32' ? 'assis.exe' : 'assis'; return options.compilerPath || [path.resolve(__dirname,'../bin',name),path.resolve(__dirname,'../../../bin',name)].find(file=>fs.existsSync(file)) || name; }
function project(uri) {
    const file = fileURLToPath(uri), overlays = new Map([...documents].map(([u, d]) => [fileURLToPath(u), d.text]));
    const settings = { overlays, includePaths: options.includePaths || [], stdlibRoots: [path.resolve(path.dirname(compiler()), '../stdlib'), path.resolve(path.dirname(compiler()), '../share/assisscript/stdlib')] };
    let models = language.collectProject(path.join(root, options.entryFile || 'assis.assis'), settings);
    if (!models.some(m => m.file === file)) models = language.collectProject(file, settings);
    const model = models.find(m => m.file === file) || language.analyze(documents.get(uri)?.text || '', file);
    return { models, model, entry: models[0]?.file || file };
}
async function execute(args, signal) {
    return await new Promise((resolve, reject) => {
        const child = spawn(compiler(), args, { cwd: root, windowsHide: true, shell: false, signal }); children.add(child);
        let stdout = '', stderr = ''; const timeout = setTimeout(() => child.kill(), 15000);
        child.stdout.on('data', b => { stdout += b.toString('utf8'); if (Buffer.byteLength(stdout) > MAX) child.kill(); });
        child.stderr.on('data', b => { stderr += b.toString('utf8'); if (Buffer.byteLength(stderr) > MAX) child.kill(); });
        child.on('error', reject); child.on('close', code => { clearTimeout(timeout); children.delete(child); resolve({ code, stdout, stderr }); });
    });
}
async function diagnostics(uri) {
    const doc = documents.get(uri); if (!doc || shutdown) return;
    const generation = (generations.get(uri) || 0) + 1; generations.set(uri, generation);
    const controller = new AbortController(); pending.get(uri)?.abort(); pending.set(uri, controller);
    const folder = await fsp.mkdtemp(path.join(os.tmpdir(), 'assis-lsp-'));
    try {
        const context=project(uri), useEntry=context.entry!==fileURLToPath(uri)&&fs.existsSync(path.join(path.dirname(context.entry),'assis.pkg'));
        const args = ['check', useEntry?context.entry:fileURLToPath(uri), '--diagnostics=json'];
        if (!useEntry&&!language.analyze(doc.text, fileURLToPath(uri)).symbols.some(s => s.kind === 'function' && s.name === 'assis_assis')) args.push('--library');
        for (const include of options.includePaths || []) args.push('-I', include);
        let i = 0; for (const [u, d] of documents) { const snapshot = path.join(folder, `${i++}.assis`); await fsp.writeFile(snapshot, d.text, 'utf8'); args.push('--overlay', fileURLToPath(u), snapshot); }
        const result = await execute(args, controller.signal);
        if (generations.get(uri) !== generation || !documents.has(uri) || shutdown) return;
        const groups = new Map([[uri, []]]);
        for (const line of result.stderr.split(/\r?\n/).filter(Boolean)) {
            let error; try { error = JSON.parse(line); } catch { continue; }
            const target = error.file ? pathToFileURL(error.file).href : uri;
            const item = { range: { start: { line: Math.max(0, (error.line || 1) - 1), character: Math.max(0, (error.column || 1) - 1) }, end: { line: Math.max(0, (error.line || 1) - 1), character: Math.max(1, (error.endColumn || error.column + 1 || 2) - 1) } }, severity: 1, code: error.code, source: 'AssisScript', message: error.message + (error.hint ? '\n' + error.hint : '') };
            if (!groups.has(target)) groups.set(target, []); groups.get(target).push(item);
        }
        if (result.code && ![...groups.values()].some(items => items.length)) groups.get(uri).push({ range: { start: { line: 0, character: 0 }, end: { line: 0, character: 1 } }, severity: 1, source: 'AssisScript', message: result.stderr || 'O compilador não concluiu a análise.' });
        for (const old of published) if (!groups.has(old)) notify('textDocument/publishDiagnostics', { uri: old, diagnostics: [] });
        published.clear(); for (const [target, items] of groups) { notify('textDocument/publishDiagnostics', { uri: target, version: target === uri ? doc.version : undefined, diagnostics: items }); published.add(target); }
    } catch (error) {
        if (error.name !== 'AbortError' && generations.get(uri) === generation) notify('window/logMessage', { type: 1, message: `AssisScript: ${error.message}` });
    } finally { if (pending.get(uri) === controller) pending.delete(uri); await fsp.rm(folder, { recursive: true, force: true }); }
}
function schedule(uri) { clearTimeout(timers.get(uri)); timers.set(uri, setTimeout(() => { timers.delete(uri); diagnostics(uri); }, 80)); }
async function handle(method, params) {
    if (method === 'initialize') {
        root = params.rootUri ? fileURLToPath(params.rootUri) : params.workspaceFolders?.[0]?.uri ? fileURLToPath(params.workspaceFolders[0].uri) : root; options = params.initializationOptions || {};
        return { serverInfo: { name: 'AssisScript', version: packageInfo.version }, capabilities: { positionEncoding: 'utf-16', textDocumentSync: { openClose: true, change: 2, save: { includeText: true } }, completionProvider: { triggerCharacters: ['.', ':'] }, hoverProvider: true, definitionProvider: true, documentSymbolProvider: true, signatureHelpProvider: { triggerCharacters: ['(', ','] }, documentFormattingProvider: true } };
    }
    if (method === 'shutdown') { shutdown = true; for (const timer of timers.values()) clearTimeout(timer); for (const controller of pending.values()) controller.abort(); return null; }
    if (method === 'exit') { process.exitCode = shutdown ? 0 : 1; process.stdin.destroy(); for (const child of children) child.kill(); return; }
    if (shutdown) throw Object.assign(new Error('Servidor encerrado'), { code: -32600 });
    if (method === 'initialized' || method === '$/cancelRequest' || method === '$/setTrace') return;
    const uri = params?.textDocument?.uri;
    if (uri && !uri.startsWith('file:')) throw Object.assign(new Error('Somente documentos file: são suportados'), { code: -32602 });
    if (method === 'textDocument/didOpen') { const d = params.textDocument; if (Buffer.byteLength(d.text) > MAX) throw new Error('Documento maior que 16 MiB'); documents.set(uri, { text: d.text, version: d.version }); schedule(uri); return; }
    if (method === 'textDocument/didChange') {
        const doc = documents.get(uri); if (!doc || params.textDocument.version <= doc.version) return;
        for (const change of params.contentChanges) doc.text = change.range ? doc.text.slice(0, offset(doc.text, change.range.start)) + change.text + doc.text.slice(offset(doc.text, change.range.end)) : change.text;
        if (Buffer.byteLength(doc.text) > MAX) throw new Error('Documento maior que 16 MiB'); doc.version = params.textDocument.version; pending.get(uri)?.abort(); generations.set(uri, (generations.get(uri) || 0) + 1); schedule(uri); return;
    }
    if (method === 'textDocument/didSave') { if (params.text !== undefined && documents.has(uri)) documents.get(uri).text = params.text; schedule(uri); return; }
    if (method === 'textDocument/didClose') { documents.delete(uri); clearTimeout(timers.get(uri)); timers.delete(uri); pending.get(uri)?.abort(); generations.set(uri, (generations.get(uri) || 0) + 1); notify('textDocument/publishDiagnostics', { uri, diagnostics: [] }); return; }
    if (!uri) throw Object.assign(new Error(`Método não suportado: ${method}`), { code: -32601 });
    const { model, models } = project(uri), at = params.position ? offset(model.text, params.position) : 0;
    if (method === 'textDocument/completion') return language.visibleSymbols(model, at, models).map(s => ({ label: s.name, kind: s.kind === 'class' ? 7 : s.kind === 'function' ? 3 : 6, detail: s.label || s.type, documentation: s.documentation }));
    if (method === 'textDocument/hover') { const s = language.resolveSymbol(model, at, models); return s ? { contents: { kind: 'markdown', value: '```assis\n' + (s.label || s.name + ': ' + s.type) + '\n```\n\n' + (s.documentation || '') } } : null; }
    if (method === 'textDocument/definition') { const s = language.resolveSymbol(model, at, models), target = models.find(m => m.file === s?.file); return s && target ? { uri: pathToFileURL(s.file).href, range: range(target, s) } : null; }
    if (method === 'textDocument/signatureHelp') { const s = language.signatureAt(model, at, models); return s ? { signatures: [{ label: s.label, documentation: s.documentation, parameters: s.params.map(label => ({ label })) }], activeSignature: 0, activeParameter: s.active } : null; }
    if (method === 'textDocument/documentSymbol') return model.symbols.map(s => ({ name: s.name, kind: s.kind === 'class' ? 5 : s.kind === 'function' ? 12 : s.kind === 'method' ? 6 : 13, range: { start: position(model.text, s.start), end: position(model.text, s.bodyEnd || s.end) }, selectionRange: range(model, s) }));
    if (method === 'textDocument/formatting') {
        const folder = await fsp.mkdtemp(path.join(os.tmpdir(), 'assis-lsp-format-'));
        try { const file = path.join(folder, 'format.assis'); await fsp.writeFile(file, model.text, 'utf8'); const r = await execute(['fmt', file]); if (r.code) throw new Error(r.stderr); const text = await fsp.readFile(file, 'utf8'); return text === model.text ? [] : [{ range: { start: { line: 0, character: 0 }, end: position(model.text, model.text.length) }, newText: text }]; }
        finally { await fsp.rm(folder, { recursive: true, force: true }); }
    }
    throw Object.assign(new Error(`Método não suportado: ${method}`), { code: -32601 });
}
process.stdin.on('data', chunk => {
    input = Buffer.concat([input, chunk]);
    while (true) {
        const end = input.indexOf('\r\n\r\n'); if (end < 0) { if (input.length > 8192) process.exit(1); return; }
        const header = input.subarray(0, end).toString('ascii'), match = /^Content-Length:\s*(\d+)\s*$/im.exec(header);
        if (!match || Number(match[1]) > MAX) { process.exitCode = 1; process.stdin.destroy(); return; }
        const length = Number(match[1]); if (input.length < end + 4 + length) return;
        const body = input.subarray(end + 4, end + 4 + length); input = input.subarray(end + 4 + length);
        let request; try { request = JSON.parse(body.toString('utf8')); } catch { send({ jsonrpc: '2.0', id: null, error: { code: -32700, message: 'JSON inválido' } }); continue; }
        Promise.resolve().then(() => handle(request.method, request.params || {})).then(result => { if ('id' in request) send({ jsonrpc: '2.0', id: request.id, result: result ?? null }); }, error => { if ('id' in request) send({ jsonrpc: '2.0', id: request.id, error: { code: error.code || -32603, message: error.message } }); else notify('window/logMessage', { type: 1, message: error.message }); });
    }
});
process.stdin.on('end', () => { for (const timer of timers.values()) clearTimeout(timer); for (const controller of pending.values()) controller.abort(); });
