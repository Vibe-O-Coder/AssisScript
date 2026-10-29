"""Check the applied v1 identity and its propagation into shipped artifacts."""
from pathlib import Path
import hashlib
import json
import re
import struct
import zipfile
ROOT=Path(__file__).resolve().parent.parent
digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
manifest=json.loads((ROOT/'assets/IDENTIDADE-V1.json').read_text(encoding='utf-8'))
assert manifest['selected']=='v1'
for name,value in manifest['files'].items():assert digest(ROOT/name)==value,name
assert not list((ROOT/'assets').glob('*-original.*'))
for name in ('source','compiled'):
    svg=(ROOT/f'assets/propostas/{name}-v1.svg').read_text(encoding='utf-8')
    assert not re.search(r'<(?:image|text|script|foreignObject)\b|(?:href|url\s*\()',svg,re.I)
    assert (ROOT/f'assets/{name}.png').read_bytes()==(ROOT/f'vscode-assisscript/icons/{name}.png').read_bytes()
icns=bytes(map(int,re.findall(r'\d+',(ROOT/'src/icon_icns.h').read_text().split('{',1)[1].rsplit('}',1)[0])))
assert icns==(ROOT/'assets/compiled.icns').read_bytes()
def image(ico):
    raw=ico.read_bytes();count=struct.unpack_from('<H',raw,4)[0]
    return [raw[offset:offset+size] for _,_,_,_,_,_,size,offset in [struct.unpack_from('<BBBBHHII',raw,6+16*k) for k in range(count)]]
for binary,icon in [('bin/assis.exe','source'),('bin/assis-setup.exe','compiled')]:
    raw=(ROOT/binary).read_bytes()
    assert all(payload in raw for payload in image(ROOT/f'assets/{icon}.ico')),(binary,icon)
for payload in image(ROOT/'assets/compiled.ico'):assert payload in (ROOT/'bin/assis.exe').read_bytes()
for platform in ('windows','linux'):
    record=json.loads((ROOT/f'docs/build-audit-{platform}.json').read_text())
    assert all(b['identicalToRelease'] and all(x['licenseGroup']!='unclassified' for x in b['inputs']) for b in record['binaries'])
    assert record['sourceHashes']=={p.relative_to(ROOT).as_posix():digest(p) for p in sorted((ROOT/'src').iterdir()) if p.is_file()}
    for b in record['binaries']:assert b['sha256']==digest(ROOT/b['path'])
assert not (ROOT/'dist/AssisScript-historical.zip').exists(),'Retired binaries must not accompany the current distribution'
for archive in (ROOT/'dist').glob('*'):
    if archive.suffix not in ('.zip','.vsix') or 'historical' in archive.name:continue
    with zipfile.ZipFile(archive) as z:
        names=z.namelist();assert not any('-original.' in n or '/historical/' in n for n in names),archive
        prefix='extension/' if archive.suffix=='.vsix' else 'AssisScript/'
        for name in ('bin/assis','bin/assis.exe','vscode-assisscript/icons/source.png','vscode-assisscript/icons/compiled.png'):
            at=prefix+name.replace('vscode-assisscript/','' if archive.suffix=='.vsix' else 'vscode-assisscript/')
            assert z.read(at)==(ROOT/name).read_bytes(),(archive,at)
print('v1 source, editor, compiler, installer, generated PE resources, notices and packages: PASS')
