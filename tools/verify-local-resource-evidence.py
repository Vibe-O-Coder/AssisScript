"""Verify resource/UI evidence, immutable rubric scope, hashes and real skips."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'docs/ecossistema/evidencias/m3-local-resources-2026-11-04'
BASE='33b7431da1e84c8cdc26a8639290e42ba5a14e72'
parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--write',action='store_true');args=parser.parse_args()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda name:json.loads((OUT/name).read_text(encoding='utf-8'))
git=lambda *parts:subprocess.check_output(['git',*parts],cwd=ROOT)
before=json.loads(git('show',BASE+':docs/ecossistema/PROGRESSO.json'))
after=json.loads((ROOT/'docs/ecossistema/PROGRESSO.json').read_text(encoding='utf-8'));changes={}
for old,new in zip(before['groups'],after['groups']):
    assert (old['id'],old['weight'],old['dependencies'])==(new['id'],new['weight'],new['dependencies'])
    for a,b in zip(old['items'],new['items']):
        assert (a['id'],a['name'],a['acceptance'])==(b['id'],b['name'],b['acceptance'])
        if a['level']!=b['level']:changes[a['id']]=[a['level'],b['level']]
assert changes=={'E08-05':[1,2]}
assert before['gates']==after['gates'] and not any(g['passed'] for g in after['gates'])
assert after['history'][:-1]==before['history']
assert after['history'][-1]['levels']=={i['id']:i['level'] for g in after['groups'] for i in g['items']}
assert after['history'][-1]['gates']=={g['id']:g['passed'] for g in after['gates']}
assert (ROOT/'docs/ecossistema/BASELINE-2026-10-29.json').read_bytes()==git('show',BASE+':docs/ecossistema/BASELINE-2026-10-29.json')
expected={(s,m) for s in ('page-resources','frame-worker') for m in ('optimized','reference')}|{(s,'optimized') for s in ('frame-responsiveness','framehost','framereader','catalog-frame','reader-transactions','motionpage','pagepresent','install-mask')}
hosts={}
for host in ('windows','linux'):
    native=read(host+'.json');assert native['passed'] and native['base']==BASE
    assert len(native['checks'])==len(expected) and {(r['suite'],r['worker_mode']) for r in native['checks']}==expected
    for record in native['checks']:
        log=(OUT/record['log']).read_bytes();assert record['returncode']==0 and sha(OUT/record['log'])==record['sha256']
        total=re.search(rb'Ran (\d+) tests? in',log);skipped=re.search(rb'skipped=(\d+)',log)
        assert total and int(total[1])==record['executed']+record['not_run']
        assert record['not_run']==(int(skipped[1]) if skipped else 0)
        if record['executed']==0:assert host=='linux' and record['suite']=='frame-responsiveness' and record['not_run']==5
    examples=read(host+'-examples.json');assert examples['passed'] and examples['compilerSha256']==native['compiler_sha256']
    assert len(examples['examples'])==69 and all(r['passed'] for r in examples['examples'])
    assert {r['ending'] for r in examples['rpg']}=={'victory','defeat'}
    install=read(host+'-install.json');assert install['passed'] and install['compiler_sha256']==native['compiler_sha256']
    assert 'pageresources' in install['selected_libraries'] and 'frameworker' in install['selected_libraries']
    assert len(install['selected_libraries'])==24
    for record in install['checks']:
        assert record['returncode']==0
        if 'log' in record:assert sha(OUT/record['log'])==record['sha256']
    hosts[host]=dict(executed=sum(r['executed'] for r in native['checks']),not_run=sum(r['not_run'] for r in native['checks']),examples=69,libraries=24,compiler_sha256=native['compiler_sha256'])
response=read('response.json');assert response['passed'] and response['base']==BASE and response['compiler_sha256']==hosts['windows']['compiler_sha256']
for version in response['comparisons'].values():
    for demo in version['demos'].values():assert sha(OUT/demo['log'])==demo['log_sha256']
desktop=read('desktop.json');assert desktop['automatic_capture']['screenshots']==0 and desktop['automatic_capture']['inputs']==0
assert desktop['manual']['reading_counter_shortcuts']=='accepted-by-user'
bundle=read('development-bundle.json');assert bundle['installation_validation']=='pass' and not bundle['release']
assert bundle['compiler_sha256']==hosts['windows']['compiler_sha256']
sources=['stdlib/'+name+'.assis' for name in ('pageresources','frameworker','framehost','framereader','pagepresent','motionpage','sanscript')]
sources+=['providers/platform/'+name for name in ('windows.c','frame.inc','assis_platform_v1.h')]
sources+=['tests/'+name for name in ('test-page-resources.py','test-frame-responsiveness.py','test-framehost.py','test-motionpage.py')]
sources+=['exemplos/'+name for name in ('59_page_motion_window.assis','65_frame_worker_window.assis','66_resource_frame.assis','67_resource_frame_window.assis')]
sources += [p.relative_to(ROOT).as_posix() for p in sorted((ROOT/'exemplos/resource-demo').iterdir()) if p.is_file()]
sources+=['stdlib/catalogo.json','stdlib/catalogo.sh','src/install_files.inc','src/install_optional.inc','Makefile','.github/workflows/ci.yml','tools/collect-local-resource-evidence.py','tools/verify-local-resource-evidence.py','tools/verify-local-resource-install.py','tools/prepare-development-installer.py','tools/measure-frame-response.py','docs/BIBLIOTECA-pageresources.md','docs/ecossistema/PERFIL-RECURSOS-LOCAIS-V1.md']
summary=dict(schema='local-resource-evidence-v1',base=BASE,points_before=47.90,points_after=48.30,level_changes=changes,gates_passed=0,native=hosts,
    source_sha256={name:sha(ROOT/name) for name in sources},auxiliary_sha256={p.name:sha(p) for p in sorted(OUT.glob('*.json')) if p.name not in ('summary.json','publication.json')},
    limitations=['Local immutable batches and explicit OS file grants; no directory-root confinement, symlink/TOCTOU guarantee, src/import resolver or network','ASCII logical keys and host-only opaque data; SDK strings/cells/subscriptions/mutations and controls/images/live regions remain open','Manual reading/counter/shortcuts acceptance is separate from absent desktop screenshots, screen reader, DPI/multiple monitors and IME','One Windows timing comparison; not a universal latency/FPS or 24h promise','Windows/Linux x64 native; graphics Linux and ARM/macOS native remain not-run','Matched Windows development bundle; no release, merge or new remote CI approval'])
rendered=json.dumps(summary,ensure_ascii=False,indent=2)+'\n'
if args.write:(OUT/'summary.json').write_text(rendered,encoding='utf-8',newline='\n')
else:assert (OUT/'summary.json').read_text(encoding='utf-8')==rendered,'Evidence changed; inspect before regenerating'
print(json.dumps(dict(native=hosts,points=48.30,gates=0),indent=2))
