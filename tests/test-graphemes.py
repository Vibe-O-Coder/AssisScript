"""Official UAX #29 corpus, adversarial UTF-8 and integrated reader behavior."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import unittest

def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result

reader = module('grapheme_reader', Path(__file__).with_name('test-htdl-reader.py'))
base = reader.base
DATA = base.ROOT / 'tests/fixtures/unicode-17.0.0'
PREFIX = 'import "std/graphemes.assis";\n'

def cases():
    result = []
    for number, line in enumerate((DATA / 'GraphemeBreakTest.txt').read_text(encoding='utf-8').splitlines(), 1):
        tokens = line.split('#')[0].split()
        if not tokens:
            continue
        data = bytearray()
        boundaries = []
        for token in tokens:
            if token == '÷':
                boundaries.append(len(data))
            elif token != '×':
                data.extend(chr(int(token, 16)).encode())
        result.append((number, bytes(data), boundaries))
    return result

class Graphemes(base.Evolution):
    def invoke(self, *args, **kwargs):
        if args and args[0] in ('check', 'build', 'run', 'ir'):
            args = (*args, '--safe')
        return super().invoke(*args, **kwargs)

    def test_pinned_provenance_and_reproducible_properties(self):
        provenance = json.loads((DATA / 'PROVENANCE.json').read_text())
        for item in provenance['files']:
            self.assertEqual(hashlib.sha256((DATA / item['path']).read_bytes()).hexdigest(), item['sha256'])
        run = subprocess.run([os.sys.executable, base.ROOT / 'tools/generate-grapheme-data.py', '--check'], capture_output=True)
        self.assertEqual(run.returncode, 0, run.stderr)

    def test_all_official_extended_grapheme_cases_both_modes(self):
        # Corpus markers are the oracle; no property lookup/rule model is shared.
        corpus = cases()
        self.assertEqual(len(corpus), 766)
        for offset in range(0, len(corpus), 64):
            body = PREFIX + 'safe fn main():int{'
            for number, data, boundaries in corpus[offset:offset + 64]:
                body += '{own data:*byte=try_alloc<byte>(' + str(len(data)) + ');assert(data!=null);'
                body += ''.join(f'data[{i}]=byte({b});' for i, b in enumerate(data))
                body += 'own index:graphemes::Index=try_new graphemes::Index(slice_of(data,0,len(data)));'
                body += f'assert(index!=null && index.status()==0 && index.count()=={len(boundaries)-1});'
                body += ''.join(f'assert(index.boundary({i})=={str(i in boundaries).lower()});' for i in range(len(data) + 1))
                for a, b in zip(boundaries, boundaries[1:]):
                    body += f'assert(index.next({a})=={b} && index.previous({b})=={a});'
                body += f'print({number});}}'
            body += 'return 0;}'
            self.accepted(body, ''.join(str(n) + '\n' for n, _, _ in corpus[offset:offset + 64]))

    def test_invalid_utf8_offsets_empty_nul_limit_and_cursor_reset(self):
        body = PREFIX + 'safe fn main():int{'
        for data in ([128], [192, 128], [237, 160, 128], [244, 144, 128, 128], [240, 159]):
            body += '{own b:*byte=try_alloc<byte>(' + str(len(data)) + ');'
            body += ''.join(f'b[{i}]=byte({v});' for i, v in enumerate(data))
            body += 'own x:graphemes::Index=try_new graphemes::Index(slice_of(b,0,len(b)));assert(x.status()== -1 && !x.boundary(0));}'
        body += ('own empty:graphemes::Index=try_new graphemes::Index(utf8(""));'
                 'assert(empty.status()==0 && empty.count()==0 && empty.next(0)==0 && empty.previous(0)==0);'
                 'assert(empty.next(-1)== -1 && empty.previous(1)== -1);'
                 'own huge:*byte=try_alloc<byte>(1048577);'
                 'own limit:graphemes::Index=try_new graphemes::Index(slice_of(huge,0,len(huge)));assert(limit.status()== -1);'
                 'own c:graphemes::Cursor=try_new graphemes::Cursor();'
                 'assert(c.push(65)==1 && c.push(-1)== -1 && c.push(55296)== -1 && c.push(1114112)== -1);'
                 'assert(c.push(769)==0);c.reset();assert(c.push(769)==1);return 0;}')
        self.accepted(body)

    def test_long_regional_emoji_and_indic_context_is_linear_and_bounded(self):
        self.accepted(PREFIX + 'safe fn main():int{'
            'own c:graphemes::Cursor=try_new graphemes::Cursor();'
            'for(let i:int=0;i<20000;i++){assert(c.push(127462)==int(i%2==0));}'
            'c.reset();assert(c.push(128105)==1);'
            'for(let i:int=0;i<20000;i++){assert(c.push(769)==0);}'
            'assert(c.push(8205)==0 && c.push(128187)==0);'
            'c.reset();assert(c.push(2325)==1 && c.push(2381)==0);'
            'for(let i:int=0;i<20000;i++){assert(c.push(769)==0);}'
            'assert(c.push(2325)==0);return 0;}')

class Integrated(reader.HtdlReader):
    def test_narrow_wrap_keeps_combining_marks_with_their_base(self):
        self.execute(reader.setup('<div type=paragraph>abcafe\u0301</div>',width=96)+
            'for(let i:int=0;i<r.snapshot().line_count();i++){print(r.snapshot().line_text(i));}',
            'abc\naf\ne\u0301\n')

    def test_trailing_space_inside_prepend_cluster_is_never_trimmed(self):
        self.execute(reader.setup('<div type=paragraph>aa\u0600 bb</div>',width=104)+
            'own index:graphemes::Index=try_new graphemes::Index(r.snapshot().text_bytes());'
            'for(let i:int=0;i<r.snapshot().line_count();i++){val line:viewer::Line=r.snapshot().line(i);'
            'assert(index.boundary(line.start) && index.boundary(line.start+line.size));print(r.snapshot().line_text(i));}',
            'aa\u0600 \nbb\n')

    def test_grapheme_keyboard_pointer_wrap_and_reflow(self):
        text = 'Ae\u0301👩\u200d💻🇧🇷Z'
        boundaries = [0, 1, 4, 15, 23, 24, 25]
        body = reader.setup('<div type=paragraph>' + text + '</div>', width=240)
        for i in range(26):
            body += f'assert(r.select({i},0)=={str(i in boundaries).lower()});'
        body += 'assert(r.select(1,1));r.dispatch(1,event(3,16,1,1));'
        for request, end in enumerate(boundaries[2:], 2):
            body += f'r.dispatch(1,event(3,39,1,{request}));assert(r.selection_end()=={end});'
        body += 'assert(r.select(1,4));'
        body += ('own index:graphemes::Index=try_new graphemes::Index(r.snapshot().text_bytes());'
                 'for(let i:int=0;i<r.snapshot().line_count();i++){val line:viewer::Line=r.snapshot().line(i);'
                 'assert(index.boundary(line.start) && index.boundary(line.start+line.size));}')
        body += ('own next:reader::Reader=try_new reader::Reader(store.active_document(),7,120,160,16,cells);'
                 'assert(next.is_open());next.restore(r);print(next.selected_text());')
        self.execute(body, 'e\u0301\n')

    def test_oversized_cluster_refusal_preserves_transaction_and_neighbor(self):
        self.execute('own s:reader::Session=try_new reader::Session(32000000,250000,7);'
            'assert(s.prepare(1,' + reader.viewer.parser.literal(reader.viewer.parser.document('<div type=paragraph>Keep</div>')) + ',240,160,16,cells)==0 && s.commit());'
            'assert(s.prepare(2,' + reader.viewer.parser.literal(reader.viewer.parser.document('<div type=paragraph>👩\u200d❤️\u200d💋\u200d👨</div>')) + ',96,160,16,cells)!=0);'
            'assert(s.has_active() && !s.has_pending() && s.document().instance()==1);'
            'print(s.active_reader().item_name(0));', 'Keep\n')

    def test_oom_in_boundary_index_is_recoverable(self):
        warm, drain, cleanup = reader.viewer.parser.preparation.exhaustion()
        code = PREFIX + 'safe fn main():int{unsafe{' + warm + drain
        code += 'own index:graphemes::Index=try_new graphemes::Index(utf8("café"));assert(index==null || index.status()!=0);'
        code += cleanup + '}return 0;}'
        reader.viewer.HtdlViewer.fault_program(self, code, '')

if __name__ == '__main__':
    for name in list(vars(reader.HtdlReader)):
        if name.startswith('test_'):
            delattr(reader.HtdlReader, name)
    for name in list(vars(base.Evolution)):
        if name.startswith('test_'):
            delattr(base.Evolution, name)
    unittest.main(verbosity=2)
