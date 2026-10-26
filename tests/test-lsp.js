'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { spawn, spawnSync } = require('node:child_process');
const { pathToFileURL } = require('node:url');
const language = require('../vscode-assisscript/src/language');

test('namespaces no editor conservam privacidade, tipos e navegação', () => {
    const a = language.analyze('namespace a;public value struct P<T>{let x:T;}pure assis hidden(n:int):int{return n;}public pure assis f(n:int):int{return hidden(n);}', '/a.assis');
    const b = language.analyze('assis assis_assis():int{val p:a::P<int>=new a::P<int>(42);return a::f(p.x);}', '/b.assis');
    const resolved = language.resolveSymbol(b, b.text.indexOf('a::f'), [a,b]); assert.equal(resolved?.name,'a::f');
    assert.equal(language.members([a,b], 'a::P<int>')[0].type, 'int');
    assert.ok(!language.visibleSymbols(b,b.text.length-1,[a,b]).some(s => s.name.includes('hidden')));
    assert.equal(language.resolveSymbol(a,a.text.lastIndexOf('hidden(n)'),[a,b])?.name,'hidden');
});

test('LSP independente: framing, UTF-16, overlays, navegação e correção de erros', async () => {
    const folder = fs.mkdtempSync(path.join(os.tmpdir(),'assis-lsp-test-'));
    const file = path.join(folder,'assis.assis'), uri=pathToFileURL(file).href;
    const original = 'pure assis dobro(x:int):int{return x*2;}\nassis assis_assis():int{print("😀");return dobro(21);}\n';fs.writeFileSync(file,original);
    const child = spawn(process.execPath,[path.resolve(__dirname,'../tools/assis-lsp.js')],{stdio:['pipe','pipe','pipe'],windowsHide:true});
    let buffer=Buffer.alloc(0),id=0,stderr='',closed=false;const waiting=new Map(),notifications=[],events=[];
    child.stderr.on('data',b=>stderr+=b);
    child.stdout.on('data',b=>{buffer=Buffer.concat([buffer,b]);while(true){const end=buffer.indexOf('\r\n\r\n');if(end<0)return;const n=Number(/Content-Length: (\d+)/.exec(buffer.subarray(0,end).toString())[1]);if(buffer.length<end+4+n)return;const message=JSON.parse(buffer.subarray(end+4,end+4+n));buffer=buffer.subarray(end+4+n);if('id' in message){const w=waiting.get(message.id);waiting.delete(message.id);clearTimeout(w.timer);message.error?w.reject(new Error(message.error.message)):w.resolve(message.result);}else{notifications.push(message);for(const event of events)event();}}});
    const send=message=>{const body=Buffer.from(JSON.stringify({jsonrpc:'2.0',...message}));child.stdin.write(`Content-Length: ${body.length}\r\n\r\n`);child.stdin.write(body);};
    const request=(method,params={})=>new Promise((resolve,reject)=>{const number=++id;const timer=setTimeout(()=>reject(new Error('Timeout '+method)),15000);waiting.set(number,{resolve,reject,timer});send({id:number,method,params});});
    const until=predicate=>new Promise((resolve,reject)=>{const timer=setTimeout(()=>reject(new Error('Diagnostic timeout '+JSON.stringify(notifications))),15000);const check=()=>{const value=notifications.find(predicate);if(value){clearTimeout(timer);events.splice(events.indexOf(check),1);resolve(value);}};events.push(check);check();});
    try {
        const result=await request('initialize',{rootUri:pathToFileURL(folder).href});assert.equal(result.capabilities.textDocumentSync.change,2);
        send({method:'initialized'});send({method:'textDocument/didOpen',params:{textDocument:{uri,languageId:'assisscript',version:1,text:original}}});
        const callPosition={line:1,character:original.split('\n')[1].indexOf('dobro')+2};
        const definition=await request('textDocument/definition',{textDocument:{uri},position:callPosition});assert.equal(definition?.uri,uri);
        const hover=await request('textDocument/hover',{textDocument:{uri},position:callPosition});assert.match(hover.contents.value,/dobro/);
        const completion=await request('textDocument/completion',{textDocument:{uri},position:{line:1,character:50}});assert.ok(completion.some(s=>s.label==='dobro'));
        const symbols=await request('textDocument/documentSymbol',{textDocument:{uri}});assert.equal(symbols.filter(s=>s.kind===12).length,2);
        const broken=original.replace('dobro(21)','ausente(21)');send({method:'textDocument/didChange',params:{textDocument:{uri,version:2},contentChanges:[{text:broken}]}});
        const error=await until(m=>m.method==='textDocument/publishDiagnostics'&&m.params.version===2&&m.params.diagnostics.length);assert.match(error.params.diagnostics[0].message,/ausente/);assert.ok(error.params.diagnostics[0].range.start.character>40);
        send({method:'textDocument/didChange',params:{textDocument:{uri,version:3},contentChanges:[{text:original}]}});
        await until(m=>m.method==='textDocument/publishDiagnostics'&&m.params.version===3&&m.params.diagnostics.length===0);
        assert.equal(fs.readFileSync(file,'utf8'),original);
        const edits=await request('textDocument/formatting',{textDocument:{uri},options:{tabSize:4,insertSpaces:true}});assert.ok(Array.isArray(edits));
        send({method:'textDocument/didClose',params:{textDocument:{uri}}});
        const util=path.join(folder,'vendor/util'),core=path.join(folder,'vendor/core');fs.mkdirSync(util,{recursive:true});fs.mkdirSync(core,{recursive:true});
        fs.writeFileSync(path.join(folder,'assis.pkg'),'package app 1.0.0\ndep util 1.0.0 vendor/util\n');
        fs.writeFileSync(path.join(util,'assis.pkg'),'package util 1.0.0\ndep core 1.0.0 ../core\n');fs.writeFileSync(path.join(core,'assis.pkg'),'package core 1.0.0\n');
        fs.writeFileSync(path.join(core,'api.assis'),'namespace core;public pure assis answer():int{return 42;}');
        const utilText='#yuri <pkg/core/api.assis>\nnamespace util;public pure assis answer():int{return core::answer();}';fs.writeFileSync(path.join(util,'api.assis'),utilText);
        fs.writeFileSync(file,'#yuri <pkg/util/api.assis>\nassis assis_assis():int{print(util::answer());return 0;}');
        const locked=spawnSync(path.resolve(__dirname,'../bin',process.platform==='win32'?'assis.exe':'assis'),['lock',file],{encoding:'utf8',windowsHide:true});assert.equal(locked.status,0,locked.stderr);
        const utilUri=pathToFileURL(path.join(util,'api.assis')).href;send({method:'textDocument/didOpen',params:{textDocument:{uri:utilUri,languageId:'assisscript',version:1,text:utilText}}});
        await until(m=>m.method==='textDocument/publishDiagnostics'&&m.params.uri===utilUri&&m.params.version===1&&m.params.diagnostics.length===0);
        send({method:'textDocument/didChange',params:{textDocument:{uri:utilUri,version:2},contentChanges:[{text:utilText.replace('core::answer()','7')}]}});
        const lockedError=await until(m=>m.method==='textDocument/publishDiagnostics'&&m.params.uri===utilUri&&m.params.version===2&&m.params.diagnostics.length>0);assert.match(lockedError.params.diagnostics[0].message,/lockfile divergente/);
        await assert.rejects(request('unknownMethod'),/não suportado/);
        await request('shutdown');send({method:'exit'});child.stdin.end();await new Promise(resolve=>child.on('exit',()=>{closed=true;resolve();}));assert.equal(child.exitCode,0);assert.equal(stderr,'');
    } finally {if(!closed)child.kill();for(const w of waiting.values())clearTimeout(w.timer);fs.rmSync(folder,{recursive:true,force:true});}
});
