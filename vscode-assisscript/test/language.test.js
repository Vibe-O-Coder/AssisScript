'use strict';
const { test } = require('node:test');
const assert = require('node:assert/strict');
const path = require('node:path');
const l = require('../src/language');

test('receptores não viram argumentos explícitos e fatias conservam o tipo', () => {
    const text='ASSIS C{own b:*byte;assis ver(borrow self,n:int):borrow(self) slice<byte>{return fatia(self.b,0,n);}}';
    const m=l.analyze(text,'slice.assis');const fn=m.symbols.find(s=>s.name==='ver');
    assert.equal(fn.receiver,'borrow self');assert.equal(fn.params.length,1);assert.equal(fn.params[0].name,'n');
    assert.match(fn.type,/borrow\(self\) slice<byte>/);assert.equal(fn.safe,true);
    const exported=l.analyze('namespace x;public final ASSIS C{}','final.assis').symbols.find(s=>s.name==='x::C');
    assert.equal(exported.modulePrivate,false);
});

test('classes genéricas substituem métodos, construtores e bases antes da navegação', () => {
    const text = 'ASSIS Base<A,B>{private let segredo:A;let valor:B;assis ler(v:A):B{return self.valor;}}' +
        'ASSIS Filho<T,U> extends Base<U,T>{private let local:T;assis assis_fodase(v:T):void{self.local=v;}' +
        'assis obter():T{return self.local;}}' +
        'assis assis_assis():int{let c:Filho<int,bool>=new Filho<int,bool>(42);c.ler(true);print(c.valor,c.obter());return 0;}';
    const m = l.analyze(text, 'classes.assis');
    const child = m.symbols.find(s => s.name === 'Filho');
    assert.equal(child.base, 'Base<U, T>');
    assert.equal(m.symbols.find(s => s.name === 'local').kind, 'field');
    assert.equal(l.resolveSymbol(m, text.indexOf('c.valor') + 2, [m]).type, 'int');
    const read = l.resolveSymbol(m, text.indexOf('c.ler') + 2, [m]);
    assert.equal(read.type, 'int'); assert.equal(read.params[0].type, 'bool');
    assert.match(l.signatureAt(m, text.indexOf('(true)') + 2, [m]).label, /ler\(v: bool\): int/);
    assert.match(l.signatureAt(m, text.indexOf('(42)') + 2, [m]).label, /assis_fodase\(v: int\)/);
    assert.equal(l.resolveSymbol(m, text.indexOf('self.local') + 5, [m]).type, 'T');
    assert(!l.members([m], 'Filho<int, bool>').some(s => s.name === 'segredo' || s.name === 'local'));
    assert(!l.members([m], 'Filho<int, bool>', new Set(), 'Filho<T, U>').some(s => s.name === 'local'));
    assert(l.members([m], 'Filho<T, U>', new Set(), 'Filho<T, U>').some(s => s.name === 'local'));
    const cycle = l.analyze('ASSIS C<T> extends C<Array<T>>{}', 'cycle.assis');
    assert.deepEqual(l.members([cycle], 'C<int>'), []);
});

