"""Native regressions for encapsulation and the first functional increment.

Run this same suite on Windows and Linux. ASSIS_BIN selects a candidate build.
All rejected sources are checked before any generated program can run.
"""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent.parent
COMPILER = Path(os.environ.get('ASSIS_BIN', ROOT / 'bin' / ('assis.exe' if os.name == 'nt' else 'assis'))).resolve()
INVOCATIONS = 0


def main(body):
    return 'fn main(): int {' + body + 'return 0;}'


class Evolution(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix='assis-evolution-')
        self.addCleanup(self.directory.cleanup)
        self.temp = Path(self.directory.name)

    def source(self, text, name='main.assis'):
        file = self.temp / name
        file.write_text(text, encoding='utf-8')
        return file

    def invoke(self, *args, input=None):
        global INVOCATIONS
        INVOCATIONS += 1
        # Historical corpus deliberately exercises legacy APIs. New safety
        # regressions override this with a direct invocation of the default.
        if args and args[0] in ('check','build','run','ir','lock','doc','test') and '--safe' not in args and '--legacy' not in args:
            args = (*args, '--legacy')
        return subprocess.run([str(COMPILER), *map(str, args)], input=input,
                              capture_output=True, text=True, encoding='utf-8', timeout=30)

    def rejected(self, text, message):
        file = self.source(text)
        output = self.temp / 'sentinel.exe'
        for mode in ['check', 'build', 'run']:
            for flags in [[], ['--no-opt']]:
                output.write_bytes(b'preservar')
                extra = ['-o', output] if mode == 'build' else []
                result = self.invoke(mode, file, *extra, *flags, '--diagnostics=json')
                self.assertEqual(result.returncode, 1, (mode, text, result.stderr))
                diagnostic = json.loads(result.stderr)
                self.assertEqual(diagnostic['code'], 'A001')
                self.assertIn(message, diagnostic['message'], text)
                self.assertEqual(output.read_bytes(), b'preservar')
        for target in ['windows-x64', 'linux-x64']:
            result = self.invoke('build', file, '--target', target, '-o', output, '--diagnostics=json')
            self.assertEqual(result.returncode, 1, result.stderr)
            self.assertIn(message, json.loads(result.stderr)['message'])

    def accepted(self, text, stdout=''):
        file = self.source(text)
        for flags in [[], ['--no-opt']]:
            checked = self.invoke('check', file, *flags)
            self.assertEqual(checked.returncode, 0, checked.stderr)
            ran = self.invoke('run', file, '--debug', *flags)
            self.assertEqual((ran.returncode, ran.stdout, ran.stderr), (0, stdout, ''))
        for target in ['windows-x64', 'linux-x64']:
            binary = self.temp / (target + '.exe')
            built = self.invoke('build', file, '--target', target, '-o', binary)
            self.assertEqual(built.returncode, 0, built.stderr)
            self.assertTrue(binary.exists())

    def test_all_collection_fields_are_private(self):
        for ty, fields in [('Array<int>', ['_length', '_capacity', '_data']),
                           ('HashMap<int,int>', ['_length', '_capacity', '_used', '_keys', '_values', '_states'])]:
            for field in fields:
                with self.subTest(ty=ty, field=field):
                    self.rejected(main(f'let a:{ty}=new {ty}();print(a.{field});'), 'campo privado')

    def test_aliases_borrows_indirection_and_nested_types(self):
        bodies = [
            'own a:Array<int>=[1];a._length=999999;',
            'own a:Array<int>=[1];print(a._data[999999]);',
            'let a:Array<int>=[1];let b:Array<int>=a;b._capacity=9;',
            'own a:Array<int>=[1];borrow b:Array<int>=a;print(b._data);',
            'own a:Array<int>=[1];borrow mut b:Array<int>=a;b._length=9;',
            'let a:Array<int>=[1];let p:*Array<int>=&a;print((*p)._data);',
            'let a:Array<Array<int>>=[[]];print(a[0]._length);',
            'let a:Array<int>=[1];let p:*int=&a._length;',
        ]
        for body in bodies:
            with self.subTest(body=body):
                self.rejected(main(body), 'campo privado')
        self.rejected('fn create():Array<int>{return [1];}' + main('print(create()._data);'), 'campo privado')
        self.rejected('struct S {let itens:Array<int>;}' + main('let s:S=new S([1]);print(s.itens._data);'), 'campo privado')

    def test_collection_private_methods(self):
        for call in ['_hash(1)', '_find(1)', '_rehash(8)']:
            self.rejected(main('let m:HashMap<int,int>=new HashMap<int,int>();m.' + call + ';'), 'método privado')

    def test_private_members_are_nominal_not_filename_privileges(self):
        cls = 'class Cofre {private let segredo:int;private fn value():int{return self.segredo;}fn ler():int{return self.value();}}'
        self.rejected(cls + main('let c:Cofre=new Cofre();print(c.segredo);'), 'campo privado')
        self.rejected(cls + main('let c:Cofre=new Cofre();print(c.value());'), 'método privado')
        self.rejected(cls + 'class Filho extends Cofre {fn ler_segredo():int{return self.segredo;}}' + main(''), 'campo privado')
        self.rejected(cls + 'class Filho extends Cofre {fn value():int{return 0;}}' + main(''), 'sobrescrita')
        self.rejected('class A {fn v():int{return 1;}} class B extends A {private fn v():int{return 2;}}' + main(''), 'sobrescrita')
        self.rejected('struct Oculto {private let v:int;}' + main('let p:Oculto=new Oculto(1);'), 'campo privado')
        self.rejected('class Oculto {private fn init():void{}}' + main('let o:Oculto=new Oculto();'), 'inicializador privado')
        result = self.invoke('check', '<colecoes>.assis', '--stdin', '--diagnostics=json',
                             input='class __assis_falso {}' + main(''))
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn('reservado', json.loads(result.stderr)['message'])

    def test_private_positive_paths_and_underscore_is_not_visibility(self):
        self.accepted('class C {private let value:int;let _publico:int;private fn somar(n:int):int{return self.value+n;}fn init():void{self.value=40;}fn ler(outro:C):int{return outro.somar(2);}}' +
                      main('let c:C=new C();c._publico=7;print(c.ler(c),c._publico);free(c);'), '42 7\n')

    def test_collections_keep_bounds_and_public_operations(self):
        self.accepted(main('own a:Array<int>=[1,2];a.push(3);a[0]+=4;own m:HashMap<int,int>=new HashMap<int,int>();m.set(1,a[0]);print(len(a),m.get(1));'), '3 5\n')
        for flags in [[], ['--no-opt']]:
            result = self.invoke('run', self.source(main('own a:Array<int>=[1];print(a[999999]);')), *flags)
            self.assertEqual(result.returncode, 70, result.stderr)
            self.assertIn('limite', result.stderr)

    def test_standard_library_internals_and_reuse(self):
        for source, body in [('strings', 'let t:String=new String();print(t._dados);'),
                             ('csv', 'let d:CsvDocument=new CsvDocument();print(d._campos);')]:
            self.rejected('import \"std/' + source + '.assis\";\n' + main(body), 'campo privado')
        self.accepted('import "std/csv.assis";\n' + main('let d:CsvDocument=read_csv("a,b",byte(44));assert(d.ok);d.parse("c",byte(44));d.parse(d.rows[0][0],byte(44));print(d.rows[0][0]);d.parse("",byte(44));assert(d.ok && len(d.rows)==0);d.dispose();free(d);'), 'c\n')

    def test_val_values_scope_and_legacy_mutability(self):
        self.accepted(main('val a:int=42;val b:byte=byte(255);val c:bool=true;val s:text="ação";{val a:int=7;print(a);}let x:int=a;x+=1;print(a,b,c,len(s),x);'), '7\n42 255 true 6 43\n')
        for body, message in [
            ('val a:int=1;a=2;', 'imutável'), ('val a:int=1;a+=1;', 'imutável'),
            ('val a:int=1;let p:*int=&a;', 'imutável'),
            ('val a:text="a";let p:*text=&a;', 'imutável'),
            ('val a:Array<int>=[1];', 'val aceita'),
            ('for(val i:int=0;i<2;i+=1){}', 'imutável')]:
            self.rejected(main(body), message)

    def test_pure_composition_recursion_and_local_state(self):
        funcs = '''pure fn dobro(n:int):int{return n*2;}
pure fn composto(n:int):int{val d:int=dobro(n);return d+1;}
pure fn fat(n:int):int{if(n<2){return 1;}return n*fat(n-1);}
pure fn par(n:int):bool{if(n==0){return true;}return impar(n-1);}
pure fn impar(n:int):bool{if(n==0){return false;}return par(n-1);}
pure fn soma(n:int):int{let total:int=0;for(let i:int=0;i<n;i+=1){total+=i;}return total;}
pure fn estreitar(n:int):byte{return byte(n);}
'''
        self.accepted(funcs + main('print(composto(20),fat(10),par(10),soma(100),estreitar(256));'), '41 3628800 true 4950 0\n')

    def test_pure_rejects_effects_even_in_unreachable_branches(self):
        bodies = ['print(n);return n;', 'return monotonic_ms();', 'let p:*int=alloc<int>(1);return n;',
                  'let p:*byte=alloc<byte>(1);return n;', 'assert(true);return n;',
                  'if(false){print(1);}return n;', 'let a:Array<int>=[1];return n;',
                  'let s:text="a";return n;', 'free(null);return n;',
                  'let p:*int=&n;return n;', 'n=2;return n;']
        for body in bodies:
            self.rejected('pure fn f(n:int):int{' + body + '}' + main(''), 'pure' if 'n=2;' not in body else 'imutável')
        self.rejected('fn efeito(n:int):int{print(n);return n;}pure fn f(n:int):int{return efeito(n);}' + main(''), 'com efeitos')
        self.rejected('pure fn f(n:int):int{return g(n);}pure fn g(n:int):int{return monotonic_ms();}' + main(''), 'pure')

    def test_pure_signature_boundaries(self):
        for declaration in ['pure fn f(n:*int):int{return 1;}', 'pure fn f(n:text):int{return 1;}',
                            'pure fn f():text{return "a";}', 'pure fn f():void{return;}']:
            self.rejected(declaration + main(''), 'pure')

    def test_module_diagnostics_preserve_origin(self):
        library = self.source('pure fn proibido():int {\n return monotonic_ms();\n}', 'lib.assis')
        file = self.source('import "lib.assis";\n' + main(''))
        result = self.invoke('check', file, '--diagnostics=json')
        diagnostic = json.loads(result.stderr)
        self.assertEqual((result.returncode, diagnostic['file'], diagnostic['line']), (1, str(library), 2))
        library.write_text('pure fn dobro(n:int):int{return n*2;}', encoding='utf-8')
        self.accepted('import "lib.assis";\n' + main('print(dobro(21));'), '42\n')


if __name__ == '__main__':
    program = unittest.main(exit=False, verbosity=2)
    print(f'ASSIS evolution: {INVOCATIONS} invocações; {os.name}; {COMPILER}')
    raise SystemExit(not program.result.wasSuccessful())
