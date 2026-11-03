"""Audit fresh SSC evidence and unchanged rubric contracts against the public base."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'docs/ecossistema/evidencias/m5-page-motion-2026-11-02'
BASE='3a58c8f5e64b0550f46f7ec1982afccde8a7a9cd'
parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--write',action='store_true');args=parser.parse_args()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
git=lambda *parts:subprocess.check_output(['git',*parts],cwd=ROOT)
before=json.loads(git('show',BASE+':docs/ecossistema/PROGRESSO.json'))
after=json.loads((ROOT/'docs/ecossistema/PROGRESSO.json').read_text(encoding='utf-8'))
for old_group,new_group in zip(before['groups'],after['groups']):
    assert (old_group['id'],old_group['weight'],old_group['dependencies'])==(new_group['id'],new_group['weight'],new_group['dependencies'])
    for old,new in zip(old_group['items'],new_group['items']):
        assert (old['id'],old['name'],old['acceptance'])==(new['id'],new['name'],new['acceptance'])
        assert new['level']==old['level']+(1 if old['id'] in ('E08-03','E08-04') else 0)
assert before['gates']==after['gates'] and before['history']==after['history'][:-1]
assert len(after['history'][-1]['levels'])==60 and len(after['history'][-1]['gates'])==5
assert (ROOT/'docs/ecossistema/BASELINE-2026-10-29.json').read_bytes()==git('show',BASE+':docs/ecossistema/BASELINE-2026-10-29.json')
expected={'motionpage':14,'pageframe':17,'pagepresent':9,'flowpage':17,'fluxstyle':17,'sanscript':9,'document-memory':12,'htdl-parser':16,'htdl-reader':10,'reader-transactions':15}
counts={}
for host in ('windows','linux'):
    report=json.loads((OUT/f'{host}.json').read_text());assert report['passed'] and report['base']==BASE
    assert {r['name'] for r in report['checks']}==set(expected)
    for record in report['checks']:
        skipped=0 if host=='windows' else {'pagepresent':6,'htdl-reader':3,'reader-transactions':4}.get(record['name'],0)
        assert record['returncode']==0 and record['not_run']==skipped and record['executed']==expected[record['name']]-skipped
        path=OUT/record['log'];assert sha(path)==record['sha256']
        assert re.search(rb'\nOK(?: \(skipped=\d+\))?\r?\n',path.read_bytes())
    examples=json.loads((OUT/f'{host}-examples.json').read_text(encoding='utf-8'))
    assert examples['passed'] and len(examples['examples'])==61 and examples['compilerSha256']==report['compiler_sha256']
    install=json.loads((OUT/f'{host}-install.json').read_text());assert install['passed'] and install['compiler_sha256']==report['compiler_sha256']
    assert set(install['selected_libraries'])=={'pagepresent','pageframe','flowpage','fluxstyle','sanscript','motionpage','htdl','documents','doctree','buffers','owned','unicode','graphemes','reader','viewer','window'}
    for record in install['checks']:
        assert record['returncode']==0
        if 'log' in record:assert sha(OUT/record['log'])==record['sha256']
    if host=='windows':assert sorted(r['executed'] for r in install['checks'] if 'executed' in r)==[4,23]
    counts[host]=dict(executed=sum(r['executed'] for r in report['checks']),not_run=sum(r['not_run'] for r in report['checks']),examples=61)
reference=json.loads((OUT/'reference-integrity.json').read_text(encoding='utf-8'));assert reference['integrity']=='pass' and reference['runtime_conformance']=='not-run'
desktop=json.loads((OUT/'desktop.json').read_text());assert desktop['status']=='not-run' and desktop['acceptance'] is False
coefficient=subprocess.run(['python' if __import__('os').name=='nt' else 'python3',str(ROOT/'tools/generate-ssc-coefficients.py'),'--check'],cwd=ROOT,capture_output=True,check=True)
sources=['.gitattributes','Makefile','.github/workflows/ci.yml','stdlib/sanscript.assis','stdlib/motionpage.assis','stdlib/pageframe.assis','stdlib/pagepresent.assis',
    'stdlib/catalogo.json','stdlib/catalogo.sh','src/install_files.inc','src/install_optional.inc','tests/test-motionpage.py','tests/test-pagepresent.py',
    'tools/collect-motionpage-evidence.py','tools/verify-motionpage-evidence.py','tools/verify-motionpage-install.py',
    'exemplos/58_page_motion.assis','exemplos/59_page_motion_window.assis','docs/BIBLIOTECA-motionpage.md','docs/ecossistema/PERFIL-MOVIMENTO-PAGINA-V1.md']
summary=dict(schema='motionpage-summary-v1',base=BASE,validation='pass',counts=counts,
    points_before='45.70',points_after='46.50',gates_passed=0,
    coefficient_validation=coefficient.stdout.decode().strip(),
    source_sha256={p:sha(ROOT/p) for p in sources},
    auxiliary_sha256={p.name:sha(p) for p in OUT.glob('*.json') if p.name!='summary.json'},
    limitations=['Finite 42-matrix SSC profile; no continuous physical domain or global error bound',
        'Bootstrap visual catalog; Reader selection, editing and IME are not integrated',
        'Host owns semantic focus, clock rebasing and non-dispatching publish/commit boundary',
        'Per-frame candidate allocation/work is bounded but no UI latency SLA or aggregate RSS quota is claimed',
        'No targetable desktop window after Computer Use app approval timed out; no screen reader, DPI, multiple monitor or IME acceptance',
        'Linux graphical provider unavailable; macOS and ARM native execution not-run',
        'No new 24h soak, third-party acceptance, release, merge or remote CI approval'])
path=OUT/'summary.json'
if args.write:path.write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
else:assert json.loads(path.read_text(encoding='utf-8'))==summary
print('Whole-page SSC evidence: sources, native results, 60 states, baseline and five unchanged gates verified')