test('generics do usuário preservam navegação, campos concretos e assinaturas', () => {
    const text = 'struct Caixa<T> { let valor: T; private let segredo: int; } struct Par<A,B> { let a:A; let b:B; } pure assis id<T>(valor:T):T { return valor; } assis assis_assis():int { let c:Caixa<Array<int>>=new Caixa<Array<int>>([1]); print(c.valor); id::<HashMap<text, int>>(new HashMap<text, int>()); new Caixa<int>(42); return 0; }';
    const model = l.analyze(text, 'main.assis');
    const identity = model.symbols.find(s => s.name === 'id');
    assert.deepEqual(identity.typeParams, ['T']); assert.match(identity.label, /^pure id<T>/);
    assert.equal(l.resolveSymbol(model, text.indexOf('id::<') + 1, [model]).start, identity.start);
    assert.equal(l.resolveSymbol(model, text.indexOf('c.valor') + 2, [model]).type, 'Array<int>');
    assert.deepEqual(l.members([model], 'Par<byte, bool>').map(s => s.type), ['byte', 'bool']);
    assert(!l.members([model], 'Caixa<int>').some(s => s.name === 'segredo'));
    const call = l.signatureAt(model, text.indexOf('new HashMap<text, int>()') + 1, [model]);
    assert.match(call.label, /id<HashMap<text, int>>\(valor: HashMap<text, int>\)/);
    const constructor = l.signatureAt(model, text.lastIndexOf('42)') + 1, [model]);
    assert.match(constructor.label, /new Caixa<int>\(valor: int\)/);
    const nested = 'struct C<T>{let v:T;}assis id<T>(v:T):T{return v;}assis assis_assis():int{print(id::<C<int>>(new C<int>(1)).v);return 0;}';
    const n = l.analyze(nested, 'nested.assis');
    assert.equal(l.resolveSymbol(n, nested.lastIndexOf('.v') + 1, [n]).type, 'int');
});

test('val, pure e private preservam símbolos e visibilidade nominal', () => {
    const text = 'ASSIS C {private let oculto:int;let _publico:int;private assis interno():int{return self.oculto;}assis ler():int{return self.interno();}} ASSIS D extends C {} pure assis dobro(n:int):int{val d:int=n*2;return d;} assis assis_assis():int{let c:C=new C();print(c.oculto);return dobro(21);}';
    const model = l.analyze(text, 'main.assis');
    for (const word of ['val', 'pure', 'private']) assert(l.keywords[word]);
    assert.equal(model.symbols.find(s => s.name === 'd').immutable, true);
    assert.equal(model.symbols.find(s => s.name === 'n').immutable, true);
    assert.match(model.symbols.find(s => s.name === 'dobro').label, /^pure /);
    assert.deepEqual(l.members([model], 'C').map(s => s.name), ['_publico', 'ler']);
    assert(!l.members([model], 'D', new Set(), 'D').some(s => s.name === 'oculto'));
    assert(l.resolveSymbol(model, text.indexOf('self.oculto') + 5, [model]));
    assert(l.resolveSymbol(model, text.indexOf('self.interno') + 5, [model]));
    assert.equal(l.resolveSymbol(model, text.indexOf('c.oculto') + 2, [model]), undefined);
});

