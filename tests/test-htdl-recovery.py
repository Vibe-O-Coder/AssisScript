"""Editor syntax recovery: source-derived ranges, isolation and strict loader."""
import importlib.util
import json
import os
from pathlib import Path
import random
import subprocess
import unittest

spec = importlib.util.spec_from_file_location('catalog', Path(__file__).with_name('test-htdl-catalog.py'))
catalog = importlib.util.module_from_spec(spec)
spec.loader.exec_module(catalog)
base, bootstrap = catalog.base, catalog.bootstrap
document, element = catalog.document, catalog.element


class Recovery(base.Evolution):
    setUpClass = classmethod(catalog.Catalog.setUpClass.__func__)
    tearDownClass = classmethod(catalog.Catalog.tearDownClass.__func__)
    inspect = catalog.Catalog.inspect
    parse = catalog.Catalog.parse
    def invoke(self, *args, **kwargs):
        if args and args[0] in ('check','build','run','ir'):
            args = (*args, '--safe')
        return base.Evolution.invoke(self, *args, **kwargs)

    def ranges(self, source, diagnostics):
        data = source.encode()
        for code, start, end, line, column, end_line, end_column in diagnostics:
            self.assertTrue(0 <= start <= end <= len(data))
            for offset, actual in [(start, (line, column)), (end, (end_line, end_column))]:
                prefix = data[:offset].decode().replace('\r\n', '\n').replace('\r', '\n')
                expected = (prefix.count('\n') + 1, len(prefix.split('\n')[-1].encode('utf-16-le')) // 2 + 1)
                self.assertEqual(actual, expected)

    def test_independent_entities_and_later_siblings(self):
        source = document(element('paragraph', 'A &wrong; B &other; C') + element('paragraph', '&third;'))
        ds, truncated = self.inspect(source)
        self.assertEqual([d[0] for d in ds], [102]*3)
        self.assertEqual([d[1] for d in ds], [source.index('&'+name) for name in ['wrong', 'other', 'third']])
        self.assertEqual(truncated, 0)
        self.parse(source, 102)

    def test_missing_quotes_and_attribute_syntax_preserve_following_siblings(self):
        for broken in ['<div type="paragraph>', '<div type=paragraph bogus>', '<div type=paragraph class=>']:
            source = document(broken+'broken</div>'+element('paragraph','&later;'))
            ds, truncated = self.inspect(source)
            self.assertGreaterEqual(len(ds), 2, (broken, ds))
            self.assertEqual(ds[-1][1], source.index('&later;'))
            self.assertEqual(truncated, 0)
            self.parse(source, 102)

    def test_unknown_tags_duplicate_and_unsupported_attributes(self):
        source = document('<span>foreign</span>'+element('paragraph', '', 'id=x id=y')+element('paragraph', '', 'bogus=x')+element('paragraph','&last;'))
        ds, truncated = self.inspect(source)
        self.assertEqual([d[0] for d in ds], [102,102,202,203,102])
        self.assertEqual(truncated, 0)
        self.parse(source, 102)

    def test_comment_recovery_ignores_markup_until_terminator(self):
        source = document('<!-- invalid -- <div type=heading>&ignored;</div> -->'+element('paragraph','&later;'))
        ds, truncated = self.inspect(source)
        self.assertEqual([d[0] for d in ds], [102,102])
        self.assertEqual(ds[-1][1], source.index('&later;'))
        self.assertFalse(any(d[1] == source.index('&ignored;') for d in ds))
        self.assertEqual(truncated, 0)
        self.parse(source, 102)

    def test_utf16_multiline_bom_and_crlf_positions(self):
        source = '\ufeff'+document(element('paragraph','🙂 é\r\n&one;\r&two;\n&three;'))
        ds, truncated = self.inspect(source)
        self.assertEqual([d[0] for d in ds], [102]*3)
        self.assertEqual(truncated, 0)
        self.ranges(source, ds)

    def test_limits_saturation_and_incomplete_documents(self):
        ds, truncated = self.inspect(document(element('paragraph','&bad;')*90))
        self.assertEqual((len(ds), truncated), (64,1))
        for source in ['', '   ', '<!-- only -->', '<div', '</div>', document()[:-1]]:
            ds, truncated = self.inspect(source)
            self.assertTrue(ds)
            self.assertEqual(truncated, 0)
        deep = document('<div type=container>'*256)
        self.assertEqual(self.inspect(deep)[0][-1][0], 401)
        self.assertEqual(self.inspect(b'\xff')[0][0][0], 101)
        self.assertEqual(self.inspect(b'x'*1048577)[0][0][0], 401)

    def test_valid_sources_have_identical_static_semantics(self):
        self.assertEqual(self.inspect(document(element('paragraph','A &amp; B é🙂'))), ([],0))
        source = document(element('heading','No level')+element('image','','src=x.png')+element('input','','placeholder=X'))
        self.assertEqual([d[0] for d in self.inspect(source)[0]], [206,206,207])
        # A syntax error suppresses semantic checks on the partial tree.
        source = document(element('paragraph','&bad;')+element('heading','No level'))
        self.assertEqual([d[0] for d in self.inspect(source)[0]], [102])

    def test_seeded_mutation_and_all_utf8_boundary_truncations(self):
        source = document(element('section',element('paragraph','A &amp; B é🙂')*2))
        rng = random.Random(2026110201)
        samples = [source[:n] for n in range(0,len(source),7)]
        for _ in range(90):
            at = rng.randrange(len(source))
            samples.append(source[:at]+rng.choice(['<','>','&bad;','"','</div>'])+source[at+1:])
        for draft in samples:
            ds, truncated = self.inspect(draft)
            self.ranges(draft, ds)
            self.assertLessEqual(len(ds),64)
            self.assertIn(truncated,[0,1])

    def test_active_neighbor_and_foreign_candidate_survive_damaged_draft(self):
        good = bootstrap.literal(document(element('paragraph','Old')))
        broken = bootstrap.literal(document(element('paragraph','&one; &two;')))
        self.accepted(bootstrap.PREFIX+bootstrap.main(
            'own s:documents::Store=try_new documents::Store(1000000,1000,100);'
            'own neighbor:documents::Store=try_new documents::Store(1000000,1000,100);'
            'own out:htdl::Diagnostics=try_new htdl::Diagnostics(64);'
            f'assert(htdl::load_catalog(s,1,{good}).code==0 && htdl::load_catalog(neighbor,1,{good}).code==0);'
            'val old:doctree::NodeId=s.active_document().nodes().root();val held:int=s.storage_bytes();'
            f'assert(htdl::inspect(s,2,{broken},out) && out.size()==2);'
            'assert(s.active_document().nodes().contains(old) && s.storage_bytes()==held && !s.has_candidate());'
            'assert(neighbor.active_document().instance()==1);'
            f'assert(htdl::load_catalog(s,3,{broken}).code==102 && s.storage_bytes()==held);'
            'assert(s.begin(4,utf8("foreign"))==0);'
            f'assert(htdl::inspect(s,5,{broken},out) && out.size()==1 && out.get(0).code==401);'
            'assert(s.candidate().instance()==4 && s.candidate().source_size()==7 && s.abort(4));'))


if __name__ == '__main__':
    for name in list(vars(base.Evolution)):
        if name.startswith('test_'): delattr(base.Evolution,name)
    unittest.main(verbosity=2)
