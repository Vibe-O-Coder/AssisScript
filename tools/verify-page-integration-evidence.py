"""Bind this unit's native results, corpus and unchanged rubric contracts."""
import argparse
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'docs/ecossistema/evidencias/m0-page-integration-2026-11-02'
BASE='0345d567a7ade632546805fc18eca5ca32749cdb'
CHANGES={'E00-03':[2,3],'E06-01':[2,3],'E06-03':[2,3],'E11-04':[1,2]}
parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--write',action='store_true');args=parser.parse_args()
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def canonical(path):return hashlib.sha256(path.read_bytes().replace(b'\r\n',b'\n')).hexdigest()
def read(path):return json.loads(path.read_text(encoding='utf-8'))
def levels(d):return {i['id']:i['level'] for g in d['groups'] for i in g['items']}
def score(d):return sum(Decimal(g['weight'])*sum(i['level'] for i in g['items'])/20 for g in d['groups'])
base=json.loads(subprocess.check_output(['git','show',BASE+':docs/ecossistema/PROGRESSO.json'],cwd=ROOT))
current=read(ROOT/'docs/ecossistema/PROGRESSO.json')
changes={k:[levels(base)[k],v] for k,v in levels(current).items() if levels(base)[k]!=v}
assert changes==CHANGES and len(levels(current))==60
assert score(base)==Decimal('40.20') and score(current)==Decimal('41.70')
assert current['history'][:-1]==base['history'] and current['gates']==base['gates']
for a,b in zip(base['groups'],current['groups']):
    assert (a['id'],a['weight'],a['dependencies'])==(b['id'],b['weight'],b['dependencies'])
    for x,y in zip(a['items'],b['items']):assert (x['id'],x['name'],x['acceptance'])==(y['id'],y['name'],y['acceptance'])
assert subprocess.check_output(['git','show',BASE+':docs/ecossistema/BASELINE-2026-10-29.json'],cwd=ROOT).replace(b'\r\n',b'\n')==(ROOT/'docs/ecossistema/BASELINE-2026-10-29.json').read_bytes().replace(b'\r\n',b'\n')
hosts={};corpus=read(ROOT/'tests/fixtures/page-execution-comparison.json')
for host,counts in [('windows',(151,2)),('linux',(142,11))]:
    report=read(OUT/f'{host}.json');assert report['passed']
    assert len({(c['name'],c['mode']) for c in report['checks']})==len(report['checks'])==12
    assert (sum(c['executed'] for c in report['checks']),sum(c['not_run'] for c in report['checks']))==counts
    for check in report['checks']:
        assert check['returncode']==0 and check['executed']>0
        assert sha(OUT/check['log'])==check['log_sha256']
        if check['name']=='page-reader':
            assert check['candidates']['mode']==check['mode']
            assert (check['executed'],check['not_run'])==((10,0) if host=='windows' else (9,1))
    examples=read(OUT/f'{host}-examples.json');assert examples['passed'] and len(examples['examples'])==52
    assert {r['ending'] for r in examples['rpg']}=={'victory','defeat'} and examples['compilerSha256']==report['compiler_sha256']
    environment=read(OUT/f'{host}-environment.json');assert environment['compiler_sha256']==report['compiler_sha256']
    benchmark=read(OUT/f'{host}-benchmark.json');assert benchmark['compiler_sha256']==report['compiler_sha256']
    assert benchmark['repeats']==40 and benchmark['samples']==7
    assert [c['id'] for c in benchmark['cases']]==[c['id'] for c in corpus['cases']]
    for observed,expected in zip(benchmark['cases'],corpus['cases']):
        assert observed['expected']==str(expected['expected'])
        assert len(observed['vm_samples'])==len(observed['wasm_samples'])==7
        assert all(s['linear_bytes']==131072 for s in observed['wasm_samples'])
        assert observed['steps']>0 and observed['asv2_bytes']>0 and observed['wasm_bytes']>0
    hosts[host]=dict(executed=counts[0],not_run=counts[1],examples=52,compiler_sha256=report['compiler_sha256'],
        reader_candidates={c['mode']:c['candidates'] for c in report['checks'] if c['name']=='page-reader'},node=environment['node']['node'])
