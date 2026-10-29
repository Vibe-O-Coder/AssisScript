"""Typed CFG, conservative dead code and real PIE/scalar debugging."""
import importlib.util
import json
import os
import platform
import sys
from pathlib import Path
import struct
import subprocess
import unittest

spec=importlib.util.spec_from_file_location('evolution',Path(__file__).with_name('test-evolution.py'))
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
main=base.main

class Backend(base.Evolution):
    def test_ir_cfg_types_effects_and_all_successors(self):
        source=self.source('safe fn f(n:int):int{let x:int=0;while(x<n){if(x==2){break;}x+=1;}return x;}' +
            'safe '+main('own b:*byte=alloc<byte>(3);print(f(4));'))
        r=self.invoke('ir',source);self.assertEqual(r.returncode,0,r.stderr);data=json.loads(r.stdout)
        self.assertEqual(data['format'],'AssisScript-HIR-v1')
        terms=set();effects=0
        for f in data['functions']:
            for b in f['blocks']:
                terms.add(b['terminator'])
                for successor in b['successors']: self.assertIn(successor,range(len(f['blocks'])))
                for op in b['operations']: effects|=op['effects'];self.assertIsInstance(op['type'],str)
        self.assertTrue({'branch','jump','return'}<=terms);self.assertEqual(effects&4,4);self.assertEqual(effects&8,8)

    def test_dead_code_preserves_diagnostics_and_runtime(self):
        self.accepted(main('if(false){print(987);}else{print(42);}return 0;print(321);'),'42\n')
        source=self.source(main('if(false){own b:*byte=alloc<byte>(1000);print(len(b));}print(42);'))
        sizes=[]
        for flags in [[],['--no-opt']]:
            output=self.temp/('program'+str(len(flags))+'.exe');r=self.invoke('build',source,*flags,'--target','linux-x64','-o',output);self.assertEqual(r.returncode,0,r.stderr);sizes.append(struct.unpack_from('<Q',output.read_bytes(),64+56+32)[0])
        self.assertLess(sizes[0],sizes[1])
        self.rejected('pure fn bad():int{if(false){print(1);}return 0;}'+main(''),'pure')
        self.rejected(main('if(false){own b:*int=alloc<int>(1);free(b);print(b[0]);}'),'movido')

    def test_elf_is_position_independent_with_no_writable_code(self):
        source=self.source('pure fn id(n:int):int{return n;}'+main('val f:pure fn(int):int=id;print(f,f(42));'))
        binary=self.temp/'pie';r=self.invoke('build',source,'--target','linux-arm64' if platform.machine().lower() in ('arm64','aarch64') else 'linux-x64','-o',binary);self.assertEqual(r.returncode,0,r.stderr)
        data=binary.read_bytes();self.assertEqual(struct.unpack_from('<H',data,16)[0],3)
        offset=struct.unpack_from('<Q',data,32)[0];count=struct.unpack_from('<H',data,56)[0]
        for i in range(count):
            kind,flags=struct.unpack_from('<II',data,offset+i*56)
            self.assertNotEqual(flags&3,3)
        if sys.platform=='linux':
            outputs=[subprocess.check_output([binary],text=True).strip().split() for _ in range(3)]
            self.assertTrue(all(out[1]=='42' for out in outputs));self.assertGreater(len({out[0] for out in outputs}),1)

    @unittest.skipIf(os.name=='nt' or os.environ.get('ASSIS_CROSS_DEBUG')=='1','Native GDB is validated on a matching Linux host; cross runs use the remote ARM64 gate')
    def test_gdb_parameters_locals_and_nested_shadowing(self):
        source=self.source('pure fn calc(n:int):int{\nlet x:int=n+2;\n{let x:int=99;\nn=x;\n}\nreturn x;\n}\n'+main('print(calc(40));'))
        # Pure parameters are immutable; use a separate local at the inner stop.
        source.write_text(source.read_text().replace('n=x;','let y:int=x;'),encoding='utf-8')
        for flags in [[],['--no-opt']]:
            binary=self.temp/'debug';r=self.invoke('build',source,'--symbols','-o',binary,*flags);self.assertEqual(r.returncode,0,r.stderr)
            r=subprocess.run(['gdb','-nx','-nh','-batch','-ex',f'break {source}:4','-ex','run','-ex','print n','-ex','print x','-ex','bt',binary],capture_output=True,text=True,timeout=20)
            self.assertEqual(r.returncode,0,r.stderr);self.assertIn('= 40',r.stdout);self.assertIn('= 99',r.stdout);self.assertIn('main',r.stdout)


if __name__=='__main__':
    for name in list(vars(base.Evolution)):
        if name.startswith('test_'):delattr(base.Evolution,name)
    unittest.main(verbosity=2)
