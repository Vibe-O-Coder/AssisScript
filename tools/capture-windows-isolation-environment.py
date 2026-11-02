"""Capture the actual native host/toolchain and fresh compiler hash."""
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'docs/ecossistema/evidencias/m0-windows-isolation-2026-11-02';OUT.mkdir(parents=True,exist_ok=True)
host='windows' if os.name=='nt' else 'linux';compiler=Path(os.environ['ASSIS_BIN']).resolve();cc=shutil.which('gcc')
report=dict(host=host,platform=platform.platform(),machine=platform.machine(),processor=platform.processor(),python=sys.version,
    base='f12a1f2a9a7edf97e829d5f7c6e2f29980961414',compiler_sha256=hashlib.sha256(compiler.read_bytes()).hexdigest(),
    cc=cc,cc_version=subprocess.check_output([cc,'--version'],text=True).splitlines()[0],
    node_version=subprocess.check_output(['node','--version'],text=True).strip() if shutil.which('node') else None,
    node_status='available' if shutil.which('node') else 'not-run/unavailable (Node tests are Windows-only in this unit)')
(OUT/f'{host}-environment.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
print(host,report['platform'],report['compiler_sha256'])
