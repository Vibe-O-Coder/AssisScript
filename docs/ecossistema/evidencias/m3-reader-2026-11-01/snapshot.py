"""Actual provider surfaces; these are not desktop or screen-reader captures."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
from PIL import Image

ROOT=Path(__file__).resolve().parents[4];OUT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('builder',ROOT/'tools/build-platform.py')
builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder)
compiler=Path(os.environ['ASSIS_BIN']).resolve()
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
with tempfile.TemporaryDirectory(prefix='assis-reader-snapshot-') as folder:
    folder=Path(folder);dll=folder/'assis_platform_v1.dll';builder.build(dll,testing=True)
    program='''import "std/reader.assis";
extern("assis_platform_v1.dll","assis_platform_v1.dll","assisp_test_snapshot") fn dump(window:int,borrow mut data:*byte,capacity:int):int;
safe fn main():int{
 own store:documents::Store=try_new documents::Store(32000000,250000,1000);
 assert(htdl::load(store,1,utf8(SOURCE)).code==0);
 own r:reader::Reader=reader::create(store.active_document(),1,780,520,SCALE);assert(r!=null && r.is_open());
 own w:window::Window=try_new window::Window(1,780,520,"reader snapshot");assert(w!=null && w.opened());
 ACTION assert(r.publish(w)==0 && r.paint(w,SCALE));
 own pixels:*byte=try_alloc<byte>(780*520*4);assert(pixels!=null);
 val capacity:int=len(pixels);unsafe{assert(dump(w.platform_token(),pixels,capacity)==capacity);}
 assert(write_bytes(1,pixels,len(pixels))==len(pixels));assert(w.close()==0);return 0;}
'''.replace('SOURCE',json.dumps((ROOT/'exemplos/45_leitura.htdl').read_text(encoding='utf-8'),ensure_ascii=False))
    records=[]
    for name,scale,action in [('reading-100',1000,''),('selection-100',1000,'r.dispatch(1,new window::Event(0,3,1,1,9,1,1));r.select(0,r.snapshot().text_size());'),
        ('reading-200',2000,''),('focus-200',2000,'r.dispatch(1,new window::Event(0,3,1,1,9,1,1));')]:
        source=program.replace('SCALE',str(scale)).replace('ACTION',action)
        path=folder/(name+'.assis');path.write_text(source,encoding='utf-8')
        surfaces=[]
        for mode,flags in [('optimized',[]),('reference',['--no-opt'])]:
            binary=folder/(name+'-'+mode+'.exe')
            built=subprocess.run([compiler,'build',path,'--safe','--debug','-o',binary,*flags],capture_output=True)
            assert built.returncode==0,built.stderr
            ran=subprocess.run([binary],capture_output=True,timeout=30)
            assert ran.returncode==0 and not ran.stderr and len(ran.stdout)==780*520*4,(ran.returncode,ran.stderr)
            surfaces.append(ran.stdout)
        assert surfaces[0]==surfaces[1],name
        output=OUT/(name+'.png');Image.frombytes('RGBA',(780,520),surfaces[0],'raw','BGRA').convert('RGB').save(output)
        records.append(dict(name=name,scale=scale,optimized_reference_equal=True,source_sha256=hashlib.sha256(source.encode()).hexdigest(),
            pixels_sha256=hashlib.sha256(surfaces[0]).hexdigest(),png_sha256=digest(output)))
    report=dict(kind='native provider surface dumps; not desktop screenshots',width=780,height=520,compiler_sha256=digest(compiler),
        provider_testing_sha256=digest(dll),document_sha256=digest(ROOT/'exemplos/45_leitura.htdl'),scenarios=records,
        production_diagnostic_exports=False,desktop_acceptance=False,real_screen_reader='not-run')
    (OUT/'surfaces.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
print('Four reader surfaces: optimized/reference bytes equal')
