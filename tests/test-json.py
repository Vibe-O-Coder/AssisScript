"""JSON grammar/Unicode and serializer with Python's independent JSON decoder."""
import importlib.util
import json
import os
import random
import subprocess
import unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location('evolution',Path(__file__).with_name('test-evolution.py'));base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)

class Json(base.Evolution):
    def build(self,body,flags):
        source=self.source('#yuri <std/json.assis>\nsafe '+base.main(body));binary=self.temp/('json.exe' if os.name=='nt' else 'json');r=self.invoke('build',source,'--safe','--debug','-o',binary,*flags);self.assertEqual(r.returncode,0,r.stderr);return binary

    def test_grammar_and_utf8_adversarial_against_oracle(self):
        rng=random.Random(446)
        values=[None,True,False,0,-42,1.25,'ação 日本 😀\0\n"\\',[],{}, {'a':[1,True,None,{'b':'ç'}]}]
        values += [{str(i):[rng.randint(-10000,10000),rng.random(),'\u0000😀']} for i in range(30)]
        valid=[json.dumps(v,ensure_ascii=ascii_mode,separators=(',',':')).encode() for v in values for ascii_mode in [False,True]]
        valid += [b'1e9999',b'0.000000000001',b'-0',b'{"a":1,"a":2}',b'[1,2,3]\r\n',b'"\\ud83d\\ude00"']
        invalid=[b'',b'+1',b'01',b'1.',b'1e',b'--1',b'NaN',b'Infinity',b'[1,]',b'{"a":1,}',b'{1:2}',b'{"a" 1}',b'true false',b'"\0"',b'"\\uD800"',b'"\\uDC00"',b'"\\uD800\\u0041"',b'"\xc0\x80"',b'"\xed\xa0\x80"',b'"\\q"',b'\xef\xbb\xbfnull',b'[[]',b']',b'[}',b'"x',b'null\0']
        for flags in [[],['--no-opt']]:
            binary=self.build('own b:*byte=alloc<byte>(8192);val n:int=read_bytes(b,8192);val r:json::ValidationResult=json::validate(b,n,64,4096);print(r.valid,r.position,r.tokens);',flags)
            for data in valid+invalid:
                r=subprocess.run([binary],input=data,capture_output=True,timeout=10);self.assertEqual(r.returncode,0,(data,r.stderr));self.assertEqual(r.stderr,b'');self.assertEqual(r.stdout.split()[0]==b'aSsIs',data in valid,(data,r.stdout))
                if data in valid and data!=b'1e9999':json.loads(data)

    def test_budgets_and_error_position(self):
        for flags in [[],['--no-opt']]:
            binary=self.build('own b:*byte=alloc<byte>(8192);val n:int=read_bytes(b,8192);val r:json::ValidationResult=json::validate(b,n,4,10);print(r.valid,r.position);',flags)
            for data,ok in [(b'[1,2,3]',True),(b'[[[[0]]]]',True),(b'[[[[[0]]]]]',False),(b'[1,2,3,4,5]',False),(b'{"x":}',False)]:
                r=subprocess.run([binary],input=data,capture_output=True,timeout=10);self.assertEqual(r.returncode,0,r.stderr);valid,pos=r.stdout.split();self.assertEqual(valid==b'aSsIs',ok,(data,r.stdout));self.assertTrue(0<=int(pos)<=len(data))

    def test_serializer_preserves_nul_unicode_and_destination_on_failure(self):
        for flags in [[],['--no-opt']]:
            binary=self.build('own b:*byte=alloc<byte>(8192);own out:*byte=alloc<byte>(65536);val n:int=read_bytes(b,8192);val size:int=json::quote(b,n,out);assert(size>=0);for(let i:int=0;i<size;i+=1){print(out[i]);}',flags)
            for text in ['','\0\n\r\t"\\','ação 日本 😀',''.join(map(chr,range(128)))]:
                r=subprocess.run([binary],input=text.encode(),capture_output=True,timeout=10);self.assertEqual(r.returncode,0,r.stderr);encoded=bytes(map(int,r.stdout.split()));self.assertEqual(json.loads(encoded),text)
        self.accepted('#yuri <std/json.assis>\n'+base.main('own a:*byte=alloc<byte>(1);a[0]=byte(34);own b:*byte=alloc<byte>(2);b[0]=byte(42);assert(json::quote(a,1,b)==-1);print(b[0]);'),'42\n')

    def test_tokens_offsets_and_no_pointer_escape(self):
        self.accepted('#yuri <std/json.assis>\n'+base.main('own b:*byte=alloc<byte>(5);b[0]=byte(32);b[1]=byte(91);b[2]=byte(48);b[3]=byte(93);val a:json::Token=json::next(b,4,0);val c:json::Token=json::next(b,4,a.next);print(a.kind,a.start,a.end,c.kind,c.start,c.end);'),'91 1 2 2 2 3\n')

if __name__=='__main__':
    for name in list(vars(base.Evolution)):
        if name.startswith('test_'):delattr(base.Evolution,name)
    unittest.main(verbosity=2)
