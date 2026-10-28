'use strict';
const vscode = require('vscode');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

async function run() {
    const root = path.resolve(__dirname, '../..'), folder = path.join(root, 'build', 'editor-fixture');
    fs.mkdirSync(folder, { recursive: true });
    const file = path.join(folder, 'assis.assis'), library = path.join(folder, 'biblioteca.assis');
    const source = `import "biblioteca";
import "std/math";
fn main(): int {
    let AssisAssis: FodaseAssis = new FodaseAssis();
    print(AssisAssis.AssisFodase());
    print(Assis_fodase_fodase(99, 0, 10));
    let AssisFodase: int = Assis_Assis(); print(AssisFodase);
    free(AssisAssis);
    return 0;
}`;
    const libSource = 'class AssisAssis { fn AssisFodase(): int { return 42; } } class FodaseAssis extends AssisAssis {}\nfn Assis_Assis(): int { return 21; }';
    fs.writeFileSync(file, source); fs.writeFileSync(library, libSource);
    const checks = [];
    const pause = ms => new Promise(resolve => setTimeout(resolve, ms));
    async function until(predicate, message) { for (let i = 0; i < 100; i++) { const value = predicate(); if (value) return value; await pause(100); } throw new Error(message); }
    async function replace(doc, text) { const edit = new vscode.WorkspaceEdit(); edit.replace(doc.uri, new vscode.Range(doc.positionAt(0), doc.positionAt(doc.getText().length)), text); assert(await vscode.workspace.applyEdit(edit)); }
    let document, dependency;
    try {
        const extension = vscode.extensions.getExtension('assisscript-local.assisscript'); assert(extension, 'Extensão registrada'); await extension.activate(); checks.push('ativação');
        document = await vscode.workspace.openTextDocument(file); await vscode.window.showTextDocument(document); assert.equal(document.languageId, 'assisscript'); checks.push('associação .assis');
        const global = await vscode.commands.executeCommand('vscode.executeCompletionItemProvider', document.uri, document.positionAt(source.indexOf('Assis_fodase_fodase')));
        assert(global.items.some(i => i.label === 'Assis_assis_fodase'), 'Sugestões da biblioteca padrão'); checks.push('completar imports');
        const member = await vscode.commands.executeCommand('vscode.executeCompletionItemProvider', document.uri, document.positionAt(source.indexOf('AssisAssis.AssisFodase') + 'AssisAssis.'.length), '.');
        assert(member.items.some(i => i.label === 'AssisFodase'), 'Sugestões de método herdado'); checks.push('membros herdados');
        const definition = await vscode.commands.executeCommand('vscode.executeDefinitionProvider', document.uri, document.positionAt(source.indexOf('AssisAssis.AssisFodase') + 'AssisAssis.'.length));
        assert(definition.some(d => (d.uri || d.targetUri).fsPath === library), 'Definição em outro arquivo'); checks.push('F12 entre arquivos');
        const hover = await vscode.commands.executeCommand('vscode.executeHoverProvider', document.uri, document.positionAt(source.indexOf('Assis_fodase_fodase') + 2)); assert(hover.length); checks.push('hover');
        const signature = await vscode.commands.executeCommand('vscode.executeSignatureHelpProvider', document.uri, document.positionAt(source.indexOf('99, 0') + 5), ',', undefined);
        assert(signature?.signatures.length); assert.equal(signature.activeParameter, 1); checks.push('assinatura');
        const symbols = await vscode.commands.executeCommand('vscode.executeDocumentSymbolProvider', document.uri); assert(symbols.some(s => s.name === 'main')); checks.push('estrutura');
        await vscode.commands.executeCommand('assisscript.check');
        assert.equal(vscode.languages.getDiagnostics(document.uri).filter(d => d.severity === vscode.DiagnosticSeverity.Error).length, 0); checks.push('check válido');
        await replace(document, source.replace('return 0;', 'return true;'));
        const errors = await until(() => vscode.languages.getDiagnostics(document.uri).find(d => d.code === 'A001'), 'Diagnóstico não apareceu');
        assert.match(errors.message, /Ajuda:/);
        assert.equal(errors.range.start.line, 8); checks.push('erro não salvo');
        await replace(document, source); await until(() => vscode.languages.getDiagnostics(document.uri).length === 0, 'Diagnóstico antigo não foi removido'); checks.push('remoção de erro');
        dependency = await vscode.workspace.openTextDocument(library);
        await replace(dependency, libSource.replace('fn Assis_Assis(): int { return 21; }', 'fn Assis_Assis(): text { return "strings"; }'));
        await vscode.window.showTextDocument(document); await vscode.commands.executeCommand('assisscript.check');
        assert(vscode.languages.getDiagnostics(document.uri).some(d => d.code === 'A001'), 'Snapshot de dependência não salva'); checks.push('overlay de dependência');
        await replace(dependency, libSource); await replace(document, source); await document.save(); await dependency.save();
        const tasks = await vscode.tasks.fetchTasks({ type: 'assisscript' }); assert(tasks.length >= 3); checks.push('tarefas');
        const packageFile = path.join(folder, 'src.pillow'), modernLib = path.join(folder, 'moderna.assis');
        fs.writeFileSync(packageFile, 'import "moderna.assis";\n');
        fs.writeFileSync(modernLib, '/// Retorna o dobro com overflow modular.\nfn dobro(valor: int): int { return valor * 2; }\nstruct Pessoa { let nome: text; }\n');
        const modern = `import "src.pillow";
import "std/math.assis";
fn main(): int {
    let numeros: Array<int> = [10, 20];
    numeros.push(max(30, 40));
    let mapa: HashMap<text, int> = new HashMap<text, int>();
    mapa.set("vida", dobro(21));
    print(mapa.get("vida"));
    free(mapa); free(numeros); return 0;
}`;
        await replace(document, modern); await document.save();
        const hoverText = results => results.flatMap(h => h.contents).map(c => typeof c === 'string' ? c : c.value).join('\n');
        const arrayHover = await vscode.commands.executeCommand('vscode.executeHoverProvider', document.uri, document.positionAt(modern.indexOf('.push') + 2));
        assert.match(hoverText(arrayHover), /value: int/); assert.match(hoverText(arrayHover), /amortizado/); checks.push('hover técnico Array<int>');
        const mapHover = await vscode.commands.executeCommand('vscode.executeHoverProvider', document.uri, document.positionAt(modern.indexOf('.get') + 2));
        assert.match(hoverText(mapHover), /key: text/); assert.match(hoverText(mapHover), /ausente/); checks.push('hover técnico HashMap');
        const stdHover = await vscode.commands.executeCommand('vscode.executeHoverProvider', document.uri, document.positionAt(modern.indexOf('max') + 2));
        assert.match(hoverText(stdHover), /maior/); checks.push('documentação da biblioteca legível');
        const packageHover = await vscode.commands.executeCommand('vscode.executeHoverProvider', document.uri, document.positionAt(modern.indexOf('dobro') + 2));
        assert.match(hoverText(packageHover), /overflow modular/); checks.push('documentação transitiva #body');
        const packageDefinition = await vscode.commands.executeCommand('vscode.executeDefinitionProvider', document.uri, document.positionAt(modern.indexOf('src.pillow') + 2));
        assert(packageDefinition.some(d => (d.uri || d.targetUri).fsPath === packageFile)); checks.push('F12 pacote .pillow');
        const modernSignature = await vscode.commands.executeCommand('vscode.executeSignatureHelpProvider', document.uri, document.positionAt(modern.indexOf('"vida", dobro') + 8), ',', undefined);
        assert.match(modernSignature.signatures[0].label, /key: text, value: int/); assert.equal(modernSignature.activeParameter, 1); checks.push('assinatura genérica concreta');
        await vscode.commands.executeCommand('assisscript.check'); assert.equal(vscode.languages.getDiagnostics(document.uri).filter(d => d.severity === vscode.DiagnosticSeverity.Error).length, 0); checks.push('check novas estruturas');
        const packageDocument = await vscode.workspace.openTextDocument(packageFile); assert.equal(packageDocument.languageId, 'assisscript-package'); checks.push('associação .pillow');
        const commands = await vscode.commands.getCommands(); assert(commands.includes('assisscript.documentation')); assert(commands.includes('assisscript.icons')); checks.push('comandos documentação e ícones');
        await vscode.commands.executeCommand('assisscript.documentation'); checks.push('manual offline abre no editor');
        assert(commands.includes('assisscript.libraries'));
        await vscode.commands.executeCommand('assisscript.libraries', 'csv'); checks.push('manual individual CSV abre offline');
        const v31 = 'import "std/convert.assis";\nfn main(): int { let value: IntResult = parse_int("42"); let a: Array<int> = [42]; let saida: int = 0; a.try_get(0, &saida); free(a); free(value); return 0; }';
        await replace(document, v31); await document.save();
        const converted = await vscode.commands.executeCommand('vscode.executeHoverProvider', document.uri, document.positionAt(v31.indexOf('parse_int') + 2));
        assert.match(hoverText(converted), /overflow/); checks.push('hover da conversão segura transitiva');
        const recoverable = await vscode.commands.executeCommand('vscode.executeHoverProvider', document.uri, document.positionAt(v31.indexOf('.try_get') + 2));
        assert.match(hoverText(recoverable), /output: \*int/); checks.push('hover tipado try_get');
        await vscode.commands.executeCommand('assisscript.check'); assert.equal(vscode.languages.getDiagnostics(document.uri).filter(d => d.severity === vscode.DiagnosticSeverity.Error).length, 0); checks.push('check conversões e operação recuperável');
        fs.writeFileSync(path.join(root, 'build', 'extension-host-result.json'), JSON.stringify({ ok: true, checks }, null, 2));
        console.log('ASSIS: ' + checks.length + ' verificações no VSCode real aprovadas.');
    } catch (error) {
        fs.writeFileSync(path.join(root, 'build', 'extension-host-result.json'), JSON.stringify({ ok: false, checks, error: error.stack }, null, 2)); throw error;
    } finally {
        if (document && document.getText() !== source) { await replace(document, source); await document.save(); }
        if (dependency && dependency.getText() !== libSource) { await replace(dependency, libSource); await dependency.save(); }
    }
}
module.exports = { run };
