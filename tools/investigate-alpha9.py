"""Resolve short-sample regressions using long paired workloads; preserve samples."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import statistics
import subprocess
import tempfile
import time

ROOT=Path(__file__).resolve().parent.parent
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--baseline',type=Path,required=True)
parser.add_argument('--report',type=Path,required=True)
parser.add_argument('--samples',type=int,default=21)
args=parser.parse_args();assert 7<=args.samples<=51
current=ROOT/'bin'/('assis.exe' if os.name=='nt' else 'assis');baseline=args.baseline.resolve()
report=json.loads(args.report.read_text(encoding='utf-8'));assert report['compilerSha256']==hashlib.sha256(current.read_bytes()).hexdigest()
n=10_000_000;expected=(str(n*n)+'\n').encode()
source=next(r['source'] for r in report['results'] if r['variant']=='atual-heap').replace(str(report['iterations']),str(n))
def run(command,output=None):
    r=subprocess.run(list(map(str,command)),capture_output=True,timeout=60)
    assert r.returncode==0 and not r.stderr,(command,r.returncode,r.stderr)
    if output is not None:assert r.stdout==output,(command,r.stdout,output)
with tempfile.TemporaryDirectory(prefix='assis-alpha9-investigate-') as temp:
    folder=Path(temp);file=folder/'main.assis';file.write_text(source,encoding='utf-8');rows=[]
    for compiler,label in [(baseline,'alpha8'),(current,'atual')]:
        for flags in [[],['--no-opt']]:
            variant=label+('-sem-opt' if flags else '');binary=folder/(variant+('.exe' if os.name=='nt' else ''))
            run([compiler,'build',file,'--debug','-o',binary,*flags]);run([binary],expected)
            run([compiler,'build',file,'-o',binary,*flags]);run([binary],expected)
            rows.append(dict(variant=variant,compiler=str(compiler),binary=str(binary),flags=flags,compileSamplesMs=[],samplesMs=[],binaryBytes=binary.stat().st_size,binarySha256=hashlib.sha256(binary.read_bytes()).hexdigest()))
    for sample in range(args.samples):
        for index in [(sample+j)%len(rows) for j in range(len(rows))]:
            row=rows[index];start=time.perf_counter();run([row['compiler'],'build',file,'-o',row['binary'],*row['flags']]);row['compileSamplesMs'].append((time.perf_counter()-start)*1000)
    for sample in range(args.samples+2):
        for index in [(sample+j)%len(rows) for j in range(len(rows))]:
            row=rows[index];start=time.perf_counter();run([row['binary']],expected);elapsed=(time.perf_counter()-start)*1000
            if sample>=2:row['samplesMs'].append(elapsed)
    for row in rows:
        row['medianMs']=statistics.median(row['samplesMs']);row['compileMedianMs']=statistics.median(row['compileSamplesMs']);del row['compiler'];del row['binary']
    report['investigation']=dict(iterations=n,samples=args.samples,warmups=2,source=source,expectedStdout=expected.decode(),baselineSha256=hashlib.sha256(baseline.read_bytes()).hexdigest(),rows=rows)
    args.report.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    path=args.report.with_suffix('.md');text=path.read_text(encoding='utf-8').split('\n## Investigação pareada')[0]
    text+=f'\n## Investigação pareada de variação acima de 5%\n\n{args.samples} amostras intercaladas, duas de aquecimento e 10 milhões de iterações por execução; mesma saída N² em debug e emissão normal. As amostras originais acima foram preservadas.\n\n| Variante | Compilar mediana (ms) | Executar mediana (ms) | Mínimo–máximo execução (ms) |\n| --- | ---: | ---: | ---: |\n'
    for row in rows:text+=f'| {row["variant"]} | {row["compileMedianMs"]:.3f} | {row["medianMs"]:.3f} | {min(row["samplesMs"]):.3f}–{max(row["samplesMs"]):.3f} |\n'
    text+='\nInício de processo e ASLR permanecem ativos. Diferenças de frequência/agendamento/layout podem afetar resultados; nenhum check foi retirado para melhorar números. Não há promessa de ganho geral.\n'
    path.write_text(text,encoding='utf-8',newline='\n')
    print([(row['variant'],round(row['medianMs'],3),round(row['compileMedianMs'],3)) for row in rows])
