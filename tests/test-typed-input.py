"""Run the typed readers and converters in both native emitter modes."""

from decimal import Decimal, localcontext
from fractions import Fraction
from pathlib import Path
import math
import os
import random
import struct
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SUFFIX = '.exe' if os.name == 'nt' else ''
COMPILER = Path(os.environ.get('ASSIS_BIN', ROOT / 'bin' / ('assis' + SUFFIX)))


def binary32(spelling):
    """Round the exact rational to binary32 without a binary64 intermediate."""
    value = Fraction(spelling)
    negative = spelling.startswith('-')
    value = abs(value)
    if value == 0:
        return -0.0 if negative else 0.0
    exp = value.numerator.bit_length() - value.denominator.bit_length()
    if value < Fraction(2) ** exp:
        exp -= 1
    shift = max(exp, -126) - 23
    rounded = round(value / (Fraction(2) ** shift))
    if exp > 127 or (rounded >= 1 << 24 and shift == 104):
        return math.inf
    result = math.ldexp(rounded, shift)
    return -result if negative else result


class TypedInput(unittest.TestCase):
    def run_program(self, body, data, library='cli'):
        with tempfile.TemporaryDirectory(prefix='assis-typed-') as folder:
            source = Path(folder) / 'typed.assis'
            binary = Path(folder) / ('typed' + SUFFIX)
            source.write_text(f'import "std/{library}.assis";\nsafe fn main(): int {{\n{body}\nreturn 0;\n}}\n',
                              encoding='utf-8')
            results = []
            for flags in [[], ['--no-opt']]:
                built = subprocess.run([COMPILER, 'build', source, '-o', binary, '--debug', *flags],
                                       capture_output=True, timeout=60)
                self.assertEqual(built.returncode, 0, built.stderr.decode('utf-8', 'replace'))
                ran = subprocess.run([binary], input=data, capture_output=True, timeout=60)
                self.assertEqual((ran.returncode, ran.stderr), (0, b''))
                results.append(ran.stdout)
            self.assertEqual(results[0], results[1])
            return results[0]

    def test_integer_widths(self):
        lines = []
        expected = []
        for signed in (True, False):
            for bits in (8, 16, 32, 64):
                kind = ('i' if signed else 'u') + str(bits)
                minimum = -(2 ** (bits - 1)) if signed else 0
                maximum = 2 ** (bits - signed) - 1
                cases = [
                    (str(minimum), minimum, 0, -1),
                    ('+' + str(maximum), maximum, 0, -1),
                    (str(maximum + 1), 0, 3, len(str(maximum + 1)) - 1),
                    ('', 0, 1, 0), ('+', 0, 2, 1), ('1x', 0, 2, 1),
                    (' 1', 0, 2, 0), ('00', 0, 0, -1),
                ]
                if signed:
                    cases.append((str(minimum - 1), 0, 3, len(str(minimum - 1)) - 1))
                else:
                    cases.append(('-0', 0, 2, 0))
                for spelling, value, code, position in cases:
                    lines.append(f'{{val r:parse::Parsed<{kind}>=parse::parse_{kind}("{spelling}");'
                                 'print(r.ok,r.value,r.code,r.position);}')
                    expected.append(f'{str(code == 0).lower()} {value} {code} {position}\n')
        self.assertEqual(self.run_program('\n'.join(lines), b'', 'parse'), ''.join(expected).encode())

    def test_float_rounding_against_independent_oracles(self):
        with localcontext() as context:
            context.prec = 1200
            half_min64 = str(Decimal(2) ** -1075)
            above_half64 = str(Decimal(2) ** -1075 + Decimal(10) ** -1120)
            below_half64 = str(Decimal(2) ** -1075 - Decimal(10) ** -1120)
            midpoint32 = Decimal(1) + Decimal(2) ** -24
            cases = [
                '0', '-0e9999', '+.1', '1.', '1e+3', '1e-9999', '-1e-9999', '1e9999',
                '1.7976931348623157e308', '1.7976931348623159e308',
                '4.9406564584124654e-324', '2.2250738585072014e-308',
                half_min64, above_half64, below_half64, str(Decimal(2) ** -150),
                str(midpoint32), str(midpoint32 + Decimal(10) ** -80),
                str(midpoint32 - Decimal(10) ** -80), '3.4028235e38', '3.4028236e38',
                '0.' + '0' * 850 + '1e851',
            ]
        rng = random.Random(99171)
        for _ in range(420):
            digits = ''.join(str(rng.randrange(10)) for _ in range(rng.randrange(1, 51)))
            cases.append(f'{rng.choice(["", "-"])}{digits}e{rng.randrange(-365, 315)}')
        body = '''
            own input:cli::Stdin = new cli::Stdin(2000);
            while (true) {
                val line:parse::Parsed<int> = input.readln();
                if (line.code == 5) { break; }
                assert(line.ok);
                val a:parse::Parsed<f32> = parse::parse_f32(input.line());
                val b:parse::Parsed<f64> = parse::parse_f64(input.line());
                print(a.code, a.value, b.code, b.value);
            }'''
        output = self.run_program(body, ('\n'.join(cases)).encode()).decode().splitlines()
        self.assertEqual(len(output), len(cases))
        for spelling, line in zip(cases, output):
            code32, real32, code64, real64 = line.split()
            for code, real, oracle, fmt in [
                (code32, real32, binary32(spelling), '>f'),
                (code64, real64, float(spelling), '>d'),
            ]:
                with self.subTest(spelling=spelling, format=fmt):
                    if math.isinf(oracle):
                        self.assertEqual(code, '3')
                    else:
                        self.assertEqual(code, '0')
                        self.assertEqual(struct.pack(fmt, float.fromhex(real)), struct.pack(fmt, oracle))

    def test_syntax_and_owned_utf8(self):
        body = '''
            val empty:parse::Parsed<f64> = parse::parse_f64("");
            val exponent:parse::Parsed<f64> = parse::parse_f64("1e+");
            val comma:parse::Parsed<f32> = parse::parse_f32("1,25");
            val inf:parse::Parsed<f64> = parse::parse_f64("inf");
            val b:parse::Parsed<bool> = parse::parse_bool("false");
            val c:parse::Parsed<bool> = parse::parse_bool("falsE");
            print(empty.code, exponent.code, exponent.position, comma.position, inf.position, b.ok, b.value, c.position);
            own raw:*byte=alloc<byte>(3);
            raw[0]=byte(65); raw[2]=byte(66);
            own word:unicode::String=new unicode::String();
            assert(parse::parse_string(slice_of(raw,0,3),word));
            raw[0]=byte(255);
            val utf:parse::Parsed<int> = parse::parse_text(slice_of(raw,0,3));
            assert(!parse::parse_string(slice_of(raw,0,3),word));
            print(utf.code, utf.position, word.as_slice());
            assert(parse::parse_string("",word));
            print(word.size());'''
        self.assertEqual(self.run_program(body, b'', 'parse'), b'1 2 3 1 0 true false 4\n2 0 A\x00B\n0\n')

    def test_line_boundaries_and_recovery(self):
        body = '''
            own input:cli::Stdin = new cli::Stdin(8);
            val empty:parse::Parsed<int> = input.readln();
            print(empty.code, empty.value);
            val unicode_line:parse::Parsed<int> = input.readln();
            print(unicode_line.value, input.line());
            val crlf:parse::Parsed<int> = input.readln();
            print(crlf.code, crlf.value, input.line());
            val long_line:parse::Parsed<int> = input.readln();
            val number:parse::Parsed<int> = input.readint();
            val invalid:parse::Parsed<int> = input.readln();
            val bad:parse::Parsed<int> = input.readint();
            val real:parse::Parsed<f64> = input.readfloat();
            val truth:parse::Parsed<bool> = input.readbool();
            val eof:parse::Parsed<int> = input.readln();
            print(long_line.code, long_line.position, number.value, invalid.code, invalid.position,
                  bad.code, real.value, truth.value, eof.code, input.readln().code);
            own zero:cli::Stdin = new cli::Stdin(-1);
            print(zero.readln().code);'''
        data = b'\n' + 'aé💡'.encode() + b'\r\n12345678\r\n' + b'x' * 8500 + b'\n-42\n\xff\n--1\n2.5\ntrue'
        expected = b'0 0\n7 ' + 'aé💡'.encode() + b'\n0 8 12345678\n7 8 -42 2 0 2 0x1.4000000000000p+1 true 5 5\n7\n'
        self.assertEqual(self.run_program(body, data), expected)


if __name__ == '__main__':
    unittest.main(verbosity=2)
