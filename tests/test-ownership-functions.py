"""Interprocedural ownership, evaluation order, affine records and flow.

Negative cases run only through compiler rejection paths, never unsafe binaries.
Uses the common check/build/run and both-target harness from test-evolution.
"""
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('evolution', Path(__file__).with_name('test-evolution.py'))
evolution = importlib.util.module_from_spec(spec)
spec.loader.exec_module(evolution)
main = evolution.main
RECORD = 'struct P{let x:int;}'
FUNCS = '''
assis create(n:int):own P{return new P(n);}
assis ler(borrow p:P):int{return p.x;}
assis mudar(borrow mut p:P,n:int):void{p.x=n;}
assis consumir(own p:P):int{return p.x;}
assis passar(own p:P):own P{return move(p);}
assis ver(borrow p:P):borrow(p) P{return p;}
assis exclusivo(borrow mut p:P):borrow mut(p) P{return p;}
'''


class OwnershipFunctions(unittest.TestCase):
    setUp = evolution.Evolution.setUp
    source = evolution.Evolution.source
    invoke = evolution.Evolution.invoke
    accepted = evolution.Evolution.accepted
    rejected = evolution.Evolution.rejected

    def test_consumption_return_and_borrow(self):
        self.accepted(RECORD + FUNCS + main('own p:P=create(7);print(ler(p));mudar(p,42);'
                      'own q:P=passar(move(p));print(consumir(move(q)));print(consumir(create(9)));'), '7\n42\n9\n')

    def test_borrowed_return_and_reborrowing(self):
        self.accepted(RECORD + FUNCS + main('own p:P=create(1);{borrow a:P=ver(p);borrow b:P=a;print(ler(b));}'
                      '{borrow mut a:P=exclusivo(p);{borrow b:P=ver(a);print(b.x);}mudar(a,42);}print(p.x);'), '1\n1\n42\n')

    def test_contracts_in_function_values_and_callbacks(self):
        self.accepted(RECORD + FUNCS + 'assis aplicar(f:assis(own P):own P,own p:P):own P{return f(move(p));}' +
                      main('val f:assis(borrow P):int=ler;val g:assis(borrow P):borrow(0) P=ver;'
                           'own p:P=aplicar(passar,create(42));{borrow b:P=g(p);print(f(b));}'), '42\n')
        for declaration in ['val f:assis(P):int=ler;', 'val f:assis(borrow mut P):int=ler;',
                            'val f:assis(own P):P=passar;', 'val f:assis(borrow P):borrow(0) P=exclusivo;']:
            self.rejected(RECORD + FUNCS + main(declaration), 'não é possível usar')

    def test_generic_contracts_preserve_metadata(self):
        self.accepted(RECORD + 'assis id<T>(own v:T):own T{return move(v);}'
                      'assis ref<T>(borrow v:T):borrow(v) T{return v;}' +
                      main('own p:P=id::<P>(new P(42));borrow b:P=ref::<P>(p);print(b.x);'), '42\n')

    def test_use_after_move_and_implicit_copy(self):
        for body, message in [
            ('own p:P=create(1);consumir(p);', 'alocação nova'),
            ('own p:P=create(1);consumir(move(p));print(p.x);', 'movido ou liberado'),
            ('let p:P=create(1);', 'não pode escapar'),
            ('create(1);', 'não pode escapar'),
            ('own p:P=create(1);let q:P=ver(p);', 'não pode escapar'),
            ('let p:P=new P();ler(p);', 'borrow exige'),
            ('own p:P=create(1);borrow b:P=p;consumir(move(p));', 'borrow ativo'),
        ]:
            self.rejected(RECORD + FUNCS + main(body), message)

    def test_return_lifetimes_are_not_inferred_from_type(self):
        for fn, message in [
            ('assis f(borrow p:P):borrow(p) P{own q:P=new P();return q;}', 'referência local'),
            ('assis f(borrow p:P,borrow q:P):borrow(p) P{return q;}', 'parâmetro declarado'),
            ('assis f(own p:P):borrow(p) P{return p;}', 'origem borrow'),
            ('assis f(borrow p:P):borrow mut(p) P{return p;}', 'origem borrow'),
            ('assis f(borrow p:P):P{return p;}', 'não pode escapar'),
            ('assis f():own P{own p:P=new P();return p;}', 'alocação nova'),
        ]:
            self.rejected(RECORD + fn + main(''), message)

    def test_shared_return_cannot_be_upgraded(self):
        for body in ['own p:P=new P();borrow mut b:P=ver(p);',
                     'own p:P=new P();mudar(ver(p),2);']:
            self.rejected(RECORD + FUNCS + main(body), 'compartilhada')

    def test_argument_loans_last_until_call(self):
        f = 'assis misto(borrow p:P,own q:P):int{return p.x+q.x;}'
        self.rejected(RECORD + f + main('own p:P=new P();print(misto(p,move(p)));'), 'borrow ativo')
        f = 'assis dois(borrow mut p:P,borrow q:P):void{}'
        self.rejected(RECORD + f + main('own p:P=new P();dois(p,p);'), 'borrow mut ativo')
        f = 'assis dois(borrow p:P,borrow mut q:P):void{}'
        self.rejected(RECORD + f + main('own p:P=new P();dois(p,p);'), 'incompatível')

    def test_nested_calls_and_saved_assignment_address(self):
        f = 'assis eliminar(own p:Array<int>):int{return 0;}'
        self.rejected(f + main('own a:Array<int>=[1];a[0]=eliminar(move(a));'), 'borrow ativo')
        self.rejected(f + main('own a:Array<int>=[1];a[eliminar(move(a))]=2;'), 'borrow ativo')
        self.rejected(f + main('own a:Array<int>=[1];print(a,eliminar(move(a)));'), 'borrow ativo')
        self.rejected(f + main('own a:Array<int>=[1];a.push(eliminar(move(a)));'), 'borrow ativo')

    def test_nested_reborrow_suspends_parent(self):
        for body in ['own p:P=new P();borrow mut a:P=p;borrow b:P=a;a.x=2;',
                     'own p:P=new P();borrow mut a:P=p;borrow mut b:P=a;print(a.x);']:
            self.rejected(RECORD + main(body), 'mutação' if 'borrow b' in body else 'borrow mut ativo')

    def test_branch_join_uses_only_live_paths(self):
        self.accepted(RECORD + FUNCS + 'assis f(own p:P,b:bool):int{if(b){return consumir(move(p));}return p.x+1;}' +
                      main('print(f(create(41),false),f(create(42),true));'), '42 42\n')
        self.rejected(RECORD + FUNCS + main('own p:P=create(1);if(true){consumir(move(p));}print(p.x);'), 'movido ou liberado')

    def test_loops_cannot_consume_outer_owners_even_in_condition(self):
        f = 'assis end(own p:P):bool{return false;}'
        for body in ['own p:P=new P();while(end(move(p))){}',
                     'own p:P=new P();while(true){consumir(move(p));break;}']:
            self.rejected(RECORD + FUNCS + f + main(body), 'externo dentro de laço')
        self.accepted(RECORD + FUNCS + main('for(let i:int=0;i<100;i+=1){own p:P=create(i);if(i%2==0){continue;}consumir(move(p));}'))

    def test_buffer_contracts_and_bounds(self):
        f = 'assis ver_buffer(borrow p:*int):borrow(p) *int{return p;}assis gravar(borrow mut p:*int):void{p[1]=42;}'
        self.accepted(f + main('own p:*int=alloc<int>(2);gravar(p);borrow b:*int=ver_buffer(p);print(b[1]);'), '42\n')
        source = self.source(f + main('own p:*int=alloc<int>(1);print(ver_buffer(p)[1]);'))
        for flags in [[], ['--no-opt']]:
            result = self.invoke('run', source, *flags)
            self.assertEqual(result.returncode, 70, result.stderr)
            self.assertIn('limite', result.stderr)

    def test_owned_fields_nested_drop_move_and_replacement(self):
        rec = 'struct Caixa<T>{own value:T;let id:int;}struct Par{own a:Caixa<Array<int>>;own b:*int;}'
        self.accepted(rec + main('own p:Par=new Par(new Caixa<Array<int>>([1,2],9),alloc<int>(2));'
                      'own a:Caixa<Array<int>>=move(p.a);p.a=new Caixa<Array<int>>([42],7);'
                      'p.b[1]=3;print(p.a.value[0],a.id,p.b[1]);p.a.value=[4,5];print(len(p.a.value));'), '42 9 3\n2\n')

    def test_partial_move_preserves_sibling_and_partial_drop(self):
        rec = 'struct Par{own a:Array<int>;own b:Array<int>;}'
        self.accepted(rec + main('own p:Par=new Par([1],[42]);own a:Array<int>=move(p.a);print(p.b[0]);free(p);'), '42\n')
        self.rejected(rec + main('own p:Par=new Par([1],[2]);own a:Array<int>=move(p.a);print(p.a[0]);'), 'movido ou liberado')
        self.rejected(rec + main('own p:Par=new Par([1],[2]);own a:Array<int>=move(p.a);own q:Par=move(p);'), 'parcialmente movido')

    def test_owned_field_loans_and_reinitialization_in_branches(self):
        rec = 'struct C{own a:Array<int>;}'
        self.accepted(rec + main('own c:C=new C([1]);{borrow a:Array<int>=c.a;print(a[0]);}'
                      'own a:Array<int>=move(c.a);if(true){c.a=[42];}else{c.a=[7];}print(c.a[0]);'), '1\n42\n')
        self.rejected(rec + main('own c:C=new C([1]);borrow a:Array<int>=c.a;c.a=[2];'), 'mutação')
        self.rejected(rec + main('own c:C=new C([1]);borrow a:Array<int>=c.a;own b:Array<int>=move(c.a);'), 'borrow ativo')

    def test_owned_records_cannot_enter_legacy_or_hide_raw_resources(self):
        self.rejected('struct C{own a:Array<int>;}' + main('let c:C=new C([1]);'), 'não pode escapar')
        self.rejected('struct C{let a:Array<int>;}' + main('own c:C=new C([1]);'), 'campos own explícitos')
        self.accepted('ASSIS C{own a:Array<int>;}' + main('own c:C=new C();'))

    def test_recursive_owned_records_and_empty_fields(self):
        rec = 'struct OwnedList{let n:int;own prox:OwnedList;}'
        self.accepted(rec + main('own a:OwnedList=new OwnedList();a.n=42;'
                      'own b:OwnedList=new OwnedList(7,move(a));print(b.prox.n);'), '42\n')

    def test_owned_parameters_drop_on_all_exits(self):
        f = 'assis f(own a:Array<int>,b:bool):void{if(b){return;}a.push(42);}'
        self.accepted(f + main('for(let i:int=0;i<1000;i+=1){f([1,2],i%2==0);}'))

    def test_shared_derived_results_cannot_mutate_or_free(self):
        for body in ['own p:P=new P();ver(p).x=2;', 'own p:P=new P();free(ver(p));']:
            self.rejected(RECORD + FUNCS + main(body), 'mutação' if '.x=' in body else 'proprietário original')
        f = 'assis ver_array(borrow a:Array<int>):borrow(a) Array<int>{return a;}'
        for body in ['ver_array(a)[0]=2;', 'ver_array(a).push(2);']:
            self.rejected(f + main('own a:Array<int>=[1];' + body), 'mutação')

    def test_safe_profile_and_explicit_legacy_boundary(self):
        safe_main = lambda b: main(b).replace('assis assis_assis', 'safe assis assis_assis')
        self.accepted('assis legado(n:int):int{return n+1;}safe assis f(own a:Array<int>):int{return a[0];}' +
                      safe_main('own a:Array<int>=[42];val s:text="ação";print(f(move(a)),len(s));'
                                'unsafe{let p:*int=alloc<int>(1);p[0]=7;print(legado(p[0]));free(p);}'), '42 6\n8\n')
        for body, message in [
            ('let p:*int=alloc<int>(1);free(p);', 'safe exige own/borrow'),
            ('own p:*byte=alloc<byte>(2);print(text(p));', 'ponteiro gerenciado'),
            ('let s:text="a";', 'safe exige own/borrow'),
            ('val s:text="a";print(bytes(s));', 'text externo'),
            ('print(legado(1));', 'chamada legada'),
            ('val f:assis(int):int=legado;print(f(1));', 'chamada legada'),
            ('unsafe{own a:Array<int>=[1];let b:Array<int>=a;}', 'não pode escapar'),
        ]:
            self.rejected('assis legado(n:int):int{return n;}' + safe_main(body), message)
        self.rejected('safe assis f(p:*int):int{return p[0];}' + main(''), 'safe exige own/borrow na assinatura')
        self.rejected('safe assis f(borrow p:text):int{return len(p);}' + main(''), 'text de vida externa')
        source = self.source(main(''))
        result = self.invoke('check', source, '--safe')
        self.assertEqual(result.returncode, 1)
        self.assertIn('--safe exige entrada', result.stderr)

    def test_safe_function_values_keep_effect_and_ownership(self):
        safe_main = lambda b: main(b).replace('assis assis_assis', 'safe assis assis_assis')
        f = 'safe assis size(borrow a:Array<int>):int{return len(a);}'
        self.accepted(f + safe_main('val f:safe assis(borrow Array<int>):int=size;own a:Array<int>=[1,2];print(f(a));'), '2\n')
        self.rejected('assis legado(n:int):int{return n;}' + main('val f:safe assis(int):int=legado;'), 'não é possível usar')

    def test_managed_functional_library_and_example(self):
        safe_main = lambda b: main(b).replace('assis assis_assis', 'safe assis assis_assis')
        f = '''#yuri <std/algorithms.assis>
pure assis dobro(n:int):int{return n*2;}
pure assis par(n:int):bool{return n%2==0;}
pure assis somar(a:int,b:int):int{return a+b;}
'''
        self.accepted(f + safe_main('own a:Array<int>=[1,2,3,4];own b:Array<int>=map_own::<int,int>(a,dobro);'
                      'own c:Array<int>=filter_own::<int>(a,par);'
                      'print(fold_borrow::<int,int>(b,0,somar),len(c),a[0]);'
                      'own vazio:Array<int>=[];own m:Array<int>=map_own::<int,int>(vazio,dobro);print(len(m));'), '20 2 1\n0\n')
        example = evolution.ROOT / 'exemplos/19_ownership_funcoes.assis'
        result = self.invoke('run', example, '--safe', '--debug')
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, '6 3 24\n4 8 12\n', ''))

    def test_signature_lifetime_and_type_validation(self):
        for declaration in ['assis f(own n:int):int{return n;}',
                            'assis f():own int{return 1;}',
                            'assis f(borrow p:P):borrow(inexistente) P{return p;}',
                            'assis f(cb:assis(borrow P):borrow(1) P):void{}']:
            self.rejected(RECORD + declaration + main(''), 'propriedade exige referência' if 'own n:int' in declaration or 'own int' in declaration else 'origem')
        self.rejected(RECORD + 'assis f(borrow p:P,borrow q:P):borrow(q) P{return q;}' +
                      main('val g:assis(borrow P,borrow P):borrow(0) P=f;'), 'não é possível usar')

    def test_field_lifetimes_and_bounds_survive_function_returns(self):
        rec = 'struct C{own b:*int;}'
        f = 'assis ver(borrow c:C):borrow(c) *int{return c.b;}'
        self.accepted(rec + f + main('own c:C=new C(alloc<int>(2));c.b[1]=42;{borrow b:*int=ver(c);print(b[1]);}'), '42\n')
        self.rejected(rec + f + main('own c:C=new C(alloc<int>(2));borrow b:*int=ver(c);c.b=alloc<int>(3);'), 'mutação')
        source = self.source(rec + f + main('own c:C=new C(alloc<int>(1));print(ver(c)[1]);'))
        for flags in [[], ['--no-opt']]:
            result = self.invoke('run', source, *flags)
            self.assertEqual(result.returncode, 70, result.stderr)
            self.assertIn('limite', result.stderr)

    def test_partial_state_joins_and_recursive_drop(self):
        rec = 'struct C{own a:Array<int>;}'
        self.rejected(rec + main('own c:C=new C([1]);own a:Array<int>=move(c.a);if(true){c.a=[2];}print(c.a[0]);'), 'movido ou liberado')
        rec = 'struct OwnedList{let n:int;own prox:OwnedList;}'
        f = 'assis lista(n:int):own OwnedList{if(n==0){return new OwnedList();}return new OwnedList(n,lista(n-1));}'
        self.accepted(rec + f + main('for(let i:int=0;i<50;i+=1){own l:OwnedList=lista(64);assert(l.prox.n==63);}'))


if __name__ == '__main__':
    program = unittest.main(exit=False, verbosity=2)
    print(f'ASSIS ownership-functions: {evolution.INVOCATIONS} invocações; {evolution.COMPILER}')
    raise SystemExit(not program.result.wasSuccessful())
