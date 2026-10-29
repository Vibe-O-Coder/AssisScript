"""Native nested-div microformat probe; no HTDL/browser conformance claim."""
import importlib.util
import json
from pathlib import Path
import random
import subprocess
import unittest

spec = importlib.util.spec_from_file_location('evolution', Path(__file__).with_name('test-evolution.py'))
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
FIXTURE = base.ROOT / 'tests/fixtures/htdl-core.assis'


class HtdlReadiness(base.Evolution):
    def invoke(self, *args, **kwargs):
        if args and args[0] in ('check', 'build', 'run', 'ir'):
            args = (*args, '--safe')
        return super().invoke(*args, **kwargs)

    def programs(self):
        for flags in [[], ['--no-opt']]:
            binary = self.temp / ('core-reference.exe' if flags else 'core.exe')
            result = self.invoke('build', FIXTURE, '--debug', '-o', binary, *flags)
            self.assertEqual(result.returncode, 0, result.stderr)
            yield binary

    def verify(self, binary, document, status, output):
        result = subprocess.run([str(binary)], input=document, capture_output=True, timeout=20)
        self.assertEqual((result.returncode, result.stdout, result.stderr), (status, output, b''))

    def test_tree_utf8_and_exact_index_even_when_all_hashes_collide(self):
        for binary in self.programs():
            self.verify(binary, '<div>Assis htdl assis<div>HTDL ç</div></div>'.encode(),
                        0, b'2 3 2 2\n-1 0 true\n')
            self.verify(binary, b'<div>A\x00htdl</div>', 0, b'1 2 0 1\n-1 -1 true\n')
            self.verify(binary, b'', 0, b'0 0 0 0\n')

    def test_large_tree_and_iterative_deep_nesting(self):
        for binary in self.programs():
            self.verify(binary, b'<div>assis</div>' * 5000, 0, b'5000 1 5000 0\n-1 -1 true\n')
            self.verify(binary, b'<div>' * 4096 + b'htdl' + b'</div>' * 4096,
                        0, b'4096 1 0 1\n-1 4094 true\n')

    def test_recoverable_errors_and_explicit_budgets(self):
        for binary in self.programs():
            for document, error in [(b'<div>', 4), (b'</div>', 4), (b'<bad>', 3),
                                    (b'<di', 3), (b'<div>\xff</div>', 2),
                                    (b'<div>' * 4097, 1), (b'<div></div>' * 20001, 1),
                                    (b'x' * 1048577, 1)]:
                with self.subTest(bytes=len(document), error=error):
                    self.verify(binary, document, 1, f'ERR {error}\n'.encode())

    def test_index_results_against_independent_generated_inputs(self):
        rng = random.Random(20261029)
        cases = []
        for _ in range(32):
            words = [rng.choice(['assis', 'HTDL', 'other', 'Assis', 'htdl']) for _ in range(rng.randrange(1, 50))]
            document = ('<div>' + ' '.join(words) + '</div>').encode()
            normalized = [word.lower() for word in words]
            output = f'1 {len(set(normalized))} {normalized.count("assis")} {normalized.count("htdl")}\n-1 -1 true\n'.encode()
            cases.append((document, output))
        for binary in self.programs():
            for document, output in cases:
                self.verify(binary, document, 0, output)

    def test_exact_byte_node_depth_limits_and_unsupported_syntax(self):
        for binary in self.programs():
            self.verify(binary, b'x' * 1048576, 0, b'0 1 0 0\n')
            self.verify(binary, b'<div></div>' * 20000, 0, b'20000 0 0 0\n-1 -1 true\n')
            self.verify(binary, b'<div>' * 4096 + b'</div>' * 4096, 0, b'4096 0 0 0\n-1 4094 true\n')
            for document in [b'<div type="text">x</div>', b'<!-- comment -->', b'<div/>',
                             b'<DIV></DIV>', b'<div>\xc0\x80</div>', b'<div>\xed\xa0\x80</div>']:
                error = 2 if b'\xc0' in document or b'\xed' in document else 3
                self.verify(binary, document, 1, f'ERR {error}\n'.encode())

    def test_generated_tree_shapes_against_construction_oracle(self):
        rng = random.Random(20261031)
        cases = []
        for _ in range(40):
            nodes, words = [], []

            def tree(parent, depth):
                index = len(nodes)
                nodes.append(parent)
                word = rng.choice(['assis', 'HTDL', 'Assis', 'other'])
                words.append(word.lower())
                children = rng.randrange(4) if depth < 4 else 0
                return '<div>' + word + ' ' + ''.join(tree(index, depth + 1) for _ in range(children)) + '</div>'

            document = ''.join(tree(-1, 0) for _ in range(rng.randrange(1, 5))).encode()
            output = (f'{len(nodes)} {len(set(words))} {words.count("assis")} {words.count("htdl")}\n'
                      f'-1 {nodes[-1]} true\n').encode()
            cases.append((document, output))
        for binary in self.programs():
            for document, output in cases:
                self.verify(binary, document, 0, output)

    def test_safe_native_code_has_file_access_and_no_intrinsic_cpu_budget(self):
        # Only a test-owned file is touched. This demonstrates why safe native
        # code cannot be used as an isolation boundary for downloaded scripts.
        marker = self.temp / 'capability-marker.bin'
        path = json.dumps(marker.as_posix())
        source = ('safe fn main():int{own data:*byte=alloc<byte>(1);data[0]=byte(42);'
                  'own f:File=file_open(' + path + ',1);assert(f!=null);'
                  'assert(file_write(f,data,1)==1);assert(file_close(f)==0);return 0;}')
        self.accepted(source)
        self.assertEqual(marker.read_bytes(), b'*')
        result = self.invoke('check', self.source('safe fn main():int{while(true){}return 0;}'))
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_all_output_targets_compile_the_core(self):
        for target in ['windows-x64', 'linux-x64', 'macos-x64', 'linux-arm64', 'macos-arm64']:
            for flags in [[], ['--no-opt']]:
                binary = self.temp / (target + ('-reference' if flags else '') + '.exe')
                result = self.invoke('build', FIXTURE, '--target', target, '-o', binary, *flags)
                self.assertEqual(result.returncode, 0, (target, flags, result.stderr))


if __name__ == '__main__':
    for name in list(vars(base.Evolution)):
        if name.startswith('test_'):
            delattr(base.Evolution, name)
    unittest.main(verbosity=2)
