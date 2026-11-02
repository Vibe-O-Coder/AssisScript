"""Verify native/editor evidence and hashes; no omitted test becomes a pass."""
import argparse
import hashlib
import json
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'docs/ecossistema/evidencias/m3-htdl-catalog-2026-11-02'
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--write',action='store_true');args=p.parse_args()
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
read=lambda name:json.loads((OUT/name).read_text(encoding='utf-8'))
expected={('htdl-catalog','both'),('htdl-parser','both'),('reader-transactions','both'),('htdl-reader','both'),('page-host','both'),('page-reader','optimized'),('page-reader','reference')}
hosts={}
for host,executed,not_run in [('windows',90,0),('linux',81,9)]:
    data=read(host+'.json');assert data['passed']
    assert {(c['name'],c['mode']) for c in data['checks']}==expected
    for c in data['checks']:
        log=OUT/c['log'];raw=log.read_bytes()
        assert c['returncode']==0 and c['log_sha256']==sha(log)
        count=re.search(rb'Ran (\d+) tests? in',raw);assert count and int(count[1])==c['executed']+c['not_run']
        assert re.search(rb'\nOK(?: \(skipped=\d+\))?\r?\n',raw),log
    assert sum(c['executed'] for c in data['checks'])==executed
    assert sum(c['not_run'] for c in data['checks'])==not_run
    env=read(host+'-environment.json');assert env['compiler_sha256']==data['compiler_sha256']
    example=read(host+'-example-52.json');assert example['passed'] and example['compiler_sha256']==data['compiler_sha256']
    for c in example['checks']:assert c['passed'] and sha(OUT/c['log'])==c['log_sha256']
    examples=read(host+'-examples.json');assert examples['passed'] and len(examples['examples'])==54
    assert examples['compilerSha256']==data['compiler_sha256']
    assert {r['ending'] for r in examples['rpg']}=={'victory','defeat'}
    hosts[host]=dict(executed=executed,not_run=not_run,compiler_sha256=data['compiler_sha256'],examples=54,example_52_modes=2)
editor=read('windows-editor.json');assert editor['passed'] and editor['executed']==37
assert editor['log_sha256']==sha(OUT/'windows-editor.log')
assert editor['compiler_sha256']==hosts['windows']['compiler_sha256']
assert re.search(rb'pass 37', (OUT/'windows-editor.log').read_bytes())
installer=read('windows-node.json');assert installer['passed'] and installer['tests']==23
assert installer['log_sha256']==sha(OUT/'windows-node.log')
assert installer['compiler_sha256']==hosts['windows']['compiler_sha256']
assert installer['vsix']['passed'] and installer['vsix']['windows_compiler_sha256']==hosts['windows']['compiler_sha256']
assert installer['vsix']['linux_compiler_sha256']==hosts['linux']['compiler_sha256']
for entry,digest in installer['vsix']['entries'].items():
    relative=entry.removeprefix('extension/')
    source=relative if relative.startswith(('tools/','stdlib/')) else 'vscode-assisscript/'+relative
    assert sha(ROOT/source)==digest,source
linux=read('linux-installed-checker.json');assert linux['passed'] and linux['compiler_sha256']==hosts['linux']['compiler_sha256']
before=read('before.json');assert [c['code'] for c in before['checks']]==[203,203,0]
integrity=read('reference-integrity.json');assert integrity['integrity']=='pass' and integrity['snapshot_files']==57
assert integrity['runtime_conformance']=='not-run' and integrity['integration']=='not-run'
progress=json.loads((ROOT/'docs/ecossistema/PROGRESSO.json').read_text(encoding='utf-8'))
levels={i['id']:i['level'] for g in progress['groups'] for i in g['items']}
assert len(levels)==60 and progress['history'][-1]['levels']==levels
assert levels['E00-01']==2 and levels['E07-01']==3 and not any(progress['history'][-1]['gates'].values())
previous=progress['history'][-2]['levels']
assert {key:(previous[key],level) for key,level in levels.items() if previous[key]!=level}=={'E00-01':(1,2),'E07-01':(2,3)}
score=sum(g['weight']*sum(i['level'] for i in g['items'])/20 for g in progress['groups']);assert abs(score-43.3)<0.000001
paths=['.gitattributes','Makefile','instalar.sh','src/install_files.inc','stdlib/htdl.assis','stdlib/catalogo.json',
       'tests/fixtures/htdl-catalog-driver.assis','tests/fixtures/htdl-catalog-corpus.json','tests/test-htdl-catalog.py','tests/test-htdl-editor.js','tests/test-lsp.js',
       'tools/htdl-check.assis','tools/assis-lsp.js','tools/collect-htdl-catalog-evidence.py','tools/collect-htdl-catalog-extra.py','tools/verify-htdl-catalog-evidence.py','tools/verify-htdl-catalog-install.py','tools/verify-htdl-catalog-vsix.py',
       'tools/generate-install-manifest.py','tools/package-vscode.py','exemplos/52_htdl_catalog.assis',
       'vscode-assisscript/package.json','vscode-assisscript/src/extension.js','vscode-assisscript/src/htdl.js','vscode-assisscript/test/extension.test.js',
       'vscode-assisscript/htdl-configuration.json','vscode-assisscript/syntaxes/htdl.tmLanguage.json','docs/ecossistema/PERFIL-HTDL-CATALOGO-V1.md','docs/ecossistema/PROGRESSO.json']
files={name:sha(ROOT/name) for name in paths}
artifacts={f.name:sha(f) for f in sorted(OUT.iterdir()) if f.is_file() and f.name not in ['summary.json','published-base.json','published-implementation.json']}
summary=dict(schema='htdl-catalog-evidence-v1',base='f00d1ff95694dd312f90ec46d563606bda258356',hosts=hosts,
             windows_editor_tests=37,windows_installer_tests=23,linux_installed_checker=True,before_codes=[203,203,0],
             progress_before=42.7,progress_after=43.3,gates_before=0,gates_after=0,files=files,artifacts=artifacts,
             not_run=['macOS/ARM native execution','Linux Node unavailable','interactive VS Code acceptance','desktop/screen reader/DPI/IME','historical integrated scenarios','remote CI/release/24h'],
             passed=True)
if args.write:(OUT/'summary.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8',newline='\n')
else:assert read('summary.json')==summary,'Evidence/source changed; verify results and regenerate summary'
print('Evidence verified: 90/0 Windows, 81/9 Linux, 37 editor, 23 installer; 43.30%, 0/5 gates')
