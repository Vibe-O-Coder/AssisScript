"""Check all top-level examples in the default profile and both RPG endings."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parent.parent
parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
compiler=Path(os.environ.get('ASSIS_BIN',ROOT/'bin'/('assis.exe' if os.name=='nt' else 'assis')))
records=[]
for source in sorted((ROOT/'exemplos').glob('*.assis')):
    result=subprocess.run([compiler,'check',source],capture_output=True,timeout=30)
    records.append(dict(file=source.name,passed=result.returncode==0,error=result.stderr.decode('utf-8')))
endings=[]
if (ROOT/'exemplos/rpg.assis').exists():
    for seed in [1,5]:
        result=subprocess.run([compiler,'run',ROOT/'exemplos/rpg.assis','--debug'],input=f'2\n{seed}\n'.encode(),capture_output=True,timeout=30)
        output=result.stdout.decode('utf-8');ending='victory' if 'GLÓRIA AO GRUPO' in output else 'defeat' if 'FIM DE JOGO' in output else 'unknown'
        endings.append(dict(seed=seed,ending=ending,returnCode=result.returncode,stderr=result.stderr.decode('utf-8'),outputBytes=len(result.stdout)))
passed=all(r['passed'] for r in records) and (not endings or ({r['ending'] for r in endings}=={'victory','defeat'} and all(r['returnCode']==0 and not r['stderr'] for r in endings)))
report=dict(compilerSha256=hashlib.sha256(compiler.read_bytes()).hexdigest(),passed=passed,examples=records,rpg=endings)
args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
print(f'Examples: {sum(r["passed"] for r in records)}/{len(records)}; RPG endings: '+','.join(r['ending'] for r in endings))
raise SystemExit(0 if passed else 1)
