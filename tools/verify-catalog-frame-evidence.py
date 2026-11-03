"""Verify native records, final source hashes, frozen baseline and exact rubric delta."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'docs/ecossistema/evidencias/m3-catalog-frame-2026-11-03'
BASE='6f4398c830fadde4d809bbbac104a1fa4f22c711'
parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--write',action='store_true');args=parser.parse_args()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
git=lambda *parts:subprocess.check_output(['git',*parts],cwd=ROOT)
before=json.loads(git('show',BASE+':docs/ecossistema/PROGRESSO.json'))
after=json.loads((ROOT/'docs/ecossistema/PROGRESSO.json').read_text(encoding='utf-8'))
assert after['gates']==before['gates'] and not any(g['passed'] for g in after['gates'])
changes={}
for old,new in zip(before['groups'],after['groups']):
    assert (old['id'],old['weight'],old['dependencies'])==(new['id'],new['weight'],new['dependencies'])
    for a,b in zip(old['items'],new['items']):
        assert (a['id'],a['name'],a['acceptance'])==(b['id'],b['name'],b['acceptance'])
        if a['level']!=b['level']:changes[a['id']]=(a['level'],b['level'])
assert changes=={'E07-02':(2,3)}
assert after['history'][:-1]==before['history']
assert after['history'][-1]['levels']=={c['id']:c['level'] for g in after['groups'] for c in g['items']}
assert after['history'][-1]['gates']=={g['id']:g['passed'] for g in after['gates']}
assert (ROOT/'docs/ecossistema/BASELINE-2026-10-29.json').read_bytes()==git('show',BASE+':docs/ecossistema/BASELINE-2026-10-29.json')
suites={'catalog-frame','htdl-catalog','framereader','framehost','motionpage','pageframe','pagepresent','flowpage','fluxstyle','sanscript','document-memory','htdl-parser','htdl-reader','reader-transactions'}
counts={}
for host in ['windows','linux']:
    report=json.loads((OUT/f'{host}.json').read_text(encoding='utf-8'))
    assert report['passed'] and report['base']==BASE and {c['name'] for c in report['checks']}==suites and len(report['checks'])==len(suites)
    for c in report['checks']:
        assert c['returncode']==0 and c['executed']>0 and sha(OUT/c['log'])==c['sha256']
        data=(OUT/c['log']).read_bytes();ran=re.search(rb'Ran (\d+) tests? in',data);skipped=re.search(rb'skipped=(\d+)',data)
        assert ran and int(ran[1])==c['executed']+c['not_run'] and (int(skipped[1]) if skipped else 0)==c['not_run']
        assert re.search(rb'\bOK\b',data) and b'FAILED (' not in data
    assert next(c for c in report['checks'] if c['name']=='catalog-frame')['executed']==(21 if host=='windows' else 18)
    examples=json.loads((OUT/f'{host}-examples.json').read_text(encoding='utf-8'))
    assert examples['passed'] and len(examples['examples'])==65 and examples['compilerSha256']==report['compiler_sha256']
    install=json.loads((OUT/f'{host}-install.json').read_text(encoding='utf-8'))
    assert install['passed'] and install['compiler_sha256']==report['compiler_sha256'] and len(install['selected_libraries'])==18
    for c in install['checks']:
        assert c['returncode']==0
        if 'log' in c:assert sha(OUT/c['log'])==c['sha256']
    if host=='windows':
        assert install['provider_sha256'] and sorted(c['executed'] for c in install['checks'] if 'executed' in c)==[4,23]
    counts[host]=dict(executed=sum(c['executed'] for c in report['checks']),not_run=sum(c['not_run'] for c in report['checks']),examples=65)
assert counts=={'windows':{'executed':199,'not_run':0,'examples':65},'linux':{'executed':180,'not_run':19,'examples':65}}
bundle=json.loads((OUT/'development-bundle.json').read_text(encoding='utf-8'))
assert bundle['installation_validation']=='pass' and bundle['release'] is False
assert bundle['compiler_sha256']==json.loads((OUT/'windows.json').read_text())['compiler_sha256']
assert re.fullmatch('[0-9a-f]{64}',bundle['provider_sha256'])
info=json.loads((ROOT/'build/catalog-development-windows-20261103/BUILD-INFO.json').read_text(encoding='utf-8'))
assert info['provider_sha256']==bundle['provider_sha256'] and info['installation_validation']=='pass'
for p,digest in info['source_sha256'].items():assert sha(ROOT/p)==digest
for p,digest in info['files_sha256'].items():assert sha(ROOT/'build/catalog-development-windows-20261103'/p)==digest
reference=json.loads((OUT/'reference-integrity.json').read_text(encoding='utf-8'))
assert reference['integrity']=='pass' and reference['runtime_conformance']=='not-run'
desktop=json.loads((OUT/'desktop.json').read_text(encoding='utf-8'));assert desktop['status']=='not-run' and desktop['acceptance'] is False and desktop['screenshots']==0
sources=['.gitattributes','.github/workflows/ci.yml','Makefile','stdlib/pageframe.assis','stdlib/framereader.assis','stdlib/framehost.assis','stdlib/pagepresent.assis',
    'providers/platform/windows.c','providers/platform/reader.inc','providers/platform/frame.inc','providers/platform/assis_platform_v1.h',
    'stdlib/catalogo.json','stdlib/catalogo.sh','src/install_files.inc','src/install_optional.inc','tests/test-catalog-frame.py','tests/catalog_frame_oracle.c',
    'tests/test-framereader.py','exemplos/62_catalog_reader.assis','exemplos/63_catalog_reader_window.assis',
    'tools/collect-catalog-frame-evidence.py','tools/verify-catalog-frame-evidence.py','tools/verify-catalog-frame-install.py','tools/prepare-development-installer.py',
    'docs/ecossistema/PERFIL-LEITURA-CATALOGO-V1.md','docs/ecossistema/ABI-PLATAFORMA-V1.md','docs/BIBLIOTECA-pageframe.md',
    'docs/BIBLIOTECA-pagepresent.md','docs/BIBLIOTECA-framereader.md','docs/BIBLIOTECA-framehost.md']
summary=dict(schema='catalog-reading-summary-v1',base=BASE,validation='pass',counts=counts,
    points_before='47.10',points_after='47.50',gates_passed=0,
    source_sha256={p:sha(ROOT/p) for p in sources},auxiliary_sha256={p.name:sha(p) for p in OUT.glob('*.json') if p.name!='summary.json'},
    prior_failed_run_sha256=sha(OUT/'windows-initial-pagepresent-failure.log'),
    limitations=['18-type local reading subset; script, label/input/form/image, live regions and full HTDL visual compliance remain open',
        'Fragment links only; external resources, file paths/URLs and ASV2 integration are separate',
        'Flat MSAA projection; desktop launch timed out, with no real screen reader, DPI, IME, multiple monitor or complete assistive hierarchy acceptance',
        'Local workspace/scan/command limits are not aggregate RSS quotas, UI latency guarantees or per-logical-allocation OOM injection',
        'Only Windows/Linux x64 executed; native macOS/ARM and Linux graphical provider not-run',
        'Development package installed/run/removed in isolated prefixes; no global installation, release, merge, new remote CI or 24h soak'])
path=OUT/'summary.json'
if args.write:path.write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
else:assert json.loads(path.read_text(encoding='utf-8'))==summary
print('Catalog reading: exact sources/results, baseline, 60 states and five gates verified')
