"""Verify exact source/log hashes, native counts and the frozen rubric delta."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'docs/ecossistema/evidencias/m3-frame-worker-2026-11-03'
BASE='52ef3ead2e059395dafb17771214126f578ed19c'
parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--write',action='store_true');args=parser.parse_args()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
git=lambda *parts:subprocess.check_output(['git',*parts],cwd=ROOT)
before=json.loads(git('show',BASE+':docs/ecossistema/PROGRESSO.json'))
after=json.loads((ROOT/'docs/ecossistema/PROGRESSO.json').read_text(encoding='utf-8'))
changes={}
for a,b in zip(before['groups'],after['groups']):
    assert (a['id'],a['weight'],a['dependencies'])==(b['id'],b['weight'],b['dependencies'])
    for x,y in zip(a['items'],b['items']):
        assert (x['id'],x['name'],x['acceptance'])==(y['id'],y['name'],y['acceptance'])
        if x['level']!=y['level']:changes[x['id']]=[x['level'],y['level']]
assert changes=={'E07-04':[2,3]}
assert after['gates']==before['gates'] and not any(g['passed'] for g in after['gates'])
assert after['history'][:-1]==before['history']
assert after['history'][-1]['levels']=={i['id']:i['level'] for g in after['groups'] for i in g['items']}
assert after['history'][-1]['gates']=={g['id']:g['passed'] for g in after['gates']}
assert (ROOT/'docs/ecossistema/BASELINE-2026-10-29.json').read_bytes()==git('show',BASE+':docs/ecossistema/BASELINE-2026-10-29.json')
expected={(s,m) for s,m in [('frame-worker','optimized'),('frame-worker','reference'),('page-worker','optimized'),('page-worker','reference'),('page-reader','optimized'),('page-reader','reference')]}|{(s,'optimized') for s in ['page-compiler','page-host','page-backend','pagevm','windows-isolation','framehost','catalog-frame','install-mask']}
hosts={}
for host in ('windows','linux'):
    native=json.loads((OUT/f'{host}.json').read_text(encoding='utf-8'))
    assert native['passed'] and native['base']==BASE
    assert {(r['suite'],r['worker_mode']) for r in native['checks']}==expected and len(native['checks'])==len(expected)
    for record in native['checks']:
        assert record['returncode']==0 and sha(OUT/record['log'])==record['sha256']
        log=(OUT/record['log']).read_bytes();ran=re.search(rb'Ran (\d+) tests? in',log);skipped=re.search(rb'skipped=(\d+)',log)
        assert ran and int(ran[1])==record['executed']+record['not_run']
        assert (int(skipped[1]) if skipped else 0)==record['not_run']
        if record['executed']==0:assert host=='linux' and record['suite']=='windows-isolation' and record['not_run']==4 and record['status']=='not-run'
    examples=json.loads((OUT/f'{host}-examples.json').read_text(encoding='utf-8'))
    assert examples['passed'] and examples['compilerSha256']==native['compiler_sha256'] and len(examples['examples'])==67
    assert all(x['passed'] for x in examples['examples']) and {r['ending'] for r in examples['rpg']}=={'victory','defeat'}
    install=json.loads((OUT/f'{host}-install.json').read_text(encoding='utf-8'))
    assert install['passed'] and install['compiler_sha256']==native['compiler_sha256']
    assert 'frameworker' in install['selected_libraries'] and install['runtime_sha256']
    for record in install['checks']:
        assert record['returncode']==0
        if 'log' in record:assert sha(OUT/record['log'])==record['sha256']
    hosts[host]=dict(executed=sum(r['executed'] for r in native['checks']),not_run=sum(r['not_run'] for r in native['checks']),examples=len(examples['examples']),libraries=len(install['selected_libraries']),compiler_sha256=native['compiler_sha256'],record_sha256=sha(OUT/f'{host}.json'))
desktop=json.loads((OUT/'desktop.json').read_text());assert desktop['status']=='not-run' and desktop['screenshots']==0 and desktop['inputs']==0
bundle=json.loads((OUT/'development-bundle.json').read_text());assert bundle['installation_validation']=='pass' and not bundle['release'] and bundle['compiler_sha256']==hosts['windows']['compiler_sha256']
files=['stdlib/frameworker.assis','stdlib/pageworker.assis','stdlib/pagehost.assis','stdlib/pageframe.assis','stdlib/framehost.assis','stdlib/pagepresent.assis','stdlib/framereader.assis','stdlib/pagecompiler.assis','stdlib/pagewire.assis','stdlib/catalogo.json','stdlib/catalogo.sh','tools/page-worker.assis','tests/test-frame-worker.py','tests/test-page-worker.py','exemplos/64_frame_worker.assis','exemplos/65_frame_worker_window.assis','tools/collect-frame-worker-evidence.py','tools/verify-frame-worker-evidence.py','tools/verify-frame-worker-install.py','tools/prepare-development-installer.py','docs/BIBLIOTECA-frameworker.md','docs/ecossistema/PERFIL-FRAME-WORKER-V1.md']
summary=dict(schema='frame-worker-evidence-v1',base=BASE,points_before=47.50,points_after=47.90,level_changes=changes,gates_passed=0,native=hosts,source_sha256={name:sha(ROOT/name) for name in files},auxiliary_sha256={p.name:sha(p) for p in sorted(OUT.glob('*.json')) if p.name!='summary.json'},initial_fixture_failures_sha256={p.name:sha(p) for p in sorted(OUT.glob('*initial*.log'))},limitations=['Local scalar ASV2/read-only SDK; per-node cells, subscriptions, strings and visual mutation remain open','External resources, complete HTDL controls/images/live regions, network/profile/search are separate','Both Computer Use captures of previous catalog demo timed out; new window has native once/smoke tests only, no desktop/screen-reader/DPI/IME acceptance','Windows/Linux x64 native only; Windows-isolation is not-run on Linux, Linux graphical tests and native ARM/macOS are not-run','Slab refusal supplies 0/1/2/4/8 are not exhaustive per-allocation failure injection or aggregate RSS quotas','Linux installer selects compiler/libraries; native worker/provider explicitly granted and staged separately','Matched Windows development package is not a release, merge, new CI approval, third-party acceptance or 24h soak'])
path=OUT/'summary.json';rendered=json.dumps(summary,ensure_ascii=False,indent=2)+'\n'
if args.write:path.write_text(rendered,encoding='utf-8',newline='\n')
else:assert path.read_text(encoding='utf-8')==rendered,'Evidence changed; inspect and regenerate summary'
print(json.dumps(dict(native=hosts,points=47.90,gates=0),indent=2))
