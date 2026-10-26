"""Replay the independently checked Windows/Node corpus on Linux without Node.

Generate first: ASSIS_V32_FIXTURE_DIR=build/v32-fixtures node --test tests/test-v32.js
Then run: python3 tests/test-v32-portable.py
"""
from pathlib import Path
import base64
import json
import subprocess
import sys
root=Path(__file__).resolve().parent.parent
compiler=root/'bin'/('assis.exe' if sys.platform=='win32' else 'assis')
fixtures=sorted((root/'build/v32-fixtures').glob('*.json'))
assert len(fixtures)>=70, 'Gere o corpus Node 3.2 antes de executar'
for file in fixtures:
    case=json.loads(file.read_text(encoding='utf-8'))
    source=file.with_suffix('.assis')
    args=case['args']
    result=subprocess.run([compiler,args[0],source,*args[1:]],input=base64.b64decode(case['input']),capture_output=True,timeout=30)
    assert result.returncode==case['status'], (file.name,result.returncode,result.stderr)
    assert result.stdout.decode('utf-8')==case['stdout'], (file.name,'stdout')
    actual=result.stderr.decode('utf-8')
    if '--diagnostics=json' in args:
        expected=json.loads(case['stderr']); actual_json=json.loads(actual)
        expected.pop('file',None);actual_json.pop('file',None)
        assert actual_json==expected,(file.name,actual_json,expected)
    else:
        assert actual.replace(str(source),'<source>')==case['stderr'].replace(case['sourcePath'],'<source>'),(file.name,actual,case['stderr'])
print(f'ASSIS 3.2: {len(fixtures)} casos portáveis aprovados em {sys.platform}.')
