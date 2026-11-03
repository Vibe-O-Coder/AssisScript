"""Verify native evidence, preserved rubric, baseline and exact source hashes."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'docs/ecossistema/evidencias/m5-page-frame-2026-11-02'
BASE='542827e43143c94a977d26e116308036cefc7f1d'
parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--write',action='store_true')
parser.add_argument('--allow-incomplete',action='store_true',help='Record pending distribution checks explicitly; never label the whole delivery passed')
args=parser.parse_args()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
git=lambda *parts:subprocess.check_output(['git',*parts],cwd=ROOT)
before=json.loads(git('show',BASE+':docs/ecossistema/PROGRESSO.json'))
after=json.loads((ROOT/'docs/ecossistema/PROGRESSO.json').read_text(encoding='utf-8'))
for old_group,new_group in zip(before['groups'],after['groups']):
    assert (old_group['id'],old_group['weight'],old_group['dependencies'])==(new_group['id'],new_group['weight'],new_group['dependencies'])
    for old,new in zip(old_group['items'],new_group['items']):
        assert (old['id'],old['name'],old['acceptance'])==(new['id'],new['name'],new['acceptance'])
        assert new['level']==old['level']+(1 if old['id']=='E08-02' else 0)
assert before['gates']==after['gates'] and before['history']==after['history'][:-1]
assert len(after['history'][-1]['levels'])==60 and len(after['history'][-1]['gates'])==5
assert (ROOT/'docs/ecossistema/BASELINE-2026-10-29.json').read_bytes()==git('show',BASE+':docs/ecossistema/BASELINE-2026-10-29.json')
expected={'pageframe':17,'pagepresent':6,'flowpage':17,'fluxstyle':17,'sanscript':9,'document-memory':12,'htdl-parser':16,'htdl-reader':10,'reader-transactions':15}
counts={};pending=[]
for host in ['windows','linux']:
    report=json.loads((OUT/f'{host}.json').read_text());assert report['passed'] and report['base']==BASE
    assert {r['name'] for r in report['checks']}==set(expected)
    for record in report['checks']:
        skipped=0 if host=='windows' else {'pagepresent':4,'htdl-reader':3,'reader-transactions':4}.get(record['name'],0)
        assert record['returncode']==0 and record['not_run']==skipped and record['executed']==expected[record['name']]-skipped
        path=OUT/record['log'];assert sha(path)==record['sha256'] and re.search(rb'\nOK(?: \(skipped=\d+\))?\r?\n',path.read_bytes())
    examples_path=OUT/f'{host}-examples.json';install_path=OUT/f'{host}-install.json'
    if examples_path.exists():
        examples=json.loads(examples_path.read_text());assert examples['passed'] and len(examples['examples'])==59
    else:pending.append(f'{host}: 59-example final matrix')
    if install_path.exists():
        install=json.loads(install_path.read_text());assert install['passed'] and install['compiler_sha256']==report['compiler_sha256']
        assert set(install['selected_libraries'])=={'pagepresent','pageframe','flowpage','fluxstyle','htdl','documents','doctree','buffers','owned','unicode','graphemes','reader','viewer','window'}
        for record in install['checks']:
            assert record['returncode']==0
            if 'log' in record:assert sha(OUT/record['log'])==record['sha256']
        if host=='windows':assert sorted(r['executed'] for r in install['checks'] if 'executed' in r)==[4,23]
    else:pending.append(f'{host}: isolated installation/run/uninstall and applicable installer/Node checks')
    counts[host]=dict(executed=sum(r['executed'] for r in report['checks']),not_run=sum(r['not_run'] for r in report['checks']),examples=59 if examples_path.exists() else 'not-run')
bundle=json.loads((OUT/'development-bundle.json').read_text())
if bundle['installation_validation']!='pass':pending.append('Matched Windows development bundle installation validation')
if pending and not args.allow_incomplete:raise AssertionError('Pending checks: '+'; '.join(pending))
reference=json.loads((OUT/'reference-integrity.json').read_text());assert reference['integrity']=='pass' and reference['runtime_conformance']=='not-run'
desktop=json.loads((OUT/'desktop.json').read_text());assert desktop['status']=='not-run' and desktop['acceptance'] is False
sources=['.gitattributes','Makefile','.github/workflows/ci.yml','instalar-windows.cmd','stdlib/flowpage.assis','stdlib/pageframe.assis','stdlib/pagepresent.assis',
    'stdlib/catalogo.json','stdlib/catalogo.sh','src/install_files.inc','src/install_optional.inc','providers/platform/windows.c',
    'providers/platform/assis_platform_v1.h','providers/platform/frame.inc','tests/test-pageframe.py','tests/test-pagepresent.py',
    'tools/collect-pageframe-evidence.py','tools/verify-pageframe-evidence.py','tools/verify-pageframe-install.py','tools/prepare-development-installer.py',
    'exemplos/56_page_frame.assis','exemplos/57_page_frame_window.assis','docs/BIBLIOTECA-pageframe.md','docs/BIBLIOTECA-pagepresent.md',
    'docs/ecossistema/PERFIL-FRAME-LOCAL-V1.md']
summary=dict(schema='pageframe-summary-v1',base=BASE,validation='partial' if pending else 'pass',pending=pending,counts=counts,
    points_before='45.30',points_after='45.70',gates_passed=0,
    source_sha256={p:sha(ROOT/p) for p in sources},
    auxiliary_sha256={p.name:sha(p) for p in OUT.glob('*.json') if p.name!='summary.json'},
    limitations=['Bootstrap visual catalog; no images, styled inline runs or rounded corners',
        'Independent nested scroll, automatic FS parent.availableWidth and layout-wide incremental invalidation remain open',
        'SSC aggregate quota/channels and Reader selection integration are not implemented by this unit',
        'Integer-pixel layout; OS-specific font metrics; no cross-platform pixel equality promised',
        'Desktop Computer Use did not expose a targetable window; no desktop, screen reader, DPI, multi-monitor or IME acceptance',
        'Linux graphical provider unavailable; macOS and ARM native execution not-run',
        'No new 24h soak, third-party acceptance, release, merge or remote CI approval'])
path=OUT/'summary.json'
if args.write:path.write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
else:assert json.loads(path.read_text(encoding='utf-8'))==summary
print('Frame evidence: native sources/results and unchanged rubric verified; delivery '+summary['validation'])
