"""Native confinement oracle and activation through the real Frame/worker."""
import ctypes as C
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import threading
import time
import unittest
import importlib.util

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('confined_frame', ROOT/'tests/test-frame-worker.py')
fw = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fw)
SUPPORTED = os.name == 'nt' or (os.uname().sysname == 'Linux' and os.uname().machine == 'x86_64')
MANIFEST = 'ASSIS-LOCAL/1\nhtdl 2 index.htdl\nfs 1 styles/main.fxs\nssc 1 main.sscr\nasv2 1 program.asv2\n'
IMPORT = 'import "std/localresources.assis";\n'


@unittest.skipUnless(SUPPORTED, 'native local resource provider unavailable')
class NativeConfinement(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.build = tempfile.TemporaryDirectory(prefix='assis-resource-provider-')
        cls.addClassCleanup(cls.build.cleanup)
        built = fw.pr.worker.builder.build(Path(cls.build.name), fw.base.COMPILER)
        cls.dll = C.CDLL(built['provider'])
        if os.name == 'nt':
            import _ctypes
            cls.addClassCleanup(_ctypes.FreeLibrary, cls.dll._handle)
        i64 = C.c_int64
        for name, args in {'version': [], 'open': [C.c_char_p, i64],
                           'read': [i64, C.c_char_p, i64, C.c_void_p, i64],
                           'close': [i64]}.items():
            func = getattr(cls.dll, 'assw_local_' + name)
            func.argtypes = args
            func.restype = i64

    def setUp(self):
        folder = tempfile.TemporaryDirectory(prefix='assis-root-')
        self.addCleanup(folder.cleanup)
        self.parent = Path(folder.name).resolve()
        self.root = self.parent / 'raízes com espaços'
        self.root.mkdir()
        self.outside = self.parent / 'vizinho'
        self.outside.mkdir()
        (self.root/'deep').mkdir()
        (self.root/'deep'/'asset').write_bytes(b'A\0B\xff')
        (self.outside/'asset').write_bytes(b'OUTSIDE')

    def grant(self, path):
        raw = os.fsencode(path)
        return self.dll.assw_local_open(raw, len(raw))

    def open(self, path=None):
        token = self.grant(self.root if path is None else path)
        self.assertGreater(token, 0)
        self.addCleanup(self.dll.assw_local_close, token)
        return token

    def read(self, token, key, cap=32):
        data = C.create_string_buffer(max(cap, 1))
        size = self.dll.assw_local_read(token, key, len(key), data, cap)
        return (size, data.raw[:size]) if size >= 0 else (size, b'')

    def link_directory(self, name, target):
        if os.name == 'nt':
            # Junction creation works on NTFS without enabling developer mode.
            env = dict(os.environ, ASSIS_TEST_JUNCTION=str(name), ASSIS_TEST_TARGET=str(target))
            subprocess.run(['powershell.exe', '-NoProfile', '-NonInteractive', '-Command',
                'New-Item -ItemType Junction -Path $env:ASSIS_TEST_JUNCTION -Target $env:ASSIS_TEST_TARGET -ErrorAction Stop | Out-Null'],
                env=env, check=True, capture_output=True)
        else:
            name.symlink_to(target, target_is_directory=True)

    def test_unicode_root_binary_zero_exact_size_and_limits(self):
        self.assertEqual(self.dll.assw_local_version(), 1)
        token = self.open()
        (self.root/'empty').touch()
        self.assertEqual(self.read(token, b'deep/asset', 4), (4, b'A\0B\xff'))
        self.assertEqual(self.read(token, b'deep/asset', 3), (-3, b''))
        self.assertEqual(self.read(token, b'deep/asset', 0), (-3, b''))
        self.assertEqual(self.read(token, b'empty', 0), (0, b''))
        self.assertEqual(self.read(token, b'deep'), (-6, b''))
        self.assertEqual(self.read(token, b'Deep/asset'), (-6, b''))
        self.assertEqual(self.read(token, b'deep/Asset'), (-6, b''))

    def test_authority_reparse_hardlinks_and_escape(self):
        token = self.open()
        self.link_directory(self.root/'redirect', self.outside)
        os.link(self.outside/'asset', self.root/'hard')
        self.assertLess(self.grant(self.root/'redirect'), 0)
        self.assertEqual(self.read(token, b'redirect/asset')[0], -6)
        self.assertEqual(self.read(token, b'hard')[0], -6)
        for key in [b'', b'/asset', b'deep/', b'deep//asset', b'deep/../asset', b'./asset',
                    b'../vizinho/asset', b'deep\\asset', b'deep/asset:stream', b'a\0b',
                    b'%2e%2e', b'deep/asset.', b'x'*256]:
            with self.subTest(key=key):
                self.assertEqual(self.read(token, key)[0], -1)

    @unittest.skipUnless(os.name == 'posix', 'Linux mount and FIFO checks')
    def test_mount_symlink_and_special_file_denied(self):
        (self.root/'redirect').symlink_to(self.outside/'asset')
        os.mkfifo(self.root/'pipe')
        token = self.open()
        for key in (b'redirect', b'pipe'):
            self.assertEqual(self.read(token, key)[0], -6)
        root = self.open(Path('/'))
        self.assertEqual(self.read(root, b'proc/version', 1024)[0], -6)

    def test_racing_directory_replacement_never_reads_outside(self):
        token = self.open()
        self.link_directory(self.root/'reparse', self.outside)
        safe = self.root/'deep'
        moved = self.root/'moving'
        redirect = self.root/'reparse'
        outcomes = []
        stop = threading.Event()
        swapped = threading.Event()
        observed = threading.Event()
        failures = []

        def rename(source, target):
            for attempt in range(250):
                try:
                    source.rename(target)
                    return
                except PermissionError:
                    if os.name != 'nt' or attempt == 249:
                        raise
                    time.sleep(0.001)

        def swap():
            try:
                for step in range(400):
                    if stop.is_set():
                        break
                    rename(safe, moved)
                    try:
                        rename(redirect, safe)
                        try:
                            if step == 0:
                                swapped.set()
                                observed.wait(5)
                        finally:
                            rename(safe, redirect)
                    finally:
                        rename(moved, safe)
            except OSError as error:
                failures.append(error)

        # A live reparse exists during the race, and the static test above
        # independently checks that following it would reach different bytes.
        mutation = threading.Thread(target=swap)
        mutation.start()
        try:
            self.assertTrue(swapped.wait(5))
            self.assertEqual(self.read(token, b'deep/asset'), (-6, b''))
            observed.set()
            for _ in range(400):
                outcomes.append(self.read(token, b'deep/asset'))
        finally:
            observed.set()
            stop.set()
            mutation.join(5)
        self.assertFalse(mutation.is_alive())
        self.assertEqual(failures, [])
        self.assertTrue(all(item in [(4, b'A\0B\xff'), (-6, b'')] for item in outcomes))
        self.assertEqual(self.read(token, b'deep/asset'), (4, b'A\0B\xff'))

    def test_grant_limit_wrong_thread_stale_tokens_and_reuse(self):
        tokens = [self.open() for _ in range(16)]
        self.assertEqual(self.grant(self.root), -3)
        self.assertEqual(self.dll.assw_local_close(tokens[0]), 0)
        replacement = self.open()
        self.assertNotEqual(replacement, tokens[0])
        self.assertEqual(self.read(tokens[0], b'deep/asset')[0], -2)
        wrong = []
        thread = threading.Thread(target=lambda: wrong.append(self.read(replacement, b'deep/asset')[0]))
        thread.start()
        thread.join()
        self.assertEqual(wrong, [-11])
        self.assertEqual(self.read(replacement, b'deep/asset'), (4, b'A\0B\xff'))


@unittest.skipUnless(SUPPORTED, 'native local resource provider unavailable')
class ConfinedFrame(unittest.TestCase):
    setUpClass = classmethod(fw.FrameWorker.setUpClass.__func__)
    tearDownClass = classmethod(fw.FrameWorker.tearDownClass.__func__)
    setUp = fw.FrameWorker.setUp
    binary = fw.FrameWorker.binary
    compile_page = classmethod(fw.FrameWorker.compile_page.__func__)
    execute = fw.FrameWorker.execute
    setup = fw.FrameWorker.setup
    prepare = fw.FrameWorker.prepare

    def fixture(self, name, manifest=MANIFEST, fs=b'', extra=b''):
        root = self.temp/name
        (root/'styles').mkdir(parents=True)
        (root/'resources.assr').write_bytes(manifest.encode('utf-8'))
        (root/'index.htdl').write_text(fw.document('<div type=button id=add>Confinado</div>'), encoding='utf-8')
        (root/'styles'/'main.fxs').write_bytes(fs)
        (root/'main.sscr').write_bytes(b'')
        (root/'program.asv2').write_bytes(self.code)
        (root/'payload').write_bytes(extra)
        return fw.literal(str(root.resolve()))

    def load(self, path, generation=1, maximum=262144, timeout=10000):
        return f'try_new localresources::Load({path},19,23,{generation},{maximum},monotonic_ms()+({timeout}))'

    def activate(self):
        return f's.prepare_bundle(move(batch),utf8(""),{fw.literal(str(self.worker))},false,128,3,true,320,220,65536,reader::default_preferences(),metric,limits,new frameworker::Grants(true,false),monotonic_ms())'

    def test_complete_manifest_activates_then_io_or_style_failure_preserves_frame(self):
        good = self.fixture('diretório', MANIFEST.replace('\n', '\r\n')+'data 1 payload', extra=b'A\0B')
        invalid = self.fixture('style', fs=b'bad style')
        missing = self.fixture('missing', MANIFEST.replace('main.sscr', 'missing.sscr'))
        code = self.setup() + 'drain(s,0);'
        code += f'{{own loader:localresources::Load={self.load(good)};assert(loader!=null && loader.status()==0);'
        code += ('assert(loader.advance()==0 && loader.index()==1);'
                 'assert(loader.advance()==0 && loader.advance()==0 && loader.advance()==0);'
                 'assert(loader.advance()==1 && loader.advance()==1 && loader.index()==5);'
                 'own batch:pageresources::Batch=loader.take();assert(loader.advance()== -9);'
                 'assert(batch.content(4)[1]==0 && len(batch.content(4))==3);')
        code += f'assert({self.activate()}==0);ready(s);assert(s.commit());drain(s,0);}}'
        code += ('val doc:int=s.document_id();val snapshot:int=s.snapshot().frame.version();'
                 'assert(doc==2 && s.has_resources());')
        code += f'{{own loader:localresources::Load={self.load(missing,2)};assert(loader!=null && loader.status()==0);'
        code += ('assert(loader.advance()==0 && loader.advance()==0 && loader.advance()== -6);'
                 'assert(loader.index()==2 && loader.advance()== -6 && s.worker_alive());}')
        code += f'{{own loader:localresources::Load={self.load(invalid,3)};assert(loader!=null && loader.status()==0);'
        code += ('assert(loader.advance()==0 && loader.advance()==0 && loader.advance()==0 && loader.advance()==1);'
                 'own batch:pageresources::Batch=loader.take();')
        code += f'assert({self.activate()}!=0 && !s.has_pending());}}'
        code += 'assert(s.document_id()==doc && s.snapshot().frame.version()==snapshot && s.has_resources());drain(s,0);'
        self.execute(code, IMPORT)

    def test_bad_manifest_cancellation_quota_and_deadline(self):
        valid = self.fixture('valid')
        cases = [
            (MANIFEST.replace('ASSIS-LOCAL/1', 'ASSIS-LOCAL/2'), -16, 1),
            (MANIFEST.replace('htdl 2', 'htdl 3'), -16, 2),
            (MANIFEST.replace('index.htdl', '../index.htdl'), -1, 2),
            (MANIFEST.replace('index.htdl', 'a/../index.htdl'), -1, 2),
            (MANIFEST + 'htdl 2 index.htdl\n', -1, 6),
            (MANIFEST + 'source 1 main.assis\n', -16, 6),
            (MANIFEST + 'data 1 NUL.txt\n', -1, 6),
        ]
        code = ''
        for i, (manifest, error, line) in enumerate(cases):
            path = self.fixture(f'bad-{i}', manifest)
            code += f'{{own load:localresources::Load={self.load(path)};assert(load!=null);assert(load.advance()== {error} && load.line()=={line});}}'
        code += f'{{own load:localresources::Load={self.load(valid, maximum=0)};assert(load!=null);assert(load.advance()== -3);}}'
        code += f'{{own load:localresources::Load={self.load(valid, timeout=0)};assert(load!=null);assert(load.advance()== -8);}}'
        code += f'{{own load:localresources::Load={self.load(valid)};assert(load!=null);assert(load.advance()==0);load.cancel();assert(load.advance()== -9);}}'
        # More than 16 consecutive preparations/drops prove the grant slots
        # are returned even if the caller abandons an unfinished load.
        code += f'for(let i:int=0;i<20;i++){{own load:localresources::Load={self.load(valid)};assert(load!=null && load.status()==0);}}'
        self.execute(code, IMPORT)

    def test_example_runs_from_a_copied_root_in_both_modes(self):
        root = self.temp/'demo com acentos'
        shutil.copytree(ROOT/'exemplos/resource-demo', root)
        binary = self.temp/('confined.exe' if os.name == 'nt' else 'confined')
        for flags in ([], ['--no-opt']):
            build = subprocess.run([fw.base.COMPILER, 'build', ROOT/'exemplos/69_confined_resource_frame.assis',
                                    '--safe', '--debug', '-o', binary, *flags], cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(build.returncode, 0, build.stderr)
            run = subprocess.run([binary, fw.base.COMPILER, self.worker, root], env=self.env, cwd=self.temp,
                                 capture_output=True, text=True, timeout=30)
            self.assertEqual((run.returncode, run.stdout, run.stderr), (0, 'CONFINED FRAME 4 0 1\n', ''))


if __name__ == '__main__':
    unittest.main(verbosity=2)
