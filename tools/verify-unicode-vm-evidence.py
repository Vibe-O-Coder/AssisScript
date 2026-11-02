"""Verify fresh host evidence, all 60 rubric levels and pinned source hashes."""
import argparse
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'docs/ecossistema/evidencias/m3-unicode-vm-2026-11-01'
BASE='a542aff0f6ace008e6558c1cb1553c9ea05cc2eb'
parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--write',action='store_true');args=parser.parse_args()
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def canonical(path):return hashlib.sha256(path.read_bytes().replace(b'\r\n',b'\n')).hexdigest()
def levels(data):return {i['id']:i['level'] for g in data['groups'] for i in g['items']}
def score(data):return sum(Decimal(g['weight'])*sum(i['level'] for i in g['items'])/20 for g in data['groups'])
if args.write:
    hosts={}
    for host in ('windows','linux'):
        record=json.loads((OUT/f'{host}.json').read_text());assert record['passed']
        for check in record['checks']:
            assert check['returncode']==0 and digest(OUT/check['log'])==check['log_sha256'],check
        examples=json.loads((OUT/f'{host}-examples.json').read_text(encoding='utf-8'))
        assert examples['passed'] and len(examples['examples'])==49
        assert {r['ending'] for r in examples['rpg']}=={'victory','defeat'}
        hosts[host]=dict(executed=sum(c['executed'] for c in record['checks']),
            not_run=sum(c['not_run'] for c in record['checks']),compiler_sha256=record['compiler_sha256'],examples=49)
    node=json.loads((OUT/'windows-node.json').read_text());assert node['passed'] and node['tests']==23
    assert digest(OUT/'windows-node.log')==node['log_sha256']
    base=json.loads(subprocess.check_output(['git','show',BASE+':docs/ecossistema/PROGRESSO.json'],cwd=ROOT))
    current=json.loads((ROOT/'docs/ecossistema/PROGRESSO.json').read_text(encoding='utf-8'))
    changes={key:[levels(base)[key],value] for key,value in levels(current).items() if levels(base)[key]!=value}
    assert changes=={'E06-01':[0,1],'E06-02':[0,2],'E06-03':[0,1]},changes
    assert score(base)==Decimal('30.10') and score(current)==Decimal('32.10')
    assert current['history'][:-1]==base['history'] and current['gates']==base['gates']
    assert len(levels(current))==60 and not any(g['passed'] for g in current['gates'])
    for left,right in zip(base['groups'],current['groups']):
        assert (left['id'],left['weight'],left['dependencies'])==(right['id'],right['weight'],right['dependencies'])
        for a,b in zip(left['items'],right['items']):
            assert (a['id'],a['name'],a['acceptance'],a['baseline'])==(b['id'],b['name'],b['acceptance'],b['baseline'])
    assert all(c['returncode']==1 for c in json.loads((OUT/'before.json').read_text())['checks'])
    paths=list(OUT.iterdir())+list((ROOT/'stdlib').glob('*.assis'))+list((ROOT/'src').glob('*.h'))
    paths+=list((ROOT/'src').glob('*.c'))+list((ROOT/'src').glob('*.inc'))
    paths+=list((ROOT/'tests/fixtures/unicode-17.0.0').iterdir())
    paths+=[ROOT/p for p in ['tests/test-graphemes.py','tests/test-pagevm.py','tests/test-wasm-spike.py',
        'tests/test-english-api.py','tests/test-htdl-reader.py','tests/test-htdl-viewer.py','tests/test-v31.js',
        'tools/generate-grapheme-data.py','tools/pagevm-wasm-spike.js','tools/verify-unicode-vm-evidence.py',
        'docs/BIBLIOTECA-graphemes.md','docs/BIBLIOTECA-pagevm.md','docs/FUNCTION-NAMES-2026-11-01.json',
        'docs/ecossistema/ADR-0001-EXECUCAO-PAGINA.md','docs/ecossistema/PROGRESSO.json','docs/ecossistema/PROGRESSO.md',
        'docs/relatorios/2026-11-01-m3-unicode-m0-vm.md','exemplos/47_pagevm_counter.assis']]
    paths=[p for p in paths if p.is_file() and p.name not in ('summary.json','install_files.inc','install_optional.inc')]
    report=dict(schema='assisscript-unicode-vm-evidence-v1',base=BASE,branch='work/m3-unicode-reader-2026-11-01',
        before=str(score(base)),after=str(score(current)),changed_levels=changes,gates_passed=0,hosts=hosts,node_tests=23,
        unicode=dict(version='17.0.0',uax29_revision=47,official_cases=766,modes=['optimized','reference'],
            not_implemented=['normalization','case folding','word segmentation','full shaping/bidi','editing/IME']),
        page_execution='ASV1 experimental bounded interpreter in AssisScript; trusted Wasm/V8 comparison; format choice open; no native page sandbox/backend/SDK',
        visual='Reader launched and uniquely located; two Computer Use captures timed out; desktop acceptance not-run',
        initial_failures=['restricted temporary writes/network blocked; rerun with local execution access',
            'new grapheme API used field/method count conflict; renamed private field',
            'two new test harness issues (fault helper argument and cluster too small); corrected before matrix',
            'English migration left one example method call and cli log call; corrected',
            'old textwrap oracle expected splitting a combining mark; replaced with atomic corpus plus explicit grapheme case',
            'example VM compound expression kept immutable borrow across mutation; split checks using existing ownership contract',
            'Node install test used historical setup binary; rebuilt candidate and staged current files/compiler'],
        not_run=['real screen reader','desktop screenshot','OS DPI/multiple monitors','Linux/macOS graphics',
            'native ARM64/macOS','complete HTDL/editor/loader','FS/SSC','IR-to-page backend','restricted Wasm loader/fuel',
            'OS sandbox','RSS quota','24h/global CI/third-party acceptance'],
        canonical_lf_sha256={p.relative_to(ROOT).as_posix():canonical(p) for p in sorted(set(paths))})
    (OUT/'summary.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8',newline='\n')
r=json.loads((OUT/'summary.json').read_text(encoding='utf-8'))
assert r['schema']=='assisscript-unicode-vm-evidence-v1'
for name,expected in r['canonical_lf_sha256'].items():assert canonical(ROOT/name)==expected,name
for host in ('windows','linux'):assert json.loads((OUT/f'{host}.json').read_text())['passed']
print(f"Unicode/VM: {len(r['canonical_lf_sha256'])} source/evidence hashes; 30.10 -> 32.10; 0/5 gates")
