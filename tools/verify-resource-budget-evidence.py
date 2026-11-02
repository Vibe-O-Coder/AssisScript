"""Verify exact evidence, unchanged rubric contracts, and this unit's delta."""
import argparse
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'docs/ecossistema/evidencias/m0-resource-budget-2026-11-02'
BASE='fffd1b8bd3eb4c43eeab535f586a12e2e6719c0d'
parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--write',action='store_true');args=parser.parse_args()
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path):return json.loads(path.read_text(encoding='utf-8'))
def score(d):return sum(Decimal(g['weight'])*sum(x['level'] for x in g['items'])/20 for g in d['groups'])
def levels(d):return {x['id']:x['level'] for g in d['groups'] for x in g['items']}
base=json.loads(subprocess.check_output(['git','show',BASE+':docs/ecossistema/PROGRESSO.json'],cwd=ROOT));current=read(ROOT/'docs/ecossistema/PROGRESSO.json')
assert len(levels(current))==60
assert {k:[levels(base)[k],v] for k,v in levels(current).items() if levels(base)[k]!=v}=={'E06-02':[2,3]}
assert score(base)==Decimal('41.70') and score(current)==Decimal('42.20')
assert current['history'][:-1]==base['history'] and current['gates']==base['gates']
for a,b in zip(base['groups'],current['groups']):
    assert (a['id'],a['weight'],a['dependencies'])==(b['id'],b['weight'],b['dependencies'])
    for x,y in zip(a['items'],b['items']):assert (x['id'],x['name'],x['acceptance'])==(y['id'],y['name'],y['acceptance'])
original=subprocess.check_output(['git','show',BASE+':docs/ecossistema/BASELINE-2026-10-29.json'],cwd=ROOT)
assert original.replace(b'\r\n',b'\n')==(ROOT/'docs/ecossistema/BASELINE-2026-10-29.json').read_bytes().replace(b'\r\n',b'\n')
hosts={}
for host,counts in [('windows',(194,4)),('linux',(188,10))]:
    r=read(OUT/f'{host}.json');assert r['passed'] and len(r['checks'])==14
    assert len({(x['name'],x['mode']) for x in r['checks']})==14
    assert (sum(x['executed'] for x in r['checks']),sum(x['not_run'] for x in r['checks']))==counts
    for x in r['checks']:
        assert x['returncode']==0 and x['executed']>0
        assert sha(OUT/x['log'])==x['log_sha256']
        if x['name']=='page-compiler':
            assert (x['executed'],x['not_run'])==(13,0) and x['candidates']['compiler_sha256']==r['compiler_sha256']
    examples=read(OUT/f'{host}-examples.json');assert examples['passed'] and len(examples['examples'])==53
    assert examples['compilerSha256']==r['compiler_sha256'] and {x['ending'] for x in examples['rpg']}=={'victory','defeat'}
    demo=read(OUT/f'{host}-example-51.json');assert demo['passed'] and demo['stdout']=='PAGE-STATE 42\n' and demo['compiler_sha256']==r['compiler_sha256']
    env=read(OUT/f'{host}-environment.json');assert env['compiler_sha256']==r['compiler_sha256']
    hosts[host]=dict(executed=counts[0],not_run=counts[1],examples=53,compiler_sha256=r['compiler_sha256'])
node=read(OUT/'windows-node.json');assert node['passed'] and node['tests']==23
assert node['compiler_sha256']==hosts['windows']['compiler_sha256']
assert node['log_sha256']==sha(OUT/'windows-node.log')
before=read(OUT/'before.json');assert before['base']==BASE and before['returncode']!=0 and 'desconhecido' in before['stderr']
subprocess.run(['python' if __import__('os').name=='nt' else 'python3',str(ROOT/'tools/prepare-page-sdk.py'),'--check'],check=True)
paths=set()
for folder in ['src','stdlib','providers/worker','providers/platform']:
    paths.update(p for p in (ROOT/folder).rglob('*') if p.is_file() and p.suffix in {'.c','.h','.inc','.assis','.json','.sh'})
for pattern in ['tests/test-page-*.py','tests/test-v31.js','tools/*resource-budget*.py','tools/prepare-page-sdk.py','tools/generate-install-manifest.py','tools/build-page-worker.py','tools/build-platform.py']:
    paths.update(ROOT.glob(pattern))
paths.update([ROOT/'docs/ecossistema/PROGRESSO.json',ROOT/'docs/BIBLIOTECA-pagecompiler.md',ROOT/'exemplos/51_compile_page.assis'])
summary=dict(schema='assisscript-resource-budget-evidence-v1',base=BASE,branch='work/m0-resource-budget-2026-11-02',
    before='41.70',after='42.20',changed_levels={'E06-02':[2,3]},gates_passed=0,hosts=hosts,node_tests=23,new_distinct_methods=13,
    compiler_cancel_cycles_per_mode_host=128,
    not_run=['macOS/ARM service execution','Windows/macOS authority sandbox','aggregate shell/Reader/RSS quotas','full HTDL/editor/mutable SDK/strings/subscriptions/FS/SSC/resource loader','desktop/real screen reader/DPI/monitors/IME/shaping/bidi','network/profile/persistence/search/M4-M9','24h/distribution/third-party acceptance'],
    evidence_sha256={p.relative_to(ROOT).as_posix():sha(p) for p in sorted(OUT.iterdir()) if p.is_file() and p.name!='summary.json'},
    source_sha256={p.relative_to(ROOT).as_posix():sha(p) for p in sorted(paths)})
target=OUT/'summary.json'
if args.write:target.write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
else:assert read(target)==summary,'Evidence/source changed; inspect and regenerate summary'
print('Verified resource budgets: 194/4 Windows, 188/10 Linux; 53 examples each; 23 Node; 42.20%, 0/5 gates')
