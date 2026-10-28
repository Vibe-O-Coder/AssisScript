"""Inventory/remove generated artifacts, never source or Git state.

Dry-run by default. All targets are resolved inside the repository. Existing
source snapshots and current validation outputs are kept. Reparse points cause
the containing target to be skipped rather than traversed.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil

ROOT=Path(__file__).resolve().parent.parent
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--apply',action='store_true')
args=parser.parse_args()
kept={'review-baseline','review-tests','review-tmp','clean-win32.json','clean-linux.json'}
targets=[p for p in (ROOT/'build').iterdir() if p.name not in kept]
targets += [p for p in (ROOT/'dist').iterdir() if 'alpha.14' not in p.name and p.name not in {'AssisScript-historical.zip'}]
targets += list(ROOT.glob('*.7z'))
targets += [p for p in ROOT.rglob('__pycache__') if 'historical' not in p.parts and 'build' not in p.parts]
report={'applied':args.apply,'removedFiles':0,'reclaimedBytes':0,'targets':[],'skipped':[]}
for target in targets:
    absolute=target.resolve(strict=True)
    if not absolute.is_relative_to(ROOT) or absolute==ROOT:raise RuntimeError(f'Outside repository: {absolute}')
    files=[];unsafe=False
    if target.is_dir():
        for directory,dirs,names in os.walk(target,followlinks=False):
            for name in dirs+names:
                p=Path(directory)/name
                if p.is_symlink() or p.is_junction():unsafe=True
                if not p.resolve().is_relative_to(ROOT):unsafe=True
            files.extend(Path(directory)/name for name in names)
    else:files=[target]
    if unsafe:report['skipped'].append(target.relative_to(ROOT).as_posix());continue
    size=sum(p.stat().st_size for p in files)
    record={'path':target.relative_to(ROOT).as_posix(),'files':len(files),'bytes':size}
    if target.is_file():record['sha256']=hashlib.sha256(target.read_bytes()).hexdigest()
    if args.apply:
        if target.is_dir():shutil.rmtree(target)
        else:target.unlink()
    report['targets'].append(record);report['removedFiles']+=len(files);report['reclaimedBytes']+=size
(ROOT/'docs/LIMPEZA-ALPHA14.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps({k:v for k,v in report.items() if k not in ['targets']},ensure_ascii=False))
