"""Verify worker execution logs, stable sources and unchanged rubric contracts."""
import argparse
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import subprocess
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'docs/ecossistema/evidencias/m0-page-worker-2026-11-02'
BASE='6b2ece0ba5a28b7775e9da90adade5a36c8a29bc'
CHANGES={'E03-03':[2,3],'E03-04':[2,3],'E03-05':[0,3],'E06-04':[0,2],'E06-05':[2,3]}
parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--write',action='store_true');args=parser.parse_args()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def canonical(p):return hashlib.sha256(p.read_bytes().replace(b'\r\n',b'\n')).hexdigest()
def levels(d):return {i['id']:i['level'] for g in d['groups'] for i in g['items']}
def score(d):return sum(Decimal(g['weight'])*sum(i['level'] for i in g['items'])/20 for g in d['groups'])
base=json.loads(subprocess.check_output(['git','show',BASE+':docs/ecossistema/PROGRESSO.json'],cwd=ROOT))
current=json.loads((ROOT/'docs/ecossistema/PROGRESSO.json').read_text(encoding='utf-8'))
changes={key:[levels(base)[key],value] for key,value in levels(current).items() if levels(base)[key]!=value}
assert changes==CHANGES and len(levels(current))==60
assert score(base)==Decimal('36.20') and score(current)==Decimal('40.20')
assert current['history'][:-1]==base['history'] and current['gates']==base['gates']
for a,b in zip(base['groups'],current['groups']):
    assert (a['id'],a['weight'],a['dependencies'])==(b['id'],b['weight'],b['dependencies'])
    for x,y in zip(a['items'],b['items']):assert (x['id'],x['name'],x['acceptance'])==(y['id'],y['name'],y['acceptance'])
assert subprocess.check_output(['git','show',BASE+':docs/ecossistema/BASELINE-2026-10-29.json'],cwd=ROOT).replace(b'\r\n',b'\n')==(ROOT/'docs/ecossistema/BASELINE-2026-10-29.json').read_bytes().replace(b'\r\n',b'\n')
hosts={}
for host in ['windows','linux']:
    report=json.loads((OUT/f'{host}.json').read_text());assert report['passed']
    assert len({(c['name'],c['mode']) for c in report['checks']})==len(report['checks'])==10
    for check in report['checks']:
        assert check['returncode']==0 and check['executed']>0
        assert sha(OUT/check['log'])==check['log_sha256']
        if check['name']=='page-worker':
            assert (check['executed'],check['not_run'])==(17,2)
            assert check['candidates']['mode']==check['mode']
            assert all(len(check['candidates'][k])==64 for k in ['worker_sha256','provider_sha256'])
    count=sum(c['executed'] for c in report['checks']);not_run=sum(c['not_run'] for c in report['checks'])
    assert (count,not_run)==(127,4),(host,count,not_run)
    examples=json.loads((OUT/f'{host}-examples.json').read_text())
    assert examples['passed'] and len(examples['examples'])==51 and {r['ending'] for r in examples['rpg']}=={'victory','defeat'}
    assert examples['compilerSha256']==report['compiler_sha256']
    hosts[host]=dict(executed=count,not_run=not_run,examples=51,compiler_sha256=report['compiler_sha256'],
        worker_candidates={c['mode']:c['candidates'] for c in report['checks'] if c['name']=='page-worker'})
node=json.loads((OUT/'windows-node.json').read_text());assert node['passed'] and node['tests']==23
assert sha(OUT/'windows-node.log')==node['log_sha256'] and node['compiler_sha256']==hosts['windows']['compiler_sha256']
before=json.loads((OUT/'before.json').read_text());assert before['base']==BASE and all(c['returncode']!=0 for c in before['checks'])
published=json.loads((OUT/'published-base.json').read_text());assert published['commit']==BASE and published['verified'] and published['blobs']==2068
assert published['tree']==subprocess.check_output(['git','rev-parse',BASE+'^{tree}'],cwd=ROOT,text=True).strip()
if args.write:
    paths=list((ROOT/'src').glob('*.h'))+list((ROOT/'src').glob('*.inc'))+[ROOT/'src/assisc.c',ROOT/'.gitattributes']+list((ROOT/'stdlib').glob('*.assis'))
    paths+=list((ROOT/'providers/worker').glob('*'))+[p for p in OUT.glob('*') if p.name!='summary.json']
    paths += [ROOT/p for p in ['tests/test-page-worker.py','tests/worker-isolation-oracle.c','tests/test-v31.js',
        'tools/build-page-worker.py','tools/page-worker.assis','tools/collect-page-worker-evidence.py','tools/capture-page-worker-before.py',
        'tools/verify-page-worker-evidence.py','tools/stage-page-worker-installer.py','tools/test-native.py','Makefile',
        'stdlib/catalogo.json','stdlib/catalogo.sh','docs/BIBLIOTECAS.md','docs/BIBLIOTECA-pagewire.md','docs/BIBLIOTECA-pageworker.md',
        'docs/ecossistema/PERFIL-WORKER-LOCAL-V1.md','exemplos/49_page_worker.assis','docs/ecossistema/PROGRESSO.json','docs/ecossistema/PROGRESSO.md']]
    summary=dict(schema='assisscript-page-worker-evidence-v1',base=BASE,branch='work/m0-page-worker-2026-11-02',before='36.20',after='40.20',changed_levels=changes,
        gates_passed=0,hosts=hosts,node_tests=23,new_distinct_test_methods=19,
        failed_attempts=['windows-htdl-parser-cleanup-attempt.log: WinError 5 deleting a temporary executable; affected suite rerun without weakening assertions',
            'windows-node-uninstall-attempt.log: uninstall returned 1; original assertions retained and rerun passed with diagnostic context added'],
        not_run=['Windows authority sandbox (explicit -3)','macOS/ARM64 execution and providers','restricted Wasm comparison/decision','compiler/overall RSS budget',
            'Reader/desktop/screen reader/DPI/IME integration','full HTDL/editor/FS/SSC/resource loader','network/broker/profile/search','24h/global CI/release/third-party acceptance'],
        canonical_lf_sha256={p.relative_to(ROOT).as_posix():canonical(p) for p in sorted(set(paths)) if p.is_file()})
    (OUT/'summary.json').write_text(json.dumps(summary,indent=2,ensure_ascii=False)+'\n',encoding='utf-8',newline='\n')
record=json.loads((OUT/'summary.json').read_text())
for path,digest in record['canonical_lf_sha256'].items():assert canonical(ROOT/path)==digest,path
print(f'Worker evidence: {len(record["canonical_lf_sha256"])} hashes; Windows/Linux each 127 executed, 4 not-run; Node 23; 36.20 -> 40.20; 0/5 gates')
