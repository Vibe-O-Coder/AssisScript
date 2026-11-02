"""Generated native optional masks at 31/32/33/63 entries, versus a set closure."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parent.parent
class Mask(unittest.TestCase):
    def test_native_mask_boundaries_and_transitive_dependency_closure(self):
        compiler=os.environ.get('CC','C:/msys64/ucrt64/bin/gcc.exe' if os.name=='nt' else 'gcc')
        env=dict(os.environ,PATH=str(Path(compiler).parent)+os.pathsep+os.environ.get('PATH',''))
        for count in [31,32,33,63]:
            with self.subTest(count=count),tempfile.TemporaryDirectory(prefix='assis-mask-') as folder:
                folder=Path(folder);(folder/'tools').mkdir();(folder/'stdlib').mkdir();(folder/'src').mkdir()
                shutil.copyfile(ROOT/'tools/generate-install-manifest.py',folder/'tools/generate-install-manifest.py')
                dependencies={i:[] for i in range(count)}
                for i in [30,31,32,62]:
                    if i<count:dependencies[i]=[max(0,i-1),0]
                libraries=[dict(name=f'lib{i}',required=False,dependencies=[f'lib{j}' for j in dependencies[i]]) for i in range(count)]
                (folder/'stdlib/catalogo.json').write_text(json.dumps(dict(version='test',libraries=libraries)))
                r=subprocess.run([os.sys.executable,str(folder/'tools/generate-install-manifest.py')],capture_output=True,timeout=30);self.assertEqual(r.returncode,0,r.stderr)
                included=(folder/'src/install_optional.inc').read_text()
                (folder/'probe.c').write_text('#include <stdint.h>\n#include <stddef.h>\n#include <stdio.h>\n'+included+
                    f'\nint main(void){{uint64_t mask=UINT64_C(1)<<{count-1};for(int pass=0;pass<OPTIONAL_COUNT;pass++)for(int i=0;i<OPTIONAL_COUNT;i++)if(mask&(UINT64_C(1)<<i))mask|=optional_dependencies[i];for(int i=0;i<OPTIONAL_COUNT;i++)if(mask&(UINT64_C(1)<<i))printf("%d\\n",i);return 0;}}\n')
                binary=folder/'probe.exe';r=subprocess.run([compiler,'-std=c11','-O2',str(folder/'probe.c'),'-o',str(binary)],env=env,capture_output=True,timeout=30);self.assertEqual(r.returncode,0,r.stderr)
                r=subprocess.run([str(binary)],capture_output=True,timeout=15);self.assertEqual(r.returncode,0,r.stderr)
                expected={count-1};todo=[count-1]
                while todo:
                    for other in dependencies[todo.pop()]:
                        if other not in expected:expected.add(other);todo.append(other)
                self.assertEqual(set(map(int,r.stdout.split())),expected)

    def test_rejects_64_entries_before_touching_generated_files(self):
        with tempfile.TemporaryDirectory(prefix='assis-mask-') as folder:
            folder=Path(folder);(folder/'tools').mkdir();(folder/'stdlib').mkdir();(folder/'src').mkdir()
            shutil.copyfile(ROOT/'tools/generate-install-manifest.py',folder/'tools/generate-install-manifest.py')
            (folder/'stdlib/catalogo.json').write_text(json.dumps(dict(version='test',libraries=[dict(name=f'lib{i}',required=False) for i in range(64)])))
            target=folder/'src/install_files.inc';target.write_bytes(b'preserve')
            r=subprocess.run([os.sys.executable,str(folder/'tools/generate-install-manifest.py')],capture_output=True,timeout=30)
            self.assertNotEqual(r.returncode,0);self.assertEqual(target.read_bytes(),b'preserve')

if __name__=='__main__':unittest.main(verbosity=2)
