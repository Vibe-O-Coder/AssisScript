"""Real HTDL bootstrap corpus, independent XML trees and transactional failures."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import random
import subprocess
import tempfile
import unittest
import xml.etree.ElementTree as ET

spec = importlib.util.spec_from_file_location('preparation', Path(__file__).with_name('test-buffer-preallocation.py'))
preparation = importlib.util.module_from_spec(spec)
spec.loader.exec_module(preparation)
base = preparation.base
ROOT = base.ROOT
PREFIX = 'import "std/htdl.assis";'
ATTRIBUTES = {'type': 1, 'version': 2, 'lang': 3, 'level': 4, 'id': 5,
              'class': 6, 'hidden': 7, 'disabled': 8, 'action': 9, 'a11y-label': 10}


def document(body='', title='Title'):
    return ('<div type="document" version="0.1" lang="pt-BR">'
            '<div type="head"><div type="title">' + title + '</div></div>'
            '<div type="body">' + body + '</div></div>')


def main(body):
    return 'safe fn main():int{' + body + 'return 0;}'


def literal(value):
    return 'utf8(' + json.dumps(value, ensure_ascii=False) + ')'


def xml_model(source):
    """Independent standard-library XML parser; used only for its overlapping syntax.

    ElementTree implements entity expansion/CR normalization independently. This
    oracle does not reuse the AssisScript parser, grammar routines or node layout.
    """
    root = ET.fromstring(source)

    def visit(node):
        attrs = dict(node.attrib)
        if 'class' in attrs:
            attrs['class'] = ' '.join(dict.fromkeys(attrs['class'].split()))
        content = []
        if node.text:
            content.append(node.text)
        for child in node:
            content.append(visit(child))
            if child.tail:
                content.append(child.tail)
        # Comments can split character records in HTDL; they are absent from ET.
        collapsed = []
        for value in content:
            if isinstance(value, str) and collapsed and isinstance(collapsed[-1], str):
                collapsed[-1] += value
            else:
                collapsed.append(value)
        return attrs, collapsed

    return visit(root)


def native_model(records):
    children = {}
    for record in records:
        if record['parent_instance']:
            children.setdefault(record['parent'], []).append(record)

    def visit(node):
        attrs, content = {}, []
        for child in children.get(node['slot'], []):
            if child['kind'] > 100:
                key = next(k for k, v in ATTRIBUTES.items() if v + 100 == child['kind'])
                attrs[key] = child['value']
            else:
                value = visit(child) if child['kind'] == 1 else child['value']
                if isinstance(value, str) and content and isinstance(content[-1], str):
                    content[-1] += value
                else:
                    content.append(value)
        return attrs, content

    return visit(records[0])


class HTDLParser(base.Evolution):
    fault_program = preparation.BufferPreallocation.fault_program

    @classmethod
    def setUpClass(cls):
        cls.shared = tempfile.TemporaryDirectory(prefix='assis-htdl-')
        cls.drivers = []
        for mode, flags in [('optimized', []), ('reference', ['--no-opt'])]:
            binary = Path(cls.shared.name) / (mode + '.exe')
            result = subprocess.run([str(base.COMPILER), 'build', str(ROOT / 'tests/fixtures/htdl-driver.assis'),
                                     '--safe', '--debug', '-o', str(binary), *flags],
                                    capture_output=True, text=True, encoding='utf-8', timeout=60)
            if result.returncode:
                raise AssertionError(result.stderr)
            cls.drivers.append((mode, binary))

    @classmethod
    def tearDownClass(cls):
        cls.shared.cleanup()

    def invoke(self, *args, **kwargs):
        if args and args[0] in ('check', 'build', 'run', 'ir'):
            args = (*args, '--safe')
        return super().invoke(*args, **kwargs)

    def parse(self, source, expected=0, oracle=False):
        data = source.encode('utf-8') if isinstance(source, str) else source
        outputs = []
        records = []
        for mode, binary in self.drivers:
            result = subprocess.run([str(binary)], input=data, capture_output=True, timeout=60)
            self.assertEqual(result.returncode, 0, (mode, data[:200], result.stderr.decode(errors='replace')))
            self.assertEqual(result.stderr, b'', (mode, result.stderr))
            outputs.append(result.stdout)
            lines = result.stdout.decode('utf-8').splitlines()
            diagnostic = list(map(int, lines[0].split()))
            self.assertEqual(diagnostic[0], expected, (mode, source[:200], diagnostic))
            self.assertTrue(0 <= diagnostic[1] <= diagnostic[2] <= len(data), diagnostic)
            records = []
            for index in range(1, len(lines), 2):
                slot, kind, pi, parent, start, end, size = map(int, lines[index].split())
                value = bytes.fromhex(lines[index + 1])
                self.assertEqual(len(value), size)
                self.assertTrue(0 <= start <= end <= len(data))
                records.append(dict(slot=slot, kind=kind, parent_instance=pi, parent=parent,
                                    start=start, end=end, value=value.decode('utf-8')))
            if oracle:
                self.assertEqual(native_model(records), xml_model(data))
        self.assertEqual(outputs[0], outputs[1], 'Optimized/reference tree or diagnostic differs')
        return diagnostic, records

    def test_frozen_declarative_corpus(self):
        corpus = json.loads((ROOT / 'tests/fixtures/htdl-bootstrap-corpus.json').read_text(encoding='utf-8'))
        for case in corpus['cases']:
            with self.subTest(case=case['id']):
                source = case['source'] if case.get('complete') else document(case['source'])
                self.parse(source, case['code'], case.get('xml_oracle', False))

    def test_unicode_entities_comments_and_single_decoding(self):
        self.parse(document('<div type="paragraph">A<!-- gap -->ção &amp;lt; &lt; &gt; &quot; &apos; &#65; &#x1F642; é</div>'), oracle=True)
        self.parse('\ufeff<!--bom-->' + document('<div type="paragraph">a\rb\r\nc\n</div>') + '<!--end-->', oracle=True)
        self.parse(document('<div type=button a11y-label="  Nome  " disabled=false></div>'))
        self.parse(document("<div type='heading' level='6'>Hi<div type='text'>there</div></div>"))

    def test_every_unicode_scalar_boundary_and_invalid_entity(self):
        for scalar in [9, 10, 13, 32, 127, 128, 2047, 2048, 55295, 57344, 65535, 65536, 1114111]:
            _, records = self.parse(document(f'<div type="paragraph">&#{scalar};</div>'), oracle=scalar != 65535)
            self.assertEqual(records[-1]['value'], chr(scalar))
        for value in ['0', '1', '11', '31', '55296', '57343', '1114112', '999999999999999999999999999999', '', 'x', 'xGG', '-1', '+1']:
            self.parse(document(f'<div type=paragraph>&#{value};</div>'), 102)

    def test_invalid_utf8_controls_and_exact_utf16_diagnostics(self):
        for value in [b'\x80', b'\xc0\x80', b'\xed\xa0\x80', b'\xf4\x90\x80\x80', b'\xf0\x9f', b'\xff', b'\0', b'\x01', b'\x1f']:
            self.parse(b'<!--ok-->' + value, 101)
        source = document('<div type="paragraph">🙂&bad;</div>').replace('<div type="body">', '<div type="body">\r\n')
        diagnostic, _ = self.parse(source, 102)
        start = source.encode().index(b'&bad;')
        self.assertEqual(diagnostic[1:3], [start, start + 4])
        prefix = source.encode()[:start].decode()
        column = len(prefix.rsplit('\n', 1)[-1].encode('utf-16-le')) // 2 + 1
        self.assertEqual(diagnostic[3:5], [2, column])

    def test_original_source_spans_attributes_and_decoded_values(self):
        source = document('<div type="paragraph" id="p" class="a a b">A&amp;B</div>')
        _, records = self.parse(source, oracle=True)
        data = source.encode()
        paragraph = next(r for r in records if r['kind'] == 105)
        self.assertEqual(data[paragraph['start']:paragraph['end']], b'id="p"')
        text = next(r for r in records if r['kind'] == 2 and r['value'] == 'A&B')
        self.assertEqual(data[text['start']:text['end']], b'A&amp;B')
        parent = next(r for r in records if r['slot'] == text['parent'])
        self.assertEqual(data[parent['start']:parent['end']], b'<div type="paragraph" id="p" class="a a b">A&amp;B</div>')

    def test_attribute_order_quote_forms_and_random_trees_against_xml(self):
        rng = random.Random(20261101)
        for sample in range(35):
            pieces = []
            for index in range(rng.randrange(1, 10)):
                attrs = [('type', rng.choice(['paragraph', 'heading', 'button'])), ('id', f'n{sample}_{index}'), ('class', 'one two one')]
                if attrs[0][1] == 'heading':
                    attrs.append(('level', str(rng.randrange(1, 7))))
                rng.shuffle(attrs)
                opening = '<div ' + ' '.join(k + '="' + v + '"' for k, v in attrs) + '>'
                pieces.append(opening + rng.choice(['Ação', '🙂 &amp; x', 'é<div type="text"> inline </div>tail']) + '</div>')
            source = document('<div type="container">' + ''.join(pieces) + '</div>')
            self.parse(source, oracle=True)
            # These transformations are not XML. The independent oracle remains
            # the original quoted tree, and all three HTDL spellings must agree.
            _, original = self.parse(source)
            _, single = self.parse(source.replace('"', "'"))
            self.assertEqual(native_model(original), native_model(single))
        self.parse(document('<div id=p type=paragraph class="a b">A</div>'))

    def test_depth_and_source_size_exact_boundaries(self):
        # document/body account for two levels; deepest container is level 256.
        self.parse(document('<div type=container>' * 254 + '</div>' * 254))
        self.parse(document('<div type=container>' * 255 + '</div>' * 255), 401)
        small = document('')
        exact = small + '<!--' + 'x' * (1048576 - len(small.encode()) - 7) + '-->'
        self.parse(exact)
        self.parse(exact + ' ', 401)

    def test_attribute_value_and_node_limits(self):
        self.parse(document('<div type=paragraph class="' + 'a' * 65536 + '"></div>'))
        self.parse(document('<div type=paragraph class="' + 'a' * 65537 + '"></div>'), 401)
        # Five fixed semantic nodes: document/head/title/title text/body.
        self.parse(document('<div type=paragraph></div>' * 19995))
        self.parse(document('<div type=paragraph></div>' * 19996), 401)

    def test_ids_sort_without_hash_collisions_and_report_second_occurrence(self):
        body = ''.join(f'<div type=paragraph id=n{i:05}></div>' for i in range(1200, -1, -1))
        self.parse(document(body))
        source = document('<div type=paragraph id=b></div><div type=paragraph id=a></div>'
                          '<div type=paragraph id=a></div><div type=paragraph id=b></div>')
        diagnostic, _ = self.parse(source, 205)
        self.assertEqual(diagnostic[1], source.index('id=a', source.index('id=a') + 1))
        source = document('<div type=paragraph id=x></div>' * 5)
        diagnostic, _ = self.parse(source, 205)
        self.assertEqual(diagnostic[1], source.index('id=x', source.index('id=x') + 1))

    def test_adversarial_truncations_and_mutations_are_bounded(self):
        source = document('<div type="paragraph" id="a">&amp;🙂</div>')
        data = source.encode()
        for cut in range(0, len(data), 3):
            # Cuts inside a multibyte scalar are lexical, other truncations syntactic.
            try:
                data[:cut].decode()
                code = 102
            except UnicodeDecodeError:
                code = 101
            self.parse(data[:cut], code)
        for mutation in ['<!DOCTYPE div>', '<?xml version="1.0"?>', '<![CDATA[x]]>', '<DIV type=document>', '<division>', '</div >', '<div/>']:
            self.parse(mutation, 102)

    def test_failed_reload_preserves_active_and_neighbors_and_busy_candidate(self):
        valid = literal(document('<div type=paragraph id=p>old</div>'))
        broken = literal(document('<div type=paragraph id=p>new</div><div type=button></div>'))
        self.accepted(PREFIX + main(
            'own s:documents::Store=try_new documents::Store(200000,1000,100);'
            'own neighbor:documents::Store=try_new documents::Store(200000,1000,100);'
            f'assert(htdl::load(s,1,{valid}).code==0 && htdl::load(neighbor,100,{valid}).code==0);'
            'val old:doctree::NodeId=s.active_document().nodes().root();val before:int=s.storage_bytes();'
            f'assert(htdl::load(s,2,{broken}).code==206);'
            'assert(!s.has_candidate() && s.storage_bytes()==before && s.active_document().nodes().contains(old));'
            f'assert(htdl::load(s,2,{valid}).code==401);'
            f'assert(htdl::load(s,3,{valid}).code==0 && !s.active_document().nodes().contains(old));'
            f'assert(s.begin(4,utf8("external"))==0 && htdl::load(s,5,{valid}).code==401);'
            'assert(s.has_candidate() && s.candidate().source_size()==8 && s.abort(4));'
            'assert(neighbor.active_document().instance()==100);'))

    def test_quota_sweep_reserves_workspace_and_rolls_back_complete_candidate(self):
        source = literal(document('<div type=paragraph id=p class="a b a">text</div>'))
        self.accepted(PREFIX + main(
            'let succeeded:bool=false;let refused:bool=false;'
            'for(let limit:int=72;limit<18000;limit+=97){'
            'own s:documents::Store=try_new documents::Store(limit,1000,100);'
            f'val r:htdl::Diagnostic=htdl::load(s,1,{source});'
            'if(r.code==0){succeeded=true;assert(s.storage_bytes()+htdl::workspace_bytes(' + str(len(document('<div type=paragraph id=p class="a b a">text</div>').encode())) + ')<=limit);}'
            'else{refused=true;assert(r.code==401 && !s.has_active() && !s.has_candidate() && s.storage_bytes()==72);}}'
            'assert(succeeded && refused);'
            'own s:documents::Store=try_new documents::Store(1000,1,100);'
            'assert(s.begin_reserved(1,utf8(""),-1)==4 && s.begin_reserved(1,utf8(""),9223372036854775807)==4);'))

    def test_os_refusal_at_controller_scratch_index_and_tree_preserves_active(self):
        valid = literal(document(''))
        # All supplies are bounded, and denial is local to the child process.
        # The new candidate needs source, Document, Tree, pool, OwnedArray,
        # Parser, scratch and ID index before its first element can be inserted.
        for available in [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 12, 16]:
            setup, drain, cleanup = preparation.exhaustion()
            for index in range(4):
                drain += f'for(let i:int=0;i<{available} && n{index}>0;i++){{n{index}--;free(keep{index}[n{index}]);}}'
            self.fault_program(PREFIX + main(
                'own s:documents::Store=try_new documents::Store(200000,1000,100);'
                f'assert(htdl::load(s,1,{valid}).code==0);'
                'val old:doctree::NodeId=s.active_document().nodes().root();val before:int=s.storage_bytes();'
                'unsafe{' + setup + drain + f'val r:htdl::Diagnostic=htdl::load(s,2,{valid});'
                'assert(r.code==401 && !s.has_candidate() && s.storage_bytes()==before);'
                'assert(s.active_document().nodes().contains(old));s.close();' + cleanup + '}'), '')

    def test_ir_layout_and_all_five_formats(self):
        source = ROOT / 'tests/fixtures/htdl-driver.assis'
        for flags in [[], ['--no-opt']]:
            ir = self.invoke('ir', source, *flags)
            self.assertEqual(ir.returncode, 0, ir.stderr)
            data = json.loads(ir.stdout)
            self.assertEqual(data['astFallbacks'], 0)
            allocations = {v['type']: v['allocationBytes'] for v in data['backendValues'] if 'allocationBytes' in v}
            self.assertEqual(allocations['htdl::Parser'], 96)
            for target in ['windows-x64', 'linux-x64', 'macos-x64', 'linux-arm64', 'macos-arm64']:
                built = self.invoke('build', source, '--target', target, '-o', self.temp / target, *flags)
                self.assertEqual(built.returncode, 0, (target, built.stderr))

    def test_class_normalization_work_is_bounded(self):
        tokens = ' '.join(f't{i:05}' for i in range(2500))
        self.parse(document('<div type=paragraph class="' + tokens + '"></div>'), 401)

    def test_read_only_queries_and_borrowed_views_block_reload(self):
        source = literal(document('<div type=paragraph id=p>A</div><div type=button>B</div>'))
        prefix = PREFIX + 'safe fn open(borrow mut s:documents::Store):void{assert(htdl::load(s,1,' + source + ').code==0);}'
        init = 'own s:documents::Store=try_new documents::Store(100000,1000,100);open(s);'
        self.accepted(prefix + main(init +
            'borrow t:doctree::Tree=s.active_document().nodes();'
            'val root:doctree::NodeId=t.root();assert(htdl::kind(t,root)==1);'
            'val head:doctree::NodeId=htdl::first_element(t,root);assert(htdl::kind(t,head)==2);'
            'val body:doctree::NodeId=htdl::next_element(t,head);assert(htdl::kind(t,body)==4);'
            'val p:doctree::NodeId=htdl::find_id(t,utf8("p"));assert(htdl::kind(t,p)==6);'
            'assert(doctree::absent(htdl::attribute(t,p,-98)) && doctree::absent(htdl::attribute(t,p,11)));'
            'assert(doctree::absent(htdl::find_id(t,utf8("missing"))));'
            'assert(htdl::kind(t,htdl::next_element(t,p))==9);'))
        self.rejected(prefix + main(init + 'borrow t:doctree::Tree=s.active_document().nodes();'
                                   'htdl::load(s,2,' + source + ');'), 'borrow')


if __name__ == '__main__':
    for name in list(vars(base.Evolution)):
        if name.startswith('test_'):
            delattr(base.Evolution, name)
    unittest.main(verbosity=2)
