"""Native provider surface dumps, independent of desktop screenshots."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
from PIL import Image
ROOT=Path(__file__).resolve().parents[4];OUT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('builder',ROOT/'tools/build-platform.py');builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder)
compiler=Path(os.environ['ASSIS_BIN']).resolve()
source='<div type=document version="0.1" lang="pt-BR"><div type=head><div type=title>Transações e preferências</div></div><div type=body><div type=heading level=1>Leitura acessível</div><div type=paragraph>Ação, seleção e contraste usam o mesmo documento validado. Uma mudança só entra após preparar a apresentação.</div><div type=button id=change>Mostrar detalhes</div><div type=button disabled=true>Indisponível</div><div type=container id=details hidden=true><div type=paragraph>Detalhes da nova versão, com nomes e geometria acessíveis.</div></div></div></div>'
program='''import "std/reader.assis";
extern("assis_platform_v1.dll","assis_platform_v1.dll","assisp_test_snapshot") fn dump(window:int,borrow mut data:*byte,capacity:int):int;
safe fn main():int{
 own s:reader::Session=try_new reader::Session(32000000,250000,1);
 val metrics:int=reader::measure(utf8("M"),SCALE);assert(metrics>0);
 assert(s.prepare(1,utf8(SOURCE),780,520,metrics/4294967296,METRIC)==0);
 own w:window::Window=try_new window::Window(1,780,520,"surface transaction");assert(w.opened());assert(s.publish(w)==0);
 CHANGE
 val p:reader::Preferences=PALETTE;
 assert(s.paint_with(w,SCALE,p));
 own pixels:*byte=try_alloc<byte>(780*520*4);val capacity:int=len(pixels);
 unsafe{assert(dump(w.platform_token(),pixels,capacity)==capacity);}
 assert(write_bytes(1,pixels,capacity)==capacity);assert(w.close()==0);return 0;}
'''.replace('SOURCE',json.dumps(source,ensure_ascii=False))
change='''{own p:htdl::Patch=htdl::set_boolean(s.document(),htdl::find_id(s.document().nodes(),utf8("details")),7,false);
 assert(s.prepare_patch(2,p,780,520,metrics/4294967296,METRIC)==0 && s.publish(w)==0);}
 s.dispatch(2,new window::Event(0,3,1,1,9,1,1));'''
contrast='new reader::Preferences(0,true,true,u32(0x000000ff),u32(0xffffffff),u32(0x000000ff),u32(0xffffffff),u32(0xaaaaaaff),u32(0xffff00ff),u32(0x000000ff))'
scenarios=[('before',1000,'','reader::default_preferences()'),('updated',1000,change,'reader::default_preferences()'),
    ('contrast',1000,change+'s.dispatch(2,new window::Event(0,3,1,1,17,1,2));s.dispatch(2,new window::Event(0,3,1,1,65,1,3));',contrast),
    ('contrast-200',2000,change,contrast)]
records=[]
with tempfile.TemporaryDirectory(prefix='assis-transaction-surfaces-') as directory:
    folder=Path(directory);dll=folder/'assis_platform_v1.dll';builder.build(dll,testing=True)
    for name,scale,action,palette in scenarios:
        code=program.replace('CHANGE',action).replace('SCALE',str(scale)).replace('METRIC','reader::width_200' if scale==2000 else 'reader::width_100').replace('PALETTE',palette)
        path=folder/(name+'.assis');path.write_text(code,encoding='utf-8');surfaces=[]
        for mode,flags in [('optimized',[]),('reference',['--no-opt'])]:
            binary=folder/(name+'-'+mode+'.exe')
            built=subprocess.run([compiler,'build',path,'--safe','--debug','-o',binary,*flags],capture_output=True);assert built.returncode==0,built.stderr
            run=subprocess.run([binary],capture_output=True,timeout=30)
            assert (run.returncode,len(run.stdout),run.stderr)==(0,780*520*4,b''),(run.returncode,run.stderr)
            surfaces.append(run.stdout)
        assert surfaces[0]==surfaces[1],name
        im=Image.frombytes('RGBA',(780,520),surfaces[0],'raw','BGRA').convert('RGB')
        if name.startswith('contrast'):assert im.getpixel((0,0))==(0,0,0) and (255,255,255) in im.getdata()
        output=OUT/(name+'.png');im.save(output)
        records.append(dict(name=name,scale=scale,source_sha256=hashlib.sha256(code.encode()).hexdigest(),
            png_sha256=hashlib.sha256(output.read_bytes()).hexdigest(),pixels_sha256=hashlib.sha256(surfaces[0]).hexdigest(),optimized_reference_equal=True))
    report=dict(kind='native surface dump; not desktop screenshot',scenarios=records,
        compiler_sha256=hashlib.sha256(compiler.read_bytes()).hexdigest(),provider_sha256=hashlib.sha256(dll.read_bytes()).hexdigest(),
        source=source,screen_reader_acceptance=False,os_dpi_acceptance=False)
(OUT/'surfaces.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8',newline='\n')
print('Four transaction/contrast surfaces: optimized/reference equal')
