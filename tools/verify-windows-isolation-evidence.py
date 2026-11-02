"""Verify this unit's exact evidence, unchanged rubric and bounded delta."""
import argparse
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'docs/ecossistema/evidencias/m0-windows-isolation-2026-11-02'
BASE='f12a1f2a9a7edf97e829d5f7c6e2f29980961414'
parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--write',action='store_true');args=parser.parse_args()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def levels(d):return {i['id']:i['level'] for g in d['groups'] for i in g['items']}
def score(d):return sum(Decimal(g['weight'])*sum(i['level'] for i in g['items'])/20 for g in d['groups'])
base=json.loads(subprocess.check_output(['git','show',BASE+':docs/ecossistema/PROGRESSO.json'],cwd=ROOT));current=read(ROOT/'docs/ecossistema/PROGRESSO.json')
assert len(levels(current))==60
assert {k:[levels(base)[k],v] for k,v in levels(current).items() if levels(base)[k]!=v}=={'E06-04':[2,3]}
assert (score(base),score(current))==(Decimal('42.20'),Decimal('42.70'))
assert current['history'][:-1]==base['history'] and current['gates']==base['gates']
for a,b in zip(base['groups'],current['groups']):
    assert (a['id'],a['weight'],a['dependencies'])==(b['id'],b['weight'],b['dependencies'])
    for x,y in zip(a['items'],b['items']):assert (x['id'],x['name'],x['acceptance'])==(y['id'],y['name'],y['acceptance'])
original=subprocess.check_output(['git','show',BASE+':docs/ecossistema/BASELINE-2026-10-29.json'],cwd=ROOT)
assert original.replace(b'\r\n',b'\n')==(ROOT/'docs/ecossistema/BASELINE-2026-10-29.json').read_bytes().replace(b'\r\n',b'\n')
hosts={}
for host,counts in [('windows',(202,4)),('linux',(188,18))]:
    r=read(OUT/f'{host}.json');assert r['passed'] and len(r['checks'])==16
    expected={(n,m) for n in ['windows-isolation','page-compiler','page-worker','page-reader'] for m in ['optimized','reference']}
    expected|={(n,'both') for n in ['page-host','page-backend','pagevm','htdl-parser','reader-transactions','safe-default','ownership-functions','functions']}
    assert {(c['name'],c['mode']) for c in r['checks']}==expected
    assert (sum(c['executed'] for c in r['checks']),sum(c['not_run'] for c in r['checks']))==counts
    for c in r['checks']:
        assert c['returncode']==0
        log=OUT/c['log'];assert sha(log)==c['log_sha256'];raw=log.read_bytes()
        total=re.search(rb'Ran (\d+) tests?',raw);skip=re.search(rb'skipped=(\d+)',raw)
        assert int(total[1])==c['executed']+c['not_run'] and (int(skip[1]) if skip else 0)==c['not_run']
        if c['name']=='windows-isolation':
            assert (c['executed'],c['not_run'])==((4,0) if host=='windows' else (0,4))
            if host=='windows':
                assert c['candidates']['compiler_sha256']==r['compiler_sha256']
                assert b'ISOLATION_CYCLES 64; unchanged profiles/stage directories/handles' in raw
                assert len(re.findall(rb'NATIVE_DENIALS ',raw))==2
                for item in re.findall(rb'NATIVE_DENIALS (\{[^\r\n]+\})',raw):
                    v=json.loads(item);assert v['own_read']==0 and v['inherited']==v['environment']==0
                    assert all(v[k]==5 for k in ['own_write','private_read','private_write','neighbor_read','stage_create','registry','parent','clipboard'])
                    assert v['child']==367 and v['network']==10107 and v['dynamic_code']==1655
        elif c['name']=='page-compiler':assert c['candidates']['compiler_sha256']==r['compiler_sha256']
    examples=read(OUT/f'{host}-examples.json');assert examples['passed'] and len(examples['examples'])==53
    assert examples['compilerSha256']==r['compiler_sha256'] and {x['ending'] for x in examples['rpg']}=={'victory','defeat'}
    demo=read(OUT/f'{host}-example-51.json');assert demo['passed'] and demo['stdout']=='PAGE-STATE 42\n' and demo['compiler_sha256']==r['compiler_sha256']
    assert '--trusted-local' not in demo['commands'][-1]
    assert (OUT/f'{host}-example-51.log').read_bytes()==b'PAGE-STATE 42\n'
    env=read(OUT/f'{host}-environment.json');assert env['compiler_sha256']==r['compiler_sha256']
    hosts[host]=dict(executed=counts[0],not_run=counts[1],examples=53,compiler_sha256=r['compiler_sha256'])
node=read(OUT/'windows-node.json');assert node['passed'] and node['tests']==23
assert node['compiler_sha256']==hosts['windows']['compiler_sha256'] and node['log_sha256']==sha(OUT/'windows-node.log')
before=read(OUT/'before.json');assert (before['base'],before['returncode'],before['token'])==(BASE,-3,0)
assert read(OUT/'published-base.json')['sha']==BASE
paths=set()
for folder in ['src','stdlib','providers/worker','providers/platform']:
    paths.update(p for p in (ROOT/folder).rglob('*') if p.is_file() and p.suffix in {'.c','.h','.inc','.assis','.json','.sh'})
for pattern in ['tests/test-page-*.py','tests/test-windows-isolation.py','tests/windows-isolation-oracle.c','tools/*windows-isolation*.py','tools/build-page-worker.py','tools/run-resource-budget-example.py','tools/stage-resource-budget-installer.py']:
    paths.update(ROOT.glob(pattern))
paths.update(ROOT/p for p in ['docs/ecossistema/PROGRESSO.json','docs/ecossistema/PERFIL-WINDOWS-ISOLATION-V1.md','.gitattributes','Makefile','THIRD_PARTY_NOTICES.md','exemplos/49_page_worker.assis','exemplos/50_page_reader.assis','exemplos/51_compile_page.assis'])
summary=dict(schema='assisscript-windows-isolation-evidence-v1',base=BASE,branch='work/m0-windows-isolation-2026-11-02',before='42.20',after='42.70',changed_levels={'E06-04':[2,3]},gates_passed=0,
    hosts=hosts,node_tests=23,new_distinct_methods=4,worker_cycles_per_mode=64,compiler_cancel_cycles_per_mode=128,creation_fault_boundaries=6,creation_fault_repeats=3,
    not_run=['macOS/ARM/other Windows builds','Linux Node tests unavailable','Win32k lockdown','aggregate shell/Reader/RSS quota','disk quota and orphan recovery after shell crash','full SDK/HTDL/editor/FS/SSC/resources','desktop/real reader/DPI/monitors/shaping/bidi/IME','network/broker/profile/persistence/search/M4-M9','24h/distribution/third-party acceptance'],
    evidence_sha256={p.relative_to(ROOT).as_posix():sha(p) for p in sorted(OUT.iterdir()) if p.is_file() and p.name!='summary.json'},
    source_sha256={p.relative_to(ROOT).as_posix():sha(p) for p in sorted(paths)})
target=OUT/'summary.json'
if args.write:target.write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
else:assert read(target)==summary,'Evidence/source changed: inspect and regenerate summary'
print('Verified: 202/4 Windows, 188/18 Linux; 53 examples each; 23 Node; 42.70%, 0/5 gates')