node=read(OUT/'windows-node.json');assert node['passed'] and node['tests']==23
assert sha(OUT/'windows-node.log')==node['log_sha256'] and node['compiler_sha256']==hosts['windows']['compiler_sha256']
before=read(OUT/'before.json');assert before['base']==BASE and before['checks'][0]['library']=='pagereader' and before['checks'][0]['returncode']!=0
published=read(OUT/'published-base.json');assert published['commit']==BASE and published['verified']
if args.write:
    paths=list((ROOT/'src').glob('*.h'))+list((ROOT/'src').glob('*.inc'))+[ROOT/'src/assisc.c',ROOT/'.gitattributes',ROOT/'Makefile']
    paths+=list((ROOT/'stdlib').glob('*.assis'))+list((ROOT/'providers/worker').glob('*'))+list((ROOT/'providers/platform').glob('*'))
    paths+=[p for p in OUT.glob('*') if p.name!='summary.json']
    names=['stdlib/catalogo.json','stdlib/catalogo.sh','tests/test-page-reader.py','tests/test-wasm-candidate.py','tests/fixtures/page-execution-comparison.json',
        'tests/test-v31.js','tools/asv2-wasm-candidate.py','tools/run-wasm-candidate.js','tools/benchmark-page-executors.py',
        'tools/collect-page-integration-evidence.py','tools/capture-page-integration-before.py','tools/record-page-integration-environment.py',
        'tools/stage-page-integration-installer.py','tools/verify-page-integration-evidence.py','tools/test-native.py',
        'docs/BIBLIOTECA-pagereader.md','docs/BIBLIOTECAS.md','docs/ecossistema/ADR-0001-EXECUCAO-PAGINA.md','docs/ecossistema/PERFIL-PAGINA-ASV2.md',
        'docs/ecossistema/PERFIL-VISUALIZADOR-V1.md','docs/ecossistema/PROGRESSO.json','docs/ecossistema/PROGRESSO.md',
        'exemplos/50_page_reader.assis','exemplos/pages/reader-counter.assis']
    paths += [ROOT/p for p in names]
    record=dict(schema='assisscript-page-integration-evidence-v1',base=BASE,branch='work/m0-page-integration-2026-11-02',passed=True,
        before='40.20',after='41.70',changed_levels=changes,gates_passed=0,hosts=hosts,node_tests=23,new_distinct_test_methods=19,
        benchmarks=dict(cases=4,repeats=40,samples=7,executions_per_engine_host=1120),
        preserved_failure='windows-page-reader-reference-attempt.log: temporary host.exe rewrite denied; unique per-method output paths; original assertions rerun in both modes',
        preserved_installer_failure='windows-node-uninstall-attempt.log: Windows 5 removing temporary page prefix; installer/test assertions unchanged, complete isolated suite rerun',
        not_run=['macOS/ARM native execution','Windows/macOS authority sandbox','general page values/ownership/runtime decision',
            'compiler/host overall RSS quotas','desktop/real screen reader/DPI/multimonitor/IME/shaping/bidi',
            'mutable SDK/strings/general subscriptions/full HTDL/editor/FS/SSC/resource loader','network/broker/profile/persistence/search',
            'integrated UI/crawler/search benchmark/24h/global CI/release/third-party acceptance'],
        canonical_lf_sha256={p.relative_to(ROOT).as_posix():canonical(p) for p in sorted(set(paths)) if p.is_file()})
    (OUT/'summary.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
record=read(OUT/'summary.json');assert record['passed']
for path,digest in record['canonical_lf_sha256'].items():assert canonical(ROOT/path)==digest,path
print(f'Page integration: {len(record["canonical_lf_sha256"])} hashes; Windows 151/2, Linux 142/11 executed/not-run; Node 23; 40.20 -> 41.70; 0/5 gates')
