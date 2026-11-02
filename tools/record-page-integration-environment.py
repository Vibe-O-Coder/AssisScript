"""Record toolchain and non-identifying hardware fields for this local evidence."""
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'docs/ecossistema/evidencias/m0-page-integration-2026-11-02'
host='windows' if os.name=='nt' else 'linux'
cc='C:/msys64/ucrt64/bin/gcc.exe' if os.name=='nt' else 'gcc'
data=dict(platform=platform.platform(),python=sys.version,logical_cpus=os.cpu_count(),processor=platform.processor(),
    gcc=subprocess.check_output([cc,'--version'],text=True).splitlines()[0],
    node=json.loads(subprocess.check_output(['node','-p','JSON.stringify(process.versions)'],text=True)),
    compiler_sha256=hashlib.sha256(Path(os.environ['ASSIS_BIN']).read_bytes()).hexdigest())
if os.name=='nt':
    query='Get-CimInstance Win32_Processor | Select-Object Name,NumberOfCores,NumberOfLogicalProcessors | ConvertTo-Json -Compress'
    data['cpu']=json.loads(subprocess.check_output(['powershell.exe','-NoProfile','-Command',query],text=True))
else:
    data['cpu']=dict(line.split(':',1) for line in Path('/proc/cpuinfo').read_text().splitlines() if line.startswith(('model name','cpu cores','siblings')))
    data['memory_kib']=int(Path('/proc/meminfo').read_text().splitlines()[0].split()[1])
(OUT/f'{host}-environment.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
