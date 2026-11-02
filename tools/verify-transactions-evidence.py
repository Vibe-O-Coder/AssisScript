"""Check fresh evidence and the two justified rubric changes; preserve history."""
import argparse
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import subprocess
ROOT=Path(__file__).resolve().parent.parent;OUT=ROOT/'docs/ecossistema/evidencias/m3-transactions-2026-11-01'
BASE='4ba27b3bd91bf7e033f41ba479b96255d4d90566'
parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--write',action='store_true');args=parser.parse_args()
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def canonical(p):return hashlib.sha256(p.read_bytes().replace(b'\r\n',b'\n')).hexdigest()
def levels(d):return {i['id']:i['level'] for g in d['groups'] for i in g['items']}
def score(d):return sum(Decimal(g['weight'])*sum(i['level'] for i in g['items'])/20 for g in d['groups'])
if args.write:
    hosts={}
    for host in ('windows','linux'):
        r=json.loads((OUT/f'{host}.json').read_text());assert r['passed']
        for c in r['checks']:assert c['returncode']==0 and digest(OUT/c['log'])==c['log_sha256']
        hosts[host]=dict(executed=sum(c['executed'] for c in r['checks']),not_run=sum(c['not_run'] for c in r['checks']),compiler_sha256=r['compiler_sha256'])
    base=json.loads(subprocess.check_output(['git','show',BASE+':docs/ecossistema/PROGRESSO.json'],cwd=ROOT))
    current=json.loads((ROOT/'docs/ecossistema/PROGRESSO.json').read_text(encoding='utf-8'))
    changes={k:[levels(base)[k],v] for k,v in levels(current).items() if levels(base)[k]!=v}
    assert changes=={'E07-02':[1,2],'E08-04':[0,2]},changes
    assert score(base)==Decimal('28.90') and score(current)==Decimal('30.10')
    assert current['history'][:-1]==base['history'] and not any(g['passed'] for g in current['gates'])
    assert json.loads((OUT/'linux-fallback.json').read_text())['passed']
    assert json.loads((OUT/'before.json').read_text())['returncode']==1
    surfaces=json.loads((OUT/'surfaces.json').read_text());assert len(surfaces['scenarios'])==4
    paths=list(OUT.glob('*'))+[ROOT/p for p in ['tests/test-reader-transactions.py','tests/reader_oracle.c',
        'exemplos/46_reader_transactions.assis','tools/verify-transactions-evidence.py','tools/build-platform.py',
        'docs/BIBLIOTECA-reader.md','docs/BIBLIOTECA-htdl.md','docs/ecossistema/PROGRESSO.json','docs/ecossistema/PROGRESSO.md']]
    paths+=list((ROOT/'stdlib').glob('*.assis'))+list((ROOT/'providers/platform').glob('*'))
    paths+=list((ROOT/'src').glob('*.h'))+list((ROOT/'src').glob('*.c'))+list((ROOT/'src').glob('*.inc'))
    paths=[p for p in paths if p.is_file() and p.name!='summary.json' and p.name not in ('install_files.inc','install_optional.inc')]
    report=dict(schema='assisscript-transactions-evidence-v1',base=BASE,branch='work/m3-reader-transactions-2026-11-01',
        before=str(score(base)),after=str(score(current)),changed_levels=changes,gates_passed=0,hosts=hosts,
        scope='trusted local HTDL bootstrap: semantic/source transactions, focus, MSAA, preferences and integer motion clock; no FS/SSC or page runtime',
        native_accessibility='external COM client activates two updates and observes revocation; real screen reader not-run',
        visual='four inspected native surface dumps; Computer Use launch_app approval timed out, no desktop screenshot',
        initial_failures=['temporary compiler output denied in restricted environment; rerun with local execution access',
            'frontend rejected reserved field name, mutable value-struct fields and local own reassignment; adapted library to existing contracts',
            'XML oracle input needed quoted attributes; fixed common syntax',
            'application test enumerated an extra system window; filter by provider class',
            'Windows temporary fault executable cleanup WinError 5; rerun without assertion changes'],
        not_run=['real screen reader','desktop screenshot','OS DPI/multiple monitors','grapheme editing/IME',
            'Linux/macOS graphic provider','native ARM64/macOS','complete HTDL catalog/editor recovery','FS/SSC graphs/equations',
            'VM/Wasm decision/page sandbox','RSS quota','24h soak','global CI'],
        canonical_lf_sha256={p.relative_to(ROOT).as_posix():canonical(p) for p in sorted(set(paths))})
    (OUT/'summary.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8',newline='\n')
r=json.loads((OUT/'summary.json').read_text(encoding='utf-8'))
for name,expected in r['canonical_lf_sha256'].items():assert canonical(ROOT/name)==expected,name
for host in ('windows','linux'):assert json.loads((OUT/f'{host}.json').read_text())['passed']
for item in json.loads((OUT/'surfaces.json').read_text())['scenarios']:
    assert item['optimized_reference_equal'] and digest(OUT/(item['name']+'.png'))==item['png_sha256']
print(f"Transactions evidence: {len(r['canonical_lf_sha256'])} hashes; 28.90 -> 30.10; 0/5 gates")
