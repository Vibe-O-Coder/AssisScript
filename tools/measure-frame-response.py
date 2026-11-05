"""Compare the immutable base and candidate UI on the same Windows host/compiler."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import statistics
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'docs/ecossistema/evidencias/m3-local-resources-2026-11-04'
BASE='33b7431da1e84c8cdc26a8639290e42ba5a14e72'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
if os.name!='nt':raise SystemExit('Windows graphical comparison; not-run on this host')
compiler=Path(os.environ['ASSIS_BIN']).resolve();cc=Path(os.environ.get('ASSIS_TOOLCHAIN_BIN','C:/msys64/ucrt64/bin'))/'gcc.exe'
env=dict(os.environ,PATH=str(cc.parent)+os.pathsep+os.environ.get('PATH',''),PYTHONUTF8='1')
def base_file(name):return subprocess.check_output(['git','show',BASE+':'+name],cwd=ROOT)
def run(command,cwd):
    result=subprocess.run(list(map(str,command)),cwd=cwd,env=env,capture_output=True,timeout=120)
    if result.returncode:raise RuntimeError((result.returncode,result.stdout,result.stderr))
    return result.stdout
def stats(values):
    ordered=sorted(values)
    return dict(samples=len(values),min_ms=min(values),median_ms=statistics.median(values),p95_ms=ordered[max(0,(len(ordered)*95+99)//100-1)],max_ms=max(values))
reports={}
with tempfile.TemporaryDirectory(prefix='assis-response-comparison-') as temporary:
    temporary=Path(temporary)
    spec=importlib.util.spec_from_file_location('response_worker',ROOT/'tools/build-page-worker.py')
    builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder)
    worker=builder.build(temporary/'runtime',compiler)
    for label in ('base','candidate'):
        folder=temporary/label;folder.mkdir();sources={}
        if label=='base':
            for name in subprocess.check_output(['git','ls-tree','-r','--name-only',BASE,'stdlib'],cwd=ROOT).decode().splitlines():
                if name.endswith('.assis'):
                    target=folder/'std'/Path(name).name;target.parent.mkdir(exist_ok=True);target.write_bytes(base_file(name));sources[name]=sha(target)
            native=folder/'platform';native.mkdir()
            for name in ('windows.c','frame.inc','reader.inc','assis_platform_v1.h'):
                target=native/name;target.write_bytes(base_file('providers/platform/'+name));sources['providers/platform/'+name]=sha(target)
        else:native=ROOT/'providers/platform'
        command=[cc,'-O2','-std=c11','-Wall','-Wextra','-Wpedantic','-Werror','-shared','-static-libgcc','-Wl,--no-insert-timestamp',native/'windows.c','-o',folder/'assis_platform_v1.dll','-luser32','-lgdi32','-loleacc','-loleaut32','-lole32','-luuid']
        run(command,ROOT)
        for name in ('page-worker.exe','assis_worker_v1.dll'):shutil.copyfile(temporary/'runtime'/name,folder/name)
        readings={}
        for demo,filename in [('reading','65_frame_worker_window.assis'),('panels','59_page_motion_window.assis')]:
            text=base_file('exemplos/'+filename).decode() if label=='base' else (ROOT/'exemplos'/filename).read_text(encoding='utf-8')
            clock='monotonic_ms()' if label=='base' else 'pagepresent::clock_ms()'
            if demo=='reading':
                injected='''    if(option(utf8("--bench"))){
                    for(let i:int=0;i<12;i++){
                        val a:int=monotonic_ms();
                        if(s.reflow(640,420,0,65536,0,true,policy,pagepresent::measure)!=0){return 7;}
                        val b:int=monotonic_ms();if(s.publish_reflow(w)!=0 || w.present()!=0){return 8;}
                        print("REFLOW_MS",b-a,monotonic_ms()-b);
                    }return int(w.close()!=0);
                }\n'''
                args=[compiler,folder/'page-worker.exe','--bench']
            else:
                wait='let wait:int=16;' if label=='base' else 'let wait:int=16;if(motion.moving()){wait=0;}'
                injected='''    if(option(utf8("--bench"))){
                    let expanded:bool=false;
                    for(let round:int=0;round<6;round++){
                    expanded=!expanded;assert(evaluate(page,store.active_document(),input,expanded,false));
                    let last:int=CLOCK;val endpoint:int=16+int(expanded)*28;
                    for(let i:int=0;i<24;i++){
                        WAIT val event:window::Event=window.poll(wait);val now:int=CLOCK;version++;
                        if(!refresh(drawing,store.active_document(),page,motion,window,version,width,height,now-last,true,focus) || window.present()!=0){return 9;}
                        print("PANEL_MS",now-last,drawing.frame.box(2).bounds.y,endpoint);last=now;
                    }}return int(window.close()!=0);
                }\n'''.replace('CLOCK',clock).replace('WAIT',wait)
                args=['--bench']
            point=text.index('    if(option(utf8("--once")))');text=text[:point]+injected+text[point:]
            source=folder/(demo+'.assis');source.write_text(text,encoding='utf-8')
            binary=folder/(demo+'.exe');build=[compiler,'build',source,'--safe','--debug','-o',binary]
            if label=='base':build+=['-I',folder]
            run(build,ROOT);output=run([binary,*args],ROOT)
            log=OUT/f'windows-response-{label}-{demo}.log';log.write_bytes(output)
            pattern=rb'REFLOW_MS (\d+) (\d+)' if demo=='reading' else rb'PANEL_MS (\d+) (\d+) (\d+)'
            rows=[tuple(map(int,m)) for m in re.findall(pattern,output)]
            assert len(rows)==(12 if demo=='reading' else 144)
            values=[r[0] for r in rows] if demo=='reading' else [interval for i,(interval,y,end) in enumerate(rows) if i%24>0 and y!=end]
            readings[demo]=dict(log=log.name,log_sha256=sha(log),source_sha256=sha(source),binary_sha256=sha(binary),measurements=rows,summary=stats(values),scope='warm reflow' if demo=='reading' else 'six alternating 28px/4Hz spring transitions; active frame intervals, excludes terminal position and first frame of each transition')
        reports[label]=dict(provider_sha256=sha(folder/'assis_platform_v1.dll'),sources_sha256=sources,demos=readings)
report=dict(schema='native-frame-response-comparison-v1',base=BASE,compiler_sha256=sha(compiler),comparisons=reports,passed=True,
    limitations=['One Windows x64 host; local timing samples, not a universal latency/FPS guarantee','Base sources and libraries reconstructed from exact Git revision; both built with the same candidate compiler/toolchain','Numeric spring matrices unchanged; no desktop capture or screen-reader/DPI/IME acceptance from timing'])
(OUT/'response.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps({key:{d:v['summary'] for d,v in report['demos'].items()} for key,report in reports.items()},indent=2))
