"""Exercise the public default directly, without the legacy corpus adapter."""
import importlib.util
import json
from pathlib import Path
import subprocess
import unittest

spec=importlib.util.spec_from_file_location('evolution',Path(__file__).with_name('test-evolution.py'))
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)

class SafeDefault(base.Evolution):
    def invoke(self,*args,input=None):
        return subprocess.run([str(base.COMPILER),*map(str,args)],input=input,capture_output=True,text=True,encoding='utf-8',timeout=30)

    def test_default_requires_safe_root_and_legacy_is_explicit(self):
        self.rejected('fn main():int{return 0;}','--safe exige entrada')
        self.accepted('safe fn main():int{own b:*byte=alloc<byte>(2);b[1]=byte(42);print(b[1]);return 0;}','42\n')
        legacy=self.source('fn main():int{let p:*int=alloc<int>(1);p[0]=42;print(p[0]);free(p);return 0;}')
        r=self.invoke('run',legacy,'--legacy','--debug');self.assertEqual((r.returncode,r.stdout,r.stderr),(0,'42\n',''))
        for flags in [('--safe','--legacy'),('--legacy','--safe')]:
            r=self.invoke('check',legacy,*flags);self.assertNotEqual(r.returncode,0);self.assertIn('incompatíveis',r.stderr)

    def test_raw_operations_external_text_and_hidden_calls_stay_at_boundary(self):
        for body,message in [
            ('let b:*byte=alloc<byte>(1);','safe exige own/borrow'),
            ('let s:text="a";','safe exige own/borrow'),
            ('print(legacy());','chamada legada'),
            ('if(false){print(legacy());}','chamada legada'),
            ('val f:fn():int=legacy;print(f());','chamada legada'),
            ('own b:*byte=alloc<byte>(2);print(text(b));','extração de ponteiro bruto'),
            ('unsafe{let b:*byte=alloc<byte>(2);}print(text(b));','não declarada'),
        ]:
            with self.subTest(body=body):self.rejected('fn legacy():int{return 42;}safe fn main():int{'+body+'return 0;}',message)
        for declaration in [
            'safe fn f(borrow s:text):int{return len(s);}',
            'safe fn f():borrow(s) text{return "a";}',
            'class C{let s:text;fn init(borrow mut self):void{self.s="a";}}safe fn f(own c:C):int{return 0;}',
        ]:
            r=self.invoke('check',self.source(declaration+'safe fn main():int{return 0;}'))
            self.assertEqual(r.returncode,1,r.stderr)
        # The opt-out never disables checks on explicitly checked functions.
        r=self.invoke('check',self.source('safe fn main():int{let p:*byte=alloc<byte>(1);return 0;}'),'--legacy')
        self.assertEqual(r.returncode,1);self.assertIn('safe exige own/borrow',r.stderr)

    def test_static_text_managed_utf8_and_explicit_unsafe(self):
        self.accepted('fn legacy():int{return 42;}safe fn main():int{val s:text="ação";print(len(s));unsafe{print(legacy());}return 0;}','6\n42\n')
        self.accepted('import "std/unicode.assis";\nsafe fn main():int{own b:*byte=alloc<byte>(3);b[0]=byte(65);b[2]=byte(66);own s:unicode::String=new unicode::String();assert(s.load(slice_of(b,0,3)));borrow v:slice<byte>=s.as_slice();print(len(v),v[1]);return 0;}','3 0\n')

    def test_new_project_runs_in_default_profile_without_toolchain(self):
        folder=self.temp/'new project';r=self.invoke('new',folder);self.assertEqual(r.returncode,0,r.stderr)
        r=self.invoke('run',folder/'assis.assis','--debug');self.assertEqual((r.returncode,r.stdout,r.stderr),(0,'Hello, world! 42\n',''))

    def test_managed_initializer_cannot_reenter_or_replace_live_native_state(self):
        prefix='final class C{own data:*byte;fn init(borrow mut self):void{self.data=alloc<byte>(1);}}'
        for call in ['c.init();','c.init();']:
            self.rejected(prefix+'safe fn main():int{own c:C=new C();'+call+'return 0;}','inicializador gerenciado')
        self.rejected('final class C{fn init(borrow mut self):void{self.init();}}safe fn main():int{own c:C=new C();return 0;}','inicializador gerenciado')

if __name__=='__main__':
    for name in list(vars(base.Evolution)):
        if name.startswith('test_'):delattr(base.Evolution,name)
    unittest.main(verbosity=2)
