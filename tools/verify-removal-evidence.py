"""Check identities and counts of M1 removal evidence; does not run native tests."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parent.parent
DIRECTORY = ROOT / 'docs/ecossistema/evidencias/m1-removal-2026-10-30'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--revision', help='Also compare identities with exact Git blobs')
    args = parser.parse_args()
    report = json.loads((DIRECTORY / 'summary.json').read_text(encoding='utf-8'))
    assert report['schema'] == 'assisscript-removal-evidence-v1'
    count = 0
    for group, directory in [('inputs', ROOT), ('artifacts', DIRECTORY)]:
        for name, expected in report[group].items():
            path = (directory / name).resolve()
            assert path.is_relative_to(directory.resolve()), name
            assert re.fullmatch('[0-9a-f]{64}', expected), name
            assert digest(path.read_bytes()) == expected, f'Changed {group}: {name}'
            if args.revision:
                blob = subprocess.check_output(['git', 'show', args.revision + ':' + path.relative_to(ROOT).as_posix()], cwd=ROOT)
                assert digest(blob) == expected, f'Git blob differs: {name}'
            count += 1
    for host in ['windows', 'linux']:
        record = report['native'][host]
        raw = json.loads((DIRECTORY / f'{host}.json').read_text(encoding='utf-8'))
        assert raw['passed'] and len(raw['suites']) == record['suite_count'] == 39
        assert raw['compilerSha256'] == record['compiler_sha256']
        assert record['registered'] == record['executed'] + record['not_run']
        assert record['executed'] == sum(s['executed'] for s in record['suites'])
        assert record['not_run'] == sum(s['not_run'] for s in record['suites'])
        for suite, normalized in zip(raw['suites'], record['suites'], strict=True):
            assert suite['returnCode'] == 0
            log = (DIRECTORY / suite['log']).read_text(encoding='utf-8')
            registered = int(re.search(r'Ran (\d+) tests?', log)[1])
            skipped = re.search(r'skipped=(\d+)', log)
            not_run = int(skipped[1]) if skipped else 0
            assert registered == suite['tests'] == normalized['registered']
            assert not_run == normalized['not_run']
            assert normalized['executed'] == registered - not_run
            if suite['suite'] == 'arena-removal':
                assert registered == 10 and not_run == 0
        for suffix in ['portability', 'examples']:
            result = json.loads((DIRECTORY / f'{host}-{suffix}.json').read_text(encoding='utf-8'))
            assert result['passed'] and result['compilerSha256'] == record['compiler_sha256']
            if suffix == 'portability':
                assert len(result['cases']) == 26 and all(c['passed'] for c in result['cases'])
            else:
                assert len(result['examples']) == 40 and all(c['passed'] for c in result['examples'])
        before = json.loads((DIRECTORY / f'{host}-before.json').read_text(encoding='utf-8'))
        assert len(before) == 2 and all(c['returnCode'] == 70 and 'R001' in c['stderr'] for c in before)
    emulated = json.loads((DIRECTORY / 'arm64-emulated.json').read_text(encoding='utf-8'))
    assert emulated['passed'] and len(emulated['cases']) == 2
    assert emulated['compiler_sha256'] == report['native']['linux']['compiler_sha256']
    for case in emulated['cases']:
        assert case['source_sha256'] == digest((ROOT / case['source']).read_bytes())
        assert (case['returnCode'], case['stdout'], case['stderr']) == (0, '42 0\n', '')
    progress = json.loads((ROOT / 'docs/ecossistema/PROGRESSO.json').read_text(encoding='utf-8'))
    assert progress['history'][-1]['levels'] == progress['history'][-2]['levels']
    assert not any(g['passed'] for g in progress['gates'])
    print(f'Removal evidence: {count} identities verified; native skips kept separate; no new runtime execution')


if __name__ == '__main__':
    main()
