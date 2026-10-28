"""Collect current validation evidence; roadmap credit is recorded separately."""
import argparse
from datetime import date
import hashlib
import json
import os
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parent.parent
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--windows',type=Path,default=ROOT/'build/review-tests/windows-release.json')
parser.add_argument('--linux',type=Path,default=ROOT/'build/review-tests/linux-release.json')
args=parser.parse_args()
def read(path):return json.loads(path.read_text(encoding='utf-8'))
version=read(ROOT/'vscode-assisscript/package.json')['version']
record=dict(version=version,date=date.today().isoformat(),status='passed',scope='Windows/Linux native execution, scalar IR/liveness and Mach-O structural validation',native={},cleanBuilds={},examples={},macos=dict(status='experimental; native execution pending',validated='Mach-O structure, segments, bindings and entry; PE/ELF cross-generation'),notes=['Manual-memory teaching examples use explicit unsafe blocks.','Roadmap credit and outstanding gates are recorded in PROGRESSO.json.','This is a local working-tree revision, not a published clean tag.'])
for platform,path,binary in [('windows',args.windows,'assis.exe'),('linux',args.linux,'assis')]:
    result=read(path);expected=hashlib.sha256((ROOT/'bin'/binary).read_bytes()).hexdigest()
    assert result['passed'] and result['compilerSha256']==expected,(platform,'stale or failed native results')
    result['testCount']=sum(r['tests'] or 0 for r in result['suites']);record['native'][platform]=result
    clean=ROOT/'build'/('clean-win32.json' if platform=='windows' else 'clean-linux.json')
    if clean.exists():
        proof=read(clean)
        if proof['workspaceBinarySha256']==expected and proof['identicalToWorkspaceBinary']:record['cleanBuilds'][platform]=proof
    examples=ROOT/'build/review-tests'/('examples-'+platform+'.json')
    if examples.exists():
        proof=read(examples)
        assert proof['passed'] and proof['compilerSha256']==expected,(platform,'stale example report')
        record['examples'][platform]=proof
record['sourceHashes']={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((ROOT/'src').iterdir()) if p.is_file()}
record['benchmarks']={};record['shortSoak']={}
for platform,binary in [('windows','assis.exe'),('linux','assis')]:
    expected=hashlib.sha256((ROOT/'bin'/binary).read_bytes()).hexdigest()
    record['benchmarks'][platform]={}
    for name in ['backend','optimization']:
        path=ROOT/f'benchmarks/resultados/{name}-alpha15-{platform}.json';proof=read(path)
        assert proof['compilers']['candidate']['sha256']==expected,(platform,name,'stale measurement')
        record['benchmarks'][platform][name]=dict(path=path.relative_to(ROOT).as_posix(),sha256=hashlib.sha256(path.read_bytes()).hexdigest())
    path=ROOT/f'benchmarks/resultados/soak-alpha15-short-{platform}.json';proof=read(path)
    assert proof['passed'] and proof['compilerSha256']==expected and not proof['qualifies24Hours']
    record['shortSoak'][platform]=dict(path=path.relative_to(ROOT).as_posix(),elapsedSeconds=proof['elapsedSeconds'],workers=proof['workers'],qualifies24Hours=False)
record['supplemental']={}
for name,pattern in [('node-windows',r'\btests (\d+)'),('native-windows',r'(\d+) testes nativos'),('native-linux',r'(\d+) (?:testes nativos|testes adicionais|casos PE32)')]:
    path=ROOT/f'build/review-tests/{name}.log';contents=path.read_text(encoding='utf-8')
    counts=[int(n) for n in re.findall(pattern,contents)];assert counts,(name,'missing test evidence')
    record['supplemental'][name]=dict(counts=counts,log=path.relative_to(ROOT).as_posix(),sha256=hashlib.sha256(path.read_bytes()).hexdigest())
record['remoteCI']='current workflow job; overall workflow result is determined by GitHub' if os.environ.get('GITHUB_ACTIONS') else 'not triggered; local results do not assert remote success'
validation_path=ROOT/f'docs/VALIDACAO-ALPHA{version.split("alpha.")[1]}.json'
previous=read(validation_path) if validation_path.exists() else {}
record['longSoak']={}
for platform,binary in [('windows','assis.exe'),('linux','assis')]:
    path=ROOT/f'build/soak-alpha15/paced/{platform}.json'
    saved=previous.get('longSoak',{}).get(platform,{})
    if path.exists():
        proof=read(path);report_hash=hashlib.sha256(path.read_bytes()).hexdigest()
    elif saved.get('report'):
        proof=saved['report'];report_hash=saved['sha256']
    else:continue
    assert hashlib.sha256((json.dumps(proof,indent=2)+'\n').encode()).hexdigest()==report_hash
    assert proof['passed'] and proof['error'] is None and proof['qualifies24Hours']
    assert proof['requestedSeconds']>=86400 and proof['elapsedSeconds']>=86400
    assert len(proof['results'])==proof['workers']==4
    assert sorted(r['worker'] for r in proof['results'])==list(range(4))
    assert proof['networkMode']=='polling' and proof['intervalSeconds']==1
    for result in proof['results']:
        assert result['rounds']>0 and 0<result['peakRssBytes']<134217728
        assert result['peakHandles']<=result['initial']['handles']+32
    expected=hashlib.sha256((ROOT/'bin'/binary).read_bytes()).hexdigest()
    current=proof['compilerSha256']==expected and all((ROOT/name).is_file() and hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==value for name,value in proof['sourceHashes'].items())
    record['longSoak'][platform]=dict(originalPath=path.relative_to(ROOT).as_posix(),sha256=report_hash,compilerSha256=proof['compilerSha256'],matchesCurrentSourcesAndCompiler=current,elapsedSeconds=proof['elapsedSeconds'],workers=proof['workers'],rounds=sum(r['rounds'] for r in proof['results']),intervalSeconds=proof['intervalSeconds'],qualifies24Hours=True,report=proof)
qualified=len(record['longSoak'])==2 and all(r['matchesCurrentSourcesAndCompiler'] for r in record['longSoak'].values())
record['remainingGates']=[] if qualified else ['24 hours of actual qualified execution on current binaries and sources']
record['remainingGates']+=['complete IR statement/resource emission','native ARM64/macOS validation','asset rights and redistribution review','independent human acceptance']
if qualified:record['scope']+='; qualified 24-hour Windows/Linux polling and persistence endurance'
(ROOT/f'docs/VALIDACAO-ALPHA{version.split("alpha.")[1]}.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
print('Validation evidence recorded:',{p:r['testCount'] for p,r in record['native'].items()})
