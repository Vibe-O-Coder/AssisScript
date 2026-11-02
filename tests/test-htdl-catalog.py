"""HTDL 0.1 static catalog: independent XML trees, constraints and editor isolation."""
import importlib.util
import json
import os
from pathlib import Path
import random
import subprocess
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('bootstrap', Path(__file__).with_name('test-htdl-parser.py'))
bootstrap = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bootstrap)
base = bootstrap.base
ROOT = base.ROOT
KEYS = dict(bootstrap.ATTRIBUTES, **dict(zip(
    ['name','content','src','format','href','ordered','for','kind','value','placeholder','required','checked','alt',
     'a11y-live','on:click','on:input','on:change','on:submit','on:focus','on:blur'], range(11,31))))


def document(body='', head=None):
    return ('<div type="document" version="0.1" lang="pt-BR"><div type="head">' +
            (head if head is not None else '<div type="title">Title</div>') +
            '</div><div type="body">' + body + '</div></div>')


def element(kind, content='', attrs=''):
    return f'<div type="{kind}"{(" " + attrs) if attrs else ""}>{content}</div>'


class Catalog(base.Evolution):
    fault_program = bootstrap.HTDLParser.fault_program

    def invoke(self, *args, **kwargs):
        if args and args[0] in ('check','build','run','ir'):
            args = (*args, '--safe')
        return super().invoke(*args, **kwargs)

    @classmethod
    def setUpClass(cls):
        cls.shared = tempfile.TemporaryDirectory(prefix='assis-catalog-')
        cls.drivers, cls.inspectors = [], []
        for mode, flags in [('optimized', []), ('reference', ['--no-opt'])]:
            for source, targets in [('tests/fixtures/htdl-catalog-driver.assis', cls.drivers),
                                    ('tools/htdl-check.assis', cls.inspectors)]:
                binary = Path(cls.shared.name) / (mode + str(len(targets)) + Path(source).stem + '.exe')
                r = subprocess.run([str(base.COMPILER),'build',str(ROOT/source),'--safe','--debug','-o',str(binary),*flags],
                                   capture_output=True,timeout=60)
                if r.returncode:
                    raise AssertionError(r.stderr.decode(errors='replace'))
                targets.append((mode,binary))

    @classmethod
    def tearDownClass(cls):
        cls.shared.cleanup()

    def parse(self, source, code=0, oracle=False):
        data = source.encode() if isinstance(source,str) else source
        outputs=[]
        for mode,binary in self.drivers:
            r=subprocess.run([str(binary)],input=data,capture_output=True,timeout=30)
            self.assertEqual((r.returncode,r.stderr),(0,b''),(mode,r.stderr))
            outputs.append(r.stdout)
            lines=r.stdout.decode().splitlines()
            d=list(map(int,lines[0].split()))
            self.assertEqual(d[0],code,(mode,source[:400],d))
            self.assertTrue(0<=d[1]<=d[2]<=len(data))
            if code:
                self.assertEqual(len(lines),1)
            if oracle:
                records=[]
                for i in range(1,len(lines),2):
                    slot,kind,pi,parent,start,end,size=map(int,lines[i].split())
                    value=bytes.fromhex(lines[i+1]).decode()
                    self.assertEqual(len(value.encode()),size)
                    records.append(dict(slot=slot,kind=kind,parent_instance=pi,parent=parent,start=start,end=end,value=value))
                children={}
                for n in records:
                    if n['parent_instance']:children.setdefault(n['parent'],[]).append(n)
                def visit(n):
                    attrs,content={},[]
                    for child in children.get(n['slot'],[]):
                        if child['kind']>100:
                            key=(data[child['start']:child['end']].split(b'=')[0].strip().decode() if child['kind']==200 else
                                 next(k for k,v in KEYS.items() if v+100==child['kind']))
                            attrs[key]=child['value']
                        else:
                            value=visit(child) if child['kind']==1 else child['value']
                            if isinstance(value,str) and content and isinstance(content[-1],str):content[-1]+=value
                            else:content.append(value)
                    return attrs,content
                self.assertEqual(visit(records[0]),bootstrap.xml_model(data))
        self.assertEqual(outputs[0],outputs[1])
        return d

    def inspect(self,source):
        data=source.encode() if isinstance(source,str) else source
        outputs=[]
        for mode,binary in self.inspectors:
            r=subprocess.run([str(binary)],input=data,capture_output=True,timeout=30)
            self.assertEqual((r.returncode,r.stderr),(0,b''),(mode,r.stderr))
            outputs.append(r.stdout)
        self.assertEqual(outputs[0],outputs[1])
        lines=outputs[0].decode().splitlines();count,truncated=map(int,lines[0].split())
        ds=[list(map(int,line.split())) for line in lines[1:]]
        self.assertEqual(count,len(ds));self.assertLessEqual(count,64)
        return ds,truncated

    def test_all_23_types_with_independent_xml_tree(self):
        body=element('main',element('header',element('heading','Title','level="1"'))+
             element('section',element('paragraph','A '+element('text','fragment')),'a11y-label="Section"')+
             element('nav',element('link','Jump','href="#target"'),'a11y-label="Navigation"')+
             element('list',element('item',element('paragraph','One')),'ordered="true"')+
             element('container',element('button','OK')+element('image','','src="./a.png" alt=""'),'data-count="2" data-label="A &amp; B"')+
             element('form',element('label','Name','for="field"')+element('input','','id="field" name="user" placeholder="Name" required="true"')+
                     element('button','Send','action="submit"'),'id="target"')+
             element('footer',element('paragraph','End')))
        head=element('script','','src="./app.assis" format="source"')+element('meta','','name="description" content="Demo"')+element('title','Catalog')
        self.parse(document(body,head),oracle=True)

    def test_declarative_catalog_cases(self):
        corpus=json.loads((ROOT/'tests/fixtures/htdl-catalog-corpus.json').read_text(encoding='utf-8'))
        for case in corpus['cases']:
            with self.subTest(case=case['id']):self.parse(case['source'],case['code'],case.get('xml_oracle',False))

    def test_head_cardinality_order_and_empty_models(self):
        self.parse(document('',element('meta','','name="description" content=""')+element('title','Title')),oracle=True)
        for head in ['',element('title','A')*2,element('title','A')+element('meta','','name="description" content="a"')*2,
                     element('title','A')+element('script','','src="a.wasm" format="wasm"')*2]:
            self.parse(document('',head),204)
        for kind,attrs in [('meta','name="description" content="x"'),('script','src="a.assis" format="source"')]:
            self.parse(document('',element('title','A')+element(kind,'source',attrs)),204)
        self.parse(document(element('input','text','a11y-label="X"')),204)
        self.parse(document(element('image',element('text','x'),'src="x.png" alt="x"')),204)

    def test_body_content_models_and_ancestor_constraints(self):
        for body in [element('item'),element('list',element('paragraph','x')),element('paragraph',element('input','','a11y-label="X"')),
                     element('form',element('container',element('form'))),element('main')*2,
                     *[element(k,element('section',element('main'))) for k in ['header','footer','nav']],
                     element('button','Send','action="submit"'),element('section','loose text')]:
            self.parse(document(body),204)
        self.parse(document(element('form',element('section',element('button','Send','action="submit"')))),oracle=True)

    def test_required_attributes_enums_and_accessible_names(self):
        cases=[('link','Text','',206),('label','Text','',206),('image','','src="x.png"',206),
               ('input','','kind="password" a11y-label="X"',206),('input','','checked="false" a11y-label="X"',206),
               ('input','','required="yes" a11y-label="X"',206),('list','','ordered="1"',206),
               ('paragraph','x','a11y-live="loud"',206),('link','','href="a.htdl"',206),
               ('button',element('text','Hidden','hidden="true"'),'',206),('section','','a11y-label="  "',206),
               ('paragraph','x','disabled="true"',203),('nav','','a11y-live="polite"',203)]
        for kind,content,attrs,code in cases:self.parse(document(element(kind,content,attrs)),code)
        for kind in ['text','number','checkbox']:
            attrs=f'kind="{kind}" value="temporarily invalid" a11y-label="Field" disabled="false" required="true"'
            if kind=='checkbox':attrs+=' checked="false"'
            self.parse(document(element('input','',attrs)),oracle=True)

    def test_cross_references_forward_labels_and_form_names(self):
        self.parse(document(element('input','','id="x"')+element('label','Name','for="x"')),oracle=True)
        for body in [element('input','','placeholder="Not a name"'),element('label','Name','for="missing"'),
                     element('paragraph','X','id="x"')+element('label','Name','for="x"')]:self.parse(document(body),207)
        field=element('input','','a11y-label="X" name="shared"')
        self.parse(document(element('form',field*2)),205)
        self.parse(document(element('form',field)*2+field*2),oracle=True)

    def test_events_require_script_and_references_are_identifiers(self):
        head=element('title','A')+element('script','','src="./app.assis" format="source"')
        cases=[('button','Act','on:click="activate" on:focus="focus" on:blur="blur"'),
               ('link','Link','href="./a.htdl" on:click="go"'),('input','','a11y-label="X" on:input="edit" on:change="change"'),
               ('form','','on:submit="submit"')]
        for kind,content,attrs in cases:
            self.parse(document(element(kind,content,attrs),head))
            self.parse(document(element(kind,content,attrs)),301)
        for value in ['run()','run-now','x.y','_a b','']:
            self.parse(document(element('button','X',f'on:click="{value}"'),head),206)
        self.parse(document(element('paragraph','X','on:click="go"'),head),203)
        self.parse(document(element('button','X','on:unknown="go"'),head),203)

    def test_dynamic_data_attributes_and_duplicates(self):
        self.parse(document(element('paragraph','X','data-a="1" data-b="2" data-abc-2="3"')),oracle=True)
        self.parse(document(element('paragraph','X','data-a="1" data-a="2"')),202)
        for key in ['data-','data-X','data-2','data-a_b']:
            self.parse(document(element('paragraph','X',key+'="x"')),203)
        self.parse(document('',element('title','X','data-a="x"')),203)

    def test_resource_references_are_data_with_no_execution_schemes(self):
        for href in ['#x','./a.htdl','../a.htdl','https://example.test/a','a/b?key:value']:
            self.parse(document(element('link','Link',f'href="{href}"')),oracle=True)
        for href in ['','javascript:run','file:///x','http://example.test','//example.test/a','C:\\file','https:///x','a/b c']:
            self.parse(document(element('link','Link',f'href="{href}"')),206)
        # No resource is opened: these intentionally do not exist.
        self.parse(document(element('image','','src="./not-found.png" alt="text"')))

    def test_random_structural_documents_against_xml(self):
        rng=random.Random(20261102)
        for _ in range(35):
            blocks=[element('paragraph',f'{rng.randrange(10000)} &amp; é🙂','data-n="x"') for _ in range(rng.randrange(1,12))]
            for _ in range(rng.randrange(1,8)):
                blocks=[element(rng.choice(['section','container','header','footer','nav']),''.join(blocks))]
            self.parse(document(''.join(blocks)),oracle=True)

    def test_inspector_recovers_semantic_errors_and_preserves_utf16_spans(self):
        source=document(element('paragraph','🙂')+'\r\n'+element('heading','Missing level')+'\r\n'+element('image','','src="x.png"')+
                        element('input','','placeholder="X"'))
        ds,truncated=self.inspect(source)
        self.assertEqual([d[0] for d in ds],[206,206,207]);self.assertEqual(truncated,0)
        data=source.encode()
        for d in ds:
            prefix=data[:d[1]].decode().replace('\r\n','\n').replace('\r','\n')
            self.assertEqual(d[3],prefix.count('\n')+1)
            self.assertEqual(d[4],len(prefix.split('\n')[-1].encode('utf-16-le'))//2+1)
        self.assertEqual(self.inspect(document()),([],0))
        self.assertEqual(self.inspect(b'\xff')[0][0][0],101)
        self.assertEqual(self.inspect(document()[:-1])[0][0][0],102)
        # Syntactically complete yet malformed semantic roots must never trap.
        for draft in [element('button','X','on:click="go"'),element('label','Missing target'),
                      '<div></div>',element('document','','version="0.1" lang="en"'),
                      element('document',element('button','X','on:click="go"'),'version="0.1" lang="en"')]:
            self.assertTrue(self.inspect(draft)[0])

    def test_inspector_cap_work_and_truncation_never_activate(self):
        ds,truncated=self.inspect(document(element('heading','X')*80))
        self.assertEqual((len(ds),truncated),(64,1))
        ds,truncated=self.inspect(b'x'*1048577)
        self.assertEqual(ds[0][0],401)
        # Many reference-bearing controls force the explicit comparison-work limit.
        body=element('form',''.join(element('input','',f'a11y-label="X" name="n{i}"') for i in range(200)))
        self.parse(document(body),401)

    def test_editor_hostile_semantic_roots_and_truncated_unicode(self):
        types=['document','head','title','body','container','paragraph','text','heading','button','meta','script','main','section','header','footer','nav','link','list','item','label','input','form','image','unknown']
        for kind in types:
            draft=element(kind,'X','on:click="run"')
            self.assertTrue(self.inspect(draft)[0],kind)
        data=document(element('paragraph','é🙂 &amp;')).encode()
        for stop in range(0,len(data),11):self.assertTrue(self.inspect(data[:stop])[0])

    def test_catalog_quota_rollback_queries_and_caller_owned_diagnostics(self):
        source=document(element('form',element('input','','id="field" a11y-label="X" data-note="A &amp; B"')))
        literal=bootstrap.literal(source)
        self.accepted(bootstrap.PREFIX+bootstrap.main(
            'own s:documents::Store=try_new documents::Store(200000,1000,100);'
            'own out:htdl::Diagnostics=try_new htdl::Diagnostics(64);assert(out!=null && out.is_ready());'
            f'assert(htdl::load_catalog(s,1,{literal}).code==0);'
            'val old:doctree::NodeId=s.active_document().nodes().root();val held:int=s.storage_bytes();'
            f'assert(htdl::inspect(s,2,{literal},out) && out.size()==0 && !out.truncated());'
            'assert(s.storage_bytes()==held && s.active_document().nodes().contains(old) && !s.has_candidate());'
            '{borrow d:documents::Document=s.active_document();val input:doctree::NodeId=htdl::find_id(d.nodes(),utf8("field"));'
            'assert(htdl::kind(d.nodes(),input)==21 && htdl::query(d.nodes(),21,utf8(""),new doctree::NodeId()).slot==input.slot);'
            'assert(htdl::value_equals(d.nodes(),htdl::data_attribute(d,input,utf8("data-note")),utf8("A & B")));}'
            f'assert(htdl::load(s,3,{literal}).code==203 && s.storage_bytes()==held && s.active_document().nodes().contains(old));'
            'own bad:htdl::Diagnostics=try_new htdl::Diagnostics(0);assert(!bad.is_ready());'
            f'assert(!htdl::inspect(s,4,{literal},bad));'
            'assert(s.begin(5,utf8("external"))==0);'
            f'assert(htdl::inspect(s,6,{literal},out) && out.size()==1 && out.get(0).code==401);'
            'assert(s.has_candidate() && s.candidate().instance()==5 && s.candidate().source_size()==8 && s.abort(5));'
            'let ok:bool=false;let refused:bool=false;'
            'for(let limit:int=72;limit<18000;limit+=193){own t:documents::Store=try_new documents::Store(limit,1000,100);'
            f'val r:htdl::Diagnostic=htdl::load_catalog(t,1,{literal});'
            'if(r.code==0){ok=true;}else{refused=true;assert(r.code==401 && t.storage_bytes()==72 && !t.has_candidate());}}assert(ok && refused);'))

    def test_os_allocation_refusal_retains_active_and_neighbor(self):
        valid=bootstrap.literal(document(element('paragraph','Old')))
        candidate=bootstrap.literal(document(element('section',element('paragraph','New'))))
        init='own s:documents::Store=try_new documents::Store(1000000,1000,100);own neighbor:documents::Store=try_new documents::Store(1000000,1000,100);own out:htdl::Diagnostics=try_new htdl::Diagnostics(64);'+f'assert(htdl::load_catalog(s,1,{valid}).code==0 && htdl::load_catalog(neighbor,100,{valid}).code==0);val old:doctree::NodeId=s.active_document().nodes().root();val held:int=s.storage_bytes();'
        # Independent OS denial plus bounded slab draining, including editor output.
        for operation in [f'val r:htdl::Diagnostic=htdl::load_catalog(s,2,{candidate});assert(r.code==401);',
                          f'assert(htdl::inspect(s,2,{candidate},out) && out.size()==1 && out.get(0).code==401);']:
            setup,drain,cleanup=bootstrap.preparation.exhaustion()
            self.fault_program(bootstrap.PREFIX+bootstrap.main(init+'unsafe{'+setup+drain+operation+
                'assert(s.storage_bytes()==held && !s.has_candidate() && s.active_document().nodes().contains(old));'
                'assert(neighbor.active_document().instance()==100);s.close();neighbor.close();'+cleanup+'}'), '')

    def test_ir_layout_and_five_generated_formats(self):
        for flags in [[],['--no-opt']]:
            result=self.invoke('ir',ROOT/'tools/htdl-check.assis',*flags)
            self.assertEqual(result.returncode,0,result.stderr)
            ir=json.loads(result.stdout);self.assertEqual(ir['astFallbacks'],0)
            allocations={v['type']:v['allocationBytes'] for v in ir['backendValues'] if 'allocationBytes' in v}
            self.assertEqual(allocations['htdl::Parser'],96)
            self.assertEqual(allocations['htdl::Diagnostics'],40)
            for target in ['windows-x64','linux-x64','linux-arm64','macos-x64','macos-arm64']:
                result=self.invoke('build',ROOT/'tools/htdl-check.assis','--target',target,'-o',self.temp/target,*flags)
                self.assertEqual(result.returncode,0,(target,result.stderr))


if __name__=='__main__':
    for name in list(vars(base.Evolution)):
        if name.startswith('test_'):delattr(base.Evolution,name)
    unittest.main(verbosity=2)
