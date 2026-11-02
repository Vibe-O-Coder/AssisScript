"""Independent Wasm engine vs actual source/native/ASV2, with hostile inputs."""
import base64
import importlib.util
import json
import os
from pathlib import Path
import random
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parent.parent

def module(name, file):
    spec = importlib.util.spec_from_file_location(name, file)
    value = importlib.util.module_from_spec(spec); spec.loader.exec_module(value); return value

backend = module('candidate_backend', ROOT/'tests/test-page-backend.py')
wasm = module('candidate_wasm', ROOT/'tools/asv2-wasm-candidate.py')
vm = backend.vm

def asv(ops, **kw): return b'ASV2' + vm.program(ops, **kw)[4:]

class WasmCandidate(backend.PageBackend):
    @classmethod
    def setUpClass(cls):
        if not shutil.which('node'): raise unittest.SkipTest('Node/V8 unavailable; no Wasm execution')
    def candidate(self, data, actions=None, mutate=None, **limits):
        generated = wasm.translate(data, **limits)
        envelope = dict(asv2=base64.b64encode(data).decode(),wasm=base64.b64encode(generated).decode(),limits=limits)
        if actions is not None: envelope['actions'] = actions
        if mutate: mutate(envelope)
        file = self.temp/'candidate.json'; file.write_text(json.dumps(envelope),encoding='utf-8')
        result = subprocess.run([shutil.which('node') or 'node',ROOT/'tools/run-wasm-candidate.js',file],capture_output=True,text=True,timeout=20)
        self.assertEqual((result.returncode,result.stderr),(0,''))
        return json.loads(result.stdout)

    def compare(self, source, expected):
        self.equivalent(source, expected)
        for flags in ((),('--no-opt',)):
            result = self.candidate(self.compile_page(source,flags))
            self.assertEqual(result['status'],'executed',result)
            self.assertEqual((result['snapshots'][-1]['state'],result['snapshots'][-1]['result']),(2,str(expected)))
            self.assertEqual(result['linear_bytes'],131072)

    def test_real_source_integer_edges_and_lazy_control(self):
        self.compare('safe fn main():int{let m:int= -9223372036854775808;let n:int= -1;let z:int=0;'
            'return m/n+m%n+int(false&&(1/z==0))+int(true||(1/z==0));}',-2**63+1)

    def test_real_functions_loops_frames_and_evaluation_order(self):
        self.compare('safe fn f(n:int):int{if(n==0){return 1;}return n*f(n-1);}'
            'safe fn main():int{let a:int=0;for(let i:int=0;i<7;i++){if(i==2){continue;}a+=f(i);}return a;}',872)

    def test_seeded_arithmetic_against_python_model(self):
        rng=random.Random(2026110201);helpers=[];body='let total:int=0;';expected=0
        for i in range(30):
            a,b=rng.randrange(-2**63,2**63),rng.randrange(-2**63,2**63)
            op=rng.choice(['+','-','*','^','&','|','<','==','>'])
            expected=vm.wrapped(expected+int(eval(f'a {op} b')))
            helpers.append(f'safe fn f{i}():int{{let a:int={a};let b:int={b};return int(a{op}b);}}')
            body+=f'total+=f{i}();'
        self.compare(''.join(helpers)+'safe fn main():int{'+body+'return total;}',expected)

    def test_shifts_and_divide_zero_preserve_trap_contract(self):
        for source,status in [('let n:int=64;return 1<<n;',-11),('let z:int=0;return 3/z;',-7),('let n:int= -1;return 1>>n;',-11)]:
            code=self.compile_page('safe fn main():int{'+source+'}')
            result=self.candidate(code)
            self.assertEqual(result['snapshots'][-1]['state'],status)
            self.execute(vm.load(code)+f'assert(v.run(1000)=={status});')
        self.compare('safe fn main():int{let a:int= -9223372036854775808;let n:int=63;return (a>>n)^(1<<n);}',2**63-1)

    def test_fuel_yield_recursion_and_independent_neighbor(self):
        loop=asv([vm.instruction(8,immediate=0)])
        result=self.candidate(loop,[dict(op='tick',quantum=4)]*4,fuel=11)
        self.assertEqual([(r['accepted'],r['steps']) for r in result['snapshots']],[(1,4),(1,8),(-3,11),(-3,11)])
        self.assertEqual(self.candidate(asv([vm.instruction(1,immediate=42),vm.instruction(0)]))['snapshots'][-1]['result'],'42')
        recursive=asv([vm.instruction(10,immediate=0)])
        self.assertEqual(self.candidate(recursive,frames=3)['snapshots'][-1]['state'],-6)

    def test_memory_zero_bounds_and_no_growth_or_user_metadata_alias(self):
        for addr,status,value in [(0,2,'255'),(1,-5,'0'),(-32768,-5,'0')]:
            data=asv([vm.instruction(1,0,immediate=addr),vm.instruction(1,1,immediate=511),vm.instruction(14,0,1),vm.instruction(13,2,0),vm.instruction(0,2)],memory=1)
            r=self.candidate(data)['snapshots'][-1]
            self.assertEqual((r['state'],r['result']),(status,value))
        zero=asv([vm.instruction(13,1,0),vm.instruction(0,1)],memory=1)
        self.assertEqual(self.candidate(zero)['snapshots'][-1]['result'],'0')
        with self.assertRaisesRegex(ValueError,'host_limit'): wasm.translate(zero,memory_limit=0)

    def test_capability_forgeries_revocation_and_call_quota(self):
        data=asv([vm.instruction(1,immediate=3),vm.instruction(12,1,0,immediate=1),vm.instruction(12,2,0,immediate=1),vm.instruction(0,2)])
        self.assertEqual(self.candidate(data)['snapshots'][-1]['state'],-2)
        r=self.candidate(data,[dict(op='grant',identity=[2,7,1]),dict(op='grant',identity=[1,8,1]),dict(op='grant',identity=[1,7,2]),dict(op='tick',quantum=100)])
        self.assertEqual([s['accepted'] for s in r['snapshots']],[False,False,False,-2])
        r=self.candidate(data,[dict(op='grant',identity=[1,7,1]),dict(op='tick',quantum=100)],calls=1)['snapshots'][-1]
        self.assertEqual((r['state'],r['counter'],r['calls']),(-8,'3',1))
        r=self.candidate(data,[dict(op='grant',identity=[1,7,1]),dict(op='tick',quantum=1),dict(op='revoke'),dict(op='grant',identity=[1,7,1]),dict(op='tick',quantum=100)])
        self.assertEqual((r['snapshots'][-2]['accepted'],r['snapshots'][-1]['state']),(False,-2))

    def test_reply_replay_event_generation_and_fuel_survive_reentry(self):
        data=asv([vm.instruction(12,0,0,immediate=2),vm.instruction(0)])
        actions=[dict(op='begin',identity=[1,7,1],request=1),dict(op='tick',quantum=1),
            dict(op='reply',identity=[1,7,2],request=1,call=1,value='42'),
            dict(op='reply',identity=[1,7,1],request=1,call=1,value='42'),
            dict(op='reply',identity=[1,7,1],request=1,call=1,value='99'),dict(op='tick',quantum=1),
            dict(op='begin',identity=[1,7,1],request=1),dict(op='begin',identity=[1,7,1],request=2),dict(op='tick',quantum=10)]
        r=self.candidate(data,actions,fuel=2)['snapshots']
        self.assertEqual([r[i]['accepted'] for i in (2,3,4,6,7)],[False,True,False,False,True])
        self.assertEqual((r[5]['result'],r[-1]['state'],r[-1]['steps']),('42',-3,2))

    def test_malformed_bytecode_and_mutated_wasm_are_rejected_before_execution(self):
        for data in [b'bad',asv([vm.instruction(27)]),asv([vm.instruction(16,c=1)]),asv([vm.instruction(8,immediate=2)])]:
            with self.assertRaises(ValueError): wasm.translate(data)
        data=asv([vm.instruction(0)])
        r=self.candidate(data,mutate=lambda e:e.update(wasm=base64.b64encode(b'\0asm\x01\0\0\0').decode()))
        self.assertEqual(r['status'],'rejected')
        for n in ('file','process','ffi','network','clock'):
            # Arbitrary valid Wasm imports, memory.grow, start or altered fuel
            # all change canonical bytes and cannot reach instantiation.
            r=self.candidate(data,mutate=lambda e,n=n:e.update(wasm=base64.b64encode(wasm.translate(data)+n.encode()).decode()))
            self.assertEqual(r['status'],'rejected')

if __name__ == '__main__':
    for cls in (backend.base.Evolution,vm.PageVM,backend.PageBackend):
        for key in list(vars(cls)):
            if key.startswith('test_'): delattr(cls,key)
    unittest.main(verbosity=2)
