"""Exercise offline installation without changing the user's shell profile."""
from pathlib import Path
import os
import subprocess
import tempfile
import platform
import json
ROOT=Path(__file__).resolve().parent.parent
with tempfile.TemporaryDirectory(prefix='assis-native-install-') as temp:
    prefix=Path(temp)/'install with spaces'
    subprocess.run(['sh',ROOT/'instalar.sh','--prefix',prefix,'--no-path','--minimal'],check=True)
    binary=prefix/'bin/assis'
    subprocess.run([binary,'version'],check=True)
    subprocess.run([binary,'run',ROOT/'exemplos/01_ola.assis','--legacy','--debug'],check=True)
    assert (prefix/'share/assisscript/assets/source.icns').is_file()
    user=prefix/'share/assisscript/docs/user-file.txt';user.write_text('preserve')
    subprocess.run(['sh',ROOT/'desinstalar.sh','--prefix',prefix],check=True)
    assert not binary.exists() and user.read_text()=='preserve'
out=ROOT/f'build/review-tests/installer-{platform.system().lower()}-{platform.machine().lower()}.json';out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(dict(passed=True,platform=platform.system(),architecture=platform.machine(),checks=['offline install','native run','v1 ICNS','uninstall','preserve user file']),indent=2)+'\n')
print('Native install, run, icons and uninstall: PASS')
