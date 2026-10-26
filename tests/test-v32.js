'use strict';
const {test, after} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const {spawnSync} = require('node:child_process');
const root = path.resolve(__dirname, '..');
const compiler = process.env.ASSIS_BIN || path.join(root, 'bin', process.platform === 'win32' ? 'assis.exe' : 'assis');
const temp = fs.mkdtempSync(path.join(os.tmpdir(), 'assis-v32-'));
after(() => {assert(path.dirname(temp) === path.resolve(os.tmpdir()) && path.basename(temp).startsWith('assis-v32-')); fs.rmSync(temp, {recursive:true, force:true});});
function invoke(args, options={}) {
    const r = spawnSync(compiler, args, {encoding:'utf8', windowsHide:true, timeout:30000,...options}); assert.ifError(r.error);
    if(process.env.ASSIS_V32_FIXTURE_DIR){
        const directory=path.resolve(process.env.ASSIS_V32_FIXTURE_DIR);fs.mkdirSync(directory,{recursive:true});
        const name=String(invoke.fixture=(invoke.fixture||0)+1).padStart(3,'0');
        const input=options.input===undefined?Buffer.alloc(0):Buffer.from(options.input);
        fs.writeFileSync(path.join(directory,name+'.assis'),fs.readFileSync(args[1]));
        fs.writeFileSync(path.join(directory,name+'.json'),JSON.stringify({args:[args[0],...args.slice(2)],input:input.toString('base64'),status:r.status,stdout:r.stdout,stderr:r.stderr,sourcePath:args[1]}));
    }
    return r;
}
let serial = 0;
function source(text) {const file=path.join(temp, `${++serial}.assis`); fs.writeFileSync(file,text); return file;}
function execute(text, expected='', options=['--debug']) {
    const file=source(text);
    for(const flags of [[], ['--no-opt']]) {const r=invoke(['run',file,...options,...flags]); assert.equal(r.status,0,r.stderr); assert.equal(r.stdout,expected); assert.equal(r.stderr,'');}
}
const record='struct P { let x: int; }\n';
const main=body=>`assis assis_assis(): int { ${body} return 0; }`;
test('own, borrow, borrow mut, move e div liberam recursos sem GC',()=>{
    execute(record+main(`own p: P = new P(42);
div { borrow a: P = p; borrow b: P = p; print(a.x, b.x); }
div { borrow mut a: P = p; a.x += 1; }
own outro: P = move(p); print(outro.x);
div { own a: Array<int> = [1,2]; div { borrow mut b: Array<int> = a; b.push(3); } print(a[2]); }
own m: HashMap<int,int> = new HashMap<int,int>(); m.set(1,7);
div { borrow r: HashMap<int,int> = m; print(r.get(1)); }`),'42 42\n43\n3\n7\n');
});
test('limpeza funciona em return, break, continue e for aninhado',()=>{
    execute(record+`assis value(): int {
own p: P = new P(91);
for(let i:int=0; i<8; i+=1) {
 own a:Array<int>=[i];
 for(let j:int=0;j<3;j+=1) { own b:*int=alloc<int>(2); if(j==1){break;} }
 if(i==2){continue;} if(i==5){return p.x;}
}
return 0;}
`+main('print(value());'),'91\n');
});
test('free consome own e zera o slot, inclusive em ramos distintos',()=>{
    execute(record+main('own p:P=new P(1); if(p.x==1){free(p);} else {own q:P=move(p); print(q.x);}'));
});
test('defer free captura uma variável estável e libera no retorno',()=>{
    execute(`assis value(): int { let p:*int=alloc<int>(2); defer free(p); p[0]=72; return p[0]; }`+main('print(value());'),'72\n');
    execute('#yuri <std/strings.assis>\n'+main('let t:String=new String();defer free(t);t.append("oi");print(t.view());t.dispose();let p:*int=alloc<int>(1);defer free(p);*p=12;print(*p);'),'oi\n12\n');
});
test('ownership rejeita alias, fuga, free duplo e conflitos de empréstimo',()=>{
    const cases=[
        ['own p:P=new P(); let q:P=p;',/escapar/],
        ['own p:P=new P(); own q:P=move(p); print(p.x);',/movido/],
        ['own p:P=new P(); free(p); free(p);',/movido|liberado/],
        ['own p:P=new P(); borrow a:P=p; a.x=2;',/mutação/],
        ['own p:P=new P(); borrow a:P=p; p.x=2;',/mutação/],
        ['own p:P=new P(); borrow a:P=p; free(p);',/borrow ativo/],
        ['own p:P=new P(); borrow a:P=p; own q:P=move(p);',/borrow ativo/],
        ['own p:P=new P(); borrow a:P=p; borrow mut b:P=p;',/incompatível/],
        ['own p:P=new P(); borrow mut a:P=p; print(p.x);',/borrow mut ativo/],
        ['own p:P=new P(); borrow mut a:P=p; borrow b:P=p;',/incompatível/],
        ['own p:P=new P(); borrow a:P=p; free(a);',/somente own/],
        ['own p:P=new P(); p=new P();',/reatribuída/],
        ['own p:P=new P(); own q:P=p;',/alocação nova/],
        ['let p:P=new P(); borrow a:P=p;',/borrow exige/],
        ['own p:P=new P(); let a:*int=&p.x;',/ponteiro gerenciado/],
        ['own p:*int=alloc<int>(1); let q:*int=p+1;',/ponteiro gerenciado/],
        ['own p:*int=alloc<int>(1); print(*p);',/ponteiro gerenciado/],
        ['own p:*byte=alloc<byte>(2); print(text(p));',/ponteiro gerenciado/],
        ['own p:P=new P(); while(true){free(p);break;}',/externo.*laço/],
        ['own p:P=new P(); if(true){free(p);} print(p.x);',/movido/],
        ['let p:P=new P(); defer free(p); free(p);',/defer/],
        ['let p:P=new P(); defer free(p); p=new P();',/reatribuída/],
        ['own a:Array<int>=[1]; borrow b:Array<int>=a; b.push(2);',/mutação/],
        ['own a:Array<int>=[1]; borrow b:Array<int>=a; a.clear();',/mutação/],
        ['own a:Array<int>=[1]; a.dispose();',/método não permitido/],
        ['own p:P=new P(); consumir(p);',/escapar/],
        ['own p:P=new P(); move(p);',/move só/]
    ];
    for(const [body,message] of cases){
        const file=source(record+'assis consumir(p:P):void {}\n'+main(body));
        const r=invoke(['check',file,'--diagnostics=json']); assert.equal(r.status,1,body+'\n'+r.stderr);
        const diagnostic=JSON.parse(r.stderr); assert.match(diagnostic.message,message,body); assert.equal(diagnostic.code,'A001');
    }
    const escaping=invoke(['check',source(record+'assis fuga():P {own p:P=new P();return p;}'+main(''))]);assert.equal(escaping.status,1);assert.match(escaping.stderr,/escapar/);
});
test('buffers gerenciados verificam limites inclusive zero e negativos',()=>{
    execute(main('own p:*int=alloc<int>(2); div {borrow mut q:*int=p; q[1]=63;} print(p[0],p[1]);'),'0 63\n');
    for(const [count,index] of [[0,0],[2,-1],[2,2]])for(const flags of [[],['--no-opt']]){
        const r=invoke(['run',source(main(`own p:*int=alloc<int>(${count}); print(p[${index}]);`)),...flags]);assert.equal(r.status,70,r.stderr);assert.match(r.stderr,/limite/);
    }
});
test('alocador reutiliza todas as classes, zera blocos e atravessa slabs',()=>{
    execute(record+main(`let slots:*P=alloc<P>(5000); let i:int=0;
while(i<5000){slots[i]=new P(i);i+=1;} i=0;
while(i<5000){assert(slots[i].x==i);free(slots[i]);i+=1;} free(slots);
let size:int=0; while(size<70000){let p:*byte=alloc<byte>(size);if(size>0){assert(p[0]==0 && p[size-1]==0);p[0]=byte(255);}free(p);if(size==0){size=1;}else{size*=2;}}
for(let j:int=0;j<5000;j+=1){own p:P=new P();assert(p.x==0);}`));
});
test('debug detecta vazamentos e free duplo pequeno/grande',()=>{
    const leak=invoke(['run',source(record+main('let p:P=new P();')),'--debug']);assert.equal(leak.status,70);assert.match(leak.stderr,/1.*alocacoes nao liberadas/s);
    for(const size of [16,65536]){const r=invoke(['run',source(main(`let p:*byte=alloc<byte>(${size});free(p);free(p);`)),'--debug']);assert.equal(r.status,70);assert.match(r.stderr,/free duplo/);}
});
test('recursão extrema termina com diagnóstico em vez de falha do sistema',()=>{
    for(const flags of [[],['--no-opt']]){
        const r=invoke(['run',source('assis rec(n:int):int {if(n==0){return 0;}return rec(n-1); }'+main('print(rec(10000000));')),...flags]);assert.equal(r.status,70,r.stderr);assert.match(r.stderr,/pilha/);
    }
});
test('divisão/resto constantes coincidem com BigInt em todos os sinais e larguras',()=>{
    const values=[0n,1n,-1n,3n,-3n,9223372036854775807n,-9223372036854775808n,123456789012345n,-123456789012345n];
    const divisors=[1n,-1n,3n,-7n,...Array.from({length:63},(_,i)=>1n<<BigInt(i+1)),...Array.from({length:62},(_,i)=>-(1n<<BigInt(i+1)))];
    let body='',expected='';
    for(const d of divisors)for(const n of values){
        body+=`{let n:int=${n};let q:int=n;let r:int=n;q/=${d};r%=${d};print(n/${d},n%${d},q,r);}\n`;
        const divisor=BigInt.asIntN(64,d),q=BigInt.asIntN(64,n/divisor),r=n%divisor;expected+=`${q} ${r} ${q} ${r}\n`;
    }
    execute(main(body),expected);
});
test('comparações fundidas preservam curto-circuito e ordem de avaliação',()=>{
    execute(`assis efeito(p:*int):int{*p+=1;return *p;}`+main(`let n:int=0;let a:int=0;
for(let i:int=-3;i<4;i+=1){if(i<0){a+=1;}if(i<=0){a+=2;}if(i>0){a+=4;}if(i>=0){a+=8;}if(i!=0){a+=16;}if(i==0){a+=32;}}
if(efeito(&n)<efeito(&n)){print(n,a);}if(false && efeito(&n)==3){print(0);}print(n);`),'2 183\n2\n');
});
test('teste de resto zero por máscara funciona para negativos e INT64_MIN',()=>{
    const values=[-9223372036854775808n,-17n,-2n,-1n,0n,1n,2n,17n,9223372036854775807n];
    const divisors=[1n,-1n,2n,-2n,8n,-8n,-9223372036854775808n];let body='',expected='';
    for(const n of values)for(const d of divisors){
        body+=`{let n:int=${n};if(n%${d}==0){print(1);}else{print(0);}if(n%${d}!=0){print(2);}else{print(3);}}`;
        expected+=n%d===0n?'1\n3\n':'0\n2\n';
    }
    execute(main(body),expected);
});
test('text local/param usa comprimento estável e ponteiro para slot invalida cache',()=>{
    const value='a'.repeat(30000);
    execute(`assis soma(s:text):int {let n:int=0;for(let i:int=0;i<len(s);i+=1){n+=s[i];}return n;}`+main(`let s:text="${value}";print(soma(s));s="ação";print(len(s),s[1]);let p:*text=&s;*p="abcdef";print(len(s),s[5]);`),'2910000\n6 195\n6 102\n');
    for(const index of [-1,3]){const r=invoke(['run',source(main(`let s:text="abc";print(s[${index}]);`))]);assert.equal(r.status,70);assert.match(r.stderr,/texto fora do limite/);}
});
test('registradores preservam valores em chamadas, recursão e alias de locais',()=>{
    execute('assis fib(n:int):int {if(n<2){return n;}return fib(n-1)+fib(n-2);}\n'+main('let a:int=11;let b:int=13;let c:int=17;let d:int=19;let p:*int=&a;*p=23;let v:byte=byte(255);v+=1;print(a,b,c,d,fib(20),v);'),'23 13 17 19 6765 0\n');
});
test('texto concatena, divide, junta e substitui preservando UTF-8 e partes vazias',()=>{
    execute('#yuri <std/strings.assis>\n'+main(`
let c:String=concat("ação", "! "); print(c.view()); c.dispose();free(c);
let a:Array<text>=["a", "", "ç"];let j:String=join(a,"|");print(j.view());j.dispose();free(j);free(a);
let partes:Array<String>=split("::ação::::x::", "::");print(len(partes));
for(let i:int=0;i<len(partes);i+=1){let p:String=partes[i];print(p.view());p.dispose();free(p);}free(partes);
let r:String=replace("aaaaa ação ação", "aa", "b");print(r.view());r.dispose();free(r);
let e:String=replace("açãoação", "ação", "");assert(e.size()==0);e.dispose();free(e);
let vazias:Array<String>=split("", ",");assert(len(vazias)==1);let v:String=vazias[0];assert(v.size()==0);free(v);free(vazias);
`),'ação! \na||ç\n5\n\nação\n\nx\n\nbba ação ação\n');
});
test('read_bytes lê entrada binária, EOF e respeita capacity de own',()=>{
    const file=source(main('own b:*byte=alloc<byte>(8);let n:int=read_bytes(b,8);print(n,b[0],b[1],b[2]);print(read_bytes(b,8));'));
    for(const flags of [[],['--no-opt']]){const r=invoke(['run',file,'--debug',...flags],{input:Buffer.from([65,0,255])});assert.equal(r.status,0,r.stderr);assert.equal(r.stdout,'3 65 0 255\n0\n');}
    const bad=invoke(['run',source(main('own b:*byte=alloc<byte>(1);print(read_bytes(b,2));'))],{input:'abc'});assert.equal(bad.status,70);assert.match(bad.stderr,/alocação inválido/);
    const shared=invoke(['check',source(main('own b:*byte=alloc<byte>(8);borrow r:*byte=b;read_bytes(r,8);'))]);assert.equal(shared.status,1);assert.match(shared.stderr,/exclusivo/);
});
test('read_line preserva rows sucessivas e monotonic_ms é monotônico em milissegundos',()=>{
    const file=source('#yuri <std/strings.assis>\n'+main('let start:int=monotonic_ms();for(let i:int=0;i<4;i+=1){let linha:String=read_line();print(linha.view());linha.dispose();free(linha);}assert(start>=0 && monotonic_ms()>=start);'));
    for(const flags of [[],['--no-opt']]){const r=invoke(['run',file,'--debug',...flags],{input:'ação\r\n\nultima'});assert.equal(r.status,0,r.stderr);assert.equal(r.stdout,'ação\n\nultima\n\n');}
});
