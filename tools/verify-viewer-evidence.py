"""Freeze/check viewer evidence hashes separately from functional execution."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'docs/ecossistema/evidencias/m2-viewer-2026-11-01'
parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--write',action='store_true');args=parser.parse_args()
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
if args.write:
    hosts={}
    for host in ['windows','linux']:
        report=json.loads((OUT/f'{host}.json').read_text(encoding='utf-8'));assert report['passed']
        for case in report['checks']:
            assert case['returncode']==0 and case['executed']>0
            assert digest(OUT/case['log'])==case['log_sha256']
        hosts[host]=dict(executed=sum(c['executed'] for c in report['checks']),
            not_run=sum(c['not_run'] for c in report['checks']),compiler_sha256=report['compiler_sha256'])
    surfaces=json.loads((OUT/'surfaces.json').read_text(encoding='utf-8'))
    assert all(s['optimized_reference_equal'] for s in surfaces['scenarios'])
    paths=list((ROOT/'src').glob('*.h'))+list((ROOT/'src').glob('*.inc'))+[ROOT/'src/assisc.c']
    paths=[p for p in paths if p.name not in ('install_files.inc','install_optional.inc')]
    paths+=list((ROOT/'stdlib').glob('*.assis'))+list((ROOT/'providers/platform').glob('*'))
    paths+=list((ROOT/'tests').glob('*.py'))+list((ROOT/'tests').glob('*.c'))
    paths+=list((ROOT/'tests/fixtures').glob('*'))
    paths+=[ROOT/'exemplos/44_htdl_viewer.assis',ROOT/'exemplos/44_artigo.htdl',ROOT/'tools/build-platform.py',
            ROOT/'tools/validate-window-fallback.py',ROOT/'tools/verify-viewer-evidence.py']
    paths+=list(OUT.glob('*'));paths=[p for p in paths if p.is_file() and p.name!='summary.json'
        and p.name not in ('window-unavailable-optimized','window-unavailable-reference')]
    record=dict(schema='assisscript-viewer-evidence-v1',base='ebd3185ae952a85c64cb2a83cd014ac07c0e8c7f',
        branch='work/m2-htdl-viewer-2026-11-01',before=23.90,after=27.00,gates_passed=0,hosts=hosts,
        generation='Viewer and provider probes: PE x64, ELF x64/ARM64, Mach-O x64/ARM64 in both modes; not execution of foreign targets',
        surfaces='Three real native surface dumps inspected; optimized/reference bytes equal. Desktop capture failed twice.',
        not_run=['native macOS x64/ARM64','native Linux ARM64','desktop screenshot','200%/multiple monitors',
                 'screen reader','IME/selection','remote sandbox','FS/SSC','integrated 24h soak','global CI'],
        hashes={p.relative_to(ROOT).as_posix():digest(p) for p in sorted(set(paths))})
    (OUT/'summary.json').write_text(json.dumps(record,indent=2,ensure_ascii=False)+'\n',encoding='utf-8',newline='\n')
record=json.loads((OUT/'summary.json').read_text(encoding='utf-8'))
for name,expected in record['hashes'].items():assert digest(ROOT/name)==expected,name
for host in ['windows','linux']:
    assert json.loads((OUT/f'{host}.json').read_text(encoding='utf-8'))['passed']
for surface in json.loads((OUT/'surfaces.json').read_text(encoding='utf-8'))['scenarios']:
    assert digest(OUT/(surface['name']+'.png'))==surface['png_sha256']
print(f"Viewer evidence: {len(record['hashes'])} hashes checked")
