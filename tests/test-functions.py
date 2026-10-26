"""Native function values and effect contracts, using the portable mode matrix."""
import importlib
import json
import unittest

evolution = importlib.import_module('test-evolution')
main = evolution.main

PURE = ('pure assis dobro(v:int):int{return v*2;}'
        'pure assis mais(v:int):int{return v+1;}')


class Functions(unittest.TestCase):
    setUp = evolution.Evolution.setUp
    source = evolution.Evolution.source
    invoke = evolution.Evolution.invoke
    accepted = evolution.Evolution.accepted
    rejected = evolution.Evolution.rejected

    def test_global_values_aliases_and_equality(self):
        self.accepted(PURE + main(
            'val f:pure assis(int):int=dobro;val g:pure assis(int):int=f;'
            'print(f(21),g(3),f==g,f!=mais,dobro==f);'),
            '42 6 aSsIs aSsIs aSsIs\n')

    def test_parameters_composition_recursion_and_forward_definitions(self):
        self.accepted(
            'pure assis compor(f:pure assis(int):int,g:pure assis(int):int,v:int):int{return f(g(v));}'
            'pure assis repetir(f:pure assis(int):int,n:int,v:int):int{if(n==0){return v;}return repetir(f,n-1,f(v));}'
            + PURE + main('print(compor(dobro,mais,20),repetir(mais,20,22));'), '42 42\n')

    def test_returns_and_chained_indirect_calls(self):
        self.accepted(PURE +
            'pure assis escolher(b:bool):pure assis(int):int{if(b){return dobro;}return mais;}'
            'pure assis fabrica():pure assis(bool):pure assis(int):int{return escolher;}' + main(
            'val f:pure assis(int):int=escolher(true);print(f(21),escolher(false)(41),fabrica()(true)(21));'),
            '42 42 42\n')

    def test_generic_specialized_values_and_function_type_substitution(self):
        self.accepted('pure assis id<T>(v:T):T{return v;}'
            'pure assis aplicar<T>(f:pure assis(T):T,v:T):T{return f(v);}'
            'pure assis get<T>():pure assis(T):T{return id::<T>;}' + main(
            'val f:pure assis(int):int=id::<int>;'
            'print(aplicar::<int>(f,42),aplicar::<byte>(id::<byte>,byte(7)),'
            'get::<bool>()(true),id::<pure assis(int):int>(f)(9));'), '42 7 aSsIs 9\n')

    def test_mutable_alias_shadowing_and_scope_restoration(self):
        self.accepted(PURE + main(
            'let f:pure assis(int):int=dobro;print(f(3));f=mais;print(f(3));'
            '{val dobro:pure assis(int):int=mais;print(dobro(3));}print(dobro(3));'),
            '6\n4\n4\n6\n')
        self.rejected(PURE + main('let dobro:int=2;dobro(3);'), 'não é uma função chamável')
        self.rejected('pure assis id<T>(v:T):T{return v;}' + main(
            'let id:pure assis(int):int=id::<int>;print(id::<int>(1));'), 'local não aceita')

    def test_effectful_callbacks_void_text_and_safe_widening(self):
        self.accepted(PURE +
            'assis eco(t:text):void{print(t);}'
            'assis run(f:assis(text):void):void{f("ação");}'
            'assis escolher():assis(int):int{return dobro;}' + main(
            'val f:assis(int):int=dobro;print(f(21),escolher()(3));run(eco);'),
            '42 6\nação\n')

    def test_reject_effect_laundering_through_assignments_returns_and_arguments(self):
        prefix = PURE + 'assis efeito(v:int):int{print(v);return v;}'
        for body in [
            'let f:pure assis(int):int=efeito;',
            'let f:pure assis(int):int=dobro;f=efeito;',
            'let f:assis(int):int=dobro;let g:pure assis(int):int=f;',
            'usar(efeito);',
        ]:
            self.rejected(prefix + 'assis usar(f:pure assis(int):int):int{return f(1);}' + main(body),
                          'não é possível usar')
        self.rejected(prefix + 'assis get():pure assis(int):int{return efeito;}' + main(''),
                      'não é possível usar')

    def test_pure_bodies_reject_transitive_effects_and_dead_branches(self):
        prefix = 'assis efeito(v:int):int{print(v);return v;}'
        for suffix in [
            'pure assis f():int{val g:assis(int):int=efeito;return g(1);}',
            'pure assis f(g:assis(int):int):int{return g(1);}',
            'pure assis f():int{if(false){efeito(1);}return 0;}',
            'pure assis f():assis(int):int{return efeito;}',
        ]:
            self.rejected(prefix + suffix + main(''), 'pure')

    def test_unused_pure_templates_check_callbacks_and_lexical_names(self):
        self.accepted(PURE +
            'pure assis f<T>(g:pure assis(T):T,v:T):T{val dobro:pure assis(T):T=g;return dobro(v);}' + main(
            'print(f::<int>(mais,41));'), '42\n')
        for template in [
            'pure assis f<T>(g:assis(T):T,v:T):T{return g(v);}',
            'pure assis f<T>(dobro:T,v:T):T{return dobro(v);}',
            'pure assis f<T>(v:T):T{let g:assis(int):int=dobro;return v;}',
            'pure assis f<T>(v:T):T{if(false){efeito(1);}return v;}',
        ]:
            self.rejected(PURE + 'assis efeito(v:int):int{print(v);return v;}' + template + main(''), 'pure')

    def test_nested_signatures_are_invariant_and_canonically_specialized(self):
        self.accepted(PURE + 'assis id<F>(f:F):F{return f;}' + main(
            'val b:assis(int):int=id::<assis(int):int>(mais);'
            'val a:pure assis(int):int=id::<pure assis(int):int>(dobro);print(a(21),b(41));'), '42 42\n')
        self.rejected(PURE + 'assis receber(f:assis(pure assis(int):int):int):int{return f(dobro);}'
            'assis outro(f:assis(int):int):int{return f(2);}' + main('receber(outro);'), 'não é possível usar')

    def test_reject_arity_signature_and_nonfunction_operations(self):
        for body, message in [
            ('val f:pure assis(byte):int=dobro;', 'não é possível usar'),
            ('val f:pure assis(int):byte=dobro;', 'não é possível usar'),
            ('val f:pure assis():int=dobro;', 'não é possível usar'),
            ('val f:pure assis(int):int=dobro;f();', 'esperados 1 argumentos'),
            ('val f:pure assis(int):int=dobro;f(true);', 'não é possível usar'),
            ('val f:pure assis(int):int=null;', 'não é possível usar'),
            ('borrow f:pure assis(int):int=dobro;', 'borrow exige o nome de um own'),
            ('let f:pure assis(int):int=dobro;print(int(f));', 'conversão'),
            ('free(dobro);', 'libera apenas'),
            ('print(dobro+1);', 'operação incompatível'),
            ('let p:*pure assis(int):int=&dobro;', 'posição gravável'),
            ('dobro=mais;', 'posição gravável'),
            ('val f:pure assis(int):int=dobro;f=mais;', 'imutável'),
            ('val f:pure assis(int):int=dobro;let p:*pure assis(int):int=&f;', 'imutável'),
        ]:
            with self.subTest(body=body):
                self.rejected(PURE + main(body), message)
        self.rejected('assis f(g:assis(void):int):int{return 0;}' + main(''), 'só pode ser retorno')
        self.rejected('assis f(g:pure assis(text):int):int{return 0;}' + main(''), 'tipo de função pure')

    def test_native_argument_order_callee_once_and_many_arguments(self):
        self.accepted('assis a(v:int):int{print(v);return v;}'
            'assis soma(a:int,b:int,c:int,d:int,e:int,f:int,g:int,h:int):int{return a+b+c+d+e+f+g+h;}'
            'assis get():assis(int,int,int,int,int,int,int,int):int{print(0);return soma;}' + main(
            'print(get()(a(1),a(2),a(3),a(4),a(5),a(6),a(7),a(8)));'),
            '0\n1\n2\n3\n4\n5\n6\n7\n8\n36\n')

    def test_fields_arrays_pointers_privacy_and_owner_lifetime(self):
        self.accepted(PURE + 'struct Caixa<T>{let f:T;}' + main(
            'own c:Caixa<pure assis(int):int>=new Caixa<pure assis(int):int>(dobro);'
            'own a:Array<pure assis(int):int>=[mais,dobro];'
            'print(c.f(21),a[0](41),a[1](21));'
            'let f:pure assis(int):int=mais;let p:*pure assis(int):int=&f;'
            '*p=dobro;print((*p)(21));'), '42 42 42\n42\n')
        self.rejected(PURE + 'struct C{private let f:pure assis(int):int;}' + main(
            'let c:C=new C();print(c.f(1));'), 'campo privado')
        self.rejected(PURE + main('own a:Array<pure assis(int):int>=[dobro];free(a);a[0](1);'), 'movido ou liberado')

    def test_managed_arguments_cannot_escape_through_indirect_calls(self):
        self.rejected('assis size(a:Array<int>):int{return len(a);}' + main(
            'val f:assis(Array<int>):int=size;own a:Array<int>=[1];print(f(a));'), 'não pode escapar')

    def test_methods_remain_bound_calls_without_implicit_closures(self):
        self.accepted(PURE + 'ASSIS C{assis usar(f:pure assis(int):int):int{return f(21);}}' + main(
            'let c:C=new C();print(c.usar(dobro));free(c);'), '42\n')
        self.rejected('ASSIS C{assis f(v:int):int{return v;}}' + main(
            'let c:C=new C();val f:assis(int):int=c.f;'), 'campo inexistente')

    def test_modules_and_diagnostics_preserve_specialization_origin(self):
        library = self.source('pure assis aplicar<T>(f:pure assis(T):T,v:T):T{\nreturn f(true);}', 'lib.assis')
        file = self.source('#yuri <lib.assis>\n' + PURE + main('aplicar::<int>(dobro,1);'))
        result = self.invoke('check', file, '--diagnostics=json')
        diagnostic = json.loads(result.stderr)
        self.assertEqual((result.returncode, diagnostic['file'], diagnostic['line']), (1, str(library), 2))
        self.assertIn('instância de aplicar', diagnostic['message'])
        self.assertIn(str(file), diagnostic['message'])
        library.write_text('pure assis id<T>(v:T):T{return v;}', encoding='utf-8')
        self.accepted('#yuri <lib.assis>\n' + main('val f:pure assis(int):int=id::<int>;print(f(42));'), '42\n')

    def test_null_default_function_has_runtime_diagnostic(self):
        file = self.source('struct C{let f:assis():int;}' + main('own c:C=new C();c.f();'))
        for flags in [[], ['--no-opt']]:
            result = self.invoke('run', file, *flags)
            self.assertEqual(result.returncode, 70, result.stderr)
            self.assertIn('nulo', result.stderr)

    def test_wide_function_types_in_intrinsic_collections_keep_structural_identity(self):
        # Exceeds the diagnostic buffer; collection types must remain structured.
        ty = 'assis(' + ','.join(['int'] * 900) + '):int'
        self.accepted(main(f'own a:Array<{ty}>=new Array<{ty}>();print(len(a));'), '0\n')

    def test_generic_map_filter_fold_empty_and_ordered_results(self):
        self.accepted('#yuri <std/algorithms.assis>\n' + PURE +
            'pure assis par(v:int):bool{return v%2==0;}'
            'pure assis somar(a:int,v:int):int{return a+v;}'
            'pure assis para_byte(v:int):byte{return byte(v);}' + main(
            'let a:Array<int>=[1,2,3,4];defer free(a);'
            'let b:Array<int>=map::<int,int>(a,dobro);defer free(b);'
            'let c:Array<int>=filter::<int>(a,par);defer free(c);'
            'let d:Array<byte>=map::<int,byte>(a,para_byte);defer free(d);'
            'print(fold::<int,int>(b,0,somar),len(c),c[0],c[1],a[0],d[3]);'
            'let vazio:Array<int>=[];defer free(vazio);'
            'let m:Array<int>=map::<int,int>(vazio,dobro);defer free(m);'
            'let f:Array<int>=filter::<int>(vazio,par);defer free(f);'
            'print(len(m),len(f),fold::<int,int>(vazio,42,somar));'),
            '20 2 2 4 1 4\n0 0 42\n')
        self.rejected('#yuri <std/algorithms.assis>\n'
            'assis efeito(v:int):int{print(v);return v;}' + main(
            'let a:Array<int>=[1];map::<int,int>(a,efeito);'), 'não é possível usar')


if __name__ == '__main__':
    program = unittest.main(exit=False, verbosity=2)
    print(f'ASSIS functions: {evolution.INVOCATIONS} invocações; {evolution.COMPILER}')
    raise SystemExit(not program.result.wasSuccessful())
