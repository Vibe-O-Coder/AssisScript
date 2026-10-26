'use strict';
const vscode = require('vscode');
const fs = require('node:fs');
const fsp = fs.promises;
const path = require('node:path');
const os = require('node:os');
const { spawn } = require('node:child_process');
const language = require('./language');
const selector = [{ language: 'assisscript', scheme: 'file' }, { language: 'assisscript-package', scheme: 'file' }];

function activate(context) {
    const diagnostics = vscode.languages.createDiagnosticCollection('assisscript');
    const output = vscode.window.createOutputChannel('AssisScript');
    const timers = new Map(), running = new Map(), reports = new Map(), generations = new Map();
    const config = uri => vscode.workspace.getConfiguration('assisscript', uri);
    const workspace = uri => vscode.workspace.getWorkspaceFolder(uri)?.uri.fsPath || path.dirname(uri.fsPath);
    function compiler(uri) {
        const configured = config(uri).get('compilerPath');
        if (configured) return path.isAbsolute(configured) || !/[\\/]/.test(configured) ? configured : path.resolve(workspace(uri), configured);
        const name = process.platform === 'win32' ? 'assis.exe' : 'assis';
        for (const candidate of [path.join(context.extensionPath, 'bin', name), path.join(context.extensionPath, '..', 'bin', name)]) if (fs.existsSync(candidate)) return candidate;
        return name;
    }
    function options(document) {
        const bin = compiler(document.uri), base = path.dirname(bin);
        return {
            includePaths: config(document.uri).get('includePaths', []).map(p => path.resolve(workspace(document.uri), p)),
            stdlibRoots: [path.resolve(base, '../stdlib'), path.resolve(base, '../share/assisscript/stdlib'), path.join(context.extensionPath, 'stdlib'), path.resolve(context.extensionPath, '../stdlib')],
            overlays: new Map(vscode.workspace.textDocuments.filter(d => ['assisscript', 'assisscript-package'].includes(d.languageId) && d.uri.scheme === 'file').map(d => [path.resolve(d.uri.fsPath), d.getText()]))
        };
    }
    function project(document) {
        const opts = options(document), entry = path.resolve(workspace(document.uri), config(document.uri).get('entryFile', 'assis.assis'));
        let models = language.collectProject(entry, opts);
        if (!models.some(m => m.file === document.uri.fsPath)) models = language.collectProject(document.uri.fsPath, opts);
        return { models, model: models.find(m => m.file === document.uri.fsPath) || language.analyze(document.getText(), document.uri.fsPath), opts };
    }
    const range = (model, symbol) => {
        const doc = vscode.workspace.textDocuments.find(d => d.uri.fsPath === model.file);
        const position = offset => {
            if (doc) return doc.positionAt(offset);
            const lines = model.text.slice(0, offset).split('\n'); return new vscode.Position(lines.length - 1, lines.at(-1).length);
        };
        return new vscode.Range(position(symbol.start), position(symbol.end));
    };
    const completionKind = s => ({ class: vscode.CompletionItemKind.Class, function: vscode.CompletionItemKind.Function, method: vscode.CompletionItemKind.Method, field: vscode.CompletionItemKind.Field, parameter: vscode.CompletionItemKind.Variable, variable: vscode.CompletionItemKind.Variable }[s.kind]);
    function publishReports() {
        diagnostics.clear(); const combined = new Map();
        for (const items of reports.values()) for (const [file, itemsForFile] of items) {
            const previous = combined.get(file) || [];
            for (const item of itemsForFile) if (!previous.some(p => p.message === item.message && p.range.isEqual(item.range))) previous.push(item);
            combined.set(file, previous);
        }
        for (const [file, items] of combined) diagnostics.set(vscode.Uri.file(file), items);
    }
    async function validate(document, manual = false) {
        const key = document.uri.toString();
        clearTimeout(timers.get(key)); timers.delete(key);
        if (!vscode.workspace.isTrusted || document.isClosed || !config(document.uri).get('diagnostics', true) && !manual) return;
        const generation = (generations.get(key) || 0) + 1; generations.set(key, generation);
        running.get(key)?.kill();
        let temporary;
        try {
            const text = document.getText(), opts = options(document), model = language.analyze(text, document.uri.fsPath);
            const entry = path.resolve(workspace(document.uri), config(document.uri).get('entryFile', 'assis.assis'));
            const useEntry=document.uri.fsPath!==entry&&fs.existsSync(path.join(path.dirname(entry),'assis.pkg'))&&language.collectProject(entry,opts).some(m=>m.file===document.uri.fsPath);
            const args = ['check', useEntry?entry:document.uri.fsPath, ...(useEntry?[]:['--stdin']), '--diagnostics=json'];
            if (!useEntry&&document.uri.fsPath !== entry && !model.symbols.some(s => s.kind === 'function' && s.name === 'assis_assis')) args.push('--library');
            for (const dir of opts.includePaths) args.push('-I', dir);
            const dirty = vscode.workspace.textDocuments.filter(d => d.uri.scheme === 'file' && ['assisscript', 'assisscript-package'].includes(d.languageId) && ((d.isDirty&&d.uri.toString()!==key)||(useEntry&&d.uri.toString()===key)));
            if (dirty.length) {
                temporary = await fsp.mkdtemp(path.join(os.tmpdir(), 'assisscript-editor-'));
                for (let i = 0; i < dirty.length; i++) {
                    const snapshot = path.join(temporary, `${i}.assis`); await fsp.writeFile(snapshot, dirty[i].getText(), 'utf8');
                    args.push('--overlay', dirty[i].uri.fsPath, snapshot);
                }
            }
            if (generations.get(key) !== generation || document.isClosed) return false;
            const result = await new Promise((resolve, reject) => {
                const child = spawn(compiler(document.uri), args, { cwd: workspace(document.uri), windowsHide: true, shell: false });
                running.set(key, child); let stdout = '', stderr = '', timedOut = false;
                const timer = setTimeout(() => { timedOut = true; child.kill(); }, 10000);
                child.stdout.setEncoding('utf8'); child.stderr.setEncoding('utf8');
                child.stdout.on('data', data => { stdout += data; if (stdout.length > 1024 * 1024) child.kill(); });
                child.stderr.on('data', data => { stderr += data; if (stderr.length > 1024 * 1024) child.kill(); });
                child.on('error', error => { clearTimeout(timer); reject(error); });
                child.on('close', code => { clearTimeout(timer); if (running.get(key) === child) running.delete(key); resolve({ code, stdout, stderr, timedOut }); });
                child.stdin.on('error', () => {}); child.stdin.end(useEntry?'':text, 'utf8');
            });
            if (generations.get(key) !== generation || document.isClosed) return false;
            const report = new Map(); let structured = false;
            for (const line of result.stderr.split(/\r?\n/)) {
                let error; try { error = JSON.parse(line); } catch { continue; }
                if (!error.message) continue; structured = true;
                const file = error.file || document.uri.fsPath, row = Math.max(0, (error.line || 1) - 1), col = Math.max(0, (error.column || 1) - 1);
                const end = Math.max(col + 1, (error.endColumn || error.column + 1 || 2) - 1);
                const message = error.message + (error.hint ? '\nAjuda: ' + error.hint : '');
                const diagnostic = new vscode.Diagnostic(new vscode.Range(row, col, row, end), message, vscode.DiagnosticSeverity.Error);
                diagnostic.source = 'AssisScript'; diagnostic.code = error.code; report.set(file, [...(report.get(file) || []), diagnostic]);
            }
            if (result.code !== 0 && !structured) throw new Error(result.timedOut ? 'A verificação excedeu 10 segundos.' : result.stderr || 'O compilador encerrou a verificação sem diagnóstico JSON. Use AssisScript 2.2 ou posterior.');
            reports.set(key, report); publishReports();
            if (manual) { output.appendLine(result.stdout || result.stderr); output.show(true); }
            return true;
        } catch (error) {
            if (generations.get(key) !== generation || document.isClosed) return false;
            reports.delete(key); publishReports();
            output.appendLine(`Não foi possível verificar ${document.uri.fsPath}: ${error.message}`);
            const diagnostic = new vscode.Diagnostic(new vscode.Range(0, 0, 0, 1), `Verificação indisponível: ${error.message}. Confira assisscript.compilerPath.`, vscode.DiagnosticSeverity.Warning);
            diagnostic.source = 'AssisScript'; reports.set(key, new Map([[document.uri.fsPath, [diagnostic]]])); publishReports();
            if (manual) output.show(true);
        } finally { if (temporary) await fsp.rm(temporary, { recursive: true, force: true }); }
    }
    function schedule(document) {
        if (!['assisscript', 'assisscript-package'].includes(document.languageId) || document.uri.scheme !== 'file') return;
        const key = document.uri.toString(); generations.set(key, (generations.get(key) || 0) + 1); running.get(key)?.kill(); clearTimeout(timers.get(key));
        timers.set(key, setTimeout(() => validate(document), config(document.uri).get('validationDelay', 350)));
    }
    function refresh() { for (const document of vscode.workspace.textDocuments) schedule(document); }
    context.subscriptions.push(diagnostics, output,
        vscode.languages.registerCompletionItemProvider(selector, {
            provideCompletionItems(document, position) {
                const { model, models } = project(document), offset = document.offsetAt(position);
                if (model.regions.some(r => r.start < offset && r.end > offset)) return [];
                const before = model.tokens.filter(t => t.start < offset), last = before.at(-1);
                const dot = last?.value === '.' ? model.tokens.indexOf(last) : before.at(-2)?.value === '.' ? model.tokens.indexOf(before.at(-2)) : -1;
                const symbols = dot >= 0 ? language.members(models, language.receiverType(model, dot, models), new Set(), language.ownerAt(model, offset)) : language.visibleSymbols(model, offset, models);
                const result = symbols.map(symbol => {
                    const item = new vscode.CompletionItem(symbol.name, completionKind(symbol)); item.detail = symbol.label || `${symbol.name}${symbol.type ? ': ' + symbol.type : ''}`;
                    item.documentation = symbol.documentation; return item;
                });
                if (dot < 0) for (const [word, description] of Object.entries(language.keywords)) { const item = new vscode.CompletionItem(word, vscode.CompletionItemKind.Keyword); item.documentation = description; result.push(item); }
                return result;
            }
        }, '.'),
        vscode.languages.registerHoverProvider(selector, {
            provideHover(document, position) {
                const { model, models } = project(document), offset = document.offsetAt(position);
                if (model.regions.some(r => r.start <= offset && r.end > offset)) return;
                const symbol = language.resolveSymbol(model, offset, models), word = document.getText(document.getWordRangeAtPosition(position));
                if (!symbol && !language.keywords[word]) return;
                const markdown = new vscode.MarkdownString(); markdown.appendCodeblock(symbol?.label || (symbol ? `${symbol.name}${symbol.type ? ': ' + symbol.type : ''}` : word), 'assisscript');
                markdown.appendMarkdown('\n\n' + (symbol?.documentation || language.keywords[word] || '')); return new vscode.Hover(markdown);
            }
        }),
        vscode.languages.registerDefinitionProvider(selector, {
            provideDefinition(document, position) {
                const { model, models, opts } = project(document), offset = document.offsetAt(position), imported = model.imports.find(i => i.start <= offset && i.end >= offset);
                if (imported) { const file = language.resolveImport(imported.name, model.file, opts); return file ? new vscode.Location(vscode.Uri.file(file), new vscode.Position(0, 0)) : undefined; }
                const symbol = language.resolveSymbol(model, offset, models); if (!symbol || symbol.builtin) return;
                const source = models.find(m => m.file === symbol.file); return new vscode.Location(vscode.Uri.file(symbol.file), range(source, symbol));
            }
        }),
        vscode.languages.registerSignatureHelpProvider(selector, {
            provideSignatureHelp(document, position) {
                const { model, models } = project(document), found = language.signatureAt(model, document.offsetAt(position), models); if (!found) return;
                const signature = new vscode.SignatureInformation(found.label, found.documentation); signature.parameters = found.params.map(p => new vscode.ParameterInformation(p));
                const help = new vscode.SignatureHelp(); help.signatures = [signature]; help.activeSignature = 0; help.activeParameter = found.active; return help;
            }
        }, '(', ','),
        vscode.languages.registerDocumentSymbolProvider(selector, {
            provideDocumentSymbols(document) {
                const model = language.analyze(document.getText(), document.uri.fsPath), classes = new Map(), result = [];
                for (const s of model.symbols.filter(s => !['variable', 'parameter'].includes(s.kind))) {
                    const kind = { class: vscode.SymbolKind.Class, function: vscode.SymbolKind.Function, method: vscode.SymbolKind.Method, field: vscode.SymbolKind.Field }[s.kind];
                    const item = new vscode.DocumentSymbol(s.name, s.label || s.type || '', kind, new vscode.Range(document.positionAt(s.start), document.positionAt(s.bodyEnd || s.end)), range(model, s));
                    if (s.kind === 'class') { classes.set(s.name, item); result.push(item); }
                    else if (s.owner) classes.get(s.owner)?.children.push(item); else result.push(item);
                }
                return result;
            }
        }),
        vscode.workspace.onDidOpenTextDocument(schedule),
        vscode.workspace.onDidChangeTextDocument(event => { if (event.contentChanges.length) refresh(); }),
        vscode.workspace.onDidSaveTextDocument(() => refresh()),
        vscode.workspace.onDidCloseTextDocument(document => {
            const key = document.uri.toString(); clearTimeout(timers.get(key)); timers.delete(key); generations.set(key, (generations.get(key) || 0) + 1); running.get(key)?.kill(); reports.delete(key); publishReports(); refresh();
        }),
        vscode.workspace.onDidChangeConfiguration(() => { reports.clear(); publishReports(); refresh(); }),
        vscode.workspace.onDidGrantWorkspaceTrust(refresh),
        { dispose() { for (const timer of timers.values()) clearTimeout(timer); for (const child of running.values()) child.kill(); } }
    );
    const watcher = vscode.workspace.createFileSystemWatcher('**/*.{assis,pillow,pkg,lock}');
    context.subscriptions.push(watcher, watcher.onDidChange(refresh), watcher.onDidCreate(refresh), watcher.onDidDelete(refresh));
    function task(command, uri, supplied = {}) {
        const folder = vscode.workspace.getWorkspaceFolder(uri), root = workspace(uri);
        const entry = path.resolve(root, supplied.file || (['fmt','test','doc'].includes(command) ? uri.fsPath : config(uri).get('entryFile', 'assis.assis')));
        const file = fs.existsSync(entry) ? entry : uri.fsPath;
        const args = [command, file]; if(command !== 'fmt')for (const dir of config(uri).get('includePaths', [])) args.push('-I', path.resolve(root, dir));
        if (command === 'run' || command === 'test') args.push('--timeout', String(config(uri).get('runTimeout', 10)));
        const definition = { ...supplied, type: 'assisscript', command };
        const result = new vscode.Task(definition, folder || vscode.TaskScope.Workspace, { build: 'Compilar', check: 'Verificar', run: 'Compilar e run', fmt: 'Formatar', test: 'Testar', doc: 'Gerar API' }[command], 'AssisScript', new vscode.ProcessExecution(compiler(uri), args, { cwd: root }), '$assisscript');
        if (command === 'build') result.group = vscode.TaskGroup.Build;
        return result;
    }
    for (const command of ['check', 'build', 'run', 'fmt', 'test', 'doc']) context.subscriptions.push(vscode.commands.registerCommand(`assisscript.${command}`, async () => {
        const document = vscode.window.activeTextEditor?.document;
        if (!document || document.languageId !== 'assisscript' || document.uri.scheme !== 'file') { vscode.window.showInformationMessage('Abra um arquivo .assis salvo no disco.'); return; }
        if (!vscode.workspace.isTrusted) { vscode.window.showWarningMessage('Confie nesta pasta para usar o compilador AssisScript.'); return; }
        if (command === 'check') { for (let attempt = 0; attempt < 3; attempt++) if (await validate(document, true) !== false) break; }
        else {
            for (const doc of vscode.workspace.textDocuments.filter(d => d.languageId === 'assisscript' && d.isDirty)) if (!await doc.save()) return;
            await vscode.tasks.executeTask(task(command, document.uri));
        }
    }));
    context.subscriptions.push(vscode.tasks.registerTaskProvider('assisscript', {
        provideTasks() {
            if (!vscode.workspace.isTrusted) return [];
            return (vscode.workspace.workspaceFolders || []).flatMap(folder => ['build', 'check', 'run', 'test', 'doc'].map(command => task(command, vscode.Uri.file(path.join(folder.uri.fsPath, config(folder.uri).get('entryFile', 'assis.assis'))))));
        },
        resolveTask(candidate) {
            if (!vscode.workspace.isTrusted || !['build', 'check', 'run', 'fmt', 'test', 'doc'].includes(candidate.definition.command)) return undefined;
            const folder = candidate.scope?.uri || vscode.workspace.workspaceFolders?.[0]?.uri;
            return folder ? task(candidate.definition.command, folder, candidate.definition) : undefined;
        }
    }));
    context.subscriptions.push(vscode.commands.registerCommand('assisscript.documentation', () => {
        const candidates = [path.join(context.extensionPath, 'docs', 'LINGUAGEM.md'), path.resolve(context.extensionPath, '../docs/LINGUAGEM.md')];
        const file = candidates.find(candidate => fs.existsSync(candidate));
        if (file) return vscode.commands.executeCommand('markdown.showPreview', vscode.Uri.file(file));
    }));
    context.subscriptions.push(vscode.commands.registerCommand('assisscript.libraries', async name => {
        const roots = [context.extensionPath, path.resolve(context.extensionPath, '..')];
        const root = roots.find(dir => fs.existsSync(path.join(dir, 'stdlib', 'catalogo.json'))); if (!root) return;
        const catalog = JSON.parse(fs.readFileSync(path.join(root, 'stdlib', 'catalogo.json'), 'utf8'));
        let library = typeof name === 'string' ? catalog.libraries.find(item => item.name === name) : undefined;
        if (!library) {
            const choice = await vscode.window.showQuickPick(catalog.libraries.map(item => ({ label: item.name, description: item.required ? 'Obrigatória' : 'Opcional', detail: item.description, library: item })), { placeHolder: 'Documentação das bibliotecas nativas' });
            library = choice?.library;
        }
        if (library) return vscode.commands.executeCommand('markdown.showPreview', vscode.Uri.file(path.join(root, 'docs', library.doc)));
    }));
    context.subscriptions.push(vscode.commands.registerCommand('assisscript.icons', () => vscode.workspace.getConfiguration('workbench').update('iconTheme', 'assisscript-icons', vscode.ConfigurationTarget.Global)));
    refresh();
}
module.exports = { activate };
