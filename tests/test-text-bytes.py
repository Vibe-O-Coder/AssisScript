"""Explicit buffer lengths and strict UTF-8 against Python's independent decoder."""
import importlib.util
from pathlib import Path
import random
import unittest

spec = importlib.util.spec_from_file_location('evolution', Path(__file__).with_name('test-evolution.py'))
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)


class TextBytes(base.Evolution):
    def test_utf8_matches_independent_decoder(self):
        rng = random.Random(3327)
        samples = [b'', b'\x00', 'á日本😀'.encode(), bytes(range(256)), b'\xc0\x80',
                   b'\xed\xa0\x80', b'\xf4\x90\x80\x80', b'\xf0\x90\x80', b'\x80',
                   b'\xef\xbf\xbf', b'\xf4\x8f\xbf\xbf', b'ASCII\x00binary']
        samples += [bytes(rng.randrange(256) for _ in range(rng.randrange(1, 8))) for _ in range(100)]
        samples += [chr(rng.choice([0, 127, 128, 2047, 2048, 55295, 57344, 65535, 65536, 1114111])).encode() for _ in range(30)]
        blocks, expected = [], []
        for data in samples:
            try:
                count = len(data.decode('utf-8', errors='strict'))
            except UnicodeDecodeError:
                count = -1
            blocks.append('{own b:*byte=alloc<byte>(%d);%sprint(utf8_contar(b,%d));}' %
                          (len(data), ''.join(f'b[{i}]=byte({b});' for i, b in enumerate(data)), len(data)))
            expected.append(str(count))
        self.accepted('#yuri <std/texto.assis>\n' + base.main(''.join(blocks)), '\n'.join(expected) + '\n')

    def test_length_is_element_count_through_fields_and_borrowed_returns(self):
        code = 'value struct P{let x:int;let y:int;}struct C{own b:*P;}'
        code += 'safe assis ver(borrow c:C):borrow(c) *P{return c.b;}'
        self.accepted(code + base.main('own c:C=new C(alloc<P>(7));print(len(c.b),len(ver(c)));own z:*int=alloc<int>(0);print(len(z));'), '7 7\n0\n')
        self.rejected(base.main('let p:*byte=alloc<byte>(3);print(len(p));free(p);'), 'exige own/borrow')

    def test_explicit_length_failure_and_nul_codepoint(self):
        self.accepted('#yuri <std/texto.assis>\n' + base.main('own b:*byte=alloc<byte>(1);b[0]=byte(0);'
                      'val p:Utf8Passo=utf8_proximo(b,1,0);print(p.valido,p.ponto,p.proximo,utf8_contar(b,2),utf8_contar(b,-1));'),
                      'aSsIs 0 1 -1 -1\n')

    def test_decimal_buffer_matches_python_including_int64_min(self):
        numbers = [0, 1, -1, 9223372036854775807, -9223372036854775808, 123456789, -123456789]
        blocks = []
        for n in numbers:
            digits = str(n)
            checks = ''.join(f'assert(b[{i}]=={ord(char)});' for i, char in enumerate(digits))
            blocks.append(f'{{own b:*byte=alloc<byte>(20);assert(formatar_int_buffer({n},b)=={len(digits)});{checks}}}')
        self.accepted('#yuri <std/conversoes.assis>\n' + base.main(''.join(blocks) + 'own curto:*byte=alloc<byte>(19);print(formatar_int_buffer(0,curto));'), '-1\n')


if __name__ == '__main__':
    suite = unittest.TestSuite(TextBytes(name) for name in TextBytes.__dict__ if name.startswith('test_'))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    print(f'ASSIS text bytes: {base.INVOCATIONS} invocações; {base.COMPILER}')
    raise SystemExit(not result.wasSuccessful())
