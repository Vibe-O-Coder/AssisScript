"""Native managed IO, Unicode arguments, failure recovery and bounded streaming."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import unittest

spec = importlib.util.spec_from_file_location('evolution', Path(__file__).with_name('test-evolution.py'))
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)


class Files(base.Evolution):
    def literal(self, path):
        return json.dumps(str(path).replace('\\', '/'), ensure_ascii=False)

    def native(self, text, args=(), flags=()):
        source = self.source(text)
        binary = self.temp / ('app.exe' if os.name == 'nt' else 'app')
        built = self.invoke('build', source, '-o', binary, *flags)
        self.assertEqual(built.returncode, 0, built.stderr)
        return subprocess.run([str(binary), *map(str, args)], capture_output=True, text=True, encoding='utf-8', timeout=30)

    def test_binary_unicode_path_roundtrip_and_append(self):
        file = self.temp / 'dados á 日本 😀.bin'
        path = self.literal(file)
        source = base.main(f'own f:Arquivo=arquivo_abrir({path},1);assert(f!=null);'
                          'own b:*byte=alloc<byte>(4);b[0]=byte(65);b[1]=byte(0);b[2]=byte(255);b[3]=byte(10);'
                          'assert(arquivo_escrever(f,b,4)==4);assert(arquivo_fechar(f)==0);'
                          f'own a:Arquivo=arquivo_abrir({path},2);assert(arquivo_escrever(a,b,4)==4);arquivo_fechar(a);'
                          f'own r:Arquivo=arquivo_abrir({path},0);print(arquivo_ler(r,b,4),b[0],b[1],b[2],b[3]);'
                          'print(arquivo_ler(r,b,4),arquivo_ler(r,b,4),arquivo_fechar(r),arquivo_fechar(r));')
        self.accepted(source, '4 65 0 255 10\n4 0 0 0\n')
        self.assertEqual(file.read_bytes(), bytes([65, 0, 255, 10]) * 2)

    def test_failed_open_invalid_mode_and_closed_resource_recover(self):
        path = self.literal(self.temp / 'missing' / 'data.bin')
        existing = self.literal(self.temp / 'exists.bin')
        error = 6 if os.name == 'nt' else 9
        self.accepted(base.main(f'own f:Arquivo=arquivo_abrir({path},0);assert(f==null);assert(erro_io()>0);'
                      f'own g:Arquivo=arquivo_abrir({existing},9);assert(g==null);assert(erro_io()>0);'
                      f'own h:Arquivo=arquivo_abrir({existing},1);arquivo_fechar(h);own b:*byte=alloc<byte>(2);'
                      'print(arquivo_ler(h,b,2),erro_io(),arquivo_fechar(h));'), f'-{error} {error} 0\n')

    def test_composite_drop_returns_and_all_control_exits(self):
        path = self.literal(self.temp / 'scope.bin')
        code = 'struct Pack{own file:Arquivo;own b:*byte;}'
        code += f'safe assis abrir():own Arquivo{{return arquivo_abrir({path},1);}}'
        code += 'safe assis f(own p:Pack,b:bool):int{if(b){return 1;}return 2;}'
        self.accepted(code + base.main('for(let i:int=0;i<500;i+=1){own p:Pack=new Pack(abrir(),alloc<byte>(8));'
                      'if(i%3==0){continue;}if(i>490){break;}f(move(p),i%2==0);}print(42);'), '42\n')

    def test_no_implicit_copy_or_discard_or_use_after_move(self):
        for body, message in [
            ('arquivo_abrir("x",0);', 'exige destino own'),
            ('let f:Arquivo=arquivo_abrir("x",0);', 'exige destino own'),
            ('own f:Arquivo=arquivo_abrir("x",0);let g:Arquivo=f;', 'não pode escapar'),
            ('own f:Arquivo=arquivo_abrir("x",0);own g:Arquivo=move(f);arquivo_fechar(f);', 'movido ou liberado'),
            ('own f:Arquivo=arquivo_abrir("x",0);borrow r:Arquivo=f;arquivo_fechar(r);', 'compartilhada'),
            ('own f:Arquivo=arquivo_abrir("x",0);borrow r:Arquivo=f;arquivo_fechar(f);', 'incompatível'),
        ]:
            self.rejected(base.main(body), message)

    def test_generics_callbacks_and_borrowed_file_returns(self):
        path = self.literal(self.temp / 'generic.bin')
        code = 'struct Caixa<T>{own valor:T;}safe assis caixa<T>(own v:T):own Caixa<T>{return new Caixa<T>(move(v));}'
        code += 'safe assis passar(own f:Arquivo):own Arquivo{return move(f);}'
        code += 'safe assis observar(borrow mut f:Arquivo):borrow mut(f) Arquivo{return f;}'
        self.accepted(code + base.main(f'val transferir:safe assis(own Arquivo):own Arquivo=passar;'
                      f'own c:Caixa<Arquivo>=caixa::<Arquivo>(transferir(arquivo_abrir({path},1)));'
                      'print(arquivo_fechar(observar(c.valor)));'), '0\n')

    def test_automatic_drop_preserves_the_error_of_the_operation(self):
        existing = self.literal(self.temp / 'exists.bin')
        missing = self.literal(self.temp / 'missing' / 'data.bin')
        code = 'struct C{own f:Arquivo;}'
        code += f'safe assis falhar(own anterior:Arquivo):own Arquivo{{return arquivo_abrir({missing},0);}}'
        self.accepted(code + base.main(f'own f:Arquivo=falhar(arquivo_abrir({existing},1));assert(f==null);assert(erro_io()>0);'
                      f'own c:C=new C(arquivo_abrir({existing},1));c.f=arquivo_abrir({missing},0);'
                      'assert(c.f==null);assert(erro_io()>0);print(42);'), '42\n')

    def test_argument_list_utf8_quotes_empty_and_backslashes(self):
        code = 'assis assis_assis():int{print(argumentos());for(let i:int=1;i<argumentos();i+=1){'
        code += 'let n:int=argumento_tamanho(i);let b:*byte=alloc<byte>(n+1);defer free(b);'
        code += 'print(argumento_copiar(i,b,n+1),text(b));}return 0;}'
        args = ['á 日本 😀', '', 'com espaço', 'a"b', 'a\\b\\', '\\"teste']
        expected = f'{len(args)+1}\n' + ''.join(f'{len(arg.encode())} {arg}\n' for arg in args)
        for flags in [[], ['--no-opt']]:
            result = self.native(code, args, flags)
            self.assertEqual((result.returncode, result.stdout, result.stderr), (0, expected, ''))

    def test_argument_bounds_preserve_buffer_and_error(self):
        code = 'safe assis assis_assis():int{own b:*byte=alloc<byte>(4);b[0]=byte(42);'
        code += 'print(argumento_copiar(1,b,1),b[0]);print(argumento_tamanho(-1),argumento_tamanho(999));return 0;}'
        result = self.native(code, ['abc'], ['--safe', '--debug'])
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, '-1 42\n-1 -1\n', ''))

    def test_managed_buffer_capacity_checked_before_os_call(self):
        path = self.literal(self.temp / 'bounds.bin')
        for op in ['arquivo_ler', 'arquivo_escrever']:
            source = self.source(base.main(f'own f:Arquivo=arquivo_abrir({path},1);own b:*byte=alloc<byte>(2);{op}(f,b,3);'))
            for flags in [[], ['--no-opt']]:
                result = self.invoke('run', source, *flags)
                self.assertEqual(result.returncode, 70, result.stderr)
                self.assertIn('tamanho', result.stderr)

    def test_mutable_buffer_loan_is_required(self):
        self.rejected(base.main('own f:Arquivo=arquivo_abrir("x",0);own b:*byte=alloc<byte>(8);borrow r:*byte=b;arquivo_ler(f,r,8);'), 'buffer mutável')
        self.rejected('pure assis f():int{return argumentos();}' + base.main(''), 'pure')


if __name__ == '__main__':
    suite = unittest.TestSuite(Files(name) for name in Files.__dict__ if name.startswith('test_'))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    print(f'ASSIS files: {base.INVOCATIONS} invocações; {base.COMPILER}')
    raise SystemExit(not result.wasSuccessful())
