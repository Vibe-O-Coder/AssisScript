"""Compare a GitHub recursive tree with the immutable local implementation."""
import argparse
import json
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parent.parent
BASE='1e574736ce33a16e442fb270e9d42c8c884d29f6'
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--remote-tree',type=Path,required=True)
parser.add_argument('--commit',required=True)
parser.add_argument('--pr',required=True)
args=parser.parse_args()
remote=json.loads(args.remote_tree.read_text(encoding='utf-8'));assert not remote['truncated']
expected={}
for row in subprocess.check_output(['git','ls-tree','-rz',args.commit],cwd=ROOT).split(b'\0'):
    if not row:continue
    info,name=row.split(b'\t',1);mode,kind,sha=info.decode().split()
    assert kind=='blob';expected[name.decode('utf-8')]=(mode,sha)
observed={item['path']:(item['mode'],item['sha']) for item in remote['tree'] if item['type']=='blob'}
assert observed==expected,'Published tree paths/modes/blobs differ'
local_tree=subprocess.check_output(['git','rev-parse',args.commit+'^{tree}'],cwd=ROOT,text=True).strip()
assert local_tree==remote['sha']
changed=[name.decode('utf-8') for name in subprocess.check_output(['git','diff','--name-only','-z',BASE,args.commit],cwd=ROOT).split(b'\0') if name]
record=dict(commit=args.commit,base=BASE,tree=remote['sha'],all_blobs_checked=len(expected),changed_paths=len(changed),
    pr=args.pr,draft=True,merged=False,files={name:expected[name][1] for name in changed})
path=ROOT/'docs/ecossistema/evidencias/m0-page-runtime-2026-11-02/published-implementation.json'
path.write_text(json.dumps(record,indent=2,ensure_ascii=False)+'\n',encoding='utf-8',newline='\n')
print(f'Published {args.commit}: {len(expected)} blobs and {len(changed)} changed paths/modes match GitHub')
