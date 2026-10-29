"""Check snapshot integrity and inventory scenarios without executing languages."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
SNAPSHOT = ROOT / 'docs/ecossistema/referencias/htdl-drafts-2026-10-29'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check(snapshot):
    manifest = json.loads((snapshot / 'PROVENANCE.json').read_text(encoding='utf-8'))
    if manifest['schema'] != 'assisscript-reference-snapshot-v1':
        raise ValueError('Unknown reference schema')
    seen = set()
    for record in manifest['files']:
        relative = record['path']
        path = (snapshot / relative).resolve()
        if relative in seen or not path.is_relative_to(snapshot.resolve()):
            raise ValueError(f'Duplicate or escaping path: {relative}')
        seen.add(relative)
        if digest(path) != record['snapshot_sha256']:
            raise ValueError(f'Snapshot hash mismatch: {relative}')
    corpus = snapshot / 'exemplos/conformidade/cenarios.json'
    data = json.loads(corpus.read_text(encoding='utf-8'))
    if data['format'] != 'htdl-scenarios-draft-1' or data['status'] != 'not-run':
        raise ValueError('Unexpected declarative corpus status or format')
    records, identities = [], set()
    for scenario in data['scenarios']:
        identity = scenario['id']
        if identity in identities:
            raise ValueError(f'Duplicate scenario: {identity}')
        identities.add(identity)
        inputs = [scenario['document'], *scenario.get('resources', [])]
        hashes = {}
        for name in inputs:
            path = (corpus.parent / name).resolve()
            if not path.is_relative_to(snapshot.resolve()) or path.relative_to(snapshot).as_posix() not in seen:
                raise ValueError(f'Uninventoried scenario input: {identity}: {name}')
            hashes[name] = digest(path)
        records.append(dict(id=identity, state='not-run', phase=scenario['phase'], inputs=hashes,
                            reason='No HTDL/FS/SSC engine or integrated Browser driver in this unit'))
    return dict(schema='assisscript-reference-integrity-v1', integrity='pass',
                snapshot_files=len(seen), scenario_count=len(records),
                runtime_conformance='not-run', integration='not-run', scenarios=records)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    try:
        report = check(SNAPSHOT)
    except (ValueError, KeyError, OSError) as error:
        print(str(error), file=sys.stderr)
        return 1
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(f'Integrity pass: {report["snapshot_files"]} files; {report["scenario_count"]} scenarios not-run')
    return 0


if __name__ == '__main__':
    sys.exit(main())
