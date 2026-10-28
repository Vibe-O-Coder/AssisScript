"""Reproduce release binaries and inventory every input in the actual link map.

Records archive members, startup objects, toolchain identity and system imports.
Does not infer legal clearance or image rights from technical provenance.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parent.parent
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--cc',default='gcc')
parser.add_argument('--output',type=Path,required=True)
parser.add_argument('--check',action='store_true',help='Check recorded release/source hashes, without rebuilding')
args=parser.parse_args()
digest=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()

def source_hashes():
    return {p.relative_to(ROOT).as_posix():digest(p) for p in sorted((ROOT/'src').iterdir()) if p.is_file()}

if args.check:
    report=json.loads(args.output.read_text(encoding='utf-8'))
    assert report['format']=='AssisScript-link-audit-v1'
    assert report['auditToolSha256']==digest(Path(__file__)),'Inventory tool changed; regenerate the report'
    assert report['sourceHashes']==source_hashes(),'Source inventory is stale'
    for binary in report['binaries']:
        assert binary['sha256']==digest(ROOT/binary['path']),binary['path']
        assert binary['identicalToRelease'] and binary['inputs']
        assert all(i['sha256'] and i['licenseGroup']!='unclassified' for i in binary['inputs'])
    print('Verified',args.output)
    raise SystemExit(0)

cc=shutil.which(args.cc)
if not cc:parser.error('Compiler not found')
cc=Path(cc).resolve();environment=os.environ.copy();environment['PATH']=str(cc.parent)+os.pathsep+environment.get('PATH','')

def run(command):
    return subprocess.check_output(list(map(str,command)),env=environment,stderr=subprocess.STDOUT,text=True,encoding='utf-8',errors='replace').strip()

def group(path):
    name=path.name
    if name.startswith(('libgcc','crtbegin','crtend')):return 'GCC runtime / GPL-3.0 with GCC Runtime Library Exception'
    if os.name=='nt':
        if name in ('libpthread.a','libwinpthread.a'):return 'MinGW-w64 winpthreads / bundled winpthreads notices (members list determines inclusion)'
        if name in ('crt2.o','crt2u.o','dllcrt2.o','default-manifest.o','libmingw32.a','libmingwex.a','libmoldname.a','libmsvcrt.a','libucrt.a','libucrtbase.a','libadvapi32.a','libkernel32.a','libshell32.a','libuser32.a'):
            return 'MinGW-w64 runtime and Windows import libraries / bundled MinGW-w64 notices'
        return 'unclassified'
    if name.startswith(('libc','libm','libpthread','librt','libdl','crt','Scrt','rcrt')):return 'GNU C Library / LGPL-2.1-or-later and component notices'
    return 'unclassified'

def package(path):
    try:
        if os.name=='nt':
            msys=cc.parents[2];local='/'+path.relative_to(msys).as_posix()
            return run([msys/'usr/bin/pacman.exe','-Qoq',local])
        return run(['dpkg-query','-S',path]).split(': /')[0]
    except (subprocess.CalledProcessError,ValueError):return 'unresolved; exact file hash recorded'

flags=['-O2','-std=c11','-Wall','-Wextra','-Wpedantic','-Wno-misleading-indentation','-static','-s']
if os.name=='nt':flags+=['-municode','-static-libgcc','-Wl,--no-insert-timestamp']
report=dict(format='AssisScript-link-audit-v1',platform=os.name,auditToolSha256=digest(Path(__file__)),compiler={'version':run([cc,'--version']).splitlines()[0],'target':run([cc,'-dumpmachine']),'sha256':digest(cc)},sourceHashes=source_hashes(),binaries=[])
with tempfile.TemporaryDirectory(prefix='assis-link-audit-') as temp:
    folder=Path(temp)
    sources=[('src/assisc.c','bin/assis.exe' if os.name=='nt' else 'bin/assis',[])]
    if os.name=='nt':sources.append(('src/windows_setup.c','bin/assis-setup.exe',['-lshell32','-ladvapi32','-luser32']))
    for source,destination,libs in sources:
        obj=folder/'source.o';output=folder/Path(destination).name;linkmap=folder/'link.map'
        run([cc,*flags,'-c',ROOT/source,'-o',obj])
        run([cc,*flags,obj,*libs,'-Wl,-Map,'+str(linkmap),'-Wl,--cref','-o',output])
        text=linkmap.read_text(encoding='utf-8',errors='replace')
        inputs={};synthetic=[]
        for line in text.splitlines():
            if line.startswith('LOAD '):
                name=line[5:].strip()
                if name=='dll stuff':synthetic.append('GNU ld generated PE import tables')
                elif name!=str(obj):inputs.setdefault(name,set())
        for archive,member in re.findall(r'([^\s()]+\.a)\(([^)]+)\)',text):inputs.setdefault(archive,set()).add(member)
        entries=[]
        for name,members in sorted(inputs.items()):
            path=Path(name).resolve()
            if path==obj.resolve():continue
            assert path.is_file(),('Unresolved link input',name)
            entries.append(dict(path=str(path),sha256=digest(path),licenseGroup=group(path),package=package(path),members=sorted(members)))
        objdump=cc.with_name('objdump.exe' if os.name=='nt' else 'objdump')
        if not objdump.is_file():objdump=shutil.which('objdump')
        imports=re.findall(r'DLL Name:\s*(\S+)',run([objdump,'-p',output])) if os.name=='nt' else re.findall(r'NEEDED\s+(\S+)',run([objdump,'-p',output]))
        record=dict(path=destination,source=source,sourceObjectSha256=digest(obj),sha256=digest(output),identicalToRelease=digest(output)==digest(ROOT/destination),flags=flags,linkLibraries=libs,systemImports=sorted(imports),inputs=entries,syntheticInputs=synthetic)
        assert entries and record['identicalToRelease'],('Audited build differs from distributed binary',destination)
        assert all(e['licenseGroup']!='unclassified' for e in entries),entries
        report['binaries'].append(record)
args.output.parent.mkdir(parents=True,exist_ok=True)
args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
print(args.output)