test('ownership e div têm referências e for limita a variável de inicialização', () => {
    const text='assis assis_assis():int { own a:Array<int>=[1]; div { borrow mut b:Array<int>=a; b.push(2); } for(let i:int=0;i<2;i+=1){print(i);} print(a[0]); return 0; }';
    const model=l.analyze(text,'main.assis');
    assert.equal(l.resolveSymbol(model,text.indexOf('b.push'),[model]).type,'Array<int>');
    assert(l.visibleSymbols(model,text.indexOf('print(i)'),[model]).some(s=>s.name==='i'));
    assert(!l.visibleSymbols(model,text.indexOf('print(a[0])'),[model]).some(s=>s.name==='i'));
    for(const word of ['own','borrow','mut','move','defer','div','for','ler_bytes','agora'])assert(l.keywords[word],word);
});
test('ignora strings e comentários aninhados, preservando posições UTF-16', () => {
    const text = 'miyabi assis FodaseAssis() {}\r\nte te interno to externo to\nassis AssisAssis(): FoDaSe { Fodase "😀 te miyabi"; }';
    const m = l.analyze(text, 'a.assis'); assert.deepEqual(m.symbols.map(s => s.name), ['AssisAssis']); assert.equal(m.symbols[0].start, text.indexOf('AssisAssis'));
});
test('resolve escopos, parâmetros, herança e membros com tipos', () => {
    const text = 'ASSIS AssisAssis { Assis AssisFodase: AssIs; assis Assis_assis(): AssIs { Fodase 42; } } ASSIS FodaseAssis ASSIS_FODASE AssisAssis {} assis assis_assis(): AssIs { Assis FodaseFodase: FodaseAssis = fodase FodaseAssis(); { Assis AssisFodase: FoDaSe = "a"; FODASE(AssisFodase); } FODASE(FodaseFodase.AssisFodase); Fodase 0; }';
    const m = l.analyze(text, 'a.assis');
    assert.equal(l.resolveSymbol(m, text.indexOf('FODASE(AssisFodase)') + 7, [m]).type, 'FoDaSe');
    const field = l.resolveSymbol(m, text.indexOf('FodaseFodase.AssisFodase') + 'FodaseFodase.'.length, [m]); assert.equal(field.kind, 'field'); assert.equal(field.owner, 'AssisAssis');
    assert.deepEqual(l.members([m], 'FodaseAssis').map(s => s.name), ['AssisFodase', 'Assis_assis']);
    assert(!l.visibleSymbols(m, text.indexOf('FODASE(FodaseFodase'), [m]).some(s => s.name === 'AssisFodase'));
});
test('assinaturas contam argumentos sem contar chamadas internas', () => {
    const text = 'assis AssisAssis(AssisFodase: AssIs, FodaseAssis: AssIs): AssIs { Fodase 0; } assis assis_assis(): AssIs { Fodase AssisAssis(AssIs(1), 2); }';
    const m = l.analyze(text, 'a.assis'), found = l.signatureAt(m, text.lastIndexOf('2)') + 1, [m]); assert.equal(found.active, 1); assert.equal(found.params.length, 2);
});
test('coleta imports transitivos e fontes não salvos', () => {
    const entry = path.resolve('teste/main.assis'), dep = path.resolve('teste/lib.assis');
    const options = { overlays: new Map([[entry, 'importa "lib"; assis assis_assis(): AssIs { Fodase AssisAssis(); }'], [dep, 'assis AssisAssis(): AssIs { Fodase 42; }']]) };
    const models = l.collectProject(entry, options); assert.equal(models.length, 2);
    const resolved = l.resolveSymbol(models[0], models[0].text.lastIndexOf('AssisAssis'), models); assert.equal(resolved.file, dep);
});
test('cadeias de campos e retornos de método conservam o tipo do receptor', () => {
    const text = 'ASSIS AssisAssis { Assis AssisFodase: AssisAssis; assis Assis_assis(): AssisAssis { Fodase aSSIS; } } assis assis_assis(): AssIs { Assis FodaseAssis: AssisAssis = fodase AssisAssis(); FODASE(FodaseAssis.Assis_assis().AssisFodase.AssisFodase); Fodase 0; }';
    const m = l.analyze(text, 'a.assis'); const offset = text.lastIndexOf('.AssisFodase') + 1; assert.equal(l.resolveSymbol(m, offset, [m]).kind, 'field');
});

