"""Render the example smoke paths with the native Windows test provider."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess

from PIL import Image, ImageChops

ROOT = Path(__file__).resolve().parents[1]
CAPTURE = '''
extern("assis_platform_v1.dll","assis_platform_v1.dll","assisp_test_control") fn visual_control(op:int,value:int):int;
extern("assis_platform_v1.dll","assis_platform_v1.dll","assisp_test_snapshot") fn visual_pixels(token:int,borrow mut pixels:*byte,size:int):int;
safe fn visual_capture(borrow mut output:File,width:int,height:int):void{
    val size:int=width*height*4;
    own pixels:*byte=try_alloc<byte>(size);
    assert(pixels!=null);
    unsafe{
        assert(visual_pixels(visual_control(8,0),pixels,size)==size);
        assert(file_write(output,pixels,size)==size);
    }
}
'''


def module(filename):
    spec = importlib.util.spec_from_file_location(filename, ROOT/'tools'/filename)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def replace_once(source, before, after):
    assert source.count(before) == 1, before
    return source.replace(before, after, 1)


def build_sources(output):
    reading = (ROOT/'exemplos/65_frame_worker_window.assis').read_text(encoding='utf-8')
    panels = (ROOT/'exemplos/59_page_motion_window.assis').read_text(encoding='utf-8')
    forms = (ROOT/'exemplos/72_local_forms_window.assis').read_text(encoding='utf-8')
    reading = replace_once(reading, '\nsafe fn main():int{', CAPTURE+'\nsafe fn main():int{')
    reading = replace_once(reading, 'if(option(utf8("--smoke"))){', '''if(option(utf8("--smoke"))){
        assert(status_line(w,0,640,420,policy)==0 && w.present()==0);
        {own picture:File=file_open("reading-100.raw",1);assert(picture!=null);
         visual_capture(picture,640,420);assert(file_close(picture)==0);}
        s.dispatch(1,1,new window::Event(0,3,7,1,9,1,10));
        for(let press:int=0;press<10;press++){
            val seq:int=11+press*2;
            assert(s.dispatch(1,1,new window::Event(0,3,7,1,13,1,seq)).status==0);
            s.dispatch(1,1,new window::Event(0,3,7,1,13,0,seq+1));
        }
        let counter:int=0;
        for(let turn:int=0;turn<5000;turn++){
            assert(s.advance(monotonic_ms())>=0);
            if(s.result().code==2){counter=s.result().result;if(counter==10){break;}}
            sleep_ms(1);
        }
        assert(counter==10 && s.queued()==0);
        assert(status_line(w,counter,640,420,policy)==0 && w.present()==0);
        {own picture:File=file_open("reading-counter.raw",1);assert(picture!=null);
         visual_capture(picture,640,420);assert(file_close(picture)==0);}''')
    reading = replace_once(reading,
        's.dispatch(1,1,new window::Event(0,3,7,1,17,1,1));s.dispatch(1,1,new window::Event(0,3,7,1,65,1,2));',
        's.dispatch(1,1,new window::Event(0,3,7,1,17,1,40));s.dispatch(1,1,new window::Event(0,3,7,1,65,1,41));')
    reading = replace_once(reading, 'assert(len(s.snapshot().reading.selected_text())==selected);',
        'assert(selected>0 && len(s.snapshot().reading.selected_text())==selected);'
        'assert(status_line(w,counter,640,420,policy)==0 && w.present()==0);'
        '{own picture:File=file_open("reading-200.raw",1);assert(picture!=null);'
        'visual_capture(picture,640,420);assert(file_close(picture)==0);}')
    panels = replace_once(panels, '\nsafe fn main():int{', CAPTURE+'\nsafe fn main():int{')
    panels = replace_once(panels, 'if(option(utf8("--smoke"))){',
        'if(option(utf8("--smoke"))){'
        '{own picture:File=file_open("panels-initial.raw",1);assert(picture!=null);'
        'visual_capture(picture,600,360);assert(file_close(picture)==0);}')
    panels = replace_once(panels, 'assert(drawing.frame.box(2).bounds.y>before_left',
        '{own picture:File=file_open("panels-moved.raw",1);assert(picture!=null);'
        'visual_capture(picture,600,360);assert(file_close(picture)==0);}'
        'assert(drawing.frame.box(2).bounds.y>before_left')
    forms = replace_once(forms, '\nsafe fn smoke(', CAPTURE+'\nsafe fn smoke(')
    for state, marker in [('unchecked', '    assert(session.snapshot().frame.checked(check)==0);\n    assert(session.dispatch(1'),
                          ('checked', '    assert(session.publish_reflow(window)==0 && window.present()==0);'),
                          ('200', '    print("FORMS WINDOW"')]:
        capture = (f'    {{own picture:File=file_open("forms-{state}.raw",1);assert(picture!=null);'
                   'visual_capture(picture,620,360);assert(file_close(picture)==0);}\n')
        if state == 'checked':
            forms = replace_once(forms, marker, marker+'\n'+capture)
        else:
            forms = replace_once(forms, marker, capture+marker)
    paths = []
    for name, source in [('reading', reading), ('panels', panels), ('forms', forms)]:
        path = output/f'{name}.assis'
        path.write_text(source, encoding='utf-8', newline='\n')
        paths.append(path)
    return paths


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if os.name != 'nt':
        parser.error('Windows native provider required')
    compiler = Path(os.environ['ASSIS_BIN']).resolve()
    out = args.output.resolve()
    work = ROOT/'build/visual-oracle'
    work.mkdir(parents=True, exist_ok=True)
    out.mkdir(parents=True, exist_ok=True)
    provider = work/'assis_platform_v1.dll'
    module('build-platform.py').build(provider, testing=True)
    worker = module('build-page-worker.py').build(work, compiler)
    paths = build_sources(work)
    sizes = {'reading-100': (640,420), 'reading-counter': (640,420), 'reading-200': (640,420),
             'panels-initial': (600,360), 'panels-moved': (600,360),
             'forms-unchecked': (620,360), 'forms-checked': (620,360), 'forms-200': (620,360)}
    modes = {}
    runs = {}
    for mode in ('optimized', 'reference'):
        run_dir = work/mode
        run_dir.mkdir(exist_ok=True)
        for name in sizes:
            (run_dir/f'{name}.raw').unlink(missing_ok=True)
        environment = dict(os.environ, PATH=str(work)+os.pathsep+os.environ['PATH'])
        modes[mode] = {}
        runs[mode] = {}
        for path in paths:
            binary = run_dir/(path.stem+'.exe')
            flags = ['--no-opt'] if mode == 'reference' else []
            subprocess.run([compiler,'build',path,'--safe','--debug','-o',binary,*flags], cwd=ROOT, check=True)
            extra = [compiler, worker['worker']] if path.stem == 'reading' else []
            run = subprocess.run([binary,*extra,'--smoke'], cwd=run_dir, env=environment,
                                 check=True, capture_output=True, text=True, timeout=30)
            expected = {'reading': 'FRAME WORKER WINDOW 2 11', 'panels': 'MOTION FRAME 2 10',
                        'forms': 'FORMS WINDOW 3 1'}[path.stem]
            assert run.stdout.strip() == expected and not run.stderr, (path.stem, run.stdout, run.stderr)
            runs[mode][path.stem] = dict(stdout=run.stdout.strip(), stderr=run.stderr, sha256=sha(binary))
        for name, size in sizes.items():
            raw = (run_dir/f'{name}.raw').read_bytes()
            assert len(raw) == size[0]*size[1]*4
            modes[mode][name] = raw
    assert modes['optimized'] == modes['reference']
    images = {name: Image.frombytes('RGB', size, modes['optimized'][name], 'raw', 'BGRX')
              for name,size in sizes.items()}
    counter = ImageChops.difference(images['reading-100'], images['reading-counter']).getbbox()
    panels = ImageChops.difference(images['panels-initial'], images['panels-moved']).getbbox()
    zoom = ImageChops.difference(images['reading-100'], images['reading-200']).getbbox()
    checkbox = ImageChops.difference(images['forms-unchecked'], images['forms-checked']).getbbox()
    form_zoom = ImageChops.difference(images['forms-checked'], images['forms-200']).getbbox()
    assert counter and counter[1] >= 392 and counter[3] <= 420
    assert panels and panels[2] <= 240
    assert zoom and zoom[1] < 100
    assert checkbox and checkbox[0] >= 24 and checkbox[2] <= 64 and checkbox[3] < 180
    assert form_zoom and form_zoom[1] < 100 and form_zoom[3] >= 339
    artifacts = {}
    for name, image in images.items():
        target = out/f'{name}.png'
        image.save(target)
        artifacts[target.name] = dict(width=image.width,height=image.height,sha256=sha(target))
    summary = dict(source='native GDI client raster from test-only provider', desktop_capture=False,
                   compiler_sha256=sha(compiler), provider_sha256=sha(provider),
                   worker_sha256=sha(Path(worker['worker'])), native_runs=runs, artifacts=artifacts,
                   difference_boxes=dict(counter=counter,panels=panels,zoom=zoom,checkbox=checkbox,form_zoom=form_zoom),
                   byte_identical_modes=True)
    (out/'visual.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(summary['difference_boxes']))


if __name__ == '__main__':
    main()
