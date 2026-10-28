"""Translate historical AssisScript source to the canonical syntax.

Strings and ordinary comments are preserved. This is a source migration tool,
not a compatibility mode in the compiler. Always review the resulting diff.
"""
import argparse
from pathlib import Path
import re

WORDS = dict(zip(
    'ASSIS ASSIS_FODASE assis Assis AssIs AssiS FodAsE FoDaSe FODase assIS fodASE ASSis Fodase FODASE fodase foDASE aSSIS aSsIs fOdAsE fOdase FODasE FodASE ASSIS_fodase FODASE_fodase importa assis_assis assis_fodase ler_bytes agora escrever_bytes dormir relogio_civil arquivo_sincronizar arquivo_substituir arquivo_remover Arquivo arquivo_abrir arquivo_ler arquivo_escrever arquivo_fechar erro_io argumentos argumento_tamanho argumento_copiar fatia'.split(),
    'class extends fn let int byte bool text void if else while return print new free self true false null break continue alloc<byte> len import main init read_bytes monotonic_ms write_bytes sleep_ms civil_ms file_sync file_replace file_remove File file_open file_read file_write file_close io_error arg_count arg_size arg_copy slice_of'.split()))

def migrate(source):
    out=[];i=0
    while i<len(source):
        start=i
        if source[i] in ('"',"'"):
            quote=source[i];i+=1
            while i<len(source):
                if source[i]=='\\':i+=2
                elif source[i]==quote:i+=1;break
                else:i+=1
            out.append(source[start:i]);continue
        if source.startswith('//',i) or re.match(r'miyabi\b',source[i:]):
            end=source.find('\n',i);end=len(source) if end<0 else end
            out.append(source[i:end] if source.startswith('//',i) else '//'+source[i+6:end]);i=end;continue
        if source.startswith('/*',i) or re.match(r'te\b',source[i:]):
            historical=not source.startswith('/*',i);depth=1;i+=2;parts=['/*']
            while i<len(source) and depth:
                boundary=i==0 or not(re.match(r'\w',source[i-1]))
                opening=bool(re.match(r'te\b',source[i:])) and boundary if historical else source.startswith('/*',i)
                closing=bool(re.match(r'to\b',source[i:])) and boundary if historical else source.startswith('*/',i)
                if opening:depth+=1;parts.append('/*');i+=2
                elif closing:depth-=1;parts.append('*/');i+=2
                else:parts.append(source[i]);i+=1
            out.extend(parts);continue
        directive=re.match(r'#yuri[ \t]*<([^>\r\n]+)>|#body[ \t]+([^\s;]+)',source[i:])
        if directive:
            name=directive[1] or directive[2]
            # Historical dotted package paths resolve to directories.
            if directive[2] and name.endswith('.pillow'):name=name[:-7].replace('.','/')+'.pillow'
            out.append('import "'+name+'";');i+=len(directive[0]);
            if i<len(source) and source[i]==';':i+=1
            continue
        word=re.match(r'[A-Za-z_]\w*',source[i:])
        if word:
            out.append('' if word[0]=='div' else WORDS.get(word[0],word[0]));i+=len(word[0]);continue
        out.append(source[i]);i+=1
    return ''.join(out)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('files', type=Path, nargs='+')
    parser.add_argument('--write', action='store_true', help='replace input files')
    args = parser.parse_args()
    for file in args.files:
        result = migrate(file.read_text(encoding='utf-8-sig'))
        if args.write:
            file.write_text(result, encoding='utf-8', newline='\n')
        else:
            print(result, end='')

if __name__ == '__main__':
    main()
