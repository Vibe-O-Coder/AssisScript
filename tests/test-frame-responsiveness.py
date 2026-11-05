"""Independent Win32 metric and event oracles for the reported input backlog."""
import ctypes as C
import importlib.util
import os
from pathlib import Path
import tempfile
import threading
import time
import unittest

ROOT=Path(__file__).resolve().parent.parent

@unittest.skipUnless(os.name=='nt','Windows native graphics provider unavailable')
class FrameResponsiveness(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.folder=tempfile.TemporaryDirectory(prefix='assis-frame-response-');out=Path(cls.folder.name)
        spec=importlib.util.spec_from_file_location('response_provider',ROOT/'tools/build-platform.py')
        builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder)
        builder.build(out/'assis_platform_v1.dll',testing=True)
        cls.dll=C.CDLL(str(out/'assis_platform_v1.dll'));cls.instance=100
        i64=C.c_int64;i32=C.c_int32;ptr=C.POINTER(i64)
        signatures={'open':(i32,[i64,i32,i32,C.c_char_p,i64,ptr]),'close':(i32,[i64]),
            'test_control':(i64,[i64,i64]),'poll':(i32,[i64,i32,ptr,i64]),'preferences':(i32,[i64,ptr,i64]),
            'frame_measure':(i64,[C.c_char_p,i64,i32,i32]),'frame_clock':(i64,[])}
        for name,(result,args) in signatures.items():
            fn=getattr(cls.dll,'assisp_'+name);fn.restype=result;fn.argtypes=args
        cls.user=C.WinDLL('user32');cls.user.SendMessageW.restype=C.c_ssize_t
        cls.user.SendMessageW.argtypes=[C.c_void_p,C.c_uint,C.c_size_t,C.c_ssize_t]

    @classmethod
    def tearDownClass(cls):
        import _ctypes
        _ctypes.FreeLibrary(cls.dll._handle);cls.folder.cleanup()

    def setUp(self):
        self.assertEqual(self.dll.assisp_test_control(0,-1),0)

    def test_exact_metric_cache_matches_uncached_font_oracle_and_failures(self):
        values=[(b'',16,400),(b'W',16,400),(b'i',16,400),(b'Wide',24,700),('Ação café'.encode(),16,400),(b'A\0B',16,400),(b'a'*256,16,400),(b'a'*257,16,400)]
        oracle=[]
        for text,size,weight in values:
            self.dll.assisp_test_control(0,-1)
            value=self.dll.assisp_frame_measure(text,len(text),size,weight);self.assertGreater(value,0)
            oracle.append(value)
        self.dll.assisp_test_control(0,-1)
        for _ in range(3):
            for (text,size,weight),expected in zip(values,oracle):
                self.assertEqual(self.dll.assisp_frame_measure(text,len(text),size,weight),expected)
        self.assertEqual(self.dll.assisp_test_control(10,0),14) # Seven cacheable keys, twice warm.
        self.assertEqual(self.dll.assisp_test_control(11,0),10)
        self.assertEqual(self.dll.assisp_frame_measure(b'\xff',1,16,400),-1)
        self.assertEqual(self.dll.assisp_frame_measure(None,1,16,400),-1)
        self.assertEqual(self.dll.assisp_frame_measure(b'x',-1,16,400),-1)
        self.assertEqual(self.dll.assisp_frame_measure(b'x',1,0,400),-1)
        self.dll.assisp_test_control(0,0)
        self.assertEqual(self.dll.assisp_frame_measure(b'W',1,16,400),-4)
        self.dll.assisp_test_control(0,-1)
        self.assertEqual(self.dll.assisp_frame_measure(b'W',1,16,400),oracle[1])

    def test_bounded_eviction_uses_exact_text_length_size_and_weight(self):
        for i in range(600):
            text=f'metric-{i}'.encode();self.assertGreater(self.dll.assisp_frame_measure(text,len(text),16,400),0)
        self.assertEqual(self.dll.assisp_test_control(11,0),600)
        self.assertGreater(self.dll.assisp_frame_measure(b'metric-0',8,16,400),0)
        self.assertEqual(self.dll.assisp_test_control(11,0),601)
        for size,weight in [(24,400),(16,700),(24,700)]:
            self.assertGreater(self.dll.assisp_frame_measure(b'metric-0',8,size,weight),0)
        self.assertEqual(self.dll.assisp_test_control(11,0),604)

    def open(self):
        type(self).instance+=1;token=C.c_int64()
        self.assertEqual(self.dll.assisp_open(self.instance,160,100,b'Response oracle',15,C.byref(token)),0)
        self.addCleanup(self.dll.assisp_close,token.value)
        return token.value,self.dll.assisp_test_control(4,token.value)

    def events(self,token):
        words=(C.c_int64*10)();result=[]
        while True:
            status=self.dll.assisp_poll(token,0,words,10)
            if status==1:return result
            self.assertEqual(status,0);result.append(tuple(words[:8]))

    def test_resize_burst_coalesces_without_redundant_visibility_or_lost_keys(self):
        token,hwnd=self.open();self.events(token);words=(C.c_int64*10)()
        self.assertEqual(self.dll.assisp_preferences(token,words,10),0)
        for width in range(161,190):self.user.SendMessageW(hwnd,0x5,0,(100<<16)|width)
        events=self.events(token)
        self.assertEqual([(e[1],e[5],e[6]) for e in events],[(13,1,0),(2,189,100)])
        self.user.SendMessageW(hwnd,0x5,0,(100<<16)|200)
        self.user.SendMessageW(hwnd,0x100,9,0)
        self.user.SendMessageW(hwnd,0x5,0,(100<<16)|210)
        events=self.events(token)
        self.assertEqual([(e[1],e[5]) for e in events],[(2,200),(3,9),(2,210)])
        self.assertEqual(sorted(e[7] for e in events),[e[7] for e in events])
        for _ in range(10):self.user.SendMessageW(hwnd,0x5,1,0)
        self.assertEqual([(e[1],e[5]) for e in self.events(token)],[(13,0)])
        self.user.SendMessageW(hwnd,0x5,0,(100<<16)|210)
        self.assertEqual([(e[1],e[5]) for e in self.events(token)],[(13,1),(2,210)])

    def test_theme_dpi_and_last_window_close_invalidate_private_metrics(self):
        token,hwnd=self.open()
        for message in [0x1a,0x15,0x31a,0x1d,0x2e0]:
            self.assertGreater(self.dll.assisp_frame_measure(b'private',7,16,400),0)
            self.assertGreater(self.dll.assisp_frame_measure(b'private',7,16,400),0)
            self.assertGreater(self.dll.assisp_test_control(10,0),0)
            self.user.SendMessageW(hwnd,message,96<<16,0)
            self.assertEqual(self.dll.assisp_test_control(10,0),0)
            self.assertEqual(self.dll.assisp_test_control(11,0),0)
        self.assertGreater(self.dll.assisp_frame_measure(b'private',7,16,400),0)
        self.assertEqual(self.dll.assisp_close(token),0)
        self.assertEqual(self.dll.assisp_test_control(11,0),0)

    def test_animation_clock_matches_independent_elapsed_time_and_owner_thread(self):
        start=time.perf_counter();a=self.dll.assisp_frame_clock();time.sleep(0.025)
        b=self.dll.assisp_frame_clock();elapsed=(time.perf_counter()-start)*1000
        self.assertGreaterEqual(a,0);self.assertGreaterEqual(b-a,20)
        self.assertLess(abs((b-a)-elapsed),10)
        values=[self.dll.assisp_frame_clock() for _ in range(100)]
        self.assertEqual(values,sorted(values))
        wrong=[];thread=threading.Thread(target=lambda:wrong.append(self.dll.assisp_frame_clock()));thread.start();thread.join()
        self.assertEqual(wrong,[-5])

if __name__=='__main__':unittest.main(verbosity=2)
