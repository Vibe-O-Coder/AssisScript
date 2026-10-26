"""Embed both position-independent runtimes using GNU binutils on either host."""
from pathlib import Path
import os
import re
import subprocess

root = Path(__file__).resolve().parent.parent
build = root / 'build'
build.mkdir(exist_ok=True)
prefix = os.environ.get('BINUTILS_DIR', '')

def run(tool, *args):
    executable = str(Path(prefix) / tool) if prefix else tool
    return subprocess.check_output([executable, *map(str, args)], text=True)

for source, macro, blob in [('runtime', 'RT', 'runtime_blob'), ('runtime_win', 'WRT', 'runtime_win_blob')]:
    obj, binary = build / f'{source}.o', build / f'{source}.bin'
    assembly = root / 'src' / f'{source}.S'
    lines = assembly.read_text(encoding='utf-8').splitlines()
    if os.name == 'nt':
        lines = [line for line in lines if not line.startswith('.section .note.GNU-stack')]
    # COFF rounds the raw text section to an alignment boundary. An explicit
    # end symbol excludes that padding and makes both hosts embed the same bytes.
    assembly = build / f'{source}-embed.S'
    assembly.write_text('\n'.join(lines) + '\n.text\nassis_runtime_blob_end:\n', encoding='utf-8')
    run('as', '--64', '-I', root / 'src', assembly, '-o', obj)
    run('objcopy', '-O', 'binary', '--only-section=.text', obj, binary)
    # Local references must be resolved by the assembler. External references
    # would make the raw blob invalid, so reject them before writing a header.
    relocs = run('objdump', '-r', obj)
    if re.search(r'(R_X86_64|IMAGE_REL_AMD64)', relocs):
        raise RuntimeError(f'Unresolved relocations in {source}: {relocs}')
    symbols = []
    end = None
    for line in run('nm', '-n', obj).splitlines():
        fields = line.split()
        if len(fields) == 3 and fields[2] == 'assis_runtime_blob_end':
            end = int(fields[0], 16)
        if len(fields) == 3 and fields[2].startswith('asrt_'):
            symbols.append((int(fields[0], 16), fields[2][5:]))
    data = binary.read_bytes()
    if end is None or not 0 < end <= len(data):
        raise RuntimeError(f'Invalid runtime boundary in {source}')
    data = data[:end]
    lines = [f'/* Generated from {source}.S by tools/embed-runtime.py. */', f'static const unsigned char {blob}[] = {{']
    lines += [','.join(map(str, data[i:i+24])) + ',' for i in range(0, len(data), 24)]
    lines += ['};']
    lines += [f'#define {macro}_{name} 0x{offset:x}' for offset, name in symbols if not name.startswith('import_')]
    if source == 'runtime_win':
        lines += ['static const struct { size_t offset; const char *name; } windows_import_patches[] = {']
        lines += [f'{{0x{offset:x}, "{re.sub(r"_[0-9]+$", "", name[7:])}"}},' for offset, name in symbols if name.startswith('import_')]
        lines += ['};']
    (root / 'src' / f'{blob}.h').write_text('\n'.join(lines) + '\n', encoding='utf-8')
print('Runtimes Linux e Windows incorporados.')
