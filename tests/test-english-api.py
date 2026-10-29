"""Canonical English syntax, standard library APIs and migration coverage."""
import importlib.util
import json
from pathlib import Path
import re
import unittest

spec=importlib.util.spec_from_file_location('evolution',Path(__file__).with_name('test-evolution.py'))
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)

class English(base.Evolution):
    def test_canonical_catalog_and_every_module(self):
        catalog=json.loads((base.ROOT/'stdlib/catalogo.json').read_text(encoding='utf-8'))
        self.assertEqual({x['name'] for x in catalog['libraries']},{'math','strings','memory','errors','convert','algorithms','csv','encoding','cli','json','time','log','iterators','events','unicode','owned','arena','http','process','net','random'})
        mapping=json.loads((base.ROOT/'docs/API-MIGRATION.json').read_text(encoding='utf-8'))
        obsolete=set(mapping['modules'])|set(mapping['identifiers'])|set(mapping['builtins'])
        for library in catalog['libraries']:
            path=base.ROOT/'stdlib'/(library['name']+'.assis')
            result=self.invoke('check',path,'--library');self.assertEqual(result.returncode,0,result.stderr)
            text=re.sub(r'//[^\n]*|miyabi[^\n]*|"(?:[^"\\]|\\.)*"','',path.read_text(encoding='utf-8'))
            public=set(re.findall(r'\b(?:fn|class|struct|enum|namespace)\s+(\w+)',text))
            self.assertFalse(public&obsolete,(library['name'],public&obsolete))

    def test_entry_constructor_import_and_callbacks(self):
        helper=self.source('public pure fn double(n:int):int{return n*2;}','helper.assis')
        # Public without a namespace is intentionally rejected; use an ordinary module.
        helper.write_text('pure fn double(n:int):int{return n*2;}',encoding='utf-8')
        self.accepted('import "helper.assis";\nclass Counter{let value:int;fn init(n:int):void{self.value=n;}fn get():int{return self.value;}}\nfn main():int{let c:Counter=new Counter(21);val f:pure fn(int):int=double;print(f(c.get()));free(c);return 0;}','42\n')
        self.accepted('class Base<T>{let item:T;fn init(n:T):void{self.item=n;}}fn main():int{let b:Base<int>=new Base<int>(42);print(b.item);free(b);return 0;}','42\n')
        self.rejected('fn main():int{return 0;}fn main():int{return 0;}','função declarada duas vezes')
        self.rejected('fn main<T>():int{return 0;}','gen')
        self.rejected('namespace x;public fn main():int{return 0;}','sem namespace')
        self.rejected('class C{fn init():void{}fn init():void{}}fn main():int{return 0;}','duas vezes')

    def test_managed_english_libraries(self):
        self.accepted('import "std/unicode.assis";\nimport "std/owned.assis";\nsafe fn main():int{own b:*byte=alloc<byte>(3);b[0]=byte(65);b[1]=byte(0);b[2]=byte(66);own s:unicode::String=new unicode::String();assert(s.load(slice_of(b,0,3)));assert(s.size()==3);own list:owned::OwnedList<unicode::String>=new owned::OwnedList<unicode::String>();list.push_front(move(s));assert(list.get(0).size()==3);own result:unicode::String=list.pop_front();assert(result.size()==3);return 0;}')

    def test_english_builtin_aliases_remain_compatible(self):
        self.accepted('safe fn main():int{assert(monotonic_ms()>=0);assert(civil_ms()>0);assert(sleep_ms(0)==0);own b:*byte=alloc<byte>(3);assert(len(slice_of(b,0,3))==3);return 0;}')
        self.accepted('safe fn main():int{assert(monotonic_ms()>=0);assert(sleep_ms(0)==0);own b:*byte=alloc<byte>(1);assert(len(slice_of(b,0,1))==1);return 0;}')

if __name__=='__main__':
    for name in list(vars(base.Evolution)):
        if name.startswith('test_'):delattr(base.Evolution,name)
    unittest.main(verbosity=2)
