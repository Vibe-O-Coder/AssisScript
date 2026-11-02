"""Reproduce the Unicode 17 property lookup from the pinned, licensed UCD."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / 'tests/fixtures/unicode-17.0.0'
NAMES = ['Other', 'CR', 'LF', 'Control', 'Extend', 'ZWJ', 'Regional_Indicator',
         'Prepend', 'SpacingMark', 'L', 'V', 'T', 'LV', 'LVT']

def records(name):
    for line in (DATA / name).read_text(encoding='utf-8').splitlines():
        fields = [s.strip() for s in line.split('#')[0].split(';')]
        if len(fields) < 2:
            continue
        bounds = fields[0].split('..')
        yield int(bounds[0], 16), int(bounds[-1], 16), fields[1:]

def generate():
    provenance = json.loads((DATA / 'PROVENANCE.json').read_text())
    for item in provenance['files']:
        assert hashlib.sha256((DATA / item['path']).read_bytes()).hexdigest() == item['sha256']
    values = [0] * 0x110000
    for start, end, fields in records('GraphemeBreakProperty.txt'):
        for cp in range(start, end + 1):
            # Algorithmic Hangul syllables avoid 798 alternating table ranges.
            if not 0xAC00 <= cp <= 0xD7A3:
                values[cp] |= NAMES.index(fields[0])
    for start, end, fields in records('emoji-data.txt'):
        if fields[0] == 'Extended_Pictographic':
            for cp in range(start, end + 1):
                values[cp] |= 64
    for start, end, fields in records('DerivedCoreProperties.txt'):
        if fields[0] == 'InCB':
            flag = {'Consonant': 1, 'Extend': 2, 'Linker': 3}[fields[1]] * 16
            for cp in range(start, end + 1):
                values[cp] |= flag
    ranges = []
    start = 0
    for end in range(1, len(values) + 1):
        if end == len(values) or values[start] != values[end]:
            if values[start]:
                ranges.append((start, end - 1, values[start]))
            start = end

    def tree(items, indent='    '):
        if not items:
            return indent + 'return 0;\n'
        middle = len(items) // 2
        start, end, value = items[middle]
        return (f'{indent}if(cp<{start}){{\n' + tree(items[:middle], indent + '    ') +
                f'{indent}}}\n{indent}if(cp<={end}){{return {value};}}\n' +
                tree(items[middle + 1:], indent))

    content = ('// BEGIN GENERATED UNICODE 17.0.0 DATA; tools/generate-grapheme-data.py\n'
               '// Unicode License V3: docs/licenses/UNICODE-LICENSE.txt.\n'
               '// Low nibble: GCB; bits 4..5: InCB; bit 6: Extended_Pictographic.\n'
               'pure fn properties(cp:int):int{\n'
               '    if(cp>=44032 && cp<=55203){if((cp-44032)%28==0){return 12;}return 13;}\n' +
               tree(ranges) + '}\n// END GENERATED UNICODE DATA')
    path = ROOT / 'stdlib/graphemes.assis'
    text = path.read_text(encoding='utf-8')
    begin = text.index('// BEGIN GENERATED')
    end = text.index('// END GENERATED UNICODE DATA') + len('// END GENERATED UNICODE DATA')
    return path, text[:begin] + content + text[end:], len(ranges)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    path, content, count = generate()
    if args.check:
        assert path.read_text(encoding='utf-8') == content, 'Regenerate grapheme properties'
    else:
        path.write_text(content, encoding='utf-8', newline='\n')
    print(f'Unicode 17.0.0: {count} merged property ranges')
