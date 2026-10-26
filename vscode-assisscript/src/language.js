'use strict';
const fs = require('node:fs');
const path = require('node:path');
const reference = require('./reference.json');

const keywords = {
    ASSIS: 'Declara uma classe.', ASSIS_FODASE: 'Herança simples entre classes.',
    assis: 'Declara função ou método.', Assis: 'Declara variável ou campo com tipo explícito.',
    AssIs: 'Inteiro com sinal de 64 bits; overflow modular.', AssiS: 'Byte sem sinal, de 0 a 255.',
    FodAsE: 'Booleano.', FoDaSe: 'Texto imutável em UTF-8.', FODase: 'Retorno sem valor.',
    assIS: 'Executa um bloco quando a condição é verdadeira.', fodASE: 'Bloco alternativo.',
    ASSis: 'Repete enquanto a condição for verdadeira.', Fodase: 'Retorna da função.',
    FODASE: 'Imprime valores separados por espaço e termina a linha.',
    fodase: 'Aloca e inicializa um objeto.', foDASE: 'Libera um objeto ou ponteiro.',
    aSSIS: 'Instância atual dentro de um método.', aSsIs: 'Verdadeiro.', fOdAsE: 'Falso.', fOdase: 'Nulo.',
    FODasE: 'Interrompe o laço.', FodASE: 'Continua a próxima iteração.',
    ASSIS_fodase: 'Aloca uma quantidade de bytes zerados e retorna *AssiS.',
    FODASE_fodase: 'Conta bytes UTF-8 até o primeiro byte nulo.',
    importa: 'Inclui um módulo na compilação. Exemplo: importa "std/matematica";',
    miyabi: 'Comentário até o final da linha.', te: 'Abre comentário de bloco; aceita aninhamento.', to: 'Fecha comentário de bloco.'
};
const builtinSignatures = {
    FODASE: { label: 'FODASE(valores...)', params: ['valores...'] },
    foDASE: { label: 'foDASE(AssisAssis: objeto ou ponteiro): FODase', params: ['AssisAssis: objeto ou ponteiro'] },
    ASSIS_fodase: { label: 'ASSIS_fodase(AssisAssis: AssIs): *AssiS', params: ['AssisAssis: AssIs'] },
    FODASE_fodase: { label: 'FODASE_fodase(AssisAssis: FoDaSe): AssIs', params: ['AssisAssis: FoDaSe'] },
    ...Object.fromEntries(['AssIs', 'AssiS', 'FodAsE'].map(name => [name, { label: `${name}(AssisAssis: inteiro ou booleano): ${name}`, params: ['AssisAssis: inteiro ou booleano'] }]))
};
Object.assign(keywords, reference.keywords);
Object.assign(builtinSignatures, reference.signatures);
for (const [name, signature] of Object.entries(builtinSignatures)) signature.documentation = keywords[name];
for (const [legacy, readable] of Object.entries({ FODASE: 'print', foDASE: 'free', FODASE_fodase: 'len', AssIs: 'int', AssiS: 'byte', FodAsE: 'bool' })) {
    keywords[legacy] = keywords[readable]; builtinSignatures[legacy].documentation = keywords[readable];
}
const stripOwnership = type => (type || '').replace(/^(?:own\s+|borrow(?:\s+mut)?(?:\([^)]*\))?\s+)/, '');
const parameterLabel = p => `${p.ownership ? p.ownership + ' ' : ''}${p.name}: ${p.type}`;
function genericParts(type) {
    type = stripOwnership(type);
    const found = /^([A-Za-z_]\w*(?:::[A-Za-z_]\w*)*)<(.*)>$/.exec(type || ''); if (!found) return undefined;
    const params = []; let depth = 0, start = 0;
    for (let i = 0; i < found[2].length; i++) { const c = found[2][i]; if ('<('.includes(c)) depth++; if ('>)'.includes(c)) depth--; if (c === ',' && depth === 0) { params.push(found[2].slice(start, i).trim()); start = i + 1; } }
    params.push(found[2].slice(start).trim()); return { kind: found[1], params };
}
function substituteType(type, names = [], args = []) {
    const substitutions = new Map(names.map((name, i) => [name, args[i] || name]));
    return (type || '').replace(/\b[A-Za-z_]\w*\b/g, word => substitutions.get(word) || word);
}
function specializeSymbol(symbol, args) {
    if (!symbol?.typeParams?.length || !args) return symbol;
    const type = substituteType(symbol.type, symbol.typeParams, args);
    const params = symbol.params.map(p => ({ ...p, type: substituteType(p.type, symbol.typeParams, args) }));
    return { ...symbol, type, params, label: `${symbol.pure ? 'pure ' : symbol.safe ? 'safe ' : ''}${symbol.name}<${args.join(', ')}>(${params.map(parameterLabel).join(', ')}): ${type}` };
}
function tokenize(text) {
    const tokens = [], regions = []; let i = text.charCodeAt(0) === 0xfeff ? 1 : 0;
    const wordAt = (at, word) => text.startsWith(word, at) && !/[\w\u0080-\uffff]/.test(text[at + word.length] || '');
    while (i < text.length) {
        if (/\s/.test(text[i])) { i++; continue; }
        const start = i;
        if (text[i] === '#') {
            const directive = /^#(yuri)\s*<([^>\r\n]*)>|^#(body)[ \t]+([^\s;]+)/.exec(text.slice(i));
            if (directive) {
                const name = directive[2] ?? directive[4], kind = directive[1] || directive[3], at = i + directive[0].indexOf(name, kind.length + 1);
                tokens.push({ value: '#' + kind, start, end: start + kind.length + 1, kind: 'code' });
                tokens.push({ value: name, start: at, end: at + name.length, kind: 'importPath' });
                i += directive[0].length; regions.push({ start: at, end: at + name.length, kind: 'string' }); continue;
            }
        }
        if (text.startsWith('//', i) || wordAt(i, 'miyabi')) {
            while (i < text.length && text[i] !== '\n') i++;
            regions.push({ start, end: i, kind: 'comment' }); continue;
        }
        if (text.startsWith('/*', i) || wordAt(i, 'te')) {
            const legacy = text.startsWith('/*', i); let depth = 1; i += 2;
            while (i < text.length && depth) {
                const boundary = !/[\w\u0080-\uffff]/.test(text[i - 1] || '');
                if (legacy ? text.startsWith('/*', i) : boundary && wordAt(i, 'te')) { depth++; i += 2; }
                else if (legacy ? text.startsWith('*/', i) : boundary && wordAt(i, 'to')) { depth--; i += 2; }
                else i++;
            }
            regions.push({ start, end: i, kind: 'comment' }); continue;
        }
        if (text[i] === '"') {
            i++; while (i < text.length && text[i] !== '"') { if (text[i] === '\\') i++; i++; }
            i = Math.min(text.length, i + (text[i] === '"' ? 1 : 0));
            tokens.push({ value: text.slice(start, i), start, end: i, kind: 'string' });
            regions.push({ start, end: i, kind: 'string' }); continue;
        }
        if (/[A-Za-z_]/.test(text[i])) { while (i < text.length && /[A-Za-z_0-9]/.test(text[i])) i++; while (text.slice(i, i + 2) === '::' && /[A-Za-z_]/.test(text[i + 2] || '')) { i += 2; while (i < text.length && /[A-Za-z_0-9]/.test(text[i])) i++; } }
        else if (/[0-9]/.test(text[i])) { while (i < text.length && /[A-Za-z_0-9]/.test(text[i])) i++; }
        else i++;
        tokens.push({ value: text.slice(start, i), start, end: i, kind: 'code' });
    }
    return { tokens, regions };
}
function analyze(text, file) {
    const { tokens, regions } = tokenize(text), pairs = new Map(), stack = [], scopes = [], symbols = [], imports = [];
    const v = i => tokens[i]?.value;
    for (let i = 0; i < tokens.length; i++) {
        if (['{', '(', '['].includes(v(i))) stack.push(i);
        else if (['}', ')', ']'].includes(v(i))) {
            const expected = { '}': '{', ')': '(', ']': '[' }[v(i)];
            if (v(stack.at(-1)) === expected) { const open = stack.pop(); pairs.set(open, i); pairs.set(i, open); }
        }
    }
    for (let i = 0; i < tokens.length; i++) if (v(i) === '{') scopes.push({ open: i, start: tokens[i].start, end: tokens[pairs.get(i)]?.end ?? text.length });
    for (let i = 0; i < tokens.length; i++) if (v(i) === 'for' && v(i + 1) === '(') {
        const close = pairs.get(i + 1), body = close + 1;
        if (v(body) === '{') scopes.push({ open: i + 1, start: tokens[i].start, end: tokens[pairs.get(body)]?.end ?? text.length });
    }
    const scopeAt = offset => scopes.filter(s => s.start < offset && s.end >= offset).sort((a, b) => b.start - a.start)[0];
    const readType = (i, depth = 0) => {
        if (depth > 64 || i >= tokens.length) return { type: '', next: i + 1 };
        let result = '';
        if (['own', 'borrow'].includes(v(i))) {
            result += v(i++); if (v(i) === 'mut') result += ' ' + v(i++);
            if (v(i) === '(') { result += '(' + (v(i + 1) || '') + ')'; i = (pairs.get(i) ?? i + 2) + 1; }
            result += ' ';
        }
        while (v(i) === '*') { result += '*'; i++; }
        if (['pure', 'safe', 'assis'].includes(v(i))) {
            if (['pure', 'safe'].includes(v(i))) { result += v(i) + ' '; i++; }
            result += v(i++) || '';
            if (v(i++) !== '(') return { type: result, next: i };
            const args = [];
            while (i < tokens.length && v(i) !== ')') {
                const item = readType(i, depth + 1); args.push(item.type); i = item.next;
                if (v(i) !== ',') break; i++;
            }
            if (v(i) === ')') i++;
            result += '(' + args.join(', ') + ')';
            if (v(i) === ':') { const output = readType(i + 1, depth + 1); result += ': ' + output.type; i = output.next; }
        } else {
            result += v(i++) || '';
            if (v(i) === '<') {
                i++; const args = [];
                while (i < tokens.length && v(i) !== '>') {
                    const item = readType(i, depth + 1); args.push(item.type); i = item.next;
                    if (v(i) !== ',') break; i++;
                }
                if (v(i) === '>') i++;
                result += '<' + args.join(', ') + '>';
            }
        }
        return { type: result, next: i };
    };
    const typeAt = i => readType(i).type;
    const parametersAt = i => {
        const names = [];
        if (v(i) === '<') { i++; while (i < tokens.length && v(i) !== '>') { if (v(i) !== ',') names.push(v(i)); i++; } i++; }
        return { names, next: i };
    };
    const documentation = offset => {
        const lines = text.slice(0, offset).split(/\r?\n/); lines.pop(); const result = [];
        for (let j = lines.length - 1; j >= 0 && /^\s*(?:miyabi\b|\/\/\/)/.test(lines[j]); j--) result.unshift(lines[j].replace(/^\s*(?:miyabi\s?|\/\/\/\s?)/, ''));
        if (!result.length) {
            const block = /\/\*\*((?:(?!\*\/)[\s\S])*)\*\/\s*$/.exec(text.slice(0, offset).replace(/(?:(?:private|pure)\s+)?(?:assis|ASSIS|struct)\s*$/, ''));
            if (block) result.push(block[1].split(/\r?\n/).map(line => line.replace(/^\s*\* ?/, '').trimEnd()).join('\n').trim());
        }
        return result.join('\n');
    };
    function add(token, kind, extra = {}) {
        const symbol = { name: token.value, start: token.start, end: token.end, file, kind, scopeStart: 0, scopeEnd: text.length, documentation: documentation(token.start), ...extra };
        symbols.push(symbol); return symbol;
    }
    for (let i = 0; i < tokens.length; i++) {
        if (v(i) === 'importa' && tokens[i + 1]?.kind === 'string') {
            let name; try { name = JSON.parse(v(i + 1)); } catch { continue; }
            imports.push({ name, start: tokens[i + 1].start, end: tokens[i + 1].end });
        }
        if (['#yuri', '#body'].includes(v(i)) && tokens[i + 1]?.kind === 'importPath') imports.push({ name: v(i + 1), start: tokens[i + 1].start, end: tokens[i + 1].end, package: v(i) === '#body' });
        if (['ASSIS', 'struct', 'enum'].includes(v(i)) && tokens[i + 1]) {
            const typeParams = parametersAt(i + 2), extendsClass = ['ASSIS_FODASE', 'extends'].includes(v(typeParams.next));
            const base = extendsClass ? readType(typeParams.next + 1) : undefined, open = base ? base.next : typeParams.next;
            const cls = add(tokens[i + 1], 'class', { typeParams: typeParams.names, record: v(i) === 'struct', value: v(i - 1) === 'value' || v(i) === 'enum', tagged: v(i) === 'enum', base: base?.type, bodyStart: tokens[open]?.start, bodyEnd: tokens[pairs.get(open)]?.end ?? text.length, open });
            if (cls.tagged) for (let j = open + 1; j < (pairs.get(open) ?? open); j++) {
                const token = tokens[j], params = [];
                if (!/^[A-Za-z_]\w*$/.test(v(j) || '')) continue;
                if (v(j + 1) === '(') { const close = pairs.get(j + 1); j += 2; while (j < close) { const p = readType(j); params.push({ name: 'arg' + (params.length + 1), type: p.type }); j = p.next; if (v(j) === ',') j++; } }
                const type = cls.name + (cls.typeParams.length ? '<' + cls.typeParams.join(', ') + '>' : '');
                add(token, 'variant', { owner: cls.name, type, params, label: `${token.value}(${params.map(parameterLabel).join(', ')}): ${type}` });
            }
        }
    }
    const classAt = offset => symbols.filter(s => s.kind === 'class' && s.bodyStart < offset && s.bodyEnd > offset).sort((a, b) => b.bodyStart - a.bodyStart)[0];
    for (let i = 0; i < tokens.length; i++) {
        const typeParams = parametersAt(i + 2);
        if (v(i) === 'assis' && tokens[i + 1] && v(typeParams.next) === '(') {
            const close = pairs.get(typeParams.next); if (close === undefined) continue;
            const owner = classAt(tokens[i].start), params = []; let body = close + 1;
            while (body < tokens.length && !['{', ';', '}'].includes(v(body))) body++;
            const end = tokens[pairs.get(body)]?.end ?? text.length;
            for (let j = typeParams.next + 1; j < close; j++) if (v(j + 1) === ':') {
                const ownership = v(j - 1) === 'mut' && v(j - 2) === 'borrow' ? 'borrow mut' : ['own', 'borrow'].includes(v(j - 1)) ? v(j - 1) : '';
                const parameter = readType(j + 2); params.push({ name: v(j), ownership, type: parameter.type, token: tokens[j] }); j = parameter.next - 1;
            }
            const result = v(close + 1) === ':' ? typeAt(close + 2) : 'FODase';
            const receiverAt = typeParams.next + 1;
            const receiver = v(receiverAt) === 'borrow' && v(receiverAt + 1) === 'self' ? 'borrow self' : v(receiverAt) === 'borrow' && v(receiverAt + 1) === 'mut' && v(receiverAt + 2) === 'self' ? 'borrow mut self' : undefined;
            const fn = add(tokens[i + 1], owner ? 'method' : 'function', { typeParams: typeParams.names, owner: owner?.name, receiver, params, type: result, private: v(i - 1) === 'private', pure: v(i - 1) === 'pure', safe: v(i - 1) === 'safe' || !!receiver, bodyStart: tokens[body]?.start, bodyEnd: end });
            fn.label = `${fn.pure ? 'pure ' : fn.safe ? 'safe ' : ''}${fn.name}${fn.typeParams.length ? '<' + fn.typeParams.join(', ') + '>' : ''}(${params.map(parameterLabel).join(', ')}): ${result}`;
            for (const p of params) add(p.token, 'parameter', { type: p.type, ownership: p.ownership, immutable: fn.pure, scopeStart: tokens[i].start, scopeEnd: end, function: fn.name });
        }
        const nameAt = i + (v(i) === 'borrow' && v(i + 1) === 'mut' ? 2 : 1);
        if (['Assis', 'let', 'val', 'own', 'borrow'].includes(v(i)) && tokens[nameAt] && v(nameAt + 1) === ':') {
            const token = tokens[nameAt], scope = scopeAt(token.start), owner = classAt(token.start);
            if (symbols.some(s => s.kind === 'parameter' && s.start === token.start)) continue;
            const field = owner && scope?.open === owner.open;
            add(token, field ? 'field' : 'variable', { type: typeAt(nameAt + 2), owner: field ? owner.name : undefined, private: field && v(i - 1) === 'private', immutable: v(i) === 'val', scopeStart: scope?.start ?? 0, scopeEnd: scope?.end ?? text.length });
        }
    }
    const model = { text, file, tokens, regions, symbols, imports, pairs };
    for (let i = 0; i < tokens.length; i++) if (v(i) === 'match' && v(i + 1) === '(') {
        const close = pairs.get(i + 1), open = close + 1, end = pairs.get(open);
        const subject = receiverType(model, close, [model]);
        if (v(open) !== '{' || end === undefined) continue;
        for (let j = open + 1; j < end;) {
            const variant = members([model], subject).find(s => s.kind === 'variant' && s.name === v(j));
            const bindings = [], parameters = variant?.params || []; let body = j + 1;
            if (v(body) === '(') { const stop = pairs.get(body); for (let k = body + 1; k < stop; k++) if (v(k) !== ',') bindings.push(tokens[k]); body = stop + 1; }
            const stop = pairs.get(body); if (stop === undefined) break;
            bindings.forEach((token, k) => add(token, 'variable', { type: parameters[k]?.type, immutable: true, pattern: true, patternAt: close, patternVariant: v(j), patternIndex: k, scopeStart: tokens[body].start, scopeEnd: tokens[stop].end }));
            j = stop + 1;
        }
    }
    const namespaceAt = tokens.findIndex(t => t.value === 'namespace');
    model.namespace = namespaceAt < 0 ? undefined : tokens[namespaceAt + 1]?.value;
    if (model.namespace) {
        const globals = symbols.filter(s => ['class', 'function'].includes(s.kind));
        const types = new Set(globals.filter(s => s.kind === 'class').map(s => s.name));
        const qualifyType = type => type?.replace(/(?<![\w:])[A-Za-z_]\w*(?![\w:])/g, name => types.has(name) ? model.namespace + '::' + name : name);
        for (const symbol of globals) {
            const index = tokens.findIndex(t => t.start === symbol.start); let start = index - 2;
            while (start >= 0 && ['public', 'pure', 'safe', 'value', 'final'].includes(tokens[start]?.value)) start--;
            symbol.modulePrivate = !tokens.slice(start + 1, index).some(t => t.value === 'public');
            symbol.localName = symbol.name; symbol.name = model.namespace + '::' + symbol.name;
        }
        for (const symbol of symbols) {
            if (symbol.owner) symbol.owner = model.namespace + '::' + symbol.owner;
            symbol.type = qualifyType(symbol.type); symbol.base = qualifyType(symbol.base);
            if (symbol.params) symbol.params = symbol.params.map(p => ({ ...p, type: qualifyType(p.type) }));
            if (['function', 'method'].includes(symbol.kind)) symbol.label = `${symbol.pure ? 'pure ' : symbol.safe ? 'safe ' : ''}${symbol.name}${symbol.typeParams?.length ? '<' + symbol.typeParams.join(', ') + '>' : ''}(${symbol.params.map(parameterLabel).join(', ')}): ${symbol.type}`;
        }
    }
    return model;
}
function ownerAt(model, offset) {
    const owner = model.symbols.find(s => s.kind === 'class' && s.bodyStart < offset && s.bodyEnd > offset);
    return owner ? owner.name + (owner.typeParams.length ? '<' + owner.typeParams.join(', ') + '>' : '') : undefined;
}
function members(models, className, seen = new Set(), accessOwner) {
    className = stripOwnership(className);
    if (seen.has(className) || seen.size >= 64) return []; seen.add(className);
    const generic = genericParts(className);
    if (generic && reference[generic.kind]) {
        const replace = text => text.replace(/\b[TKV]\b/g, key => ({ T: generic.params[0], K: generic.params[0], V: generic.params[1] })[key] || key);
        return Object.entries(reference[generic.kind]).map(([name, info]) => {
            const params = info.params.map(p => { const [name, type] = replace(p).split(': '); return { name, type }; }), type = replace(info.type);
            return { name, kind: 'method', owner: className, params, type, documentation: info.documentation, label: `${name}(${params.map(p => `${p.name}: ${p.type}`).join(', ')}): ${type}`, builtin: true };
        });
    }
    const all = models.flatMap(m => m.symbols), name = generic?.kind || className;
    const definition = all.find(s => s.kind === 'class' && s.name === name);
    if (!definition) return [];
    const substitute = type => substituteType(type, definition?.typeParams, generic?.params);
    const own = all.filter(s => s.owner === name && (!s.private || className === accessOwner)).map(s => {
        const type = substitute(s.type), params = s.params?.map(p => ({ ...p, type: substitute(p.type) }));
        return { ...s, type, ...(params ? { params, label: `${s.name}(${params.map(parameterLabel).join(', ')}): ${type}` } : {}) };
    });
    const base = substitute(definition?.base);
    return [...own, ...(base ? members(models, base, seen, accessOwner).filter(s => !own.some(o => o.name === s.name)) : [])];
}
function patternSymbol(model, symbol, models) {
    if (!symbol?.pattern || symbol.type) return symbol;
    const subject = receiverType(model, symbol.patternAt, models);
    const variant = members(models, subject).find(s => s.kind === 'variant' && s.name === symbol.patternVariant);
    return { ...symbol, type: variant?.params?.[symbol.patternIndex]?.type };
}
function visibleSymbols(model, offset, models) {
    const locals = model.symbols.filter(s => ['variable', 'parameter'].includes(s.kind) && s.scopeStart <= offset && s.scopeEnd >= offset && (s.kind === 'parameter' || s.start <= offset)).sort((a, b) => b.scopeStart - a.scopeStart || b.start - a.start).map(s => patternSymbol(model, s, models));
    const globals = models.flatMap(m => m.symbols.filter(s => ['class', 'function'].includes(s.kind) && (!s.modulePrivate || s.file === model.file)));
    const own = globals.filter(s => s.file === model.file && s.localName).map(s => ({ ...s, name: s.localName }));
    const seen = new Set(); return [...locals, ...own, ...globals].filter(s => !seen.has(s.name) && seen.add(s.name));
}
function typeTokenText(tokens) {
    return tokens.map((t, i) => (i && /\w$/.test(tokens[i - 1].value) && /^\w/.test(t.value) ? ' ' : '') + t.value).join('').replace(/,/g, ', ').replace(/(?<!:):(?!:)/g, ': ');
}
function functionParts(type) {
    const match = /^(?:(?:pure|safe) )?assis\(/.exec(type || ''); if (!match) return undefined;
    let depth = 0, start = match[0].length, end = start; const params = [];
    for (; end < type.length; end++) {
        const c = type[end];
        if (c === ')' && depth === 0) { if (end > start) params.push(type.slice(start, end).trim()); break; }
        if ('(<'.includes(c)) depth++; if (')>'.includes(c)) depth--;
        if (c === ',' && depth === 0) { params.push(type.slice(start, end).trim()); start = end + 1; }
    }
    return { params, type: type.slice(end + 1).replace(/^\s*:\s*/, '') };
}
function typeBefore(tokens, index) {
    const end = index; let start = index;
    let argumentsList;
    if (tokens[index]?.value === '>') {
        let depth = 0;
        for (; start >= 0; start--) { if (tokens[start].value === '>') depth++; if (tokens[start].value === '<' && --depth === 0) { start--; break; } }
        if (tokens[start]?.value === ':' && tokens[start - 1]?.value === ':') {
            argumentsList = genericParts('F' + typeTokenText(tokens.slice(start + 1, end + 1)))?.params;
            start -= 2;
        }
        if (start < 0 || !/^[A-Za-z_]\w*(?:::[A-Za-z_]\w*)*$/.test(tokens[start]?.value || '')) return undefined;
    }
    return { start, token: tokens[start], arguments: argumentsList, type: typeTokenText(tokens.slice(start, end + 1)) };
}
function receiverType(model, dotIndex, models, depth = 0) {
    if (depth > 32) return undefined;
    const tokens = model.tokens; let index = dotIndex - 1, token = tokens[index]; if (!token) return undefined;
    if (token.value === '>') return typeBefore(tokens, index)?.type;
    if (token.value === ')') {
        const open = model.pairs.get(index); if (open === undefined) return undefined;
        const callee = typeBefore(tokens, open - 1); if (!callee) return undefined;
        index = callee.start; token = tokens[index]; if (!token) return undefined;
        if (['fodase', 'new'].includes(tokens[index - 1]?.value)) return callee.type;
        if (callee.arguments) return specializeSymbol(visibleSymbols(model, token.start, models).find(s => s.name === token.value), callee.arguments)?.type;
    }
    if (['aSSIS', 'self'].includes(token.value)) return ownerAt(model, token.start);
    if (token.value === ']') {
        const open = model.pairs.get(index); if (open === undefined) return undefined;
        const generic = genericParts(receiverType(model, open, models, depth + 1)); return generic?.kind === 'Array' ? generic.params[0] : undefined;
    }
    if (tokens[index - 1]?.value === '.') {
        const parent = receiverType(model, index - 1, models, depth + 1);
        return members(models, parent, new Set(), ownerAt(model, token.start)).find(s => s.name === token.value)?.type;
    }
    return visibleSymbols(model, token.start, models).find(s => s.name === token.value)?.type;
}
function resolveSymbol(model, offset, models) {
    const i = model.tokens.findIndex(t => t.start <= offset && t.end > offset); if (i < 0) return undefined;
    const token = model.tokens[i];
    const declaration = model.symbols.find(s => s.start === token.start); if (declaration) return patternSymbol(model, declaration, models);
    if (model.tokens[i - 1]?.value === '.') return members(models, receiverType(model, i - 1, models), new Set(), ownerAt(model, offset)).find(s => s.name === token.value);
    return visibleSymbols(model, offset, models).find(s => s.name === token.value);
}
function signatureAt(model, offset, models) {
    const tokens = model.tokens; let index = tokens.findLastIndex(t => t.start < offset), nesting = 0, commas = 0;
    for (let i = index; i >= 0; i--) {
        const value = tokens[i].value;
        if ([')', ']', '}'].includes(value)) nesting++;
        else if (['(', '[', '{'].includes(value)) {
            if (nesting) { nesting--; continue; }
            if (value !== '(') return undefined;
            const callee = typeBefore(tokens, i - 1), name = callee?.token; if (!name) return undefined;
            let fn = specializeSymbol(resolveSymbol(model, name.start, models), callee.arguments);
            if (tokens[callee.start - 1]?.value === '.') {
                const parent = typeBefore(tokens, callee.start - 2);
                if (parent && ['new', 'fodase'].includes(tokens[parent.start - 1]?.value)) {
                    const variant = members(models, parent.type).find(s => s.kind === 'variant' && s.name === name.value);
                    if (variant) fn = { ...variant, label: `new ${parent.type}.${variant.name}(${variant.params.map(parameterLabel).join(', ')}): ${parent.type}` };
                }
            }
            if (['fodase', 'new'].includes(tokens[callee.start - 1]?.value)) {
                const cls = models.flatMap(m => m.symbols).find(s => s.kind === 'class' && s.name === name.value);
                if (cls?.record) {
                    const params = members(models, callee.type).filter(s => s.kind === 'field').map(s => ({ name: s.name, type: s.type }));
                    fn = { label: `new ${callee.type}(${params.map(p => `${p.name}: ${p.type}`).join(', ')}): ${callee.type}`, params, documentation: cls.documentation };
                } else if (reference[genericParts(callee.type)?.kind]) fn = { label: `new ${callee.type}(): ${callee.type}`, params: [], documentation: keywords[name.value] };
                else fn = members(models, callee.type, new Set(), ownerAt(model, offset)).find(s => s.name === 'assis_fodase');
            }
            const callback = functionParts(fn?.type);
            const signature = fn?.params ? { label: fn.label, params: fn.params.map(parameterLabel), documentation: fn.documentation }
                : callback ? { label: `${fn.name}: ${fn.type}`, params: callback.params.map((t, i) => `arg${i + 1}: ${t}`), documentation: fn.documentation } : builtinSignatures[name.value];
            return signature ? { ...signature, active: Math.min(commas, Math.max(0, signature.params.length - 1)) } : undefined;
        } else if (!nesting && value === '>') { const generic = typeBefore(tokens, i); if (generic) i = generic.start; }
        else if (!nesting && value === ',') commas++;
    }
    return undefined;
}
function resolveImport(name, from, options = {}) {
    if (name.startsWith('pkg/')) {
        const [, alias, ...rest] = name.split('/'); let folder = path.dirname(from);
        for (let depth = 0; depth < 128; depth++) {
            const manifest = path.join(folder, 'assis.pkg');
            if (fs.existsSync(manifest)) {
                try {
                    const dependencies = fs.readFileSync(manifest, 'utf8').split(/\r?\n/).map(line => /^\s*dep\s+(\S+)\s+\d+\.\d+\.\d+\s+(?:"([^"]*)"|(\S+))/.exec(line));
                    const dependency = dependencies.find(d => d?.[1] === alias); if (!dependency) return undefined;
                    const root = fs.realpathSync(path.resolve(folder, dependency[2] ?? dependency[3]));
                    const candidate = fs.realpathSync(path.resolve(root, ...rest));
                    if (path.relative(root, candidate).startsWith('..') || path.isAbsolute(path.relative(root, candidate))) return undefined;
                    return candidate;
                } catch { return undefined; }
            }
            const parent = path.dirname(folder); if (parent === folder) break; folder = parent;
        }
        return undefined;
    }

    const roots = [path.dirname(from), ...(options.includePaths || []), ...(process.env.ASSIS_PATH || '').split(path.delimiter).filter(Boolean)];
    const candidates = roots.map(root => path.resolve(root, name));
    if (name.endsWith('.pillow')) candidates.push(...roots.map(root => path.resolve(root, name.slice(0, -7).replace(/\./g, path.sep) + '.pillow')));
    if (/^std[/\\]/.test(name)) candidates.push(...(options.stdlibRoots || []).map(root => path.join(root, name.slice(4))));
    for (const candidate of candidates) for (const file of name.endsWith('.pillow') ? [candidate] : [candidate, candidate + '.assis']) {
        if (options.overlays?.has(path.resolve(file)) || (fs.existsSync(file) && fs.statSync(file).isFile())) return path.resolve(file);
    }
    return undefined;
}
function collectProject(entry, options = {}) {
    const result = [], seen = new Set(); let bytes = 0;
    function visit(file, depth) {
        file = path.resolve(file); if (seen.has(file) || result.length >= 1024 || depth > 128 || bytes > 16 * 1024 * 1024) return;
        seen.add(file); let text;
        try { text = options.overlays?.get(file) ?? fs.readFileSync(file, 'utf8'); } catch { return; }
        bytes += Buffer.byteLength(text); const model = analyze(text, file); result.push(model);
        for (const item of model.imports) { const imported = resolveImport(item.name, file, options); if (imported) visit(imported, depth + 1); }
    }
    visit(entry, 0); return result;
}
module.exports = { keywords, builtinSignatures, tokenize, analyze, members, ownerAt, visibleSymbols, receiverType, resolveSymbol, signatureAt, resolveImport, collectProject };
