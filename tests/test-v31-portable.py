"""Execute the independent Node-generated corpus on another native backend.

Generate with ASSIS_FIXTURE_DIR=build/v31-fixtures node --test tests/test-v31.js.
No Node installation is required on the destination system.
"""
from pathlib import Path
import subprocess
import tempfile
import sys
import json

root = Path(__file__).resolve().parent.parent
compiler = root / 'bin' / ('assis.exe' if sys.platform == 'win32' else 'assis')
fixtures = root / 'build/v31-fixtures'
sources = sorted(fixtures.glob('*.assis'))
assert len(sources) >= 7, 'Gere o corpus com ASSIS_FIXTURE_DIR antes de executar'
count = 0
for source in sources:
    for options in [[], ['--no-opt']]:
        result = subprocess.run([compiler, 'run', source, *options], capture_output=True, timeout=30)
        assert result.returncode == 0, result.stderr.decode()
        assert result.stdout == source.with_suffix('.stdout').read_bytes(), source.name
        count += 1
for name in ['12_relatorio_vendas', '13_codificacao']:
    result = subprocess.run([compiler, 'run', root / 'exemplos' / (name + '.assis')], capture_output=True, timeout=30)
    assert result.returncode == 0, result.stderr.decode()
    count += 1
if sys.platform == 'linux':
    with tempfile.TemporaryDirectory(prefix='assis-v31-install-') as temp:
        all_optional=[lib['name'] for lib in json.loads((root/'stdlib/catalogo.json').read_text())['libraries'] if not lib['required']]
        for name, options, optional in [('minimal', ['--minimal'], []), ('selected', ['--with', 'csv,algoritmos'], ['csv', 'algoritmos']), ('full', [], all_optional), ('log', ['--with','log'], ['log','cli'])]:
            prefix = Path(temp) / name
            subprocess.run(['sh', root / 'instalar.sh', '--prefix', prefix, '--no-path', *options], check=True, capture_output=True)
            catalog = json.loads((prefix / 'share/assisscript/stdlib/catalogo.json').read_text())
            for library in catalog['libraries']:
                assert (prefix / 'share/assisscript/stdlib' / (library['name'] + '.assis')).exists() == (library['required'] or library['name'] in optional)
                assert (prefix / 'share/assisscript/docs' / library['doc']).exists()
            result = subprocess.run([prefix / 'bin/assis', 'run', sources[0]], capture_output=True, timeout=30)
            assert result.returncode == 0, result.stderr.decode()
            subprocess.run(['sh', root / 'desinstalar.sh', '--prefix', prefix], check=True, capture_output=True)
            assert not (prefix / 'share/assisscript').exists()
            count += 1
print(f'ASSIS 3.1: {count} verificações adicionais aprovadas em {sys.platform}.')
