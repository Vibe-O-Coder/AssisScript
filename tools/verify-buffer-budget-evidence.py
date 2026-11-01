"""Verify M1 buffer-budget identities/counts; does not run native tests."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parent.parent
DIRECTORY = ROOT / 'docs/ecossistema/evidencias/m1-buffer-budget-2026-11-01'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def counts(log):
    registered = int(re.search(r'Ran (\d+) tests?', log)[1])
    skipped = re.search(r'skipped=(\d+)', log)
    not_run = int(skipped[1]) if skipped else 0
    return registered, not_run


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--revision', help='Compare every recorded input/artifact with exact Git blobs')
    args = parser.parse_args()
    report = json.loads((DIRECTORY / 'summary.json').read_text(encoding='utf-8'))
    assert report['schema'] == 'assisscript-buffer-budget-evidence-v1'
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
        native = report['native'][host]
        raw = json.loads((DIRECTORY / f'{host}.json').read_text(encoding='utf-8'))
        assert raw['compilerSha256'] == native['compiler_sha256']
        assert len(raw['suites']) == native['suite_count'] == 40
        assert raw['passed'] == native['initial_matrix_passed']
        assert native['registered'] == native['executed'] + native['not_run']
        assert native['registered'] == sum(s['registered'] for s in native['suites'])
        assert native['not_run'] == sum(s['not_run'] for s in native['suites'])
        for initial, effective in zip(raw['suites'], native['suites'], strict=True):
            assert initial['suite'] == effective['suite']
            if host == 'windows' and initial['suite'] == 'net':
                repeat = json.loads((DIRECTORY / 'windows-net-retest.json').read_text(encoding='utf-8'))
                assert initial['returnCode'] != 0 and repeat['returnCode'] == 0
                assert repeat['compiler_sha256'] == native['compiler_sha256']
                assert effective['log'] == repeat['log']
            else:
                assert initial['returnCode'] == 0 and effective['log'] == initial['log']
            log = (DIRECTORY / effective['log']).read_text(encoding='utf-8')
            registered, not_run = counts(log)
            assert '\nOK' in log and 'FAILED (' not in log
            assert registered == initial['tests'] == effective['registered']
            assert not_run == effective['not_run']
            assert effective['executed'] == registered-not_run
            if initial['suite'] == 'shared-buffer-budget':
                assert (registered, not_run) == (11, 0)
        assert native['all_effective_suites_passed'] and native['coverage'] == 'partial-not-run-kept-separate'
        for suffix in ['portability', 'examples']:
            result = json.loads((DIRECTORY / f'{host}-{suffix}.json').read_text(encoding='utf-8'))
            assert result['passed'] and result['compilerSha256'] == native['compiler_sha256']
            records = result['cases'] if suffix == 'portability' else result['examples']
            assert len(records) == (28 if suffix == 'portability' else 41)
            assert all(c['passed'] for c in records)
        before = json.loads((DIRECTORY / f'{host}-before.json').read_text(encoding='utf-8'))
        assert before['compiler_sha256'] == native['compiler_sha256']
        assert before['source_sha256'] == digest((DIRECTORY / 'before.assis').read_bytes())
        assert len(before['cases']) == 2
        assert all((c['returnCode'], c['stdout'], c['stderr']) == (0, '16\n', '') for c in before['cases'])
    emulated = json.loads((DIRECTORY / 'arm64-emulated.json').read_text(encoding='utf-8'))
    assert emulated['native'] is False and emulated['execution'] == 'qemu-aarch64'
    assert emulated['compiler_sha256'] == report['native']['linux']['compiler_sha256']
    assert emulated['source_sha256'] == digest((ROOT / 'exemplos/39_shared_buffer_budget.assis').read_bytes())
    assert len(emulated['cases']) == 2
    assert all((c['returnCode'], c['stdout'], c['stderr']) == (0, '8 42\n0 1\n', '') for c in emulated['cases'])
    progress = json.loads((ROOT / 'docs/ecossistema/PROGRESSO.json').read_text(encoding='utf-8'))
    assert progress['history'][-1]['levels'] == progress['history'][-2]['levels']
    assert not any(g['passed'] for g in progress['gates'])
    print(f'Buffer-budget evidence: {count} identities verified; initial failure/retest and not-run remain explicit; no runtime reexecution')


if __name__ == '__main__':
    main()
