'use strict';
const test=require('node:test'),assert=require('node:assert/strict');
const path=require('node:path'),fs=require('node:fs'),os=require('node:os');
const htdl=require('../vscode-assisscript/src/htdl');
const compiler=process.env.ASSIS_BIN || path.resolve(__dirname,'../bin',process.platform==='win32'?'assis.exe':'assis');
test('HTDL: protocolo limitado e ranges UTF-16 multilinha',()=>{
    assert.deepEqual(htdl.parseOutput('0 0\n'),[]);
    const result=htdl.parseOutput('1 0\n206 10 22 2 3 3 4\n');
    assert.deepEqual(result[0].range,{start:{line:1,character:2},end:{line:2,character:3}});
    for(const input of ['65 0','1 0\n999 0 1 1 1 1 2','1 0\n206 1 0 1 1 1 1','0 3','0 1','1 0','1 0\n206 0 1 2 1 1 1'])assert.throws(()=>htdl.parseOutput(input));
    assert.equal(htdl.parseOutput('64 1\n'+Array(64).fill('206 0 1 1 1 1 2').join('\n')).at(-1).code,'H402');
});
test('HTDL: analisador nativo usa rascunho e não abre script ou recurso',async()=>{
    const doc=body=>`<div type=document version="0.1" lang=en><div type=head><div type=title>Catalog</div><div type=script src="./not-found.assis" format=source></div></div><div type=body>${body}</div></div>`;
    assert.deepEqual(await htdl.check(compiler,doc('<div type=image src="./not-found.png" alt=""></div>')),[]);
    const errors=await htdl.check(compiler,doc('<div type=heading>Title</div><div type=label>Missing target</div>'));
    assert.deepEqual(errors.map(d=>d.code).slice(0,2),['H206','H206']);
    assert.equal((await htdl.check(compiler,'x'.repeat(1048577)))[0].code,'H401');
});
test('HTDL: cancelamento recolhe processo e arquivos temporários',async()=>{
    const before=new Set(fs.readdirSync(os.tmpdir()).filter(n=>n.startsWith('assis-htdl-editor-')));
    for(const delay of [0,20]){
        const controller=new AbortController();if(!delay)controller.abort();
        const checking=htdl.check(compiler,'invalid',{signal:controller.signal});
        const timer=delay?setTimeout(()=>controller.abort(),delay):undefined;
        try{await assert.rejects(checking,{name:'AbortError'});}finally{clearTimeout(timer);}
    }
    const after=fs.readdirSync(os.tmpdir()).filter(n=>n.startsWith('assis-htdl-editor-')&&!before.has(n));
    assert.deepEqual(after,[]);
});

test('HTDL: recuperação sintática entrega erros posteriores com ranges Unicode',async()=>{
    const source='<div type=document version="0.1" lang=en><div type=head><div type=title>🙂</div></div><div type=body><div type=paragraph>é &wrong;\r\n&also;</div></div></div>';
    const errors=await htdl.check(compiler,source);
    assert.deepEqual(errors.map(d=>d.code),['H102','H102']);
    for(const [index,name] of ['&wrong;','&also;'].entries()){
        const prefix=source.slice(0,source.indexOf(name)).replace(/\r\n?/g,'\n');
        assert.deepEqual(errors[index].range.start,{line:prefix.split('\n').length-1,character:prefix.split('\n').at(-1).length});
    }
});
