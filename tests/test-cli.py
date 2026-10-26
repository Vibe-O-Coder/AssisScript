"""Application A: real native CSV CLI, persistent output and adversarial inputs."""
import csv
import hashlib
import importlib.util
import io
import os
from pathlib import Path
import shutil
import stat
import subprocess
import unittest

spec = importlib.util.spec_from_file_location('evolution', Path(__file__).with_name('test-evolution.py'))
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)


class Cli(base.Evolution):
    def test_application_a(self):
        source = base.ROOT / 'exemplos/21_relatorio_csv_stream.assis'
        for flags in [[], ['--no-opt']]:
            binary = self.temp / ('relatório.exe' if os.name == 'nt' else 'relatório')
            built = self.invoke('build', source, '-o', binary, '--safe', '--debug', *flags)
            self.assertEqual(built.returncode, 0, built.stderr)
            entry = self.temp / 'entrada á 日本 😀.csv'
            output = self.temp / 'saída espaço 日本.csv'
            def run(content, expected_status=0, expected_count=None, expected_total=None):
                entry.write_bytes(content)
                output.write_bytes(b'preservado')
                p = subprocess.run([binary, entry, output], capture_output=True, timeout=45)
                self.assertEqual(p.returncode, expected_status, (content[:100], p.stdout, p.stderr))
                self.assertEqual(p.stderr, b'')
                if expected_status:
                    self.assertEqual(output.read_bytes(), b'preservado')
                else:
                    rows = list(csv.reader(io.StringIO(content.decode())))
                    oracle = [int(row[0]) for row in rows[1:]]
                    count = len(oracle) if expected_count is None else expected_count
                    total = sum(oracle) if expected_total is None else expected_total
                    self.assertEqual(output.read_bytes(), f'registros,total\n{count},{total}\n'.encode())
            for data in [b'valor\n', b'valor\n1\n"-2"\n43', b'valor\r\n0\r\n-1\r\n1\r\n',
                         b'valor\n-9223372036854775808\n', b'valor\n9223372036854775807\n']:
                run(data)
            for data in [b'', b'outra\n1\n', b'valor', b'valor\n\n', b'valor\n1,2\n', b'valor\n+1\n',
                         b'valor\n1\x00\n', b'valor\n"1\n', b'valor\n1\r2\n', b'valor\n1\r',
                         b'valor\n' + b'0'*25 + b'\n', b'valor\n\xff\n']:
                run(data, 2)
            for data in [b'valor\n9223372036854775808\n', b'valor\n-9223372036854775809\n',
                         b'valor\n9223372036854775807\n1\n', b'valor\n-9223372036854775808\n-1\n']:
                run(data, 3)
            # Records cross every 64 KiB boundary; no newline-aligned read assumption.
            run(b'valor\n' + b'"1234567"\r\n' * 100_000)
            entry.write_bytes(b'valor\n1\n')
            for args, code in [([], 64), ([self.temp/'missing.csv', output], 1), ([entry, self.temp/'missing'/'out.csv'], 1), ([self.temp, output], 1)]:
                p = subprocess.run([binary, *map(str, args)], capture_output=True, timeout=30)
                self.assertEqual(p.returncode, code, (args, p.stdout, p.stderr))
                self.assertEqual(p.stderr, b'')
            # The output is not opened before complete validation of the input.
            output.write_bytes(b'preservado')
            original = hashlib.sha256(output.read_bytes()).hexdigest()
            entry.write_bytes(b'valor\n1\nruim\n')
            p = subprocess.run([binary, entry, output], capture_output=True, timeout=30)
            self.assertEqual(p.returncode, 2)
            self.assertEqual(hashlib.sha256(output.read_bytes()).hexdigest(), original)
            # Exercise OS permission errors as an unprivileged process when running as root.
            entry.write_bytes(b'valor\n1\n')
            if os.name == 'nt':
                output.chmod(stat.S_IREAD)
                try:
                    p = subprocess.run([binary, entry, output], capture_output=True, timeout=30)
                    self.assertEqual(p.returncode, 1, p.stdout)
                finally:
                    output.chmod(stat.S_IWRITE | stat.S_IREAD)
            elif os.getuid() != 0:
                output.chmod(0o400)
                try:
                    p = subprocess.run([binary, entry, output], capture_output=True, timeout=30)
                    self.assertEqual(p.returncode, 1, p.stdout)
                finally:
                    output.chmod(0o600)
            else:
                self.assertIsNotNone(shutil.which('runuser'), 'Permission test requires runuser for root')
                self.temp.chmod(0o755); entry.chmod(0o644); binary.chmod(0o755); output.chmod(0o600)
                p = subprocess.run(['runuser', '-u', 'nobody', '--', binary, entry, output], capture_output=True, timeout=30)
                self.assertEqual(p.returncode, 1, (p.stdout, p.stderr))
                self.assertIn(b'Erro ao abrir saida', p.stdout)


if __name__ == '__main__':
    result = unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite([Cli('test_application_a')]))
    print(f'ASSIS CLI A: {base.INVOCATIONS} compilações; {base.COMPILER}')
    raise SystemExit(not result.wasSuccessful())
