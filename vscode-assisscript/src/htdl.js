'use strict';
// Protocol/IDE adapter only. All syntax and semantic analysis is AssisScript.
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const { spawn } = require('node:child_process');
const types = ['document','head','title','body','container','paragraph','text','heading','button','meta','script','main','section','header','footer','nav','link','list','item','label','input','form','image'];
const attributes = ['type','version','lang','level','id','class','hidden','disabled','action','a11y-label','name','content','src','format','href','ordered','for','kind','value','placeholder','required','checked','alt','a11y-live','data-','on:click','on:input','on:change','on:submit','on:focus','on:blur'];
const messages = { 101:'UTF-8 ou caractere inválido.',102:'Sintaxe HTDL inválida ou incompleta.',200:'Versão HTDL não suportada.',201:'O atributo type é obrigatório.',202:'Atributo repetido.',203:'Tipo, atributo ou recurso fora deste perfil.',204:'Modelo de conteúdo ou estrutura inválida.',205:'Identificador ou nome de controle duplicado.',206:'Atributo obrigatório, valor ou nome acessível inválido.',207:'Rótulo ou nome acessível sem associação válida.',301:'Evento declarado sem script. A assinatura da função será verificada pelo loader.',401:'Limite de fonte, memória ou trabalho excedido.' };
function parseOutput(text) {
    const lines = text.trim().split(/\r?\n/), header = lines.shift()?.split(/\s+/).map(Number);
    if (header?.length !== 2 || !Number.isInteger(header[0]) || header[0] < 0 || header[0] > 64 || ![0,1].includes(header[1]) || (header[1] && header[0]!==64) || lines.length !== header[0]) throw new Error('Resposta inválida do analisador HTDL.');
    const result = lines.map(line => {
        const v = line.split(/\s+/).map(Number);
        if (v.length !== 7 || v.some(n => !Number.isSafeInteger(n)) || !messages[v[0]] || v[1] < 0 || v[2] < v[1] || v.slice(3).some(n => n < 1) || v[5] < v[3] || (v[5] === v[3] && v[6] < v[4])) throw new Error('Diagnóstico HTDL inválido.');
        return { code: `H${v[0]}`, severity: 1, source: 'HTDL static-catalog-0.1-v1', message: messages[v[0]], range: { start: { line:v[3]-1,character:v[4]-1 }, end: { line:v[5]-1,character:v[6]-1 } } };
    });
    if (header[1]) result.push({ code:'H402',severity:2,source:'HTDL',message:'Exibidos os primeiros 64 erros; corrija-os para continuar a análise.',range:{start:{line:0,character:0},end:{line:0,character:0}} });
    return result;
}
async function check(compiler, text, { signal, toolSource } = {}) {
    if (Buffer.byteLength(text,'utf8') > 1048576) return [{code:'H401',severity:1,source:'HTDL',message:messages[401],range:{start:{line:0,character:0},end:{line:0,character:0}}}];
    const tool = toolSource || [path.resolve(__dirname,'../../tools/htdl-check.assis'),path.resolve(__dirname,'../tools/htdl-check.assis')].find(p=>fs.existsSync(p));
    if (!tool) throw new Error('Instale tools/htdl-check.assis e a biblioteca HTDL da mesma revisão.');
    const folder=await fs.promises.mkdtemp(path.join(os.tmpdir(),'assis-htdl-editor-'));
    const binary=path.join(folder,process.platform==='win32'?'checker.exe':'checker'),deadline=Date.now()+15000;
    // Build trusted fixed source, then own the analyzer process directly. Abort
    // never leaves an analyzer grandchild under a terminated `assis run` parent.
    async function execute(command,args,input='') {
        return await new Promise((resolve,reject)=>{
            const child=spawn(command,args,{cwd:path.dirname(tool),windowsHide:true,shell:false,signal});
            let stdout='',stderr='',failure;
            const timer=setTimeout(()=>{failure=new Error('Análise HTDL interrompida pelo limite do editor.');child.kill();},Math.max(1,deadline-Date.now()));
            child.stdout.setEncoding('utf8');child.stderr.setEncoding('utf8');
            child.stdout.on('data',data=>{stdout+=data;if(Buffer.byteLength(stdout)>65536){failure=new Error('Saída HTDL excedeu o limite.');child.kill();}});
            child.stderr.on('data',data=>{stderr+=data;if(Buffer.byteLength(stderr)>65536){failure=new Error('Saída HTDL excedeu o limite.');child.kill();}});
            child.on('error',error=>{failure=error;});
            child.on('close',code=>{clearTimeout(timer);failure?reject(failure):code!==0?reject(new Error(stderr||'Falha no analisador HTDL.')):resolve(stdout);});
            child.stdin.on('error',()=>{});child.stdin.end(input,'utf8');
        });
    }
    try {
        await execute(compiler,['build',tool,'--safe','--debug','-o',binary]);
        return parseOutput(await execute(binary,[],text));
    } finally { await fs.promises.rm(folder,{recursive:true,force:true,maxRetries:3,retryDelay:100}); }
}
module.exports={check,parseOutput,types,attributes};