test('tipos genéricos concretos, structs e membros indexados têm documentação técnica', () => {
    const text = 'struct Pessoa { let nome: text; } assis assis_assis(): int { let pessoas: Array<Pessoa> = []; let mapa: HashMap<text, Array<int>> = new HashMap<text, Array<int>>(); pessoas.push(new Pessoa("Miyabi")); print(pessoas[0].nome); mapa.get("x").push(42); return 0; }';
    const m = l.analyze(text, 'main.assis');
    assert(m.symbols.find(s => s.name === 'Pessoa').record);
    assert.equal(m.symbols.find(s => s.name === 'mapa').type, 'HashMap<text, Array<int>>');
    const push = l.resolveSymbol(m, text.indexOf('pessoas.push') + 'pessoas.'.length, [m]);
    assert.equal(push.params[0].type, 'Pessoa'); assert.match(push.documentation, /amortizado/);
    assert.equal(l.resolveSymbol(m, text.indexOf('pessoas[0].nome') + 'pessoas[0].'.length, [m]).type, 'text');
    const returned = l.resolveSymbol(m, text.lastIndexOf('.push') + 1, [m]); assert.equal(returned.params[0].type, 'int');
    const constructor = l.signatureAt(m, text.indexOf('"Miyabi"') + 2, [m]); assert.match(constructor.label, /nome: text/);
    const generic = l.members([m], 'HashMap<text, Array<int>>').find(s => s.name === 'get'); assert.equal(generic.type, 'Array<int>');
});
test('literais, construtores genéricos e alloc não atrapalham ajuda de parâmetros', () => {
    const text = 'assis exemplo(a: HashMap<text, int>, b: int): void {} assis assis_assis(): int { exemplo(new HashMap<text, int>(), 42); let a: Array<int> = new Array<int>(); a.push(9); let p: *int = alloc<int>(5); return 0; }';
    const m = l.analyze(text, 'main.assis');
    assert.equal(l.signatureAt(m, text.indexOf('42)') + 1, [m]).active, 1);
    assert.match(l.signatureAt(m, text.indexOf('int>();') + 'int>('.length, [m]).label, /new Array<int>/);
    assert.match(l.signatureAt(m, text.indexOf('(5)') + 2, [m]).documentation, /buffer zerado/);
    const ctor = 'assis assis_assis(): int { new Array<int>().push(42); return 0; }'; const c = l.analyze(ctor, 'main.assis');
    assert.equal(l.resolveSymbol(c, ctor.indexOf('.push') + 1, [c]).params[0].type, 'int');
});
test('documentação ///, miyabi e bloco inclui parâmetros e retorno de bibliotecas', () => {
    const source = '/// Retorna o dobro.\n/// @param valor Inteiro de entrada.\n/// @return Inteiro multiplicado por dois.\nassis dobro(valor: int): int { return valor * 2; }\n/** Retorna o triplo. */\nassis triplo(valor: int): int { return valor * 3; }';
    const m = l.analyze(source, 'lib.assis');
    assert.match(m.symbols.find(s => s.name === 'dobro').documentation, /@param valor/);
    assert.match(m.symbols.find(s => s.name === 'triplo').documentation, /Retorna o triplo/);
    assert.match(l.builtinSignatures.len.documentation, /HashMap/);
});
test('#body, #yuri e caminhos pontuados coletam docs de dependências não salvas', () => {
    const entry = path.resolve('v3/main.assis'), pkg = path.resolve('v3/meu/pacote.pillow'), lib = path.resolve('v3/lib.assis');
    const overlays = new Map([[entry, '#body meu.pacote.pillow\nassis assis_assis(): int { return dobro(21); }'], [pkg, '#yuri <../lib.assis>\n'], [lib, '/// Retorna o dobro com overflow modular.\nassis dobro(valor: int): int { return valor * 2; }']]);
    const models = l.collectProject(entry, { overlays }); assert.equal(models.length, 3);
    const symbol = l.resolveSymbol(models[0], models[0].text.indexOf('dobro'), models); assert.equal(symbol.file, lib); assert.match(symbol.documentation, /overflow modular/);
});
test('tipos de callback preservam parâmetros, retorno, efeitos e assinatura indireta', () => {
    const text = 'pure assis aplicar<T>(f:pure assis(T, T):T,v:T):T{return f(v,v);}' +
        'pure assis obter():pure assis(int):int{return dobro;}' +
        'assis assis_assis():int{val f:pure assis(int, int):int=somar;return f(1,2);}';
    const m = l.analyze(text, 'callbacks.assis');
    const apply = m.symbols.find(s => s.name === 'aplicar');
    assert.deepEqual(apply.params.map(p => p.type), ['pure assis(T, T): T', 'T']);
    assert.equal(m.symbols.find(s => s.name === 'obter').type, 'pure assis(int): int');
    assert.deepEqual(l.signatureAt(m, text.lastIndexOf('2)') + 1, [m]).params, ['arg1: int', 'arg2: int']);
    assert.equal(l.signatureAt(m, text.lastIndexOf('2)') + 1, [m]).active, 1);
    assert.equal(l.resolveSymbol(m, text.lastIndexOf('f(1'), [m]).immutable, true);
});

