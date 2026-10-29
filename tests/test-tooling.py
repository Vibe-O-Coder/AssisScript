"""Native formatter/test/doc commands and real ELF source debugging."""
import importlib.util
import json
import os
import sys
import platform
import shutil
import subprocess
import unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location('evolution',Path(__file__).with_name('test-evolution.py'));base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)

class Tooling(base.Evolution):
    def test_formatter_idempotence_comments_strings_and_crlf(self):
        text='// { } 😀\r\nfn main():int {\r\nprint("{ ação }");  \r\nif(true){\r\n/* { */ print(42);\r\n}\r\nreturn 0;\r\n}\r\n'
        source=self.source(text);before=source.read_bytes();r=self.invoke('fmt',source,'--check');self.assertEqual(r.returncode,1);self.assertEqual(source.read_bytes(),before)
        r=self.invoke('fmt',source);self.assertEqual(r.returncode,0,r.stderr);formatted=source.read_bytes();self.assertIn(b'\n    print(',formatted);self.assertIn(b'\n        /* { */ print(42);',formatted);self.assertNotIn(b'\r',formatted)
        r=self.invoke('fmt',source);self.assertEqual(r.returncode,0,r.stderr);self.assertEqual(source.read_bytes(),formatted);self.assertEqual(self.invoke('fmt',source,'--check').returncode,0)
        r=self.invoke('run',source);self.assertEqual((r.returncode,r.stdout), (0,'{ ação }\n42\n'))

    def test_formatter_lexical_error_does_not_replace(self):
        for text in ['fn f():void{','fn f():void{print("unterminated);}','}']:
            source=self.source(text);before=source.read_bytes();r=self.invoke('fmt',source);self.assertNotEqual(r.returncode,0);self.assertEqual(source.read_bytes(),before)

    def test_native_test_driver_owns_resources_and_checks_returns(self):
        source=self.source('safe fn test_one():void{own a:Array<int>=[1,2];assert(len(a)==2);}pure fn teste_two():bool{return true;}safe fn test_three():int{return 0;}fn main():int{return 99;}')
        for flags in [[],['--no-opt']]:
            r=self.invoke('test',source,'--safe','--debug',*flags);self.assertEqual((r.returncode,r.stdout,r.stderr),(0,'ASSIS: 3 testes passaram\n',''))
        for text in ['fn test_fail():bool{return false;}','fn test_fail():int{return 1;}','fn test_fail():void{assert(false);}']:
            r=self.invoke('test',self.source(text));self.assertEqual(r.returncode,70,r.stderr)
        r=self.invoke('test',self.source('fn normal():void{}'));self.assertEqual(r.returncode,1);self.assertIn('nenhum teste',r.stderr)

    def test_doc_public_api_generics_lifetimes_and_protected_output(self):
        source=self.source('namespace demo;\n/// Identidade documentada.\npublic pure fn id<T>(x:T):T{return x;}\nfn oculto():int{return 7;}\npublic safe fn view(borrow a:*byte):borrow(a) *byte{return a;}\npublic value struct P{let x:int;}')
        output=self.temp/'API.md';r=self.invoke('doc',source,'-o',output);self.assertEqual(r.returncode,0,r.stderr);text=output.read_text(encoding='utf-8');self.assertIn('Identidade documentada',text);self.assertIn('demo::id<T>',text);self.assertIn('borrow(a)',text);self.assertNotIn('oculto',text)
        before=source.read_bytes();r=self.invoke('doc',source,'-o',source);self.assertNotEqual(r.returncode,0);self.assertEqual(source.read_bytes(),before)

    def test_debug_maps_and_elf_sections_match_sources(self):
        source=self.source('pure fn dobro(x:int):int {\nreturn x*2;\n}\nfn main():int {\nprint(dobro(21));\nreturn 0;\n}\n')
        for target in ['windows-x64','linux-x64','linux-arm64','macos-x64','macos-arm64']:
            binary=self.temp/(target+'.exe');r=self.invoke('build',source,'--symbols','--target',target,'-o',binary);self.assertEqual(r.returncode,0,r.stderr)
            mapping=json.loads(Path(str(binary)+'.map.json').read_text(encoding='utf-8'));self.assertEqual(mapping['format'],'AssisScript-map-v1');self.assertTrue(any(f['name']=='dobro' and f['size']>0 for f in mapping['functions']));self.assertTrue(any(s['line']==5 for s in mapping['lines']));self.assertTrue(all(s['file']==str(source) for s in mapping['lines']))
            if sys.platform=='linux' and target==('linux-arm64' if platform.machine().lower() in ('arm64','aarch64') else 'linux-x64'):
                r=subprocess.run(['readelf','--debug-dump=decodedline','--debug-dump=info',binary],capture_output=True,text=True,timeout=15);self.assertEqual(r.returncode,0,r.stderr);self.assertEqual(r.stderr,'');self.assertIn('DW_TAG_subprogram',r.stdout)
                self.assertIsNotNone(shutil.which('gdb'),'GDB é necessário para validate o gate de depuração')
                r=subprocess.run(['gdb','-nx','-nh','-batch','-ex','break '+str(source)+':2','-ex','run','-ex','bt','-ex','info line',binary],capture_output=True,text=True,timeout=20)
                self.assertEqual(r.returncode,0,r.stderr);self.assertIn('Breakpoint 1, dobro',r.stdout);self.assertIn('main',r.stdout);self.assertIn('line 2',r.stdout.lower())

if __name__=='__main__':
    for name in list(vars(base.Evolution)):
        if name.startswith('test_'):delattr(base.Evolution,name)
    unittest.main(verbosity=2)
