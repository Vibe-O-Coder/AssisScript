"""Verify current Reader evidence without rewriting historical evidence/hashes."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
from decimal import Decimal

ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'docs/ecossistema/evidencias/m3-reader-2026-11-01'
BASE='4e7f6b84c2e933bc7b4196f06b4af80d09c289f6'
parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--write',action='store_true');args=parser.parse_args()
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def score(data):return sum(Decimal(g['weight'])*sum(i['level'] for i in g['items'])/20 for g in data['groups'])
def levels(data):return {i['id']:i['level'] for g in data['groups'] for i in g['items']}
if args.write:
    hosts={}
    for host in ['windows','linux']:
        report=json.loads((OUT/f'{host}.json').read_text(encoding='utf-8'));assert report['passed']
        for case in report['checks']:
            assert case['returncode']==0 and case['executed']>0
            assert digest(OUT/case['log'])==case['log_sha256']
        hosts[host]=dict(executed=sum(c['executed'] for c in report['checks']),not_run=sum(c['not_run'] for c in report['checks']),
            compiler_sha256=report['compiler_sha256'])
    base=json.loads(subprocess.check_output(['git','show',BASE+':docs/ecossistema/PROGRESSO.json'],cwd=ROOT))
    current=json.loads((ROOT/'docs/ecossistema/PROGRESSO.json').read_text(encoding='utf-8'))
    changed={key:(levels(base)[key],level) for key,level in levels(current).items() if levels(base)[key]!=level}
    assert changed=={'E04-04':(1,2),'E04-05':(0,2),'E08-02':(1,2)},changed
    assert score(base)==Decimal('27') and score(current)==Decimal('28.90')
    surfaces=json.loads((OUT/'surfaces.json').read_text(encoding='utf-8'))
    assert len(surfaces['scenarios'])==4 and all(s['optimized_reference_equal'] for s in surfaces['scenarios'])
    assert json.loads((OUT/'linux-fallback.json').read_text())['passed']
    paths=list((ROOT/'src').glob('*.h'))+list((ROOT/'src').glob('*.inc'))+[ROOT/'src/assisc.c']
    paths=[p for p in paths if p.name not in ('install_files.inc','install_optional.inc')]
    paths+=list((ROOT/'stdlib').glob('*.assis'))+list((ROOT/'providers/platform').glob('*'))
    paths+=list((ROOT/'tests').glob('*.py'))+list((ROOT/'tests').glob('*.c'))+list((ROOT/'tests/fixtures').glob('*'))
    paths += [ROOT/name for name in ['stdlib/catalogo.json','docs/BIBLIOTECA-reader.md','exemplos/45_htdl_reader.assis',
        'exemplos/45_leitura.htdl','tools/build-platform.py','tools/validate-reader-fallback.py','tools/verify-reader-evidence.py',
        'docs/ecossistema/PROGRESSO.json','docs/ecossistema/PROGRESSO.md']]
    paths+=list(OUT.glob('*'))
    paths=[p for p in paths if p.is_file() and p.name!='summary.json' and p.suffix not in ('.exe','.dll')
        and p.name not in ('reader-unavailable-optimized','reader-unavailable-reference')]
    record=dict(schema='assisscript-reader-evidence-v1',base=BASE,branch='work/m3-viewer-accessibility-2026-11-01',
        before=str(score(base)),after=str(score(current)),changed_levels=changed,gates_passed=0,hosts=hosts,
        generation='PE x64, ELF x64/ARM64 and Mach-O x64/ARM64 generated/inspected in both modes; foreign targets not executed',
        native_accessibility='Windows MSAA native oracle and external client; real screen reader not-run',
        native_clipboard='separate private window station/desktop; user clipboard untouched',
        native_zoom='GDI font 100/200% and reflow; not OS scaling/monitor acceptance',
        surfaces='four native surface dumps visually inspected; not desktop screenshots',
        not_run=['real screen reader','desktop screenshot: Computer Use app approval timed out','OS DPI/multiple monitors',
            'grapheme editing/IME','contrast/reduced-motion policies','native macOS x64/ARM64','native Linux ARM64',
            'Linux/macOS graphic provider','FS/SSC','remote page sandbox','24h integrated soak','global CI'],
        initial_failures=['viewer temporary executable cleanup WinError 5; passed on repeat without assertion changes',
            'English catalog expected module set needed reader; updated and passed on both hosts',
            'surface helper borrow/unsupported named entity corrected before final capture'],
        hashes={p.relative_to(ROOT).as_posix():digest(p) for p in sorted(set(paths))})
    (OUT/'summary.json').write_text(json.dumps(record,indent=2,ensure_ascii=False)+'\n',encoding='utf-8',newline='\n')
record=json.loads((OUT/'summary.json').read_text(encoding='utf-8'))
for name,expected in record['hashes'].items():assert digest(ROOT/name)==expected,name
for host in ['windows','linux']:assert json.loads((OUT/f'{host}.json').read_text(encoding='utf-8'))['passed']
for scenario in json.loads((OUT/'surfaces.json').read_text(encoding='utf-8'))['scenarios']:
    assert digest(OUT/(scenario['name']+'.png'))==scenario['png_sha256']
print(f"Reader evidence: {len(record['hashes'])} hashes checked; 27.00 -> 28.90; 0/5 gates")
