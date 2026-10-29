"""Verify new target architectures, macOS signatures/DWARF, and real execution.

--runner qemu-aarch64 explicitly records emulation of ARM64 output on x64.
On native CI no runner is used, and the executable's CPU is checked first.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import shlex
import shutil
import struct
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parent.parent
def macho(data):
    cpu=struct.unpack_from('<I',data,4)[0]
    count=struct.unpack_from('<I',data,16)[0];at=32;commands={};sections=[];ranges=[]
    for _ in range(count):
        cmd,size=struct.unpack_from('<II',data,at);assert size>=8 and at+size<=len(data)
        commands[cmd]=data[at:at+size]
        if cmd==0x19:
            name,vm,vmsize,off,used,maxp,initp,nsects=struct.unpack_from('<16sQQQQIII',data,at+8)
            assert off+used<=len(data) and not (initp&2 and initp&4)
            if vmsize:ranges.append((vm,vm+vmsize,name))
            if cpu==0x100000c:assert vm%16384==0
            for k in range(nsects):sections.append(data[at+72+80*k:at+88+80*k].rstrip(b'\0'))
        at+=size
    assert at==32+struct.unpack_from('<I',data,20)[0]
    ranges.sort()
    assert all(a[1]<=b[0] for a,b in zip(ranges,ranges[1:])),('Overlapping Mach-O segments',ranges)
    assert {b'__debug_info',b'__debug_line',b'__debug_abbrev'}<=set(sections)
    assert 2 in commands
    if cpu==0x100000c:
        offset,length=struct.unpack_from('<II',commands[0x1d],8)
        sig=data[offset:offset+length]
        assert struct.unpack_from('>III',sig)==(0xfade0cc0,length,1)
        cd_at=struct.unpack_from('>I',sig,16)[0];cd=sig[cd_at:]
        magic,cd_size,version,flags,hash_at,ident,special,slots,limit=struct.unpack_from('>9I',cd)
        assert magic==0xfade0c02 and version==0x20400 and flags&2 and special==0 and limit==offset
        assert cd_size==len(cd) and cd[36:40]==bytes([32,2,0,12])
        for k in range(slots):assert hashlib.sha256(data[k*4096:min(offset,(k+1)*4096)]).digest()==cd[hash_at+k*32:hash_at+(k+1)*32]
    return cpu

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--runner');p.add_argument('--target');p.add_argument('--debugger',action='store_true');args=p.parse_args()
    compiler=Path(os.environ.get('ASSIS_BIN',ROOT/'bin'/('assis.exe' if os.name=='nt' else 'assis'))).resolve()
    arch='arm64' if platform.machine().lower() in ('arm64','aarch64') else 'x64'
    native=('windows-x64' if os.name=='nt' else ('macos-' if sys.platform=='darwin' else 'linux-')+arch)
    target=args.target or native;runner=shlex.split(args.runner or '')
    report=dict(format='AssisScript-target-validation-v1',host=sys.platform,hostArchitecture=arch,target=target,execution=runner or 'native',compilerSha256=hashlib.sha256(compiler.read_bytes()).hexdigest(),passed=False,cases=[])
    def run(*cmd):
        v=subprocess.run(list(map(str,cmd)),capture_output=True,text=True,encoding='utf-8',timeout=60)
        assert v.returncode==0,(cmd,v.returncode,v.stdout,v.stderr)
        return v
    try:
        with tempfile.TemporaryDirectory(prefix='assis-targets-') as temp:
            folder=Path(temp)
            source=folder/'probe.assis';source.write_text('safe fn calc(n:int):int{\nlet x:int=n+2;\nprint(x);\nreturn x;\n}\nsafe fn main():int{assert(calc(40)==42);own b:*int=alloc<int>(2);b[1]=42;assert(b[1]==42);return 0;}\n',encoding='utf-8')
            for destination in ['linux-x64','windows-x64','macos-x64','linux-arm64','macos-arm64']:
                for optimize in (True,False):
                    binary=folder/(destination+('' if optimize else '-no-opt')+('.exe' if destination=='windows-x64' else ''))
                    run(compiler,'build',source,'--target',destination,'--symbols','--debug','-o',binary,*([] if optimize else ['--no-opt']))
                    data=binary.read_bytes()
                    if destination.startswith('macos'):assert macho(data)==(0x100000c if destination.endswith('arm64') else 0x1000007)
                    elif destination.startswith('linux'):assert struct.unpack_from('<H',data,18)[0]==(183 if destination.endswith('arm64') else 62)
                    else:assert data[:2]==b'MZ'
                    mapping=json.loads(Path(str(binary)+'.map.json').read_text());assert mapping['imageBase']==(0x100000000 if destination.startswith('macos') else 0x140000000 if destination.startswith('windows') else 0)
                    if destination==target:
                        result=run(*runner,binary);assert (result.stdout,result.stderr)==('42\n','')
                        if args.debugger and optimize:
                            if sys.platform=='darwin':
                                if destination.endswith('arm64'):run('codesign','--verify','--strict',binary)
                                run('dwarfdump','--verify',binary)
                                dbg=run('lldb','--batch','-o',f'breakpoint set --file {source.name} --line 3','-o','run','-o','frame variable n x','-o','bt',binary)
                                assert 'n = 40' in dbg.stdout and 'x = 42' in dbg.stdout and 'main' in dbg.stdout,dbg.stdout
                            elif sys.platform=='linux':
                                dbg=run('gdb','-nx','-nh','-batch','-ex',f'break {source}:3','-ex','run','-ex','print n','-ex','print x','-ex','bt',binary)
                                assert '= 40' in dbg.stdout and '= 42' in dbg.stdout and 'main' in dbg.stdout,dbg.stdout
                    if destination.startswith('macos') and optimize:
                        bundle=folder/(destination+'.app')
                        run(compiler,'build',source,'--target',destination,'--symbols','--app','-o',bundle)
                        assert (bundle/'Contents/Resources/compiled.icns').read_bytes()==(ROOT/'assets/compiled.icns').read_bytes()
                        assert b'CFBundleIconFile' in (bundle/'Contents/Info.plist').read_bytes()
                        assert macho((bundle/'Contents/MacOS/program').read_bytes())==(0x100000c if destination.endswith('arm64') else 0x1000007)
                    report['cases'].append(dict(target=destination,optimized=optimize,sha256=hashlib.sha256(data).hexdigest(),executed=destination==target))
            if target.endswith('arm64'):
                deep=folder/'deep.assis';deep.write_text('safe fn deep(n:int):int{own cell:*int=alloc<int>(1);cell[0]=n;if(n>0){return deep(n-1);}return cell[0];}safe fn main():int{return deep(200000);}',encoding='utf-8')
                binary=folder/'deep';run(compiler,'build',deep,'--target',target,'-o',binary)
                result=subprocess.run([*runner,str(binary)],capture_output=True,text=True,timeout=60)
                assert result.returncode==70 and 'pilha' in result.stderr,(result.returncode,result.stderr)
                report['runtimeStackGuard']=True
            report['passed']=True
    except Exception as e:report['error']=str(e);print(str(e),file=sys.stderr)
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    return 0 if report['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
