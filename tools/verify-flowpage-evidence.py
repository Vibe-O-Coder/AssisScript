"""Verify exact native results, source hashes and the unchanged ecosystem rubric."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'docs/ecossistema/evidencias/m5-page-styles-2026-11-02'
BASE='f274c9f7d4dda1e1d9a7bfe92b172354b89a4203'
parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--write',action='store_true');args=parser.parse_args()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
git=lambda *parts:subprocess.check_output(['git',*parts],cwd=ROOT)
before=json.loads(git('show',BASE+':docs/ecossistema/PROGRESSO.json'))
after=json.loads((ROOT/'docs/ecossistema/PROGRESSO.json').read_text(encoding='utf-8'))
for a,b in zip(before['groups'],after['groups']):
    assert (a['id'],a['weight'],a['dependencies'])==(b['id'],b['weight'],b['dependencies'])
    for old,new in zip(a['items'],b['items']):
        assert (old['id'],old['name'],old['acceptance'])==(new['id'],new['name'],new['acceptance'])
        assert new['level']==old['level']+(1 if old['id']=='E08-01' else 0)
assert after['gates']==before['gates'] and after['history'][:-1]==before['history']
assert (ROOT/'docs/ecossistema/BASELINE-2026-10-29.json').read_bytes()==git('show',BASE+':docs/ecossistema/BASELINE-2026-10-29.json')
counts={}
expected={'flowpage':17,'document-memory':12,'document-tree':9,'htdl-parser':16,'htdl-catalog':16,'fluxstyle':17,'sanscript':9,'reader-transactions':15,'page-reader':10}
for host in ['windows','linux']:
    data=json.loads((OUT/f'{host}.json').read_text());assert data['passed'] and data['base']==BASE
    assert {c['name'] for c in data['checks']}==set(expected)
    for check in data['checks']:
        skipped=0 if host=='windows' else {'reader-transactions':4,'page-reader':1}.get(check['name'],0)
        assert check['returncode']==0 and check['not_run']==skipped and check['executed']==expected[check['name']]-skipped
        path=OUT/check['log'];assert sha(path)==check['sha256'] and re.search(rb'\nOK(?: \(skipped=\d+\))?\r?\n',path.read_bytes())
    examples=json.loads((OUT/f'{host}-examples.json').read_text());assert examples['passed'] and len(examples['examples'])==57
    install=json.loads((OUT/f'{host}-install.json').read_text());assert install['passed']
    assert install['compiler_sha256']==data['compiler_sha256']
    assert set(install['selected_libraries'])=={'flowpage','fluxstyle','htdl','documents','doctree','buffers','owned','unicode'}
    for check in install['checks']:
        assert check['returncode']==0
        if 'log' in check:assert sha(OUT/check['log'])==check['sha256']
    counts[host]=dict(native_methods=sum(c['executed'] for c in data['checks']),not_run=sum(c['not_run'] for c in data['checks']),examples=57)
install=json.loads((OUT/'windows-install.json').read_text())
extras=sorted(c['executed'] for c in install['checks'] if 'executed' in c);assert extras==[4,23]
counts['windows']['native_methods']+=4
initial=(OUT/'windows-distribution-node-initial.log').read_text(encoding='utf-8');assert 'fail 1' in initial and 'pass 22' in initial and 'Windows 5' in initial
old=(OUT/'windows-installer-before.log').read_bytes();new=(OUT/'windows-installer-after.log').read_bytes()
assert b'FAILED (failures=2)' in old and b'Ran 4 tests' in old and b'Windows 32' in old
assert b'Ran 4 tests' in new and re.search(rb'\nOK\r?\n',new)
reference=json.loads((OUT/'reference-integrity.json').read_text());assert reference['integrity']=='pass' and reference['runtime_conformance']=='not-run'
traces=[json.loads((OUT/f'{h}-ssc-traces.json').read_text()) for h in ['windows','linux']]
assert len(traces[0]['rows'])==len(traces[1]['rows'])==42
assert [r['trace_sha256'] for r in traces[0]['rows']]==[r['trace_sha256'] for r in traces[1]['rows']]
sources=['.gitattributes','stdlib/documents.assis','stdlib/fluxstyle.assis','stdlib/flowpage.assis','stdlib/catalogo.json','stdlib/catalogo.sh',
    'src/windows_setup.c','src/install_files.inc','src/install_optional.inc','.github/workflows/ci.yml','Makefile',
    'tests/test-flowpage.py','tests/test-installer-retry.py','exemplos/55_page_styles.assis',
    'tools/collect-flowpage-evidence.py','tools/verify-flowpage-install.py','tools/verify-flowpage-evidence.py',
    'docs/BIBLIOTECA-flowpage.md','docs/BIBLIOTECA-fluxstyle.md','docs/BIBLIOTECA-documents.md','docs/ecossistema/PERFIL-APRESENTACAO-LOCAL-V1.md']
logs=['windows-distribution-node-initial.log','windows-installer-before.log','windows-installer-after.log']
summary=dict(schema='flowpage-summary-v1',base=BASE,
    base_publication=dict(url='https://api.github.com/repos/Vibe-O-Coder/AssisScript/git/commits/'+BASE,
        sha=BASE,tree='c761d1e31e54f7606d51788ac1bb01860c0008ca',verified_by='GitHub connector GET; local Git tree SHA matches'),
    counts=counts,windows_distribution_node=23,windows_installer_methods=4,
    windows_installer_linux='not-run: Windows-specific tests; excluded from applicable Linux method count',
    points_before='44.90',points_after='45.30',gates_passed=0,
    source_sha256={p:sha(ROOT/p) for p in sources},development_logs_sha256={p:sha(OUT/p) for p in logs},
    limitations=['At most 256 styled elements; exact node-level context cache, not per-expression DAG invalidation',
        'Author outputs only; no geometry, drawing, hit-test or accessibility snapshot integration',
        'SSC remains per-node with finite 42-pair profile; no aggregate channel/RSS quota',
        'Reader catalog, loader, SDK general values and desktop/DPI/IME acceptance remain open',
        'Five Linux graphical integration methods not-run; Windows installer tests not applicable to Linux',
        'ARM/macOS format generation only; native execution not-run',
        'Windows retry is bounded to one second per blocked file; persistent lock still fails; no transactional uninstall guarantee',
        'No remote CI, release, merge, new 24h run or user acceptance is asserted'])
assert git('rev-parse',BASE+'^{tree}').decode().strip()==summary['base_publication']['tree']
path=OUT/'summary.json'
if args.write:path.write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8',newline='\n')
else:assert json.loads(path.read_text())==summary,'Evidence/source hash changed'
print(json.dumps(counts)+'; 44.90 -> 45.30%, 0/5 gates')
