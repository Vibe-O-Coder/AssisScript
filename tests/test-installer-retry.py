"""Real Windows file sharing locks, bounded failure and personal-file retention."""
import ctypes as C
from ctypes import wintypes as W
import os
from pathlib import Path
import subprocess
import tempfile
import threading
import time
import unittest

@unittest.skipUnless(os.name=='nt','Windows installer semantics require native Windows')
class InstallerRetry(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.setup=Path(os.environ['ASSIS_SETUP_BIN']).resolve()
        cls.kernel=C.WinDLL('kernel32',use_last_error=True)
        cls.kernel.CreateFileW.argtypes=[W.LPCWSTR,W.DWORD,W.DWORD,C.c_void_p,W.DWORD,W.DWORD,W.HANDLE]
        cls.kernel.CreateFileW.restype=W.HANDLE
        cls.kernel.CloseHandle.argtypes=[W.HANDLE];cls.kernel.CloseHandle.restype=W.BOOL
        cls.kernel.SetFileAttributesW.argtypes=[W.LPCWSTR,W.DWORD];cls.kernel.SetFileAttributesW.restype=W.BOOL
        cls.kernel.GetFileAttributesW.argtypes=[W.LPCWSTR];cls.kernel.GetFileAttributesW.restype=W.DWORD
    def setUp(self):
        self.directory=tempfile.TemporaryDirectory(prefix='assis-locked-uninstall-');self.addCleanup(self.directory.cleanup)
        self.prefix=Path(self.directory.name)/'prefix with spaces';(self.prefix/'bin').mkdir(parents=True)
        self.exe=self.prefix/'bin/assis.exe';self.exe.write_bytes(b'fixture, never executed')
        self.marker=self.prefix/'INSTALADO';self.marker.write_text('AssisScript test\n')
        self.personal=self.prefix/'personal.txt';self.personal.write_text('preserve')
    def remove(self):
        started=time.monotonic()
        result=subprocess.run([str(self.setup),'uninstall','--prefix',str(self.prefix),'--no-path','--no-associations'],capture_output=True,timeout=6)
        self.assertEqual(self.personal.read_text(),'preserve');return result,time.monotonic()-started
    def lock(self):
        handle=self.kernel.CreateFileW(str(self.exe),0x80000000,1,None,3,0,None)
        self.assertNotEqual(handle,C.c_void_p(-1).value,C.get_last_error());return handle
    def test_transient_sharing_lock_releases_and_uninstall_finishes(self):
        handle=self.lock();timer=threading.Timer(.25,lambda:self.kernel.CloseHandle(handle));timer.start()
        try:
            result,elapsed=self.remove();self.assertEqual(result.returncode,0,result.stderr)
            self.assertFalse(self.exe.exists());self.assertFalse(self.marker.exists())
        finally:timer.join()
    def test_persistent_lock_is_bounded_and_detected_before_other_managed_files(self):
        license=self.prefix/'LICENSE';license.write_text('managed fixture')
        handle=self.lock()
        try:
            result,elapsed=self.remove();self.assertNotEqual(result.returncode,0)
            self.assertGreaterEqual(elapsed,.9);self.assertLess(elapsed,5)
            self.assertTrue(self.exe.exists() and self.marker.exists() and license.exists())
        finally:self.kernel.CloseHandle(handle)
        result,_=self.remove();self.assertEqual(result.returncode,0,result.stderr)
    def test_readonly_file_is_not_forced_or_scheduled_for_deletion(self):
        self.assertTrue(self.kernel.SetFileAttributesW(str(self.exe),1))
        try:
            result,elapsed=self.remove();self.assertNotEqual(result.returncode,0)
            self.assertTrue(self.exe.exists() and self.marker.exists());self.assertEqual(self.kernel.GetFileAttributesW(str(self.exe))&1,1)
        finally:self.kernel.SetFileAttributesW(str(self.exe),0x80)
    def test_already_absent_managed_files_are_idempotent(self):
        self.exe.unlink();result,_=self.remove();self.assertEqual(result.returncode,0,result.stderr)
        self.assertFalse(self.marker.exists())

if __name__=='__main__':unittest.main(verbosity=2)
