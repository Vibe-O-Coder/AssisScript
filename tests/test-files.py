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
        file = self.temp / 'data á 日本 😀.bin'
        path = self.literal(file)
        source = base.main(f'own f:File=file_open({path},1);assert(f!=null);'
                          'own b:*byte=alloc<byte>(4);b[0]=byte(65);b[1]=byte(0);b[2]=byte(255);b[3]=byte(10);'
                          'assert(file_write(f,b,4)==4);assert(file_close(f)==0);'
                          f'own a:File=file_open({path},2);assert(file_write(a,b,4)==4);file_close(a);'
                          f'own r:File=file_open({path},0);print(file_read(r,b,4),b[0],b[1],b[2],b[3]);'
                          'print(file_read(r,b,4),file_read(r,b,4),file_close(r),file_close(r));')
        self.accepted(source, '4 65 0 255 10\n4 0 0 0\n')
        self.assertEqual(file.read_bytes(), bytes([65, 0, 255, 10]) * 2)

    def test_failed_open_invalid_mode_and_closed_resource_recover(self):
        path = self.literal(self.temp / 'missing' / 'data.bin')
        existing = self.literal(self.temp / 'exists.bin')
        error = 6 if os.name == 'nt' else 9
        self.accepted(base.main(f'own f:File=file_open({path},0);assert(f==null);assert(io_error()>0);'
                      f'own g:File=file_open({existing},9);assert(g==null);assert(io_error()>0);'
                      f'own h:File=file_open({existing},1);file_close(h);own b:*byte=alloc<byte>(2);'
                      'print(file_read(h,b,2),io_error(),file_close(h));'), f'-{error} {error} 0\n')

    def test_composite_drop_returns_and_all_control_exits(self):
        path = self.literal(self.temp / 'scope.bin')
        code = 'struct Pack{own file:File;own b:*byte;}'
        code += f'safe fn abrir():own File{{return file_open({path},1);}}'
        code += 'safe fn f(own p:Pack,b:bool):int{if(b){return 1;}return 2;}'
        self.accepted(code + base.main('for(let i:int=0;i<500;i+=1){own p:Pack=new Pack(abrir(),alloc<byte>(8));'
                      'if(i%3==0){continue;}if(i>490){break;}f(move(p),i%2==0);}print(42);'), '42\n')

    def test_no_implicit_copy_or_discard_or_use_after_move(self):
        for body, message in [
            ('file_open("x",0);', 'exige destino own'),
            ('let f:File=file_open("x",0);', 'exige destino own'),
            ('own f:File=file_open("x",0);let g:File=f;', 'não pode escapar'),
            ('own f:File=file_open("x",0);own g:File=move(f);file_close(f);', 'movido ou liberado'),
            ('own f:File=file_open("x",0);borrow r:File=f;file_close(r);', 'compartilhada'),
            ('own f:File=file_open("x",0);borrow r:File=f;file_close(f);', 'incompatível'),
        ]:
            self.rejected(base.main(body), message)

    def test_generics_callbacks_and_borrowed_file_returns(self):
        path = self.literal(self.temp / 'generic.bin')
        code = 'struct Caixa<T>{own value:T;}safe fn caixa<T>(own v:T):own Caixa<T>{return new Caixa<T>(move(v));}'
        code += 'safe fn passar(own f:File):own File{return move(f);}'
        code += 'safe fn observar(borrow mut f:File):borrow mut(f) File{return f;}'
        self.accepted(code + base.main(f'val transferir:safe fn(own File):own File=passar;'
                      f'own c:Caixa<File>=caixa::<File>(transferir(file_open({path},1)));'
                      'print(file_close(observar(c.value)));'), '0\n')

    def test_automatic_drop_preserves_the_error_of_the_operation(self):
        existing = self.literal(self.temp / 'exists.bin')
        missing = self.literal(self.temp / 'missing' / 'data.bin')
        code = 'struct C{own f:File;}'
        code += f'safe fn falhar(own anterior:File):own File{{return file_open({missing},0);}}'
        self.accepted(code + base.main(f'own f:File=falhar(file_open({existing},1));assert(f==null);assert(io_error()>0);'
                      f'own c:C=new C(file_open({existing},1));c.f=file_open({missing},0);'
                      'assert(c.f==null);assert(io_error()>0);print(42);'), '42\n')

    def test_argument_list_utf8_quotes_empty_and_backslashes(self):
        code = 'fn main():int{print(arg_count());for(let i:int=1;i<arg_count();i+=1){'
        code += 'let n:int=arg_size(i);let b:*byte=alloc<byte>(n+1);defer free(b);'
        code += 'print(arg_copy(i,b,n+1),text(b));}return 0;}'
        args = ['á 日本 😀', '', 'com espaço', 'a"b', 'a\\b\\', '\\"teste']
        expected = f'{len(args)+1}\n' + ''.join(f'{len(arg.encode())} {arg}\n' for arg in args)
        for flags in [[], ['--no-opt']]:
            result = self.native(code, args, flags)
            self.assertEqual((result.returncode, result.stdout, result.stderr), (0, expected, ''))

    def test_argument_bounds_preserve_buffer_and_error(self):
        code = 'safe fn main():int{own b:*byte=alloc<byte>(4);b[0]=byte(42);'
        code += 'print(arg_copy(1,b,1),b[0]);print(arg_size(-1),arg_size(999));return 0;}'
        result = self.native(code, ['abc'], ['--safe', '--debug'])
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, '-1 42\n-1 -1\n', ''))

    def test_managed_buffer_capacity_checked_before_os_call(self):
        path = self.literal(self.temp / 'bounds.bin')
        for op in ['file_read', 'file_write']:
            source = self.source(base.main(f'own f:File=file_open({path},1);own b:*byte=alloc<byte>(2);{op}(f,b,3);'))
            for flags in [[], ['--no-opt']]:
                result = self.invoke('run', source, *flags)
                self.assertEqual(result.returncode, 70, result.stderr)
            self.assertIn('tamanho', result.stderr)

    def test_mutable_buffer_loan_is_required(self):
        self.rejected(base.main('own f:File=file_open("x",0);own b:*byte=alloc<byte>(8);borrow r:*byte=b;file_read(f,r,8);'), 'buffer mutável')
        self.rejected('pure fn f():int{return arg_count();}' + base.main(''), 'pure')


if __name__ == '__main__':
    suite = unittest.TestSuite(Files(name) for name in Files.__dict__ if name.startswith('test_'))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    print(f'ASSIS files: {base.INVOCATIONS} invocações; {base.COMPILER}')
    raise SystemExit(not result.wasSuccessful())
