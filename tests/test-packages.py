"""Nominal namespaces, visibility and offline locked transitive dependencies."""
import hashlib
import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path

spec=importlib.util.spec_from_file_location('evolution',Path(__file__).with_name('test-evolution.py'))
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
main=base.main

class Packages(base.Evolution):
    def put(self,name,contents):
        path=self.temp/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(contents,encoding='utf-8');return path

    def test_two_modules_same_names_and_generic_ast(self):
        self.put('a.assis','namespace a; public value struct P<T>{let n:T;} pure assis hidden(n:int):int{return n+1;} public pure assis f<T>(x:T):T{return x;} public pure assis calc():int{return hidden(40);}')
        self.put('b.assis','namespace b;public value struct P{let n:int;}public pure assis f(x:int):int{return x+1;}')
        self.accepted('#yuri <a.assis>\n#yuri <b.assis>\n'+main('val p:a::P<int>=new a::P<int>(a::f::<int>(41));val q:b::P=new b::P(b::f(p.n));print(a::calc(),q.n);'),'41 42\n')

    def test_module_local_callbacks_and_lexical_shadowing(self):
        self.put('a.assis','namespace a;pure assis f(n:int):int{return n*2;}public pure assis calc<T>(x:T):int{val g:pure assis(int):int=f;{val f:int=1;}return g(21);}')
        self.accepted('#yuri <a.assis>\n'+main('print(a::calc::<int>(0));'),'42\n')

    def test_private_globals_types_generics_and_impersonation(self):
        self.put('a.assis','namespace a;value struct P{let n:int;}pure assis f<T>(x:T):T{return x;}pure assis hidden():int{return 1;}')
        for body in ['print(a::hidden());','print(a::f::<int>(1));','val p:a::P=new a::P(1);']:
            self.rejected('#yuri <a.assis>\n'+main(body),'símbolo privado')
        self.put('b.assis','namespace a;public pure assis theft():int{return hidden();}')
        self.rejected('#yuri <a.assis>\n#yuri <b.assis>\n'+main(''),'símbolo privado')

    def test_namespace_malformed_and_public_requires_module(self):
        for code in ['namespace a;namespace b;'+main(''),'public '+main(''),'namespace a;'+main('')]:
            file=self.source(code);r=self.invoke('check',file);self.assertNotEqual(r.returncode,0)

    def setup_project(self):
        self.put('assis.pkg','package app 1.0.0\ndep util 2.0.0 "vendor/ação util"\n')
        self.put('vendor/ação util/assis.pkg','package util 2.0.0\ndep core 1.0.1 ../core\n')
        self.put('vendor/ação util/api.assis','#yuri <pkg/core/api.assis>\nnamespace util;public pure assis answer():int{return core::answer();}')
        self.put('vendor/core/assis.pkg','package core 1.0.1\n')
        self.put('vendor/core/api.assis','namespace core;public pure assis answer():int{return 42;}')
        return self.put('assis.assis','#yuri <pkg/util/api.assis>\n'+main('print(util::answer());'))

    def test_lock_transitive_offline_sha256_and_repeatability(self):
        source=self.setup_project();r=self.invoke('check',source);self.assertIn('lockfile ausente',r.stderr)
        r=self.invoke('lock',source);self.assertEqual(r.returncode,0,r.stderr)
        lock=(self.temp/'assis.lock').read_bytes()
        for kind,path,digest in [line.split('\t') for line in lock.decode().splitlines()[2:]]:
            self.assertIn(kind,['manifest','source']);self.assertEqual(digest,hashlib.sha256((self.temp/path).read_bytes()).hexdigest())
        r=self.invoke('lock',source);self.assertEqual(r.returncode,0,r.stderr);self.assertEqual(lock,(self.temp/'assis.lock').read_bytes())
        for flag in [[],['--no-opt']]:
            r=self.invoke('run',source,'--debug',*flag);self.assertEqual((r.returncode,r.stdout,r.stderr),(0,'42\n',''))
        self.put('vendor/core/api.assis','namespace core;public pure assis answer():int{return 7;}')
        for mode in ['check','run','build']:
            r=self.invoke(mode,source);self.assertIn('lockfile divergente',r.stderr)
        self.assertEqual(lock,(self.temp/'assis.lock').read_bytes())
        r=self.invoke('lock',source);self.assertEqual(r.returncode,0,r.stderr)
        r=self.invoke('run',source);self.assertEqual(r.stdout,'7\n')

    def test_version_cycle_escape_and_invalid_alias_rejected(self):
        source=self.setup_project()
        for content,message in [
            ('package app 1.0.0\ndep util 9.0.0 "vendor/ação util"\n','versão'),
            ('package app 1.0.0\ndep util 2.0.0 .\n','ciclo'),
            ('package app 1.0.0\ndep util ^2.0.0 "vendor/ação util"\n','versão exata'),
            ('package app 1.0.0\ndep util 2.0.0 "vendor/ação util"\ndep util 2.0.0 .\n','duplicado')]:
            self.put('assis.pkg',content);r=self.invoke('lock',source);self.assertNotEqual(r.returncode,0);self.assertIn(message,r.stderr)

    def test_package_import_escape_and_missing_dependency(self):
        source=self.setup_project();self.put('assis.assis','#yuri <pkg/util/../../assis.assis>\n'+main(''))
        r=self.invoke('lock',source);self.assertIn('escapa',r.stderr)
        self.put('assis.assis','#yuri <pkg/missing/api.assis>\n'+main(''))
        r=self.invoke('lock',source);self.assertIn('não declarado',r.stderr)

    def test_overlay_cannot_bypass_dependency_lock(self):
        source=self.setup_project();r=self.invoke('lock',source);self.assertEqual(r.returncode,0,r.stderr)
        overlay=self.put('changed.assis','namespace core;public pure assis answer():int{return 7;}')
        r=self.invoke('check',source,'--overlay',self.temp/'vendor/core/api.assis',overlay)
        self.assertNotEqual(r.returncode,0);self.assertIn('lockfile divergente',r.stderr)

    def test_sha256_block_boundaries_and_bom_hash_exact_loaded_bytes(self):
        source=self.setup_project();dependency=self.temp/'vendor/core/api.assis'
        for padding in [0,1,55,56,63,64,65,127,128,129,1024]:
            raw=b'\xef\xbb\xbf//'+b'x'*padding+b'\nnamespace core;public pure assis answer():int{return 42;}'
            dependency.write_bytes(raw);r=self.invoke('lock',source);self.assertEqual(r.returncode,0,r.stderr)
            lock=(self.temp/'assis.lock').read_text(encoding='utf-8');self.assertIn('vendor/core/api.assis\t'+hashlib.sha256(raw).hexdigest(),lock)

    def test_physical_dependency_path_cannot_escape_through_symlink(self):
        source=self.setup_project()
        with tempfile.TemporaryDirectory(prefix='assis-external-package-') as external:
            folder=Path(external);(folder/'assis.pkg').write_text('package external 1.0.0\n',encoding='utf-8')
            link=self.temp/'vendor/link'
            try:os.symlink(folder,link,target_is_directory=True)
            except OSError:self.skipTest('O host não permite criar symlinks de teste')
            self.put('assis.pkg','package app 1.0.0\ndep external 1.0.0 vendor/link\n')
            r=self.invoke('lock',source);self.assertNotEqual(r.returncode,0);self.assertIn('dentro do projeto',r.stderr)

    def test_hardlink_alias_deduplication_does_not_omit_dependency_hash(self):
        source=self.setup_project();shared=self.put('shared.assis','namespace util;public pure assis answer():int{return 42;}')
        dependency=self.temp/'vendor/ação util/api.assis';dependency.unlink()
        try:os.link(shared,dependency)
        except OSError:self.skipTest('O host não permite hardlinks de teste')
        self.put('assis.assis','#yuri <shared.assis>\n#yuri <pkg/util/api.assis>\n'+main('print(util::answer());'))
        r=self.invoke('lock',source);self.assertNotEqual(r.returncode,0);self.assertIn('pacotes diferentes',r.stderr)
        # Within one package physical identity remains shared, but both imported paths are pinned.
        dependency.unlink();shared=self.put('vendor/ação util/shared.assis','namespace util;public pure assis answer():int{return 42;}');os.link(shared,dependency)
        self.put('assis.assis','#yuri <pkg/util/shared.assis>\n#yuri <pkg/util/api.assis>\n'+main('print(util::answer());'))
        r=self.invoke('lock',source);self.assertEqual(r.returncode,0,r.stderr)
        lock=(self.temp/'assis.lock').read_text(encoding='utf-8');self.assertIn('vendor/ação util/api.assis\t'+hashlib.sha256(shared.read_bytes()).hexdigest(),lock)
        shared.write_text('namespace util;public pure assis answer():int{return 7;}',encoding='utf-8')
        r=self.invoke('check',source);self.assertNotEqual(r.returncode,0);self.assertIn('lockfile divergente',r.stderr)

    def test_std_prefix_cannot_disguise_escape_from_dependency(self):
        source=self.setup_project();self.put('vendor/ação util/api.assis','#yuri <std/../exemplos/15_funcional.assis>\nnamespace util;public pure assis answer():int{return 42;}')
        r=self.invoke('lock',source);self.assertNotEqual(r.returncode,0);self.assertIn('escapa',r.stderr)

if __name__=='__main__':
    for name in list(vars(base.Evolution)):
        if name.startswith('test_'):delattr(base.Evolution,name)
    unittest.main(verbosity=2)
