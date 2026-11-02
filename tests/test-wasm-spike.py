"""Measured Wasm alternative: trusted fixtures, NOT a restricted Wasm loader."""
import base64
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent.parent
NODE = shutil.which('node')

def unsigned(value):
    output = bytearray()
    while value >= 128:
        output.append((value & 127) | 128)
        value >>= 7
    output.append(value)
    return bytes(output)

def signed(value):
    output = bytearray()
    while True:
        byte = value & 127
        value >>= 7
        done = (value == 0 and byte < 64) or (value == -1 and byte >= 64)
        output.append(byte if done else byte | 128)
        if done:return bytes(output)

def section(kind, body):
    return bytes([kind]) + unsigned(len(body)) + body

def string(value):
    data = value.encode()
    return unsigned(len(data)) + data

def wasm(code, import_module='counter', import_name='add_v1', memory=False):
    types = b'\x02\x60\x01\x7e\x01\x7e\x60\x00\x01\x7e'
    imports = b'\x01' + string(import_module) + string(import_name) + b'\x00\x00'
    exports = unsigned(2 if memory else 1) + string('run') + b'\x00\x01'
    if memory:exports += string('memory') + b'\x02\x00'
    body = b'\x00' + code + b'\x0b'
    return (b'\0asm\x01\0\0\0' + section(1, types) + section(2, imports) + section(3, b'\x01\x01') +
        (section(5,b'\x01\x01\x01\x01') if memory else b'') + section(7, exports) + section(10,b'\x01'+unsigned(len(body))+body))

class WasmSpike(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not NODE:raise unittest.SkipTest('Node/V8 unavailable; no Wasm execution')
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='assis-wasm-spike-')
        self.addCleanup(self.temp.cleanup)
    def execute(self, data, grant=True, calls=10, timeout=5):
        request=Path(self.temp.name)/'request.json'
        request.write_text(json.dumps(dict(module=base64.b64encode(data).decode(),grant=grant,maxCalls=calls)))
        result=subprocess.run([NODE,ROOT/'tools/pagevm-wasm-spike.js',request],capture_output=True,text=True,timeout=timeout)
        self.assertEqual((result.returncode,result.stderr),(0,''))
        return json.loads(result.stdout)
    def test_i64_semantics_effects_and_boolean_control_against_native_values(self):
        # i64.const 6, i64.const 7, mul, host counter -> 42, as in the VM call test.
        code=b'\x42'+signed(6)+b'\x42'+signed(7)+b'\x7e\x10\x00'
        run=self.execute(wasm(code))
        self.assertEqual((run['status'],run['result'],run['counter'],run['calls']),('halted','42','42',1))
        # Signed overflow and division; i64 minimum / -1 traps in Wasm.
        run=self.execute(wasm(b'\x42'+signed(2**63-1)+b'\x42\x01\x7c'))
        self.assertEqual(run['result'],str(-2**63))
        run=self.execute(wasm(b'\x42'+signed(-2**63)+b'\x42'+signed(-1)+b'\x7f'))
        self.assertEqual(run['status'],'rejected')
        run=self.execute(wasm(b'\x41\x01\x04\x7e\x42\x2a\x05\x42\x00\x0b'))
        self.assertEqual(run['result'],'42')
    def test_malformed_and_import_default_deny(self):
        self.assertEqual(self.execute(b'bad')['status'],'rejected')
        for name in ('file_open','network','process','ffi','clock'):
            self.assertEqual(self.execute(wasm(b'\x42\x00',import_name=name))['error'],'denied_import')
        self.assertEqual(self.execute(wasm(b'\x42\x01\x10\x00'),grant=False)['error'],'denied_capability')
    def test_host_quota_and_fixed_memory_fixture(self):
        self.assertEqual(self.execute(wasm(b'\x42\x01\x10\x00'),calls=0)['error'],'host_quota')
        run=self.execute(wasm(b'\x41\x01\x40\x00\xac',memory=True))
        self.assertEqual((run['result'],run['growth']),('-1',1))
    def test_infinite_loop_requires_process_termination_no_instruction_fuel(self):
        # This is an observed deficiency, not a pass for page CPU confinement.
        with self.assertRaises(subprocess.TimeoutExpired):
            self.execute(wasm(b'\x03\x40\x0c\x00\x0b\x42\x00'),timeout=0.5)

if __name__=='__main__':unittest.main(verbosity=2)
