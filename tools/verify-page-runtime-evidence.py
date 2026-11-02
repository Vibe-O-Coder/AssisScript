"""Verify fresh execution logs, immutable rubric history and source provenance."""
import argparse
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'docs/ecossistema/evidencias/m0-page-runtime-2026-11-02'
BASE='1e574736ce33a16e442fb270e9d42c8c884d29f6'
CHANGES={'E00-02':[1,2],'E00-03':[1,2],'E03-02':[1,2],'E06-01':[1,2],
    'E06-03':[1,2],'E06-05':[0,2],'E07-03':[0,2],'E07-05':[1,2]}
parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--write',action='store_true');args=parser.parse_args()
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def canonical(path):return hashlib.sha256(path.read_bytes().replace(b'\r\n',b'\n')).hexdigest()
def levels(data):return {i['id']:i['level'] for g in data['groups'] for i in g['items']}
def score(data):return sum(Decimal(g['weight'])*sum(i['level'] for i in g['items'])/20 for g in data['groups'])
base=json.loads(subprocess.check_output(['git','show',BASE+':docs/ecossistema/PROGRESSO.json'],cwd=ROOT))
current=json.loads((ROOT/'docs/ecossistema/PROGRESSO.json').read_text(encoding='utf-8'))
changes={key:[levels(base)[key],value] for key,value in levels(current).items() if levels(base)[key]!=value}
assert changes==CHANGES,changes
assert score(base)==Decimal('32.10') and score(current)==Decimal('36.20')
assert current['history'][:-1]==base['history'] and current['gates']==base['gates']
assert len(levels(current))==60 and not any(g['passed'] for g in current['gates'])
for left,right in zip(base['groups'],current['groups']):
    assert (left['id'],left['weight'],left['dependencies'])==(right['id'],right['weight'],right['dependencies'])
    for a,b in zip(left['items'],right['items']):assert (a['id'],a['name'],a['acceptance'])==(b['id'],b['name'],b['acceptance'])
assert subprocess.check_output(['git','show',BASE+':docs/ecossistema/BASELINE-2026-10-29.json'],cwd=ROOT).replace(b'\r\n',b'\n')==(ROOT/'docs/ecossistema/BASELINE-2026-10-29.json').read_bytes().replace(b'\r\n',b'\n')
hosts={}
for host,expected in [('windows',(238,1)),('linux',(210,29))]:
    data=json.loads((OUT/f'{host}.json').read_text(encoding='utf-8'));assert data['passed']
    assert len({c['name'] for c in data['checks']})==len(data['checks'])==20
    for check in data['checks']:assert check['returncode']==0 and sha(OUT/check['log'])==check['log_sha256'],check
    count=sum(c['executed'] for c in data['checks']);not_run=sum(c['not_run'] for c in data['checks'])
    assert (count,not_run)==expected
    example=json.loads((OUT/f'{host}-examples.json').read_text(encoding='utf-8'))
    assert example['passed'] and len(example['examples'])==50 and {r['ending'] for r in example['rpg']}=={'victory','defeat'}
    assert example['compilerSha256']==data['compiler_sha256']
    hosts[host]=dict(executed=count,not_run=not_run,compiler_sha256=data['compiler_sha256'],checked_examples=50)
node=json.loads((OUT/'windows-node.json').read_text(encoding='utf-8'))
assert node['passed'] and node['tests']==23 and sha(OUT/'windows-node.log')==node['log_sha256']
assert node['compiler_sha256']==hosts['windows']['compiler_sha256']
before=json.loads((OUT/'before.json').read_text(encoding='utf-8'))
assert before['base']==BASE and all(c['returncode']!=0 for c in before['checks'])
if args.write:
    paths=list((ROOT/'stdlib').glob('*.assis'))+list((ROOT/'src').glob('*.h'))+list((ROOT/'src').glob('*.c'))+list((ROOT/'src').glob('*.inc'))
    paths+=list(OUT.glob('*'))
    paths += [ROOT/p for p in ['tests/test-page-backend.py','tests/test-page-host.py','tests/test-pagevm.py','tests/test-english-api.py','tests/test-v31.js',
        'tools/collect-page-runtime-evidence.py','tools/capture-page-runtime-before.py','tools/verify-page-runtime-evidence.py','tools/verify-page-runtime-publication.py','tools/test-native.py','tools/stage-page-runtime-installer.py',
        'docs/ecossistema/PERFIL-PAGINA-ASV2.md','docs/ecossistema/AMEACAS-PAGINA-LOCAL-V1.md','docs/ecossistema/ADR-0001-EXECUCAO-PAGINA.md',
        'docs/BIBLIOTECA-page.md','docs/BIBLIOTECA-pagevm.md','docs/BIBLIOTECA-pagehost.md','docs/ecossistema/PROGRESSO.json','docs/ecossistema/PROGRESSO.md',
        'docs/relatorios/2026-11-02-m0-page-runtime.md','exemplos/pages/counter.assis','exemplos/48_page_runtime.assis','Makefile']]
    paths=[p for p in paths if p.is_file() and p.name not in ('summary.json','published-implementation.json')]
    data=dict(schema='assisscript-page-runtime-evidence-v1',base=BASE,branch='work/m0-page-runtime-2026-11-01',
        before='32.10',after='36.20',changed_levels=changes,gates_passed=0,hosts=hosts,node_tests=23,
        new_test_methods=dict(backend=10,host=13),
        scope='Experimental scalar ASV2 backend, pointer-free htdl_v1 read-only-1 SDK, immutable local HTDL projection and cooperative Page/Group lifecycle in AssisScript',
        failed_attempts=['alias-before.log reproduced excess hard-link imports before the final guard',
            'windows-cleanup-attempt.json records a failed temporary executable cleanup; the affected suite was rerun without weakening assertions'],
        not_run=['native ARM64/macOS execution','Node on Linux','Wasm alternative rerun/restricted Wasm loader','OS sandbox/workers/IPC',
            'desktop/screen reader/DPI/multiple monitors/IME','full HTDL/editor/FS/SSC/resource loader','compiler/total RSS budgets','24h/global CI/release/third-party acceptance'],
        canonical_lf_sha256={p.relative_to(ROOT).as_posix():canonical(p) for p in sorted(set(paths))})
    (OUT/'summary.json').write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n',encoding='utf-8',newline='\n')
record=json.loads((OUT/'summary.json').read_text(encoding='utf-8'))
for path,digest in record['canonical_lf_sha256'].items():assert canonical(ROOT/path)==digest,path
print(f'Page runtime: {len(record["canonical_lf_sha256"])} hashes; Windows 238/1 not-run, Linux 210/29 not-run; 32.10 -> 36.20; 0/5 gates')
