'use strict';
const vscode = require('vscode');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { spawnSync } = require('node:child_process');

function realPath(file) {
    const resolved = fs.realpathSync(file);
    return process.platform === 'win32' ? resolved.toLowerCase() : resolved;
}

async function run() {
    const extension = vscode.extensions.getExtension('assisscript-local.assisscript');
    const installed = fs.realpathSync(process.env.ASSIS_TEST_EXTENSION);
    assert.equal(realPath(extension.extensionPath), realPath(installed));
    await extension.activate();

    const example = path.join(installed, 'exemplos', '68_typed_input.assis');
    const workspace = vscode.workspace.workspaceFolders[0].uri.fsPath;
    const source = path.join(workspace, 'assis.assis');
    fs.copyFileSync(example, source);
    const doc = await vscode.workspace.openTextDocument(source);
    await vscode.window.showTextDocument(doc);
    assert.equal(doc.languageId, 'assisscript');
    const text = doc.getText();
    const offset = text.indexOf('input.readint') + 'input.'.length;
    const definitions = await vscode.commands.executeCommand('vscode.executeDefinitionProvider', doc.uri, doc.positionAt(offset + 2));
    const cli = path.join(installed, 'stdlib', 'cli.assis');
    const targets = definitions.map(def => realPath((def.uri || def.targetUri).fsPath));
    assert(targets.includes(realPath(cli)), JSON.stringify({ targets, cli, offset, source: doc.uri.fsPath }));
    const completion = await vscode.commands.executeCommand('vscode.executeCompletionItemProvider', doc.uri, doc.positionAt(offset), '.');
    const labels = completion.items.map(item => typeof item.label === 'string' ? item.label : item.label.label);
    for (const method of ['readln', 'readint', 'readfloat', 'readbool']) assert(labels.includes(method));

    await vscode.commands.executeCommand('assisscript.check');
    assert(!vscode.languages.getDiagnostics(doc.uri).some(d => d.severity === vscode.DiagnosticSeverity.Error));
    const task = (await vscode.tasks.fetchTasks({ type: 'assisscript' })).find(t => t.definition.command === 'run');
    assert(task?.execution instanceof vscode.ProcessExecution);
    assert.equal(realPath(task.execution.process), realPath(path.join(installed, 'bin', process.platform === 'win32' ? 'assis.exe' : 'assis')));
    const ran = spawnSync(task.execution.process, task.execution.args, {
        cwd: workspace, input: 'Júlia\n3\n12.50\ntrue\n', encoding: 'utf8', timeout: 30000
    });
    assert.ifError(ran.error);
    assert.equal(ran.status, 0, ran.stderr);
    assert.match(ran.stdout, /Júlia 3 37\.50\r?\n$/);
    fs.writeFileSync(path.join(workspace, 'result.json'), JSON.stringify({
        passed: true, vscode: vscode.version, extension: extension.packageJSON.version,
        checks: ['activation', 'language association', 'F12', 'completion', 'check', 'run task executable and output']
    }, null, 2) + '\n');
    console.log('Packaged AssisScript activation, completion, F12, check and run task: PASS');
}

module.exports = { run };
