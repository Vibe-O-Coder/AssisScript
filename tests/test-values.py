"""Copy values, tagged unions, exhaustive matching and aggregate ABI on both targets."""
import importlib.util
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location('evolution', Path(__file__).with_name('test-evolution.py'))
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
main = base.main
POINT = 'value struct P{let x:int;let y:int;}'
OPTION = 'enum O<T>{None;Some(T);}'


class Values(base.Evolution):
    # Reuse the harness without inheriting its test cases a second time.
    def test_records_copy_independently(self):
        self.accepted(POINT + main('let p:P=new P(1,2);val q:P=p;p=new P(40,2);print(p.x,q.x,p==q,q==new P(1,2));'),
                      '40 1 fOdAsE aSsIs\n')

    def test_tail_recursion_preserves_argument_order_and_value_results(self):
        code = POINT + 'pure assis f(n:int,a:P):P{if(n==0){return a;}return f(n-1,new P(a.y,a.x+1));}'
        self.accepted(code + main('val p:P=f(100,new P(1,2));print(p.x,p.y);'), '51 52\n')
        source = self.source(code + main('val p:P=f(1000000,new P(1,2));print(p.x,p.y);'))
        result = self.invoke('run', source, '--debug')
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, '500001 500002\n', ''))
        result = self.invoke('run', source, '--no-opt')
        self.assertEqual(result.returncode, 70)
        self.assertIn('pilha', result.stderr)

    def test_nested_layout_and_zero_padding(self):
        self.accepted(POINT + 'value struct N{let b:byte;let p:P;let flag:bool;}' +
                      main('val n:N=new N(byte(255),new P(20,22),true);val z:N=new N();'
                           'print(n.b,n.p.x+n.p.y,n.flag,z==new N(byte(0),new P(0,0),false));'),
                      '255 42 aSsIs aSsIs\n')

    def test_layout_and_frame_limits_are_checked_without_expansion(self):
        fields = ''.join(f'let x{i}:int;' for i in range(512))
        code = 'value struct C{' + fields + '}pure assis id(c:C):C{return c;}'
        self.accepted(code + main('val c:C=id(new C());print(c.x511);'), '0\n')
        self.rejected('value struct C{' + fields + 'let extra:int;}' + main(''), 'excede 4096')
        recursive = ''.join(f'value struct C{i}{{let c:C{i+1};}}' for i in range(64)) + 'value struct C64{}'
        self.rejected(recursive + main(''), '64 níveis')
        self.rejected(code + main(''.join('new C();' for _ in range(4100))), 'frame de função')

    def test_managed_functional_callbacks_with_copy_records(self):
        code = '#yuri <std/algoritmos.assis>\n' + POINT
        code += 'pure assis dobro(p:P):P{return new P(p.x*2,p.y*2);}pure assis soma(a:int,p:P):int{return a+p.x+p.y;}'
        self.accepted(code + main('own a:Array<P>=[new P(20,1)];own b:Array<P>=map_own::<P,P>(a,dobro);'
                      'print(fold_borrow::<P,int>(b,0,soma));'), '42\n')

    def test_function_values_and_composite_returns(self):
        code = POINT + 'pure assis f(p:P,n:int):P{return new P(p.x+n,p.y);}'
        self.accepted(code + main('val g:pure assis(P,int):P=f;val p:P=g(new P(20,2),20);print(p.x+p.y);'), '42\n')

    def test_callbacks_in_records_and_symbolic_match_bindings(self):
        code = POINT + 'value struct F{let f:pure assis(P):P;}enum E<T>{None;Some(pure assis(T):T);}'
        code += 'assis executar(n:int):int{print("efeito");return n;}'
        code += 'pure assis dobro(p:P):P{return new P(p.x*2,p.y*2);}'
        code += 'pure assis aplicar<T>(e:E<T>,v:T):T{match(e){None{return v;}Some(executar){return executar(v);}}}'
        self.accepted(code + main('val f:F=new F(dobro);val p:P=f.f(new P(10,11));'
                      'val q:P=aplicar::<P>(new E<P>.Some(dobro),p);print(q.x+q.y);'), '84\n')

    def test_virtual_and_generic_methods_return_values(self):
        code = POINT + 'ASSIS A<T>{let v:T;assis assis_fodase(v:T):void{self.v=v;}assis get():T{return self.v;}}'
        code += 'ASSIS B extends A<P>{assis get():P{return new P(20,22);}}'
        self.accepted(code + main('let b:B=new B(new P(1,2));let a:A<P>=b;print(a.get().x+a.get().y);free(b);'), '42\n')

    def test_aggregate_arguments_snapshot_before_later_effects(self):
        code = POINT + 'assis mudar(p:*P):int{p[0]=new P(90,0);return 2;}'
        code += 'assis ler(p:P,n:int):int{return p.x+n;}'
        self.accepted(code + main('let p:*P=alloc<P>(1);p[0]=new P(40,0);print(ler(p[0],mudar(p)),p[0].x);free(p);'), '42 90\n')

    def test_arrays_maps_buffers_and_legacy_embedded_values(self):
        code = POINT + 'struct Caixa{let n:byte;let p:P;own b:*byte;}'
        self.accepted(code + main('own a:Array<P>=[new P(20,1)];a.push(new P(40,2));a.reverse();print(a.pop().x,a[0].y);'
                      'own m:HashMap<int,P>=new HashMap<int,P>();m.set(7,new P(20,22));print(m.get(7).x+m.get(7).y);'
                      'own c:Caixa=new Caixa(byte(7),new P(1,2),alloc<byte>(2));c.b[1]=byte(42);print(c.p.y,c.b[1]);'), '20 2\n42\n2 42\n')

    def test_enum_nested_generic_and_exhaustive_returns(self):
        code = POINT + OPTION + 'pure assis f(o:O<P>):int{match(o){None{return 0;}Some(p){return p.x+p.y;}}}'
        self.accepted(code + main('print(f(new O<P>.Some(new P(20,22))),f(new O<P>.None()));'), '42 0\n')

    def test_enum_union_size_canonical_and_copy(self):
        code = POINT + 'enum E{A;B(P,byte);C(bool);}'
        self.accepted(code + main('let a:E=new E.B(new P(1,2),byte(3));a=new E.C(true);print(a==new E.C(true),new E.A()==new E.A());'
                      'match(a){A{print(0);}B(p,b){print(p.x,b);}C(v){print(v);}}'), 'aSsIs aSsIs\naSsIs\n')

    def test_match_evaluates_subject_once_and_preserves_scope(self):
        code = OPTION + 'assis f():O<int>{print(1);return new O<int>.Some(42);}'
        self.accepted(code + main('let x:int=7;match(f()){Some(x){print(x);}None{print(0);}}print(x);'), '1\n42\n7\n')

    def test_match_flow_joins_only_continuing_arms(self):
        code = OPTION + 'struct R{let n:int;}assis f(o:O<int>,own p:R):int{match(o){None{free(p);return 1;}Some(x){print(x);}}return p.n;}'
        self.accepted(code + main('print(f(new O<int>.Some(7),new R(42)));'), '7\n42\n')
        self.rejected(OPTION + 'struct R{let n:int;}' + main('own p:R=new R(1);match(new O<int>.None()){None{free(p);}Some(x){print(x);}}print(p.n);'), 'movido ou liberado')

    def test_match_break_continue_and_drop(self):
        code = OPTION + 'struct R{let n:int;}'
        self.accepted(code + main('for(let i:int=0;i<3;i+=1){own r:R=new R(i);match(new O<int>.Some(i)){None{break;}Some(x){if(x<2){continue;}print(x);}}}'), '2\n')

    def test_result_option_standard_library(self):
        self.accepted('#yuri <std/erros.assis>\npure assis dobro(n:int):int{return n*2;}' +
                      main('print(option_or::<int>(option_map::<int,int>(new Option<int>.Some(21),dobro),0));'
                           'match(result_map::<int,int,int>(new Result<int,int>.Err(7),dobro)){Ok(v){print(v);}Err(e){print(e);}}'), '42\n7\n')

    def test_immutable_deep_fields_and_binding(self):
        for body in ['val p:P=new P(1,2);p.x=3;', 'let p:P=new P();let q:*P=&p;', 'val p:P=new P();p=new P();']:
            self.rejected(POINT + main(body), 'posição gravável' if '.x=' in body else 'imutável')
        self.rejected(OPTION + main('match(new O<int>.Some(1)){None{}Some(x){x=2;}}'), 'imutável')

    def test_rejected_layout_and_ownership(self):
        for decl in ['value struct C{let p:*int;}', 'value struct C{let t:text;}',
                     'value struct C{own a:Array<int>;}', 'value struct C{let f:assis():int;}']:
            self.rejected(decl + main(''), 'valor Copy')
        self.rejected('value struct C{let c:C;}' + main(''), 'ciclo de layout')
        self.rejected(POINT + 'assis f(own p:P):void{}' + main(''), 'contrato de propriedade')
        self.rejected(POINT + main('own p:P=new P();'), 'valor Copy não aceita own')
        self.rejected(OPTION + main('own o:O<int>=new O<int>.None();'), 'valor Copy não aceita own')
        self.rejected(POINT + 'struct C{own p:P;}' + main(''), 'valor Copy não aceita own')
        self.rejected(POINT + main('val p:P=new P();borrow q:P=p;'), 'borrow exige')
        self.rejected(POINT + main('val p:P=new P();free(p);'), 'libera apenas')

    def test_match_diagnostics_and_constructors(self):
        for body, message in [
            ('match(new O<int>.None()){None{}}', 'não exaustivo'),
            ('match(new O<int>.None()){None{}None{}Some(x){}}', 'repetida'),
            ('match(new O<int>.None()){None{}Other{}}', 'inexistente'),
            ('match(new O<int>.None()){None{}Some{}}', 'padrão exige'),
            ('val o:O<int>=new O<int>();', 'exige .Variante'),
            ('val o:O<int>=new O<int>.Some();', 'variante exige'),
            ('val o:O<int>=new O<int>.Some(true);', 'não é possível usar'),
        ]:
            self.rejected(OPTION + main(body), message)
        self.rejected('enum E{A;A;}' + main(''), 'duplicada')
        self.rejected('enum E{}' + main(''), 'ao menos')

    def test_pure_unused_templates_reject_effects_inside_match(self):
        self.rejected(OPTION + 'pure assis f<T>(o:O<T>):int{match(o){None{return 0;}Some(x){print(x);return 1;}}}' + main(''), 'template pure')

    def test_safe_value_construction_and_buffer_bounds(self):
        source = self.source(POINT + 'safe assis assis_assis():int{val p:P=new P(20,22);own b:*P=alloc<P>(1);b[0]=p;print(b[0].x+b[0].y);return 0;}')
        for flags in [[], ['--no-opt']]:
            result = self.invoke('run', source, '--safe', '--debug', *flags)
            self.assertEqual((result.returncode, result.stdout, result.stderr), (0, '42\n', ''))
        source = self.source(POINT + main('own b:*P=alloc<P>(1);print(b[1].x);'))
        for flags in [[], ['--no-opt']]:
            result = self.invoke('run', source, *flags)
            self.assertEqual(result.returncode, 70, result.stderr)
            self.assertIn('limite', result.stderr)


if __name__ == '__main__':
    # Only cases defined by this increment, sharing the existing invocation harness.
    tests = [name for name in Values.__dict__ if name.startswith('test_')]
    suite = unittest.TestSuite(Values(name) for name in tests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    print(f'ASSIS values: {base.INVOCATIONS} invocações; {base.COMPILER}')
    raise SystemExit(not result.wasSuccessful())
