"""Verify this unit's source/log hashes and recorded native test results."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
DIRECTORY = ROOT / 'docs/ecossistema/evidencias/m1-document-memory-2026-11-01'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--revision', help='Also verify the committed blobs at this revision')
    args = parser.parse_args()
    summary = json.loads((DIRECTORY / 'summary.json').read_text(encoding='utf-8'))
    checked = 0
    for group in ['sources', 'artifacts']:
        for name, expected in summary[group].items():
            path = ROOT / name
            assert hashlib.sha256(path.read_bytes()).hexdigest() == expected, name
            if args.revision:
                blob = subprocess.check_output(['git', 'show', args.revision + ':' + name], cwd=ROOT)
                assert hashlib.sha256(blob).hexdigest() == expected, f'Git blob differs: {name}'
            checked += 1
    before = json.loads((DIRECTORY / 'before.json').read_text(encoding='utf-8'))
    assert before['base_commit'] == summary['base_commit']
    assert before['returncode'] == 1 and 'std/documents.assis' in before['stderr']
    for host in ['windows', 'linux']:
        data = json.loads((DIRECTORY / f'{host}.json').read_text(encoding='utf-8'))
        assert data['passed'] and len(data['checks']) == 10
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
        assert new['name'] == 'document-memory' and new['executed'] == 12 and new['not_run'] == 0
        assert sum(r['executed'] or 0 for r in data['checks']) == summary['executed_per_host'][host]
        assert sum(r['not_run'] for r in data['checks']) == 1
        ports = json.loads((DIRECTORY / f'{host}-portability.json').read_text(encoding='utf-8'))
        assert ports['passed'] and len(ports['cases']) == 34
        assert ports['compilerSha256'] == data['compiler_sha256']
        assert all(case['passed'] and len(case['binaries']) == 5 for case in ports['cases'])
        assert sum(case['name'] == 'document-memory' for case in ports['cases']) == 2
    assert summary['points_before'] == summary['points_after'] == '22.30'
    assert summary['gates_before'] == summary['gates_after'] == 0
    print(f'Document memory: {checked} hashes checked; 12/12 new tests per host; 0/5 gates')


if __name__ == '__main__':
    main()
