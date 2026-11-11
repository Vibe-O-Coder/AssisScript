"""Compare a VSIX to its candidate files and execute its bundled console example."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import tempfile
import zipfile


ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = 'exemplos/68_typed_input.assis'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def exercise(compiler, source):
    cases = [
        ('valid-crlf', 'Júlia\r\n3\r\n12.50\r\ntrue'.encode(), 0, 'Júlia 3 37.50'),
        ('declined', b'Jo\n1\n2\nfalse\n', 0, 'Pedido cancelado'),
        ('invalid-utf8', b'a\xff\n', 1, 'Nome inválido 2 1'),
        ('eof', b'', 1, 'Nome inválido 5 -1'),
        ('line-limit', b'x' * 257 + b'\n', 1, 'Nome inválido 7 256'),
        ('integer-overflow', b'Jo\n9223372036854775808\n', 1, 'Quantidade inválida 3 18'),
        ('invalid-real', b'Jo\n1\n1,5\n', 1, 'Preço inválido 2 1'),
        ('invalid-bool', b'Jo\n1\n1.5\nTRUE\n', 1, 'Confirmação inválida 2 0'),
    ]
    environment = os.environ.copy()
    environment.pop('ASSIS_PATH', None)
    records = []
    for flags in [[], ['--no-opt']]:
        for name, data, code, tail in cases:
            ran = subprocess.run([compiler, 'run', source, '--debug', *flags], input=data,
                                 capture_output=True, timeout=30, env=environment)
            assert (ran.returncode, ran.stderr) == (code, b''), (name, ran)
            assert ran.stdout.decode('utf-8').splitlines()[-1] == tail, (name, ran.stdout)
            records.append({'case': name, 'mode': flags[0] if flags else 'optimized', 'exit': code, 'lastLine': tail})
    return records


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive', type=Path)
    parser.add_argument('--bin-dir', type=Path, required=True)
    parser.add_argument('--installed', type=Path, help='execute the VS Code installation of the same VSIX')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    native = 'assis.exe' if os.name == 'nt' else 'assis'
    compilers = {p.name: p for p in args.bin_dir.iterdir() if p.is_file()}
    assert {'assis', 'assis.exe'} <= compilers.keys()
    files = {f'bin/{name}': path for name, path in compilers.items()}
    files.update({f'stdlib/{path.name}': path for path in (ROOT / 'stdlib').iterdir() if path.is_file()})
    files.update({name: ROOT / name for name in [EXAMPLE, 'docs/BIBLIOTECA-cli.md', 'docs/BIBLIOTECA-parse.md', 'docs/VSCODE.md']})
    for name in ['package.json', 'snippets/assis.json', 'src/extension.js', 'src/language.js', 'src/reference.json']:
        files[name] = ROOT / 'vscode-assisscript' / name

    with zipfile.ZipFile(args.archive) as package, tempfile.TemporaryDirectory(prefix='assis-vsix-') as temp:
        entries = package.namelist()
        assert len(set(entries)) == len(entries), 'duplicate VSIX entries'
        assert package.testzip() is None, 'corrupt VSIX entry'
        assert {name for name in entries if name.startswith('extension/bin/')} == {
            f'extension/bin/{name}' for name in compilers}
        hashes = {}
        extracted = Path(temp) / 'extension'
        for name, path in files.items():
            entry = f'extension/{name}'
            data = package.read(entry)
            assert data == path.read_bytes(), entry
            hashes[name] = digest(data)
            package.extract(entry, temp)
            if args.installed:
                installed_data = (args.installed / name).read_bytes()
                if name == 'package.json':
                    manifest = json.loads(installed_data)
                    manifest.pop('__metadata', None)  # Added by VS Code on installation.
                    assert manifest == json.loads(data), f'installed: {name}'
                else:
                    assert data == installed_data, f'installed: {name}'
        pe = (extracted / 'bin/assis.exe').read_bytes()
        pe_offset = int.from_bytes(pe[60:64], 'little')
        assert pe[:2] == b'MZ' and pe[pe_offset:pe_offset + 6] == b'PE\0\0\x64\x86'
        elf = (extracted / 'bin/assis').read_bytes()
        assert elf[:5] == b'\x7fELF\x02' and int.from_bytes(elf[18:20], 'little') == 62
        compiler = extracted / 'bin' / native
        compiler.chmod(0o755)
        records = exercise(compiler, extracted / EXAMPLE)
        installed = exercise(args.installed / 'bin' / native, args.installed / EXAMPLE) if args.installed else []

    result = {'platform': f'{platform.system()} {platform.machine()}', 'archiveSha256': digest(args.archive.read_bytes()),
              'entryCount': len(entries), 'verifiedFiles': hashes, 'extractedRuns': records, 'installedRuns': installed}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'{len(hashes)} hashes, {len(records)} extracted runs, {len(installed)} installed runs: PASS')


if __name__ == '__main__':
    main()
