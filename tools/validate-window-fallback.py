"""Execute the explicit unsupported-provider branch on a native Linux/macOS host."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
ROOT = Path(__file__).resolve().parent.parent
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args(); output = args.output.resolve(); output.parent.mkdir(parents=True,exist_ok=True)
    if sys.platform not in ('linux','darwin'):
        print('Fallback execution requires native Linux/macOS');return 2
    compiler = Path(os.environ.get('ASSIS_BIN',ROOT/'bin/assis')).resolve()
    source = ROOT/'tests/fixtures/window-unavailable.assis'
    records = []
    for mode,flags in [('optimized',[]),('reference',['--no-opt'])]:
        binary = output.parent/f'window-unavailable-{mode}'
        built = subprocess.run([str(compiler),'build',str(source),'--safe','--debug','-o',str(binary),*flags],capture_output=True)
        code,stdout,stderr = None,b'',built.stderr
        if built.returncode == 0:
            result = subprocess.run([str(binary)],capture_output=True,timeout=10)
            code,stdout,stderr = result.returncode,result.stdout,result.stderr
        records.append(dict(mode=mode,build_return_code=built.returncode,return_code=code,
            stdout=stdout.decode('utf-8',errors='replace'),stderr=stderr.decode('utf-8',errors='replace'),
            passed=code==0 and stdout==b'provider unavailable\n' and stderr==b'',
            binary_sha256=digest(binary) if binary.is_file() else None))
    report = dict(platform=sys.platform,host=platform.platform(),architecture=platform.machine(),
        compiler_sha256=digest(compiler),source_sha256=digest(source),window_library_sha256=digest(ROOT/'stdlib/window.assis'),
        provider_state='unsupported',native_fallback_execution=records,passed=all(r['passed'] for r in records))
    output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
    print('Unsupported-provider branch:', 'pass' if report['passed'] else 'fail')
    return 0 if report['passed'] else 1
if __name__=='__main__':sys.exit(main())
