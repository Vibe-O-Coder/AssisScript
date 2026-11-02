"""Compile real scalar AssisScript to ASV2; compare native/reference and Python."""
import importlib.util
import json
import random
import struct
import unittest
from pathlib import Path

spec=importlib.util.spec_from_file_location('vm',Path(__file__).with_name('test-pagevm.py'))
vm=importlib.util.module_from_spec(spec);spec.loader.exec_module(vm)
base=vm.base

class PageBackend(vm.PageVM):
    def compile_page(self,code,flags=()):
        source=self.source(code,'page.assis');out=self.temp/'page.asv2'
        result=self.invoke('build',source,'--target','page-asv2','-o',out,*flags)
        self.assertEqual((result.returncode,result.stderr),(0,''),code)
        data=out.read_bytes();self.assertEqual(data[:4],b'ASV2')
        self.assertEqual(len(data),16+8*struct.unpack_from('<I',data,4)[0])
        return data

    def equivalent(self,code,expected):
        native=code.replace('fn main(', 'fn compute(',1)+'\nsafe fn main():int{print(compute());return 0;}'
        self.accepted(native,str(expected)+'\n')
        for flags in ((),('--no-opt',)):
            data=self.compile_page(code,flags)
            self.execute(vm.load(data)+f'assert(v.run(10000)==2);print(v.result());',str(expected)+'\n')

    def test_loops_calls_comparisons_break_continue_and_for_updates(self):
        self.equivalent('safe fn twice(x:int):int{return x*2;}'
            'safe fn main():int{let n:int=1;for(let i:int=0;i<9;i++){'
            'if(i==3){continue;}if(i>=7){break;}n=twice(n);}return n;}',64)

    def test_i64_extremes_bitwise_shifts_and_signed_remainders(self):
        self.equivalent('safe fn main():int{let m:int= -9223372036854775808;let n:int= -1;'
            'let v:int=m/n;v+=m%n;v^=~n;v+=int((m>>63)==n);v+=int((1<<63)==m);'
            'v+=(-29%6);return v;}',vm.wrapped(-2**63+2-5))

    def test_randomized_arithmetic_against_independent_wrapping_model(self):
        rng=random.Random(20261102);lines=['let result:int=0;'];answer=0
        for _ in range(60):
            a,b=rng.randrange(-2**63,2**63),rng.randrange(-2**63,2**63)
            op=rng.choice(['+','-','*','&','|','^','<','>','<=','>=','==','!='])
            if op in ['+','-','*','&','|','^']:value=eval(f'a {op} b')
            else:value=int(eval(f'a {op} b'))
            lines.append('{let a:int='+str(a)+';let b:int='+str(b)+';result+=int(a'+op+'b);}')
            answer=vm.wrapped(answer+value)
        # Eight locals is a deliberately small profile; lexical blocks still
        # count as distinct locals, so each expression gets its own function.
        helpers=[];body='let result:int=0;'
        for i,line in enumerate(lines[1:]):
            line=line[1:-1].replace('result+=','return ')
            helpers.append(f'safe fn case_{i}():int{{{line}}}')
            body+=f'result+=case_{i}();'
        self.equivalent(''.join(helpers)+'safe fn main():int{'+body+'return result;}',answer)

    def test_lazy_boolean_operators_skip_traps_and_preserve_nested_values(self):
        self.equivalent('safe fn bad():bool{let z:int=0;return 1/z==0;}'
            'safe fn main():int{let a:bool=false;let b:bool=true;'
            'return int(a&&bad())+int(b||bad())+int((b&&b)||(a&&bad()));}',2)

    def test_tail_recursion_and_non_tail_frames(self):
        code='pure fn count(n:int):int{if(n==0){return 42;}return count(n-1);}safe fn main():int{return count(8);}'
        self.equivalent(code,42)
        data=self.compile_page('safe fn r(n:int):int{if(n==0){return 1;}return 1+r(n-1);}safe fn main():int{return r(50);}')
        self.execute(vm.load(data,frames=4)+'assert(v.run(10000)== -6);')

    def test_forbidden_features_in_dead_code_do_not_overwrite_output(self):
        cases=[
            'safe fn main():int{if(false){print(1);}return 0;}',
            'safe fn main():int{if(false){own a:*byte=alloc<byte>(1);}return 0;}',
            'safe fn main():int{if(false){sleep_ms(1);}return 0;}',
            'safe fn main():int{let n:i32=i32(1);return int(n);}',
            'safe fn main():int{let f:f64=f64(1.0);return int(f);}',
            'extern("bad","bad","run") fn other():int;safe fn main():int{return 0;}',
            'safe fn other(a:int,b:int,c:int,d:int,e:int):int{return a+b;}safe fn main():int{return other(1,2,3,4,5);}',
            'safe fn main():int{unsafe{monotonic_ms();}return 0;}',
            'safe fn main():int{'+''.join(f'let x{i}:int=0;' for i in range(9))+'return 0;}',
        ]
        for code in cases:
            source=self.source(code);out=self.temp/'sentinel';out.write_bytes(b'keep')
            for flags in ((),('--no-opt',)):
                result=self.invoke('build',source,'--target','page-asv2','-o',out,*flags,'--diagnostics=json')
                self.assertNotEqual(result.returncode,0,code)
                self.assertIn('page-asv2',json.loads(result.stderr)['message'])
                self.assertEqual(out.read_bytes(),b'keep')

    def test_reject_run_native_flags_and_preserve_source(self):
        source=self.source('safe fn main():int{return 1;}')
        original=source.read_bytes()
        for extra in [('run',),('build','--symbols'),('build','--app')]:
            result=self.invoke(*extra,source,'--target','page-asv2')
            self.assertNotEqual(result.returncode,0)
        result=self.invoke('build',source,'--target','page-asv2','-o',source)
        self.assertNotEqual(result.returncode,0);self.assertEqual(source.read_bytes(),original)

    def test_asv2_unknown_operands_version_and_shift_traps(self):
        invalid=[vm.instruction(16,c=1),vm.instruction(17,c=16),vm.instruction(23,b=1),vm.instruction(12,immediate=9),vm.instruction(12,c=1,immediate=2),
            vm.instruction(24,c=1),vm.instruction(26,a=1),vm.instruction(27)]
        self.execute(''.join('{'+vm.load(b'ASV2'+vm.program([op])[4:])+'assert(v.status()== -1);}' for op in invalid))
        for shift in (-1,64):
            data=self.compile_page(f'safe fn main():int{{let n:int={shift};return 1<<n;}}')
            self.execute(vm.load(data)+'assert(v.run(100)== -11);')
        # ASV1 continues to deny all extension opcodes.
        self.execute(vm.load(vm.program([vm.instruction(16)]))+'assert(v.status()== -1);')

    def test_platform_selection_and_compilation_limits(self):
        self.compile_page('platform("page-asv2"){safe fn value():int{return 42;}}'
            'platform("windows-x64"){safe fn bad():int{print(2);return 1;}}'
            'safe fn main():int{return value();}')
        source=self.source('/*'+'x'*65536+'*/safe fn main():int{return 0;}');out=self.temp/'sentinel'
        out.write_bytes(b'keep');result=self.invoke('build',source,'--target','page-asv2','-o',out)
        self.assertNotEqual(result.returncode,0);self.assertEqual(out.read_bytes(),b'keep')
        # Different hard-link names are one source, but must not bypass the
        # bounded module/alias inventory during expansion.
        import os
        common=self.source('safe fn helper():int{return 0;}','common.assis')
        imports=''
        for i in range(17):
            alias=self.temp/f'alias_{i}.assis';os.link(common,alias);imports+=f'import "{alias.name}";'
        source=self.source(imports+'safe fn main():int{return 0;}')
        result=self.invoke('build',source,'--target','page-asv2','-o',out)
        self.assertNotEqual(result.returncode,0)
        self.assertIn('16',result.stderr);self.assertEqual(out.read_bytes(),b'keep')

    def test_sdk_import_signature_library_and_version_must_match_exactly(self):
        for libs,symbol,signature in [
            ('"assis_htdl_v1","assis_htdl_v1"','counter_add_v2','x:int):int'),
            ('"wrong","assis_htdl_v1"','counter_add_v1','x:int):int'),
            ('"assis_htdl_v1","wrong"','counter_add_v1','x:int):int'),
            ('"assis_htdl_v1","assis_htdl_v1"','counter_add_v1','x:bool):int'),
            ('"assis_htdl_v1","assis_htdl_v1"','counter_add_v1','x:int):bool'),
            ('"assis_htdl_v1","assis_htdl_v1"','state_set_v1','x:int):int'),
        ]:
            code=f'extern({libs},"{symbol}") fn imported({signature};safe fn main():int{{return 0;}}'
            source=self.source(code);output=self.temp/'sentinel';output.write_bytes(b'keep')
            result=self.invoke('build',source,'--target','page-asv2','-o',output)
            self.assertNotEqual(result.returncode,0,code);self.assertIn('page-asv2',result.stderr)
            self.assertEqual(output.read_bytes(),b'keep')

if __name__=='__main__':
    for cls in (base.Evolution,vm.PageVM):
        for name in list(vars(cls)):
            if name.startswith('test_'):delattr(cls,name)
    unittest.main(verbosity=2)