test('ownership em parâmetros e retornos conserva contratos e navegação', () => {
    const text = 'struct Caixa<T>{own valor:T;}safe assis criar<T>(own v:T):own Caixa<T>{return new Caixa<T>(move(v));}' +
        'safe assis ver(borrow c:Caixa<int>):borrow(c) Caixa<int>{return c;}' +
        'safe assis assis_assis():int{own c:Caixa<int>=criar::<int>(42);print(ver(c).valor);return 0;}';
    const m = l.analyze(text, 'vidas.assis'), create = m.symbols.find(s => s.name === 'criar');
    assert.equal(create.params[0].ownership, 'own');
    assert.equal(create.type, 'own Caixa<T>');
    assert.equal(m.symbols.filter(s => s.name === 'v' && s.kind === 'parameter').length, 1);
    assert.equal(m.symbols.filter(s => s.name === 'v' && s.kind === 'variable').length, 0);
    const field = l.resolveSymbol(m, text.lastIndexOf('valor'), [m]);
    assert.equal(field.type, 'int');
    assert.match(l.signatureAt(m, text.indexOf('(42)') + 2, [m]).label, /safe criar<int>\(own v: int\): own Caixa<int>/);
});

test('callbacks safe preservam modos aninhados e origem da vida', () => {
    const text = 'assis f(cb:safe assis(borrow Array<int>, own Array<int>):borrow(0) Array<int>):void{' +
        'own a:Array<int>=[1];borrow b:Array<int>=cb(a,[2]);}';
    const m = l.analyze(text, 'callback-vidas.assis'), f = m.symbols.find(s => s.name === 'f');
    assert.equal(f.params[0].type, 'safe assis(borrow Array<int>, own Array<int>): borrow(0) Array<int>');
    assert.deepEqual(l.signatureAt(m, text.indexOf('[2]') + 3, [m]).params, ['arg1: borrow Array<int>', 'arg2: own Array<int>']);
});

test('valores, variantes e vínculos de match preservam tipos e escopos', () => {
    const text = 'value struct P{let x:int;}enum O<T>{None;Some(T);}' +
        'assis f(o:O<P>):int{match(o){None{return 0;}Some(p){return p.x;}}}' +
        'assis assis_assis():int{val o:O<P>=new O<P>.Some(new P(42));return f(o);}';
    const model = l.analyze(text, 'valores.assis');
    assert.equal(model.symbols.find(s => s.name === 'P').value, true);
    assert.equal(model.symbols.find(s => s.name === 'O').tagged, true);
    const p = model.symbols.find(s => s.pattern && s.name === 'p');
    assert.equal(p.type, 'P'); assert.equal(p.immutable, true);
    assert.equal(l.resolveSymbol(model, text.indexOf('p.x') + 2, [model]).type, 'int');
    const signature = l.signatureAt(model, text.indexOf('.Some(') + 6, [model]);
    assert.match(signature.label, /new O<P>\.Some\(arg1: P\)/);
    assert.equal(l.visibleSymbols(model, text.lastIndexOf('return f'), [model]).some(s => s.pattern), false);
    const imported = l.analyze('enum O<T>{None;Some(T);}', 'lib.assis');
    const main = l.analyze('value struct P{let x:int;}assis f(o:O<P>):int{match(o){None{return 0;}Some(p){return p.x;}}}', 'main.assis');
    assert.equal(l.resolveSymbol(main, main.text.indexOf('p.x') + 2, [main, imported]).type, 'int');
});
