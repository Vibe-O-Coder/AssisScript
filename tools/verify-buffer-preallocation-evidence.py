"""Check the scoped metadata-preparation evidence and optional exact Git blobs."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parent.parent
DIRECTORY = ROOT / 'docs/ecossistema/evidencias/m1-buffer-preallocation-2026-11-01'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--revision')
    args = parser.parse_args()
    summary = json.loads((DIRECTORY / 'summary.json').read_text(encoding='utf-8'))
    assert summary['schema'] == 'assisscript-buffer-preallocation-evidence-v1'
    checked = 0
    for group, directory in [('sources', ROOT), ('artifacts', DIRECTORY)]:
        for name, expected in summary[group].items():
            path = (directory / name).resolve()
            assert path.is_relative_to(directory.resolve()), name
            assert digest(path.read_bytes()) == expected, name
            if args.revision:
                blob = subprocess.check_output(['git', 'show', args.revision + ':' + path.relative_to(ROOT).as_posix()], cwd=ROOT)
                assert digest(blob) == expected, f'Git blob differs: {name}'
            checked += 1
    for host in ['windows', 'linux']:
        data = json.loads((DIRECTORY / f'{host}.json').read_text(encoding='utf-8'))
        assert data['passed'] and len(data['checks']) == 6
        assert data['compiler_sha256'] == summary['compilers'][host]['sha256']
        for record in data['checks']:
            assert record['returncode'] == 0, record['name']
            log = (DIRECTORY / record['log']).read_text(encoding='utf-8')
            if record['registered'] is not None:
                assert int(re.search(r'Ran (\d+) tests?', log)[1]) == record['registered']
                skips = re.search(r'skipped=(\d+)', log)
                assert (int(skips[1]) if skips else 0) == record['not_run']
                assert record['executed'] + record['not_run'] == record['registered']
                assert '\nOK' in log and 'FAILED (' not in log
        new = data['checks'][0]
        assert new['name'] == 'buffer-preallocation' and new['executed'] == 6 and new['not_run'] == 0
        ports = json.loads((DIRECTORY / f'{host}-portability.json').read_text(encoding='utf-8'))
        assert ports['passed'] and len(ports['cases']) == 30
        assert ports['compilerSha256'] == data['compiler_sha256']
        assert all(case['passed'] for case in ports['cases'])
        assert sum(case['name'] == 'buffer-preallocation' for case in ports['cases']) == 2
    assert summary['points_before'] == summary['points_after'] == '22.30'
    assert summary['gates_before'] == summary['gates_after'] == 0
    print(f'Buffer preallocation: {checked} hashes checked; 6/6 new tests per host; 0/5 gates')


if __name__ == '__main__':
    main()
