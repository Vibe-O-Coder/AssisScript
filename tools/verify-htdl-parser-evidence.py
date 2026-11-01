"""Verify this unit's recorded native checks, source/log hashes and Git blobs."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
DIRECTORY = ROOT / 'docs/ecossistema/evidencias/m3-htdl-parser-2026-11-01'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--revision', help='Verify the same hashes against committed Git blobs')
    args = parser.parse_args()
    summary = json.loads((DIRECTORY / 'summary.json').read_text(encoding='utf-8'))
    checked = 0
    for group in ['sources', 'artifacts']:
        for name, digest in summary[group].items():
            assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest, name
            if args.revision:
                blob = subprocess.check_output(['git', 'show', args.revision + ':' + name], cwd=ROOT)
                assert hashlib.sha256(blob).hexdigest() == digest, name
            checked += 1
    before = json.loads((DIRECTORY / 'before.json').read_text(encoding='utf-8'))
    assert before['base_commit'] == summary['base_commit']
    assert before['returncode'] == 1 and 'std/htdl.assis' in before['stderr']
    for host in ['windows', 'linux']:
        report = json.loads((DIRECTORY / f'{host}.json').read_text(encoding='utf-8'))
        assert report['passed'] and len(report['checks']) == 9
        assert report['compiler_sha256'] == summary['compilers'][host]['sha256']
        for record in report['checks']:
            assert record['returncode'] == 0, (host, record['name'])
            log = (DIRECTORY / record['log']).read_text(encoding='utf-8')
            if record['registered'] is not None:
                assert int(re.search(r'Ran (\d+) tests?', log)[1]) == record['registered']
                assert '\nOK' in log and 'FAILED (' not in log
                skipped = re.search(r'skipped=(\d+)', log)
                assert record['not_run'] == (int(skipped[1]) if skipped else 0)
                assert record['executed'] + record['not_run'] == record['registered']
        assert report['checks'][0]['executed'] == 16 and report['checks'][0]['not_run'] == 0
        assert sum(r['executed'] or 0 for r in report['checks']) == summary['executed_per_host'][host]
        ports = json.loads((DIRECTORY / f'{host}-portability.json').read_text(encoding='utf-8'))
        assert ports['passed'] and len(ports['cases']) == 36
        assert ports['compilerSha256'] == report['compiler_sha256']
        assert all(c['passed'] and len(c['binaries']) == 5 for c in ports['cases'])
        assert sum(c['name'] == 'htdl-parser' for c in ports['cases']) == 2
    assert summary['points_before'] == '22.30' and summary['points_after'] == '23.90'
    assert summary['gates_before'] == summary['gates_after'] == 0
    print(f'HTDL parser: {checked} hashes checked, 16/16 new tests per host; 0/5 gates')


if __name__ == '__main__':
    main()
