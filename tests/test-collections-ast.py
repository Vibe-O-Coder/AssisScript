"""Portable acceptance tests for collections using the common AST specializer."""
import importlib
import json
import random
import unittest

evolution = importlib.import_module('test-evolution')
main = evolution.main


class CollectionsAST(unittest.TestCase):
    setUp = evolution.Evolution.setUp
    source = evolution.Evolution.source
    invoke = evolution.Evolution.invoke
    accepted = evolution.Evolution.accepted
    rejected = evolution.Evolution.rejected

    def test_array_operations_against_independent_list(self):
        rng = random.Random(51425)
        values, body = [], ['let a:Array<int>=[];']
        for _ in range(140):
            operation = rng.randrange(5)
            if not values or operation == 0:
                value = rng.randrange(-1000, 1000)
                values.append(value); body.append(f'a.push({value});')
            elif operation == 1:
                index, value = rng.randrange(len(values) + 1), rng.randrange(-1000, 1000)
                values.insert(index, value); body.append(f'a.insert({index},{value});')
            elif operation == 2:
                index = rng.randrange(len(values)); value = values.pop(index)
                body.append(f'assert(a.remove({index})=={value});')
            elif operation == 3:
                values.reverse(); body.append('a.reverse();')
            else:
                index, value = rng.randrange(len(values)), rng.randrange(-1000, 1000)
                values[index] = value; body.append(f'a[{index}]={value};')
            body.append(f'assert(len(a)=={len(values)});')
        body.extend(f'assert(a[{i}]=={value});' for i, value in enumerate(values))
        body.append('free(a);')
        self.accepted(main(''.join(body)))

    def test_map_operations_against_independent_dictionary(self):
        rng = random.Random(51025)
        values, body = {}, ['let m:HashMap<int,int>=new HashMap<int,int>();']
        for _ in range(180):
            key = rng.randrange(-30, 30) * 64
            if rng.randrange(3):
                value = rng.randrange(-1000, 1000); values[key] = value
                body.append(f'm.set({key},{value});')
            else:
                existed = key in values; values.pop(key, None)
                body.append(f'assert(m.remove({key})=={str(existed).lower()});')
            body.append(f'assert(len(m)=={len(values)});assert(m.get_or({key},123456)=={values.get(key,123456)});')
        body.extend(f'assert(m.get({key})=={value});' for key, value in values.items())
        body.append('let k:Array<int>=m.keys();let v:Array<int>=m.values();'
                    'for(let i:int=0;i<len(k);i+=1){assert(m.get(k[i])==v[i]);}'
                    'free(v);free(k);free(m);')
        self.accepted(main(''.join(body)))

    def test_text_hash_content_collisions_and_external_lifetime(self):
        data = 'ação'.encode('utf-8')
        writes = ''.join(f'p[{i}]=byte({value});' for i, value in enumerate(data))
        self.accepted(main('let m:HashMap<text,int>=new HashMap<text,int>();'
            'm.set("Aa",1);m.set("B@",2);m.set("",3);m.set("ação",42);'
            f'let p:*byte=alloc<byte>({len(data)+1});' + writes +
            'let s:text=text(p);assert(m.get(s)==42);m.set(s,43);assert(len(m)==4);'
            'assert(m.get("ação")==43);assert(m.remove("Aa"));assert(m.get("B@")==2);'
            'm.set("Aa",9);print(m.get("Aa"),m.get("B@"),m.get(""));free(m);free(p);'), '9 2 3\n')

    def test_scalar_layouts_recoverable_operations_and_dispose(self):
        self.accepted(main('own a:Array<byte>=[byte(255)];let out:byte=byte(7);'
            'assert(!a.try_get(1,&out));assert(out==7);assert(a.try_pop(&out));assert(out==255);'
            'assert(!a.try_pop(&out));a.push(byte(2));assert(a[0]==2);'
            'let m:HashMap<bool,byte>=new HashMap<bool,byte>();m.set(true,byte(255));m.set(false,byte(3));'
            'assert(m.get(true)==255);assert(m.get(false)==3);m.dispose();m.dispose();'
            'm.set(false,byte(42));print(m.get(false));free(m);'), '42\n')

    def test_callbacks_and_nested_user_types_do_not_roundtrip_through_text(self):
        self.accepted('pure assis dobro(v:int):int{return v*2;}'
            'struct Registro<T>{let v:T;}'
            'ASSIS Caixa<T>{let v:T;assis ler():T{return self.v;}}' + main(
            'let m:HashMap<text,pure assis(int):int>=new HashMap<text,pure assis(int):int>();'
            'm.set("f",dobro);let vs:Array<pure assis(int):int>=m.values();print(vs[0](21));'
            'let c:Caixa<Registro<int>>=new Caixa<Registro<int>>();c.v=new Registro<int>(7);'
            'let a:Array<Caixa<Registro<int>>>=[c];print(a[0].ler().v);'
            'free(a);free(c.v);free(c);free(vs);free(m);'), '42\n7\n')
        ty = 'pure assis(' + ','.join(['int'] * 1000) + '):int'
        self.accepted(main(f'own a:Array<{ty}>=new Array<{ty}>();print(len(a));'), '0\n')

    def test_canonical_types_and_effects_remain_distinct(self):
        self.rejected(main('let a:Array<int>=[];let b:Array<byte>=a;'), 'não é possível usar')
        self.rejected(main('let a:Array<assis(int):int>=[];let b:Array<pure assis(int):int>=a;'), 'não é possível usar')
        self.rejected(main('let m:HashMap<*int,int>=null;'), 'chave de HashMap')
        self.rejected(main('let a:Array<void>=null;'), 'não aceitam void')

    def test_separate_budgets_and_repeated_collection_cache(self):
        types = ''.join(f'struct Tipo{i}{{}}' for i in range(257))
        self.accepted(types + 'assis marca<T>():int{return 1;}' + main(
            'let a:Array<int>=[];' + ''.join(f'marca::<Tipo{i}>();' for i in range(256)) +
            'a.push(42);print(a[0]);free(a);'), '42\n')
        self.accepted(main('{let a:Array<int>=[];free(a);}' * 258))
        body = ''.join(f'let a{i}:Array<Tipo{i}>=null;' for i in range(257))
        self.rejected(types + main(body), 'limite de 256 especializações de coleções')

    def test_private_templates_never_grant_user_authority(self):
        self.rejected('assis espia<T>(a:Array<T>):int{return a._length;}' + main(
            'let a:Array<int>=[1];print(espia::<int>(a));'), 'campo privado')
        self.rejected(main('let m:HashMap<int,int>=new HashMap<int,int>();print(m._hash(1));'), 'método privado')
        for source in ['ASSIS __assis_Array<T>{}', 'ASSIS __assis_Map<K,V>{}',
                       'assis __assis_falso():int{return 0;}']:
            result = self.invoke('check', '<colecoes>.assis', '--stdin', '--diagnostics=json', input=source + main(''))
            self.assertEqual(result.returncode, 1, result.stderr)
            self.assertIn('reservado', json.loads(result.stderr)['message'])

    def test_ownership_and_functional_algorithms_keep_existing_contracts(self):
        self.accepted(main('own m:HashMap<int,int>=new HashMap<int,int>();m.set(1,42);'
            '{borrow b:HashMap<int,int>=m;assert(b.get(1)==42);}'
            '{borrow mut b:HashMap<int,int>=m;b.set(2,7);}print(m.get(2));'), '7\n')
        self.rejected('assis receber(a:Array<int>):int{return len(a);}' + main(
            'own a:Array<int>=[1];print(receber(a));'), 'não pode escapar')
        self.rejected(main('own a:Array<int>=[1];{borrow b:Array<int>=a;b.push(2);}'), 'acesso exclusivo')
        self.accepted('#yuri <std/algoritmos.assis>\n'
            'pure assis dobro(v:int):int{return v*2;}pure assis somar(a:int,b:int):int{return a+b;}' + main(
            'let a:Array<int>=[1,2,3];let b:Array<int>=map::<int,int>(a,dobro);'
            'print(fold::<int,int>(b,0,somar),a[1]);free(b);free(a);'), '12 2\n')

    def test_runtime_bounds_and_missing_keys_preserve_diagnostics(self):
        for body in ['let a:Array<int>=[1];print(a[1]);',
                     'let a:Array<int>=[];a.pop();',
                     'let a:Array<int>=[];a.reserve(-1);',
                     'let m:HashMap<text,int>=new HashMap<text,int>();m.get("ausente");']:
            file = self.source(main(body))
            for flags in [[], ['--no-opt']]:
                result = self.invoke('run', file, *flags)
                self.assertEqual(result.returncode, 70, result.stderr)
                self.assertIn('R001', result.stderr)


if __name__ == '__main__':
    program = unittest.main(exit=False, verbosity=2)
    print(f'ASSIS collections AST: {evolution.INVOCATIONS} invocações; {evolution.COMPILER}')
    raise SystemExit(not program.result.wasSuccessful())
