"""Executable regressions for the language review; default safe entry."""
import importlib.util
import json
import os
from pathlib import Path
import struct
import subprocess
import unittest

spec=importlib.util.spec_from_file_location('evolution',Path(__file__).with_name('test-evolution.py'))
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)

def main(body):return 'safe fn main():int{'+body+'return 0;}'

CLASS='''class Base{let hp:int;own data:*byte;
fn init(borrow mut self,hp:int):void{self.hp=hp;self.data=alloc<byte>(1);}
fn read(borrow self):int{return self.hp;}}
class Hero extends Base{
fn init(borrow mut self,hp:int,bonus:int):void{super.init(hp+bonus);}
fn set(borrow mut self,n:int):void{self.hp=n;}
fn read(borrow self):int{return super.read()+1;}}
'''

class Usability(base.Evolution):
    def invoke(self,*args,**kwargs):
        # Exercise default behavior rather than the manual-memory test corpus.
        if args and args[0] in ('check','build','run','doc','ir','test') and '--legacy' not in args and '--safe' not in args:args=(*args,'--safe')
        return super().invoke(*args,**kwargs)

    def test_static_utf8_slices_nul_and_unformatted_write(self):
        self.accepted(main('write("HP ",54,"/",54," ");print(utf8("a\\0b"));'
            'borrow data:slice<byte>=utf8("abc");assert(write_bytes(1,data,2)==2);print();'), 'HP 54/54 a\0b\nab\n')
        r=self.invoke('run',self.source(main('borrow b:slice<byte>=utf8("a");write_bytes(1,b,2);')))
        self.assertEqual(r.returncode,70);self.assertIn('assis: erro R001',r.stderr)

    def test_owned_utf8_builder_and_decimal_display(self):
        self.accepted('import "std/unicode.assis";'+main(
            'own s:unicode::String=new unicode::String();assert(s.append("Turno de Assis - HP "));'
            's.append_int(54);assert(s.append("/"));s.append_int(54);print(s);s.clear();'
            's.append_int(-9223372036854775808);assert(s.append(" "));assert(s.append_decimal(0.1+0.2,2));print(s);'
            'assert(!s.append_decimal(1.0,10));own bad:*byte=alloc<byte>(1);bad[0]=byte(255);assert(!s.append(slice_of(bad,0,1)));'),
            'Turno de Assis - HP 54/54\n-9223372036854775808 0.30\n')
        self.rejected('import "std/unicode.assis";safe fn make():own unicode::String{return new unicode::String();}'+main('print(make());'),'vínculo own local')
        self.rejected('safe fn make():own Array<int>{return [1];}'+main('print(len(make()));'),'vínculo own local')
        self.rejected('safe fn make():own Array<int>{return [1];}'+main('print(make()[0]);'),'vínculo own local')
        self.accepted('safe fn make():own Array<int>{return [1];}'+main('free(make());'))

    def test_constants_characters_names_and_module_visibility(self):
        self.source('namespace limits;public const MAX:int=BASE+2;const BASE:int=40;', 'limits.assis')
        self.accepted('import "limits.assis";const HASH:byte=\'#\';const NUL:byte=\'\\0\';'+main(
            'let te:int=1;let to:int=2;let miyabi:int=3;print(limits::MAX,HASH,NUL,te+to+miyabi);'), '42 35 0 6\n')
        self.rejected('const A:int=B;const B:int=A;'+main(''),'ciclo entre constantes')
        self.rejected('const A:int=monotonic_ms();'+main(''),'sem chamadas')
        self.rejected(''.join(f'const C{i}:int=C{i+1};' for i in range(600))+'const C600:int=1;'+main(''),'limite de dependências')
        self.rejected('const A:int=1;'+main('A=2;'),'posição gravável')
        self.rejected("const A:int='#';const B:byte=A;"+main(''),'não é possível usar int como byte')
        self.accepted("const A:int='#';const B:byte=byte(A);"+main('print(A,B);'),'35 35\n')
        self.rejected('import "limits.assis";'+main('print(limits::BASE);'),'privado do módulo')
        for character in ["''","'ab'","'é'","'\\q'"]:
            self.rejected(main('val c:byte='+character+';'),'caractere')

    def test_constructor_chaining_dynamic_dispatch_and_downcasts(self):
        self.accepted(CLASS+'class Other{}'+main(
            'own b:Base=new Hero(40,1);assert(b is Hero);assert(b is Base);assert(!(b is Other));'
            '{borrow h:Hero=b as Hero;h.read();assert(h!=null);print(h.read());}'
            '{borrow no:Other=b as Other;assert(no==null);}'), '42\n')
        self.accepted('class B{own data:*int;fn init(borrow mut self):void{self.data=alloc<int>(1);self.data[0]=42;}}'
            'class C extends B{fn init(borrow mut self):void{}}'+main('own c:C=new C();print(c.data[0]);'),'42\n')
        self.rejected(CLASS+'class Bad extends Base{fn init(borrow mut self):void{}}'+main(''),'super.init')
        self.rejected(CLASS+main('own h:Hero=new Hero(1,2);h.init(2,3);'),'inicializador gerenciado')
        self.rejected('class B{fn init(borrow mut self):void{}}class C extends B{fn init(borrow mut self):void{super.init();super.init();}}'+main(''),'única vez')
        self.rejected(CLASS+main('own b:Base=new Hero(1,2);borrow h:Hero=b as Hero;free(b);'),'borrow ativo')

    def test_receiver_reservations_allow_reads_and_reject_aliasing_mutations(self):
        self.accepted(main('own values:Array<int>=[42];values.push(len(values));print(values[1]);'),'1\n')
        self.accepted(CLASS+main('own h:Hero=new Hero(40,1);h.set(h.hp+1);h.set(h.read());print(h.hp);'),'43\n')
        self.rejected(CLASS+main('own h:Hero=new Hero(1,2);borrow r:Hero=h;h.set(h.hp);'),'exclusivo')
        self.rejected('class C{fn add(borrow mut self,borrow other:C):void{}}'+main('own c:C=new C();c.add(c);'),'borrow incompatível')
        self.rejected('class C{fn change(borrow mut self):int{return 1;}fn set(borrow mut self,n:int):void{}}'+main('own c:C=new C();c.set(c.change());'),'exclusivo')

    def test_owned_indexed_collection_scales_and_transfers(self):
        self.accepted('import "std/owned.assis";struct Item{let n:int;}'+main(
            'own items:owned::OwnedArray<Item>=new owned::OwnedArray<Item>();'
            'for(let i:int=0;i<4097;i+=1){items.push(new Item(i));}'
            '{borrow item:Item=items.get(4096);assert(item.n==4096);}'
            'for(let i:int=4096;i>=2048;i-=1){own item:Item=items.pop();assert(item.n==i);}'
            'items.push(new Item(42));print(items.size());{borrow item:Item=items.get(2048);print(item.n);}'), '2049\n42\n')
        self.rejected('import "std/owned.assis";struct Item{let n:int;}'+main(
            'own items:owned::OwnedArray<Item>=new owned::OwnedArray<Item>();items.push(new Item(1));'
            'borrow item:Item=items.get(0);items.pop();'),'exclusivo')

    def test_seeded_random_and_managed_sort(self):
        self.accepted('import "std/random.assis";import "std/algorithms.assis";'+main(
            'own a:random::Random=new random::Random(u64(7));own b:random::Random=new random::Random(u64(7));'
            'for(let i:int=0;i<100;i+=1){assert(a.next_u64()==b.next_u64());val n:int=a.range(-4,5);assert(n>=-4 && n<5);b.range(-4,5);}'
            'own values:Array<int>=[5,-1,5,0,-9223372036854775808,9223372036854775807];sort(values);'
            'for(let i:int=1;i<len(values);i+=1){assert(values[i]>=values[i-1]);}print(values[0],values[5]);'), '-9223372036854775808 9223372036854775807\n')

    def test_all_output_formats_and_platform_filtering(self):
        source=self.source('platform("macos-x64"){const N:int=3;}platform("linux-x64"){const N:int=2;}platform("windows-x64"){const N:int=1;}'+main('print(N);'))
        for target,magic in [('windows-x64',b'MZ'),('linux-x64',b'\x7fELF'),('macos-x64',b'\xcf\xfa\xed\xfe')]:
            binary=self.temp/(target+'.exe');r=self.invoke('build',source,'--target',target,'-o',binary);self.assertEqual(r.returncode,0,r.stderr);data=binary.read_bytes();self.assertTrue(data.startswith(magic))
            if target=='macos-x64':
                _,cpu,_,kind,count,size,flags,_=struct.unpack_from('<8I',data);self.assertEqual((cpu,kind),(0x1000007,2));self.assertTrue(flags&0x200000)
                offset=32;segments=[];bind=None;entry=None
                for _ in range(count):
                    command,length=struct.unpack_from('<II',data,offset);self.assertGreaterEqual(length,8)
                    if command==0x19:
                        name,address,memory,at,used,maxp,initp=struct.unpack_from('<16sQQQQII',data,offset+8);segments.append((name.rstrip(b'\0'),at,used,initp));self.assertLessEqual(at+used,len(data));self.assertFalse(initp&2 and initp&4)
                    if command==0x80000022:bind=struct.unpack_from('<II',data,offset+16)
                    if command==0x80000028:entry=struct.unpack_from('<Q',data,offset+8)[0]
                    offset+=length
                self.assertEqual(offset,32+size);self.assertEqual(len(segments),5);self.assertTrue(4096<=entry<segments[1][1]+segments[1][2]);self.assertIn(b'_clock_gettime\0',data[bind[0]:bind[0]+bind[1]])

    def test_historical_syntax_is_not_a_compatibility_mode(self):
        for source in ['ASSIS C{}'+main(''),'assis assis_assis():int{return 0;}','#yuri <std/math.assis>\n'+main('')]:
            r=self.invoke('check',self.source(source),'--legacy');self.assertEqual(r.returncode,1,r.stderr)

    def test_generated_api_includes_constants_and_canonical_method_syntax(self):
        source=self.source('namespace api;public const MAX:int=42;public class C{fn read(borrow self):int{return MAX;}}')
        r=self.invoke('doc',source);self.assertEqual(r.returncode,0,r.stderr)
        self.assertIn('const api::MAX: int',r.stdout);self.assertIn('fn read(borrow self)',r.stdout)
        self.assertNotIn('safe fn read',r.stdout)

if __name__=='__main__':
    for name in list(vars(base.Evolution)):
        if name.startswith('test_'):delattr(base.Evolution,name)
    unittest.main(verbosity=2)
