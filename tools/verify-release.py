"""Verify current packages against their contents and executable contracts.

Historical benchmark reports describe their original releases; they are not
relabelled as measurements of the current compiler.
"""
from pathlib import Path
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import zipfile

ROOT=Path(__file__).resolve().parent.parent
version=json.loads((ROOT/'vscode-assisscript/package.json').read_text(encoding='utf-8'))['version']
catalog=json.loads((ROOT/'stdlib/catalogo.json').read_text(encoding='utf-8'))
assert catalog['version']==version
digest=lambda data:hashlib.sha256(data).hexdigest()
validation_name=f'docs/VALIDACAO-ALPHA{version.split("alpha.")[1]}.json'
validation=json.loads((ROOT/validation_name).read_text(encoding='utf-8'))
assert validation['version']==version and validation['status']=='passed'
assert validation['sourceHashes']=={p.relative_to(ROOT).as_posix():digest(p.read_bytes()) for p in sorted((ROOT/'src').iterdir()) if p.is_file()},'Stale source validation'
for platform,binary in [('windows','assis.exe'),('linux','assis')]:
    assert validation['native'][platform]['passed']
    assert validation['native'][platform]['compilerSha256']==digest((ROOT/'bin'/binary).read_bytes())
for platform,evidence in validation.get('longSoak',{}).items():
    report=evidence['report']
    assert digest((json.dumps(report,indent=2)+'\n').encode())==evidence['sha256']
    assert report['passed'] and report['error'] is None and report['qualifies24Hours']
    assert report['requestedSeconds']>=86400 and report['elapsedSeconds']>=86400
    assert len(report['results'])==report['workers']==4
    if evidence['matchesCurrentSourcesAndCompiler']:
        assert report['compilerSha256']==validation['native'][platform]['compilerSha256']
        assert all(digest((ROOT/name).read_bytes())==value for name,value in report['sourceHashes'].items())

for archive_path,prefix in [(ROOT/'dist'/f'assisscript-{version}.vsix','extension/'),(ROOT/'dist'/f'AssisScript-{version}-windows-linux.zip','AssisScript/')]:
    with zipfile.ZipFile(archive_path) as archive:
        assert archive.testzip() is None
        names=set(archive.namelist())
        assert all(not Path(n).is_absolute() and '..' not in Path(n).parts for n in names)
        assert not any(n.endswith(('.7z','.zip','.log','.pyc')) or '/build/' in n or '/historical/' in n for n in names)
        for name in ['bin/assis','bin/assis.exe','stdlib/catalogo.json','docs/LINGUAGEM.md','docs/MACOS.md','docs/HANDOFF-3.3-ALPHA.15.md','docs/BACKEND-ALPHA15.md','docs/PROGRESSO.md','docs/PROGRESSO.json','docs/RESTANTE-PARA-100.md',validation_name,'LICENSE','THIRD_PARTY_NOTICES.md']:
            assert archive.read(prefix+name)==(ROOT/name).read_bytes(),name
        for library in catalog['libraries']:
            assert archive.read(prefix+'stdlib/'+library['name']+'.assis')==(ROOT/'stdlib'/(library['name']+'.assis')).read_bytes()
            assert prefix+'docs/'+library['doc'] in names
        if prefix=='AssisScript/':
            for line in archive.read(prefix+'SHA256SUMS').decode().splitlines():
                expected,name=line.split('  ',1);assert digest(archive.read(prefix+name))==expected,name
        with tempfile.TemporaryDirectory(prefix='assis-package-') as temp:
            archive.extractall(temp);folder=Path(temp)/prefix.rstrip('/')
            compiler=folder/'bin'/('assis.exe' if os.name=='nt' else 'assis');compiler.chmod(0o755)
            def invoke(*args,input=None):return subprocess.run([str(compiler),*map(str,args)],input=input,capture_output=True,timeout=30)
            assert version.encode() in invoke('version').stdout
            for library in catalog['libraries']:
                result=invoke('check',folder/'stdlib'/(library['name']+'.assis'),'--library');assert result.returncode==0,result.stderr
            result=invoke('run',folder/'exemplos/31_language_review.assis','--debug')
            assert (result.returncode,result.stdout,result.stderr)==(0,'Turno de Assis (Clérigo) - HP 54/54\nDecimal: 0.30\n'.encode(),b''),result
            result=invoke('run',folder/'exemplos/32_backend_evolution.assis','--debug')
            assert (result.returncode,result.stdout,result.stderr)==(0,b'18\n',b''),result
            source=folder/'format-check.assis';source.write_text('safe fn main():int{print(utf8("ok"));return 0;}',encoding='utf-8')
            for target,magic in [('windows-x64',b'MZ'),('linux-x64',b'\x7fELF'),('macos-x64',b'\xcf\xfa\xed\xfe')]:
                output=folder/(target+'.exe');result=invoke('build',source,'--target',target,'-o',output)
                assert result.returncode==0,result.stderr;assert output.read_bytes().startswith(magic)
            for text in ['ASSIS C{}safe fn main():int{return 0;}','safe fn main():int{own a:Array<int>=[1];own b:Array<int>=move(a);print(a[0]);return 0;}']:
                result=invoke('check','rejected.assis','--stdin','--diagnostics=json',input=text.encode());assert result.returncode==1;assert json.loads(result.stderr)['code']=='A001'
print(f'Verified {version}: package checksums, {len(catalog["libraries"])} libraries, native execution and ELF/PE/Mach-O generation.')
