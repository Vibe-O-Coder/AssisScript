"""Audit exact native reading results, sources, rubric and preserved obligations."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'docs/ecossistema/evidencias/m5-frame-reader-2026-11-03'
BASE='a37a39a85a64e90543eecc668aeb796cee37b27e'
parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--write',action='store_true');args=parser.parse_args()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
git=lambda *parts:subprocess.check_output(['git',*parts],cwd=ROOT)
before=json.loads(git('show',BASE+':docs/ecossistema/PROGRESSO.json'))
after=json.loads((ROOT/'docs/ecossistema/PROGRESSO.json').read_text(encoding='utf-8'))
for old_group,new_group in zip(before['groups'],after['groups']):
    assert (old_group['id'],old_group['weight'],old_group['dependencies'])==(new_group['id'],new_group['weight'],new_group['dependencies'])
    for old,new in zip(old_group['items'],new_group['items']):
        assert (old['id'],old['name'],old['acceptance'])==(new['id'],new['name'],new['acceptance'])
        assert new['level']==old['level']+(1 if old['id'] in ('E00-04','E07-05') else 0)
assert before['gates']==after['gates'] and before['history']==after['history'][:-1]
assert len(after['history'][-1]['levels'])==60 and len(after['history'][-1]['gates'])==5
assert (ROOT/'docs/ecossistema/BASELINE-2026-10-29.json').read_bytes()==git('show',BASE+':docs/ecossistema/BASELINE-2026-10-29.json')
expected={'framereader':14,'framehost':12,'motionpage':14,'pageframe':17,'pagepresent':9,'flowpage':17,'fluxstyle':17,'sanscript':9,'document-memory':12,'htdl-parser':16,'htdl-reader':10,'reader-transactions':15}
counts={}
for host in ('windows','linux'):
    report=json.loads((OUT/f'{host}.json').read_text());assert report['passed'] and report['base']==BASE
    assert {r['name'] for r in report['checks']}==set(expected)
    for record in report['checks']:
        skipped=0 if host=='windows' else {'framereader':1,'framehost':2,'pagepresent':6,'htdl-reader':3,'reader-transactions':4}.get(record['name'],0)
        assert record['returncode']==0 and record['not_run']==skipped and record['executed']==expected[record['name']]-skipped,(host,record)
        path=OUT/record['log'];assert sha(path)==record['sha256']
        assert re.search(rb'\nOK(?: \(skipped=\d+\))?\r?\n',path.read_bytes())
    examples=json.loads((OUT/f'{host}-examples.json').read_text(encoding='utf-8'))
    assert examples['passed'] and len(examples['examples'])==63 and examples['compilerSha256']==report['compiler_sha256']
    install=json.loads((OUT/f'{host}-install.json').read_text());assert install['passed'] and install['compiler_sha256']==report['compiler_sha256']
    assert set(install['selected_libraries'])=={'framehost','pagepresent','framereader','pageframe','flowpage','fluxstyle','sanscript','motionpage','htdl','documents','doctree','buffers','owned','unicode','graphemes','reader','viewer','window'}
    for record in install['checks']:
        assert record['returncode']==0
        if 'log' in record:assert sha(OUT/record['log'])==record['sha256']
    if host=='windows':assert sorted(r['executed'] for r in install['checks'] if 'executed' in r)==[4,23]
    counts[host]=dict(executed=sum(r['executed'] for r in report['checks']),not_run=sum(r['not_run'] for r in report['checks']),examples=63)
reference=json.loads((OUT/'reference-integrity.json').read_text(encoding='utf-8'));assert reference['integrity']=='pass' and reference['runtime_conformance']=='not-run'
desktop=json.loads((OUT/'desktop.json').read_text());assert desktop['status']=='not-run' and desktop['acceptance'] is False
sources=['.gitattributes','Makefile','.github/workflows/ci.yml','stdlib/framereader.assis','stdlib/framehost.assis','stdlib/pagepresent.assis','stdlib/reader.assis',
    'stdlib/catalogo.json','stdlib/catalogo.sh','src/install_files.inc','src/install_optional.inc','tests/test-framereader.py','tests/test-framehost.py',
    'tools/collect-framereader-evidence.py','tools/verify-framereader-evidence.py','tools/verify-framereader-install.py',
    'exemplos/60_frame_reader.assis','exemplos/61_frame_reader_window.assis','docs/BIBLIOTECA-framereader.md','docs/BIBLIOTECA-framehost.md']
summary=dict(schema='frame-reading-summary-v1',base=BASE,validation='pass',counts=counts,
    points_before='46.50',points_after='47.10',gates_passed=0,
    source_sha256={p:sha(ROOT/p) for p in sources},
    auxiliary_sha256={p.name:sha(p) for p in OUT.glob('*.json') if p.name!='summary.json'},
    limitations=['Local bootstrap reading bundle; full visual HTDL catalog, external resource policy and ASV2 worker integration are separate',
        'Read-only grapheme selection, without shaping/bidi, editing, IME, OS DPI, real screen reader or multiple monitor acceptance',
        'Computer Use launched the target window, but both screenshot attempts timed out; no alternate capture or UI automation',
        'Host assigns the projection envelope; uncollected OS messages do not receive retroactive semantic timestamps',
        'Bounded graph/Frame/selection workspaces are not aggregate RSS quotas or UI latency guarantees',
        'OS slab refusal exercises finite supplies, not every logical allocation checkpoint',
        'Linux graphical provider unavailable; macOS and ARM native execution not-run',
        'No new 24h soak, third-party acceptance, release, merge or remote CI approval'])
path=OUT/'summary.json'
if args.write:path.write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
else:assert json.loads(path.read_text(encoding='utf-8'))==summary
print('Frame reading evidence: sources, native results, 60 states, baseline and five unchanged gates verified')
