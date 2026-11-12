"""Large debug allocations release payload pages and retain diagnostics."""
import ctypes
import importlib.util
import os
from pathlib import Path
import platform
import subprocess
import unittest

spec = importlib.util.spec_from_file_location('evolution', Path(__file__).with_name('test-evolution.py'))
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)


def resident_bytes(child):
    if os.name != 'nt':
        status = Path(f'/proc/{child.pid}/status').read_text()
        return int(next(line.split()[1] for line in status.splitlines() if line.startswith('VmRSS:'))) * 1024
    from ctypes import wintypes

    class Counters(ctypes.Structure):
        _fields_ = [('size', wintypes.DWORD), ('faults', wintypes.DWORD)] + [
            (name, ctypes.c_size_t) for name in (
                'peak_working', 'working', 'peak_paged', 'paged', 'peak_nonpaged',
                'nonpaged', 'pagefile', 'peak_pagefile')]

    query = ctypes.WinDLL('psapi').GetProcessMemoryInfo
    query.argtypes = [wintypes.HANDLE, ctypes.POINTER(Counters), wintypes.DWORD]
    query.restype = wintypes.BOOL
    result = Counters()
    result.size = ctypes.sizeof(result)
    if not query(int(child._handle), ctypes.byref(result), result.size):
        raise OSError('GetProcessMemoryInfo failed')
    return result.working


@unittest.skipUnless(platform.system() in ('Linux','Windows') and
                     platform.machine().lower() in ('amd64','x86_64'), 'native x64 RSS oracle')
class DebugLargeFree(base.Evolution):
    def test_resident_memory_with_two_thousand_frees(self):
        source = self.source('''safe fn main():int{
            own sync:*byte=alloc<byte>(1);
            print("START");assert(read_bytes(sync,1)==1);
            for(let round:int=0;round<2000;round++){
                own p:*byte=alloc<byte>(1048576);
                for(let i:int=0;i<len(p);i+=4096){p[i]=byte(23);}
            }
            print("DONE");assert(read_bytes(sync,1)==1);
            return 0;
        }''')
        binary = self.temp/'heap.exe'
        for options in ([], ['--no-opt']):
            built = self.invoke('build', source, '--debug', '-o', binary, *options)
            self.assertEqual(built.returncode, 0, built.stderr)
            child = subprocess.Popen([binary], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            try:
                self.assertEqual(child.stdout.readline(), b'START\n')
                before = resident_bytes(child)
                child.stdin.write(b'x')
                child.stdin.flush()
                self.assertEqual(child.stdout.readline(), b'DONE\n')
                after = resident_bytes(child)
                print(f'DEBUG_LARGE_FREE {options or ["optimized"]} RSS {before} -> {after}')
                self.assertLess(after-before, 48*1024*1024)
                out, error = child.communicate(b'x', timeout=10)
                self.assertEqual((child.returncode, out, error), (0, b'', b''))
            finally:
                if child.poll() is None:
                    child.kill()
                    child.communicate(timeout=10)

    def test_large_double_free_and_leak_diagnostics_are_preserved(self):
        for body, message in [
            ('free(p);free(p);', 'free duplo'),
            ('p[0]=byte(19);', 'alocacoes nao liberadas'),
        ]:
            source = self.source('fn main():int{let p:*byte=alloc<byte>(1048576);'+body+'return 0;}')
            for options in ([], ['--no-opt']):
                result = self.invoke('run', source, '--legacy', '--debug', *options)
                self.assertEqual(result.returncode, 70, result.stderr)
                self.assertIn(message, result.stderr)


if __name__ == '__main__':
    for name in list(vars(base.Evolution)):
        if name.startswith('test_'):
            delattr(base.Evolution, name)
    unittest.main(verbosity=2)
