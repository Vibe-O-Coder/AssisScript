"""Validate native compiler hosts and x86_64 outputs, recording emulation explicitly."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import struct
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent.parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--execution', choices=['native', 'qemu', 'rosetta'], default='native')
    parser.add_argument('--expect-host', choices=['x86_64', 'arm64'])
    args = parser.parse_args()
    compiler = Path(os.environ.get('ASSIS_BIN', ROOT / 'bin' / ('assis.exe' if os.name == 'nt' else 'assis'))).resolve()
    machine = platform.machine().lower()
    arch = 'arm64' if machine in ('aarch64', 'arm64') else 'x86_64' if machine in ('amd64', 'x86_64') else machine
    target = 'windows-x64' if os.name == 'nt' else 'macos-x64' if sys.platform == 'darwin' else 'linux-x64'
    runner = {'native': [], 'qemu': ['qemu-x86_64'], 'rosetta': ['/usr/bin/arch', '-x86_64']}[args.execution]
    report = dict(platform=sys.platform, hostArchitecture=arch, execution=args.execution,
                  outputArchitecture='x86_64', nativeArm64Execution=False, passed=False, cases=[])
    args.output.parent.mkdir(parents=True, exist_ok=True)

    def invoke(*command):
        result = subprocess.run(list(map(str, command)), capture_output=True, text=True, encoding='utf-8', timeout=40)
        return result

    def checked(*command):
        result = invoke(*command)
        if result.returncode:
            raise AssertionError(f'{command}: exit {result.returncode}\n{result.stdout}{result.stderr}')
        return result

    def assert_format(path, destination):
        data = path.read_bytes()
        if destination == 'linux-x64':
            assert data[:6] == b'\x7fELF\x02\x01' and struct.unpack_from('<H', data, 18)[0] == 62, 'Expected x86_64 ELF64'
        elif destination == 'windows-x64':
            offset = struct.unpack_from('<I', data, 0x3c)[0]
            assert data[:2] == b'MZ' and data[offset:offset+4] == b'PE\0\0', 'Expected PE signature'
            assert struct.unpack_from('<H', data, offset+4)[0] == 0x8664, 'Expected x86_64 PE'
        else:
            assert struct.unpack_from('<II', data) == (0xfeedfacf, 0x01000007), 'Expected x86_64 Mach-O'

    # The same sources and independent expected results run on every host.
    cases = [
        ('branches', 'pure fn double(n:int):int{return n*2;}',
         'let sum:int=0;for(let i:int=0;i<10;i+=1){if(i%2==0){sum+=double(i);}}print(sum);', 0, '40\n'),
        ('widths', '', 'let a:i8=i8(127);a+=i8(1);let b:u64=u64(0xffffffffffffffff);'
         'if(b>u64(0)){b>>=63;}print(a,b);', 0, '-128 1\n'),
        ('ieee', '', 'let z:f64=0.0;let n:f64=z/z;if(n!=n&&!(n<z)){print(42);}let f:f32=f32(1.5);f*=f32(2.0);print(f);',
         0, '42\n0x1.8000000000000p+1\n'),
        ('ownership', '', 'own a:Array<int>=[1,2,3];a.push(4);let sum:int=0;'
         'for(let i:int=0;i<len(a);i+=1){own p:*int=alloc<int>(1);p[0]=a[i];sum+=p[0];}print(sum);', 0, '10\n'),
        ('lazy', '', 'let z:int=0;let no:bool=false;let yes:bool=true;'
         'if((no&&bool(1/z))||(!no&&yes)){print(42);}if(!(yes||bool(1/z))){print(99);}', 0, '42\n'),
        ('utf8', '', 'print(utf8("a\\0b"));', 0, 'a\0b\n'),
        ('trap', '', 'let z:int=0;print(1/z);', 70, ''),
    ]
    try:
        assert args.expect_host is None or arch == args.expect_host, f'Expected {args.expect_host} host, got {machine}'
        assert args.execution != 'native' or arch == 'x86_64', 'ARM64 output execution requires an explicit emulator'
        assert args.execution != 'qemu' or (arch == 'arm64' and sys.platform == 'linux'), 'QEMU job requires Linux ARM64'
        assert args.execution != 'rosetta' or (arch == 'arm64' and sys.platform == 'darwin'), 'Rosetta job requires macOS ARM64'
        report['compilerSha256'] = hashlib.sha256(compiler.read_bytes()).hexdigest()
        report['version'] = checked(compiler, 'version').stdout.strip()
        report['doctor'] = checked(compiler, 'doctor').stdout
        if arch == 'arm64':
            assert 'ARM64' in report['version'], 'Compiler must be built for the native ARM64 host'
        with tempfile.TemporaryDirectory(prefix='assis-ports-') as directory:
            folder = Path(directory)
            for name, helper, body, code, stdout in cases:
                source = folder / (name+'.assis')
                source.write_text(helper+'safe fn main():int{'+body+'return 0;}', encoding='utf-8')
                checked(compiler, 'check', source)
                ir = json.loads(checked(compiler, 'ir', source).stdout)
                assert ir['valueFormat'] == 'AssisScript-ScalarIR-v1'
                assert ir['backendFormat'] == 'AssisScript-TypedIR-v1' and ir['astFallbacks'] == 0
                report['backendFormat'] = ir['backendFormat']
                if arch == 'arm64':
                    for command in ['run', 'test']:
                        result = invoke(compiler, command, source, '--diagnostics=json')
                        assert result.returncode == 2 and 'ARM64' in json.loads(result.stderr)['message'], 'Expected explicit ARM64 execution limit'
                for optimized in [True, False]:
                    flags = [] if optimized else ['--no-opt']
                    outputs = {}
                    for destination in ['linux-x64', 'windows-x64', 'macos-x64']:
                        binary = folder / (name+'-'+destination+('' if optimized else '-no-opt')+('.exe' if destination == 'windows-x64' else ''))
                        checked(compiler, 'build', source, '--target', destination, '--debug', '-o', binary, *flags)
                        assert_format(binary, destination)
                        outputs[destination] = binary
                    binary = outputs[target]
                    result = invoke(*runner, binary)
                    assert (result.returncode, result.stdout) == (code, stdout), f'{name}, optimize={optimized}: {result.returncode}, {result.stdout!r}, {result.stderr}'
                    if code:
                        assert 'assis: erro' in result.stderr
                    else:
                        assert result.stderr == '', result.stderr
                    report['cases'].append(dict(name=name, optimized=optimized, passed=True,
                        target=target, returnCode=result.returncode,
                        binaries={key: hashlib.sha256(value.read_bytes()).hexdigest() for key,value in outputs.items()}))
                    print(f'{name} ({"optimized" if optimized else "no-opt"}): PASS', flush=True)
            invalid = folder / 'invalid.assis'
            invalid.write_text('safe fn main():int{let x:int="invalid";return 0;}', encoding='utf-8')
            result = invoke(compiler, 'check', invalid, '--diagnostics=json')
            assert result.returncode == 1 and json.loads(result.stderr)['code'] == 'A001'
            report['rejectedInvalidSource'] = True
        report['passed'] = True
    except Exception as error:
        report['error'] = str(error)
        print(str(error), file=sys.stderr)
    finally:
        args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False)+'\n', encoding='utf-8', newline='\n')
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
