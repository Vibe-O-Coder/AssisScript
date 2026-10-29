"""Independent C compiler oracle for the two scalar native ABIs."""
import importlib.util
import os
from pathlib import Path
import shutil
import subprocess
import struct
import unittest

spec=importlib.util.spec_from_file_location('evolution',Path(__file__).with_name('test-evolution.py'))
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)

class FFI(base.Evolution):
    def setUp(self):
        super().setUp()
        cc=os.environ.get('CC') or shutil.which('gcc')
        if not cc and os.name=='nt': cc=str(Path(os.environ.get('ASSIS_TOOLCHAIN_BIN','C:/msys64/ucrt64/bin'))/'gcc.exe')
        self.assertTrue(cc and Path(cc).exists(), 'A C compiler is required for the independent ABI oracle')
        self.library=self.temp/('oracle.dll' if os.name=='nt' else 'oracle.so')
        environment=os.environ.copy();environment['PATH']=str(Path(cc).parent)+os.pathsep+environment.get('PATH','')
        result=subprocess.run([cc,'-shared','-fPIC','-O2',str(Path(__file__).with_name('ffi-fixture.c')),'-o',str(self.library)],env=environment,capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)

    def external(self,name,params,result):
        path=self.library.as_posix()
        return f'extern("{path}","{path}","{name}") fn {name}({params}):{result};'

    def test_registers_stack_returns_and_callbacks(self):
        mixed='a:int,b:f64,c:i32,d:f32,e:int,f:int,g:int,h:f64,i:int,j:int'
        reals=','.join(f'{c}:f64' for c in 'abcdefghij')
        src=self.external('ffi_mix',mixed,'int')+self.external('ffi_reals',reals,'f64')
        src+=self.external('ffi_callback','f:u64','int')+self.external('ffi_real_callback','f:u64','f64')
        src+='fn mix('+mixed+'):int{return a+2*int(b)+3*int(c)+4*int(d)+5*e+6*f+7*g+8*int(h)+9*i+10*j;}'
        src+='fn reals('+reals+'):f64{return a+2.0*b+3.0*c+4.0*d+5.0*e+6.0*f+7.0*g+8.0*h+9.0*i+10.0*j;}'
        args='1,2.0,i32(3),f32(4.0),5,6,7,8.0,9,10'
        src+='safe fn main():int{unsafe{print(ffi_mix('+args+'));print(int(ffi_reals(1.0,2.0,3.0,4.0,5.0,6.0,7.0,8.0,9.0,10.0)));print(ffi_callback(c_callback(mix)));print(int(ffi_real_callback(c_callback(reals))));}return 0;}'
        self.accepted(src,'385\n385\n385\n385\n')

    def test_narrow_values_borrowed_buffers_and_function_values(self):
        src=self.external('ffi_narrow','a:i8,b:byte,c:i16,d:u16,e:i32,f:u32','i8')
        src+=self.external('ffi_bytes','borrow mut b:*byte,n:int','void')
        src+='safe fn main():int{own b:*byte=alloc<byte>(4);unsafe{val narrow:fn(i8,byte,i16,u16,i32,u32):i8=ffi_narrow;print(int(narrow(i8(-120),byte(250),i16(-300),u16(400),i32(-500),u32(600))));ffi_bytes(b,4);}print(b[0],b[3]);return 0;}'
        self.accepted(src,'74\n65 68\n')

    def test_nested_callback_and_alias_deduplication(self):
        src=self.external('ffi_twice','f:u64,n:int','int')
        src+='pure fn inc(n:int):int{return n+1;}fn nested(n:int):int{return ffi_twice(c_callback(inc),n);}'
        src+='safe fn main():int{unsafe{print(ffi_twice(c_callback(nested),10));}return 0;}'
        self.accepted(src,'48\n')

    def test_rejections_are_before_emission(self):
        self.rejected('extern("x","x","x") fn x(v:own *byte):int;fn main():int{return 0;}','esperado')
        self.rejected('extern("x","x","x") fn x(own v:*byte):int;fn main():int{return 0;}','ABI C')
        self.rejected('value struct V{let a:int;}extern("x","x","x") fn x():V;fn main():int{return 0;}','ABI C')
        self.rejected('extern("x","x","x") fn x():int;safe fn main():int{return x();}','unsafe')
        self.rejected('pure fn f(n:int):int{return n;}safe fn main():int{print(c_callback(f));return 0;}','unsafe')
        self.rejected('pure fn f(n:int):int{return n;}fn main():int{val g:pure fn(int):int=f;print(c_callback(g));return 0;}','global')
        self.rejected('extern("x","x","x") fn main():int;','entrada')

    def test_external_resources_drop_once_on_all_exits(self):
        src=self.external('ffi_open_handle','','int')+self.external('ffi_close_handle','h:int','void')+self.external('ffi_live_handles','','int')+self.external('ffi_closed_handles','','int')
        src+='final class R{let h:int;fn init(borrow mut self):void{unsafe{self.h=ffi_open_handle();}}fn drop(borrow mut self):void{unsafe{ffi_close_handle(self.h);}}}'
        src+='struct Pair{own a:R;own b:R;}safe fn make():own R{return new R();}safe fn early(n:int):int{own p:Pair=new Pair(make(),make());if(n==1){return 7;}own moved:R=move(p.a);free(moved);return 9;}'
        src+='safe fn main():int{print(early(1),early(0));for(let i:int=0;i<20;i+=1){own resource:R=make();}unsafe{print(ffi_live_handles(),ffi_closed_handles());}return 0;}'
        self.accepted(src,'7 9\n0 24\n')
        self.rejected('final class R{fn drop(borrow mut self):void{}}safe fn main():int{own r:R=new R();r.drop();return 0;}','reservado')
        self.rejected('class R{fn drop(borrow mut self):void{}}fn main():int{return 0;}','final class')
        self.rejected('final class R{own b:*byte;fn drop(borrow mut self):void{}}safe fn main():int{own r:R=new R();own b:*byte=move(r.b);return 0;}','parcialmente')

    def test_callback_restores_runtime_and_c_register(self):
        src=self.external('ffi_runtime_register','f:u64,n:int','int')
        src+='safe fn allocate(n:int):int{own b:*int=alloc<int>(3);b[0]=n;return b[0]+1;}fn main():int{print(ffi_runtime_register(c_callback(allocate),41));return 0;}'
        self.accepted(src,'42\n')

    def test_platform_branches_are_selected_before_binding(self):
        self.accepted('platform("windows-x64"){pure fn answer():int{return 42;}}platform("linux"){pure fn answer():int{return 42;}}platform("macos"){pure fn answer():int{return 42;}}safe fn main():int{print(answer());return 0;}','42\n')
        self.rejected('platform("other"){fn x():int{return 0;}}fn main():int{return 0;}','desconhecida')

    def test_dynamic_elf_format_and_ambiguous_symbols(self):
        source=self.source(self.external('ffi_twice','f:u64,n:int','int')+'fn main():int{return 0;}')
        binary=self.temp/'elf';result=self.invoke('build',source,'--target','linux-x64','-o',binary)
        self.assertEqual(result.returncode,0,result.stderr);data=binary.read_bytes()
        offset=struct.unpack_from('<Q',data,32)[0];count=struct.unpack_from('<H',data,56)[0];kinds=[]
        for i in range(count):
            kind,flags,file_offset,_,_,size=struct.unpack_from('<IIQQQQ',data,offset+i*56);kinds.append(kind)
            self.assertLessEqual(file_offset+size,len(data));self.assertNotEqual(flags&3,3)
        self.assertIn(3,kinds);self.assertIn(2,kinds);self.assertIn(0x6474e552,kinds)
        source=self.source('extern("a.so","a.dll","same") fn a():int;extern("b.so","b.dll","same") fn b():int;fn main():int{return 0;}')
        result=self.invoke('build',source,'--target','linux-x64','-o',binary);self.assertEqual(result.returncode,1);self.assertIn('ambíguo',result.stderr)
        result=self.invoke('build',source,'--target','windows-x64','-o',binary);self.assertEqual(result.returncode,0,result.stderr)

    def test_callback_address_without_a_c_dependency(self):
        self.accepted('pure fn f(n:int):int{return n+1;}safe fn main():int{unsafe{assert(c_callback(f)!=u64(0));}print(42);return 0;}','42\n')

if __name__=='__main__':
    for name in list(vars(base.Evolution)):
        if name.startswith('test_'):delattr(base.Evolution,name)
    unittest.main(verbosity=2)
