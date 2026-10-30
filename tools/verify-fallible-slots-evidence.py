"""Check published M1 slot evidence identities; this does not execute the runtime."""
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent.parent
DIRECTORY = ROOT / 'docs/ecossistema/evidencias/m1-slots-2026-10-29'

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    report = json.loads((DIRECTORY / 'summary.json').read_text(encoding='utf-8'))
    assert report['schema'] == 'assisscript-fallible-slots-evidence-v1'
    for group, base in [('inputs', ROOT), ('artifacts', DIRECTORY)]:
        for name, expected in report[group].items():
            path = (base / name).resolve()
            assert path.is_relative_to(base.resolve()), name
            assert re.fullmatch('[0-9a-f]{64}', expected), name
            assert digest(path) == expected, f'Changed {group}: {name}'
    for host, record in report['native'].items():
        raw = json.loads((DIRECTORY / f'{host}.json').read_text(encoding='utf-8'))
        assert raw['passed'] and len(raw['suites']) == record['suite_count'] == 38
        assert raw['compilerSha256'] == record['compiler_sha256']
        assert all(suite['returnCode'] == 0 for suite in raw['suites'])
        assert sum(suite['registered'] for suite in record['suites']) == record['registered']
        assert sum(suite['executed'] for suite in record['suites']) == record['executed']
        assert record['registered'] == record['executed'] + record['not_run']
        for raw_suite, suite in zip(raw['suites'], record['suites']):
            text = (DIRECTORY / raw_suite['log']).read_text(encoding='utf-8')
            count = int(re.search(r'Ran (\d+) tests?', text)[1])
            skips = re.search(r'skipped=(\d+)', text)
            not_run = int(skips[1]) if skips else 0
            assert count == raw_suite['tests'] == suite['registered']
            assert not_run == suite['not_run']
            if suite['suite'] == 'fallible-slots':
                assert count == suite['executed'] == 11 and not_run == 0
        for suffix in ['portability', 'examples']:
            data = json.loads((DIRECTORY / f'{host}-{suffix}.json').read_text(encoding='utf-8'))
            assert data['passed'] and data['compilerSha256'] == record['compiler_sha256']
    emulated = json.loads((DIRECTORY / 'arm64-emulated.json').read_text(encoding='utf-8'))
    assert emulated['passed'] and len(emulated['cases']) == 4
    assert emulated['compiler_sha256'] == report['native']['linux']['compiler_sha256']
    for case in emulated['cases']:
        assert case['passed'] and case['source_sha256'] == digest(ROOT / case['source'])
    editor = json.loads((DIRECTORY / 'editor.json').read_text(encoding='utf-8'))
    assert editor['tests'] == editor['passed'] == 31 and editor['skipped'] == editor['failed'] == 0
    print(f"Evidence identities verified: {len(report['inputs'])} inputs, {len(report['artifacts'])} artifacts; no new runtime execution")

if __name__ == '__main__':
    main()
