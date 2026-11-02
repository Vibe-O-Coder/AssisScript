"""Check native results, frozen rubric weights, trace equivalence and source hashes."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT=Path(__file__).resolve().parent.parent;OUT=ROOT/'docs/ecossistema/evidencias/m3-presentation-core-2026-11-02'
parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--write',action='store_true');args=parser.parse_args()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
base=json.loads(subprocess.check_output(['git','show','6701d1b6d67687144606c03e2431c0f5a6ddf313:docs/ecossistema/PROGRESSO.json'],cwd=ROOT))
current=json.loads((ROOT/'docs/ecossistema/PROGRESSO.json').read_text(encoding='utf-8'))
for before,after in zip(base['groups'],current['groups']):
    assert (before['id'],before['weight'],before['dependencies'])==(after['id'],after['weight'],after['dependencies'])
    for a,b in zip(before['items'],after['items']):
        assert (a['id'],a['acceptance'],a['name'])==(b['id'],b['acceptance'],b['name'])
        assert b['level']==(2 if a['id'] in ['E08-01','E08-03'] else a['level'])
assert current['gates']==base['gates'] and current['history'][:-1]==base['history']
counts={}
for host in ['windows','linux']:
    data=json.loads((OUT/f'{host}.json').read_text());assert data['passed']
    expected={'fluxstyle':17,'sanscript':9,'install-mask':2}
    assert {x['name'] for x in data['checks']}==set(expected)
    for check in data['checks']:
        assert check['returncode']==0 and check['not_run']==0 and check['executed']==expected[check['name']]
        log=OUT/check['log'];assert sha(log)==check['sha256'] and re.search(rb'\nOK\r?\n',log.read_bytes())
    examples=json.loads((OUT/f'{host}-examples.json').read_text());assert examples['passed'] and len(examples['examples'])==56
    install=json.loads((OUT/f'{host}-install.json').read_text());assert install['passed'] and all(x['returncode']==0 for x in install['checks'])
    assert set(install['selected_libraries'])=={'sanscript','fluxstyle','htdl','documents','doctree','buffers','unicode','owned'}
    traces=json.loads((OUT/f'{host}-ssc-traces.json').read_text());assert len(traces['rows'])==42 and traces['max_error_8px']<1/16
    for mode in ['optimized','reference']:
        assert (OUT/f'{host}-example-54-{mode}.log').read_bytes()==b'FLOW-TARGET -524288\nSSC-REST -524288 true\n'
    counts[host]=dict(native_methods=sum(x['executed'] for x in data['checks']),not_run=0,examples=56)
win=json.loads((OUT/'windows-install.json').read_text())
reproduction=json.loads((OUT/'windows.json').read_text())['import_reproduction']
assert len(reproduction['checks'])==2 and all([x['returncode'] for x in check['runs']]==[1,0] for check in reproduction['checks'])
node=next(x for x in win['checks'] if 'executed' in x)
assert node['executed']==23 and sha(OUT/node['log'])==node['sha256']
a=json.loads((OUT/'windows-ssc-traces.json').read_text());b=json.loads((OUT/'linux-ssc-traces.json').read_text())
assert [x['trace_sha256'] for x in a['rows']]==[x['trace_sha256'] for x in b['rows']]
sources=['.github/workflows/ci.yml','stdlib/fluxstyle.assis','stdlib/sanscript.assis','stdlib/catalogo.json','stdlib/catalogo.sh','src/windows_setup.c','src/install_optional.inc',
         'tests/fixtures/fluxstyle-driver.assis','tests/fixtures/sanscript-driver.assis','tests/fixtures/ssc-coefficients.json',
         'tests/test-fluxstyle.py','tests/test-sanscript.py','tests/test-install-mask.py','tests/test-v31.js','exemplos/54_fluxstyle_sanscript.assis',
         'tools/generate-install-manifest.py','tools/generate-ssc-coefficients.py','tools/collect-presentation-core-evidence.py','tools/verify-presentation-install.py',
         'tools/verify-presentation-core-evidence.py','docs/ecossistema/PERFIL-APRESENTACAO-LOCAL-V1.md','docs/BIBLIOTECA-fluxstyle.md','docs/BIBLIOTECA-sanscript.md']
summary=dict(schema='presentation-core-summary-v1',base='6701d1b6d67687144606c03e2431c0f5a6ddf313',counts=counts,windows_distribution_node=23,
    points_before='43.30',points_after='44.90',gates_passed=0,max_error_8px=a['max_error_8px'],trace_scope='42 grid pairs, 8px step over 3 seconds only',
    source_sha256={p:sha(ROOT/p) for p in sources},
    limitations=['SSC finite 42-pair profile; no intermediate parameter promise','No full-page presentation transaction','No incremental dirtiness between transactions',
        'No renderer/layout/hit-test/accessibility snapshot integration','No aggregate channel/RSS quota','No remote loader or authority change','ARM/macOS generation only; native execution not-run','No desktop/IME/screen-reader or 24h acceptance',
        'Publication blocked pending explicit user approval; no merge/release/remote CI claim'])
path=OUT/'summary.json'
if args.write:path.write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8',newline='\n')
else:assert json.loads(path.read_text())==summary,'Evidence or source hash changed'
print(json.dumps(counts)+'; 43.30 -> 44.90%, 0/5 gates')
