"""Run the typed readers and converters in both native emitter modes."""

from decimal import Decimal, localcontext
from fractions import Fraction
from pathlib import Path
import math
import os
import random
import select
import struct
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SUFFIX = '.exe' if os.name == 'nt' else ''
COMPILER = Path(os.environ.get('ASSIS_BIN', ROOT / 'bin' / ('assis' + SUFFIX)))


def ieee_round(spelling, precision, min_exponent, max_exponent):
    """Round an exact rational at the target's spacing, independently of the parser."""
    value = Fraction(spelling)
    negative = spelling.startswith('-')
    value = abs(value)
    if value == 0:
        return -0.0 if negative else 0.0
    exp = value.numerator.bit_length() - value.denominator.bit_length()
    if value < Fraction(2) ** exp:
        exp -= 1
    shift = max(exp, min_exponent) - (precision - 1)
    rounded = round(value / (Fraction(2) ** shift))
    if exp > max_exponent or (exp == max_exponent and rounded == 1 << precision):
        result = math.inf
    else:
        result = math.ldexp(rounded, shift)
    return -result if negative else result


class TypedInput(unittest.TestCase):
    def run_program(self, body, data, library='cli', execute=None, legacy=False):
        with tempfile.TemporaryDirectory(prefix='assis-typed-') as folder:
            source = Path(folder) / 'typed.assis'
            binary = Path(folder) / ('typed' + SUFFIX)
            entry = 'fn' if legacy else 'safe fn'
            source.write_text(f'import "std/{library}.assis";\n{entry} main(): int {{\n{body}\nreturn 0;\n}}\n',
                              encoding='utf-8')
            results = []
            for flags in [[], ['--no-opt']]:
                profile = ['--legacy'] if legacy else []
                built = subprocess.run([COMPILER, 'build', source, '-o', binary, '--debug', *profile, *flags],
                                       capture_output=True, timeout=60)
                self.assertEqual(built.returncode, 0, built.stderr.decode('utf-8', 'replace'))
                ran = (execute(binary) if execute else
                       subprocess.run([binary], input=data, capture_output=True, timeout=60))
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
            # Adjacent values at the zero, normal and overflow boundaries,
            # with ties of both parities and perturbations beyond 800 digits.
            for precision, exponents in [(24, [-150, -149, -126, -23, 104]),
                                         (53, [-1075, -1074, -1022, -52, 971])]:
                for exponent in exponents[1:]:
                    spacing = Decimal(2) ** exponent
                    for mantissa in [2 ** (precision - 1) - 1, 2 ** (precision - 1), 2 ** precision - 1]:
                        tie = (Decimal(mantissa) + Decimal('0.5')) * spacing
                        delta = Decimal(10) ** (tie.adjusted() - 820)
                        cases.extend(str(tie + direction * delta) for direction in [-1, 0, 1])
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
                (code32, real32, ieee_round(spelling, 24, -126, 127), '>f'),
                (code64, real64, ieee_round(spelling, 53, -1022, 1023), '>d'),
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
            val copied:parse::Parsed<int> = parse::parse_string(slice_of(raw,0,3),word);
            assert(copied.ok && copied.value == 3);
            raw[0]=byte(255);
            val utf:parse::Parsed<int> = parse::parse_text(slice_of(raw,0,3));
            val invalid:parse::Parsed<int> = parse::parse_string(slice_of(raw,0,3),word);
            assert(!invalid.ok && invalid.code == 2 && invalid.position == 0);
            print(utf.code, utf.position, word.as_slice());
            val cleared:parse::Parsed<int> = parse::parse_string("",word);
            assert(cleared.ok && cleared.value == 0);
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

    def test_zero_limit_crlf_and_final_cr(self):
        body = '''
            own input:cli::Stdin = new cli::Stdin(0);
            print(len(input.line()));
            print(input.readln().code, input.readln().code);
            print(input.readln().code, input.readln().code);
            print(input.readln().code);
            own invalid:cli::Stdin = new cli::Stdin(9223372036854775776);
            print(invalid.readln().code);'''
        self.assertEqual(self.run_program(body, b'\r\nX\n\n\r'), b'0\n0 7\n0 7\n5\n4\n')

    def test_stdin_io_error(self):
        def execute(binary):
            with (binary.parent / 'write-only').open('wb') as unreadable:
                return subprocess.run([binary], stdin=unreadable, capture_output=True, timeout=60)

        self.assertEqual(self.run_program('''
            own input:cli::Stdin = new cli::Stdin(8);
            val result:parse::Parsed<int> = input.readint();
            print(result.code, result.position, len(input.line()));''', None, execute=execute), b'6 -1 0\n')

    def test_legacy_line_and_bytes_share_stdin(self):
        body = '''
            let line: String = read_line();
            let integer: IntResult = parse_int(line.view());
            print(integer.ok, integer.value);
            free(integer); line.dispose(); free(line);
            let data: *byte = alloc<byte>(3);
            assert(read_bytes(data, 3) == 3);
            print(data[0], data[1], data[2]); free(data);
            for (let i: int = 0; i < 2; i += 1) {
                let empty: String = read_line();
                print(empty.size()); empty.dispose(); free(empty);
            }'''
        data = b'-9223372036854775808\r\nabc\n'
        expected = b'true -9223372036854775808\n97 98 99\n0\n0\n'
        self.assertEqual(self.run_program(body, data, 'convert', legacy=True), expected)

    @unittest.skipUnless(os.name == 'posix', 'requires a nonblocking stdin pipe')
    def test_io_retry_preserves_partial_line(self):
        def execute(binary):
            read_fd, write_fd = os.pipe()
            try:
                os.set_blocking(read_fd, False)
                os.write(write_fd, b'12')
                with subprocess.Popen([binary], stdin=read_fd, stdout=subprocess.PIPE,
                                      stderr=subprocess.PIPE) as process:
                    try:
                        self.assertTrue(select.select([process.stdout], [], [], 10)[0])
                        prefix = process.stdout.readline()
                        self.assertEqual(prefix, b'6\n')
                        os.write(write_fd, b'3\n')
                        output, error = process.communicate(timeout=10)
                        return subprocess.CompletedProcess(process.args, process.returncode, prefix + output, error)
                    finally:
                        if process.poll() is None:
                            process.kill()
            finally:
                os.close(read_fd)
                os.close(write_fd)

        body = '''
            own input:cli::Stdin = new cli::Stdin(8);
            let result:parse::Parsed<int> = input.readint();
            print(result.code);
            while (result.code == 6) { sleep_ms(1); result = input.readint(); }
            print(result.code, result.value);'''
        self.assertEqual(self.run_program(body, None, execute=execute), b'6\n0 123\n')

    @unittest.skipUnless(sys.platform == 'linux', 'requires Linux RLIMIT_AS')
    def test_copy_allocation_failure_preserves_destination(self):
        import resource

        def limit_memory():
            ceiling = 14 * 1024 * 1024
            resource.setrlimit(resource.RLIMIT_AS, (ceiling, ceiling))

        def execute(binary):
            return subprocess.run([binary], input=b'', capture_output=True, timeout=60,
                                  preexec_fn=limit_memory)

        body = '''
            own word:unicode::String = new unicode::String();
            val first:parse::Parsed<int> = parse::parse_string("existing", word);
            assert(first.ok);
            own raw:*byte = alloc<byte>(8388608);
            val failed:parse::Parsed<int> = parse::parse_string(slice_of(raw, 0, 8388608), word);
            print(failed.code, failed.position, word.as_slice());'''
        self.assertEqual(self.run_program(body, None, 'parse', execute), b'4 -1 existing\n')


if __name__ == '__main__':
    unittest.main(verbosity=2)
