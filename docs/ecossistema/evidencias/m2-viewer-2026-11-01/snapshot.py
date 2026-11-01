"""Dump the actual native viewer surface, not a desktop screenshot or visual gate."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
from PIL import Image

ROOT=Path(__file__).resolve().parents[4]
OUT=Path(__file__).resolve().parent
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
builder=module('builder',ROOT/'tools/build-platform.py')
compiler=Path(os.environ['ASSIS_BIN']).resolve()
source=(ROOT/'exemplos/44_artigo.htdl').read_text(encoding='utf-8')
with tempfile.TemporaryDirectory(prefix='assis-viewer-snapshot-') as folder:
    folder=Path(folder);dll=folder/'assis_platform_v1.dll';builder.build(dll,testing=True)
    program='''import "std/viewer.assis";
extern("assis_platform_v1.dll","assis_platform_v1.dll","assisp_test_control") fn control(a:int,b:int):int;
extern("assis_platform_v1.dll","assis_platform_v1.dll","assisp_test_snapshot") fn snapshot(t:int,borrow mut data:*byte,capacity:int):int;
safe fn main():int{
 own s:documents::Store=try_new documents::Store(32000000,250000,1000);
 assert(htdl::load(s,1,utf8(SOURCE)).code==0);
 val metric:int=viewer::measure(utf8("M"));assert(metric>=0);
 own v:viewer::View=try_new viewer::View(s.active_document(),1,780,520,metric/4294967296,viewer::text_width);
 assert(v!=null && v.is_open());
 own w:window::Window=try_new window::Window(1,780,520,"snapshot");assert(w!=null && w.opened());
 ACTION assert(viewer::paint(v,w));
 own pixels:*byte=try_alloc<byte>(780*520*4);assert(pixels!=null);
 val capacity:int=len(pixels);unsafe{assert(snapshot(control(8,0),pixels,capacity)==capacity);}
 assert(write_bytes(1,pixels,len(pixels))==len(pixels));assert(w.close()==0);
 unsafe{assert(control(3,0)==0);}return 0;}
'''.replace('SOURCE',json.dumps(source,ensure_ascii=False))
    modes=[]
    for name,action in [('top',''),('focused','v.dispatch(1,new window::Event(0,3,1,1,9,1,1));'),
                        ('bottom','v.scroll_to(v.max_scroll());')]:
        text=program.replace('ACTION',action);path=folder/(name+'.assis');path.write_text(text,encoding='utf-8')
        pixels=[]
        for label,flags in [('optimized',[]),('reference',['--no-opt'])]:
            binary=folder/(name+'-'+label+'.exe')
            result=subprocess.run([compiler,'build',path,'--safe','--debug','-o',binary,*flags],capture_output=True)
            assert result.returncode==0,result.stderr
            result=subprocess.run([binary],capture_output=True,timeout=30)
            assert result.returncode==0 and not result.stderr and len(result.stdout)==780*520*4,(result.returncode,result.stderr)
            pixels.append(result.stdout)
        assert pixels[0]==pixels[1],'Optimized/reference surfaces differ'
        image=Image.frombytes('RGBA',(780,520),pixels[0],'raw','BGRA').convert('RGB')
        output=OUT/(name+'.png');image.save(output)
        modes.append(dict(name=name,source_sha256=hashlib.sha256(text.encode()).hexdigest(),png_sha256=digest(output),
            pixels_sha256=hashlib.sha256(pixels[0]).hexdigest(),optimized_reference_equal=True))
    report=dict(kind='native provider surface dump; not desktop screenshot',width=780,height=520,
        compiler_sha256=digest(compiler),provider_testing_sha256=digest(dll),document_sha256=digest(ROOT/'exemplos/44_artigo.htdl'),
        scenarios=modes,production_diagnostic_exports=False,visual_gate=False)
    (OUT/'surfaces.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
print('Three native surfaces: optimized/reference byte equality')
