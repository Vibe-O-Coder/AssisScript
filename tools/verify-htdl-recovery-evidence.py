"""Validate recorded results and source hashes without claiming unrun checks."""
import argparse
import hashlib
import json
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'docs/ecossistema/evidencias/m3-htdl-recovery-2026-11-02'
parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--write',action='store_true');args=parser.parse_args()
expected={'windows':{'htdl-recovery':(9,0),'htdl-catalog':(16,0),'htdl-parser':(16,0),'reader-transactions':(15,0),'htdl-reader':(10,0),'editor':(38,0)},
          'linux':{'htdl-recovery':(9,0),'htdl-catalog':(16,0),'htdl-parser':(16,0),'reader-transactions':(11,4),'htdl-reader':(7,3)}}
counts={}
for host,jobs in expected.items():
    data=json.loads((OUT/f'{host}.json').read_text())
    assert data['passed'] and {r['name'] for r in data['checks']}==set(jobs)
    for record in data['checks']:
        assert record['returncode']==0 and (record['executed'],record['not_run'])==jobs[record['name']]
        log=(OUT/record['log']).read_bytes()
        assert hashlib.sha256(log).hexdigest()==record['sha256']
        if record['name']=='editor': assert re.search(rb'(?:# )?fail 0',log)
        else: assert re.search(rb'\nOK(?: \(skipped=\d+\))?\r?\n',log)
    examples=json.loads((OUT/f'{host}-examples.json').read_text())
    assert examples['passed'] and len(examples['examples'])==55
    counts[host]=dict(executed=sum(r['executed'] for r in data['checks']),not_run=sum(r['not_run'] for r in data['checks']))
before=json.loads((OUT/'before-after.json').read_text())
assert [r['stdout'].splitlines()[0] for r in before['observations']]==['1 0','2 0']
sources=['stdlib/htdl.assis','tools/htdl-check.assis','tests/test-htdl-recovery.py','tests/test-htdl-catalog.py','tests/test-htdl-parser.py','tests/test-htdl-editor.js','tests/test-lsp.js','exemplos/53_htdl_editor_recovery.assis',
         'tools/collect-htdl-recovery-evidence.py','tools/verify-htdl-recovery-evidence.py','docs/ecossistema/RECUPERACAO-HTDL-EDITOR-V1.md']
summary=dict(schema='htdl-recovery-summary-v1',base=before['base'],counts=counts,points_before='43.30',points_after='43.30',gates_passed=0,
             source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sources},
             limitations=['Second root stops recovery','Invalid UTF-8 stops before parsing','No semantics on syntax-damaged tree','No editor incremental identity','No desktop/screen reader/DPI/IME acceptance','ARM/macOS not-run','No FS/SSC/resource loader or remote navigation acceptance'])
path=OUT/'summary.json'
if args.write:path.write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8',newline='\n')
else:assert json.loads(path.read_text())==summary,'Evidence or sources changed; recollect and verify'
print(json.dumps(counts)+'; 43.30%, 0/5 gates')
