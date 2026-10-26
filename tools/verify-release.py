"""Verify offline VSIX/release contents, checksums and bundled compiler."""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import zipfile

root = Path(__file__).resolve().parent.parent
version = json.loads((root / 'vscode-assisscript/package.json').read_text())['version']
catalog = json.loads((root / 'stdlib/catalogo.json').read_text())
assert catalog['version'] == version
with zipfile.ZipFile(root / 'dist' / f'assisscript-{version}.vsix') as archive:
    assert archive.testzip() is None
    names = set(archive.namelist())
    for library in catalog['libraries']:
        for name in ['extension/stdlib/' + library['name'] + '.assis', 'extension/docs/' + library['doc']]:
            assert name in names, name
    for name in ['bin/assis', 'bin/assis.exe', 'stdlib/catalogo.json', 'docs/ERROS.md', 'docs/DESEMPENHO.json', 'docs/MEMORIA-OWNERSHIP.md', 'docs/MELHORIAS-3.2.md', 'benchmarks/resultados/nativo-3.2.md', 'exemplos/14_ownership.assis', 'exemplos/12_relatorio_vendas.assis', 'exemplos/13_codificacao.assis',
                 'docs/PROGRAMACAO-FUNCIONAL.md', 'docs/CONTRATOS-E-SEGURANCA.md', 'docs/PROCEDENCIA.md', 'docs/PLANO-EVOLUCAO-E-HANDOFF.md', 'docs/HANDOFF-3.3-ALPHA.md', 'docs/VALIDACAO-3.3-ALPHA.md', 'exemplos/15_funcional.assis',
                 'docs/GENERICS.md', 'docs/HANDOFF-3.3-ALPHA.2.md', 'docs/VALIDACAO-3.3-ALPHA.2.md', 'exemplos/16_generics.assis',
                 'docs/FUNCOES-E-EFEITOS.md', 'docs/HANDOFF-3.3-ALPHA.3.md', 'docs/VALIDACAO-3.3-ALPHA.3.md', 'exemplos/17_funcoes.assis',
                 'docs/HANDOFF-3.3-ALPHA.4.md', 'docs/VALIDACAO-3.3-ALPHA.4.md', 'exemplos/18_classes_genericas.assis',
                 'docs/HANDOFF-3.3-ALPHA.5.md', 'docs/VALIDACAO-3.3-ALPHA.5.md', 'docs/PROGRESSO.md', 'docs/PROGRESSO.json',
                 'docs/HANDOFF-3.3-ALPHA.6.md', 'docs/VALIDACAO-3.3-ALPHA.6.md', 'docs/OWNERSHIP-FUNCOES.md', 'exemplos/19_ownership_funcoes.assis', 'docs/HANDOFF-3.3-ALPHA.7.md', 'docs/VALIDACAO-3.3-ALPHA.7.md', 'docs/VALORES-E-VARIANTES.md', 'docs/IO-E-APLICACAO-A.md', 'docs/ABI-NATIVA.md', 'exemplos/20_valores_e_resultados.assis', 'exemplos/21_relatorio_csv_stream.assis']:
        assert 'extension/' + name in names, name
    assert archive.read('extension/bin/assis') == (root / 'bin/assis').read_bytes()
    assert archive.read('extension/bin/assis.exe') == (root / 'bin/assis.exe').read_bytes()
    for name in ['NUMEROS.md','PACOTES-E-NAMESPACES.md','FERRAMENTAS-ALPHA.8.md','EVENTOS-E-PERSISTENCIA.md','HANDOFF-3.3-ALPHA.8.md','VALIDACAO-3.3-ALPHA.8.md']:
        assert archive.read('extension/docs/'+name) == (root/'docs'/name).read_bytes()
    for name in ['RECURSOS-E-FATIAS.md','HANDOFF-3.3-ALPHA.9.md','VALIDACAO-3.3-ALPHA.9.md']:
        assert archive.read('extension/docs/'+name) == (root/'docs'/name).read_bytes()
    assert archive.read('extension/tools/assis-lsp.js') == (root/'tools/assis-lsp.js').read_bytes()
    assert 'extension/exemplos/pacote-offline/assis.lock' in names
    progress = json.loads(archive.read('extension/docs/PROGRESSO.json'))
    assert progress['version'] == version
    assert sum(phase['weight'] for phase in progress['phases']) == 100
    credits = {'complete': 1, 'partial': 0.5, 'pending': 0}
    points = sum(phase['weight'] * sum(credits[item['status']] for item in phase['items']) / len(phase['items']) for phase in progress['phases'])
    estimate = int(points + 0.5)
    assert f'**Conclusão estimada: {estimate}%**' in archive.read('extension/docs/PROGRESSO.md').decode('utf-8')
    for name in ['PROGRESSO.md', 'PROGRESSO.json']:
        assert archive.read('extension/docs/' + name) == (root / 'docs' / name).read_bytes()
    for platform_name, binary_name in [('windows', 'assis.exe'), ('linux', 'assis')]:
        report_path = f'extension/benchmarks/resultados/evolucao-alpha9-{platform_name}'
        assert report_path + '.md' in names
        report = json.loads(archive.read(report_path + '.json'))
        assert report['compilerSha256'] == hashlib.sha256(archive.read('extension/bin/' + binary_name)).hexdigest()
        assert report['completionMetricVersion'] == version and report['completionEstimatePercent'] == estimate
        assert len(report['nativeFeatures']) == 6
    assert all(not Path(name).is_absolute() and '..' not in Path(name).parts for name in names)
    with tempfile.TemporaryDirectory(prefix='assis-package-') as temp:
        archive.extractall(temp)
        folder = Path(temp) / 'extension'
        compiler = folder / 'bin' / ('assis.exe' if sys.platform == 'win32' else 'assis')
        compiler.chmod(0o755)
        result = subprocess.run([compiler, 'version'], capture_output=True, timeout=15)
        assert result.returncode == 0 and version.encode() in result.stdout, result.stderr
        result = subprocess.run([compiler, 'run', folder / 'exemplos/12_relatorio_vendas.assis'], capture_output=True, timeout=30)
        assert result.returncode == 0, result.stderr.decode()
        assert result.stdout == b'Cafe, centavos: 5000\nCha, centavos: 1700\nMenor venda: 1250\n'
        result = subprocess.run([compiler, 'run', folder / 'exemplos/14_ownership.assis', '--debug'], capture_output=True, timeout=30)
        assert result.returncode == 0 and result.stderr == b'', result.stderr.decode()
        assert result.stdout == b'Miyabi encontrou 10 20\ndiv 0 11\ndiv 1 20\n'
        result = subprocess.run([compiler, 'run', folder / 'exemplos/15_funcional.assis', '--debug'], capture_output=True, timeout=30)
        assert (result.returncode, result.stdout, result.stderr) == (0, b'306 3628800\n', b''), result.stderr.decode()
        result = subprocess.run([compiler, 'run', folder / 'exemplos/16_generics.assis', '--debug'], capture_output=True, timeout=30)
        assert (result.returncode, result.stdout, result.stderr) == (0, b'42 Assis 7 aSsIs\n', b''), result.stderr.decode()
        result = subprocess.run([compiler, 'run', folder / 'exemplos/17_funcoes.assis', '--debug'], capture_output=True, timeout=30)
        assert (result.returncode, result.stdout, result.stderr) == (0, b'42\n12\n', b''), result.stderr.decode()
        result = subprocess.run([compiler, 'run', folder / 'exemplos/18_classes_genericas.assis', '--debug'], capture_output=True, timeout=30)
        assert (result.returncode, result.stdout, result.stderr) == (0, b'21 42\n', b''), result.stderr.decode()
        result = subprocess.run([compiler, 'run', folder / 'exemplos/19_ownership_funcoes.assis', '--safe', '--debug'], capture_output=True, timeout=30)
        assert (result.returncode, result.stdout, result.stderr) == (0, b'6 3 24\n4 8 12\n', b''), result.stderr.decode()
        result = subprocess.run([compiler, 'run', folder / 'exemplos/20_valores_e_resultados.assis', '--safe', '--debug'], capture_output=True, timeout=30)
        assert (result.returncode, result.stdout, result.stderr) == (0, b'19 21 42\n42\n42\n', b''), result.stderr.decode()
        for name, expected in [('22_numeros.assis',b'0x1.8000000000000p+1 42\n0\n'),('23_eventos.assis',b'1\n2\n3\n'),('pacote-offline/assis.assis',b'42\n')]:
            result=subprocess.run([compiler,'run',folder/'exemplos'/name,'--safe','--debug'],capture_output=True,timeout=30)
            assert (result.returncode,result.stdout,result.stderr)==(0,expected,b''),(name,result.stderr.decode())
        result=subprocess.run([compiler,'run',folder/'exemplos/25_recursos_e_unicode.assis','--safe','--debug'],capture_output=True,timeout=30)
        assert (result.returncode,result.stdout,result.stderr)==(0,b'4 2 195 169\n0 4\n',b''),result.stderr.decode()
        config=folder/('config.exe' if sys.platform=='win32' else 'config')
        result=subprocess.run([compiler,'build',folder/'exemplos/24_config_json.assis','--safe','--debug','-o',config],capture_output=True,timeout=30)
        assert result.returncode==0,result.stderr.decode()
        incoming,committed,temporary=folder/'entrada á.json',folder/'persistida á.json',folder/'temporario á.json'
        incoming.write_bytes(b'{"valor":42}')
        result=subprocess.run([config,incoming,committed,temporary],capture_output=True,timeout=30)
        assert result.returncode==0 and result.stderr==b'',result.stderr.decode()
        assert committed.read_bytes()==incoming.read_bytes() and not temporary.exists()
        tests=folder/'test-tools.assis';tests.write_text('safe assis test_ok():bool{return true;}',encoding='utf-8')
        result=subprocess.run([compiler,'test',tests,'--safe','--debug'],capture_output=True,timeout=30)
        assert (result.returncode,result.stdout,result.stderr)==(0,b'ASSIS: 1 testes passaram\n',b'')
        if shutil.which('node'):
            messages=[{'jsonrpc':'2.0','id':1,'method':'initialize','params':{'rootUri':folder.as_uri()}},{'jsonrpc':'2.0','id':2,'method':'shutdown'},{'jsonrpc':'2.0','method':'exit'}]
            protocol=b''.join(b'Content-Length: '+str(len(body)).encode()+b'\r\n\r\n'+body for body in [json.dumps(m).encode() for m in messages])
            result=subprocess.run(['node',folder/'tools/assis-lsp.js'],input=protocol,capture_output=True,timeout=15)
            assert result.returncode==0 and not result.stderr,result.stderr.decode()
            assert b'textDocumentSync' in result.stdout and version.encode() in result.stdout
        app = folder / ('relatorio.exe' if sys.platform == 'win32' else 'relatorio')
        result = subprocess.run([compiler, 'build', folder / 'exemplos/21_relatorio_csv_stream.assis', '--safe', '--debug', '-o', app], capture_output=True, timeout=30)
        assert result.returncode == 0, result.stderr.decode()
        input_file, output_file = folder / 'entrada.csv', folder / 'saida.csv'
        input_file.write_bytes(b'valor\n1\n41\n')
        result = subprocess.run([app, input_file, output_file], capture_output=True, timeout=30)
        assert (result.returncode, result.stdout, result.stderr) == (0, b'Registros 2 total 42\n', b''), result.stderr.decode()
        assert output_file.read_bytes() == b'registros,total\n2,42\n'
        for library in catalog['libraries']:
            result = subprocess.run([compiler, 'check', folder / 'stdlib' / (library['name'] + '.assis'), '--library'], capture_output=True, timeout=30)
            assert result.returncode == 0, result.stderr.decode()
        for source, message in [
            ('assis assis_assis():int{own a:Array<int>=[1];a._length=999999;return 0;}', 'campo privado'),
            ('pure assis f():int{return agora();}assis assis_assis():int{return 0;}', 'pure'),
            ('assis assis_assis():int{val n:int=1;n=2;return 0;}', 'imutável'),
            ('pure assis f<T>(v:T):T{return v;}assis assis_assis():int{print(f::<text>("a"));return 0;}', 'pure'),
            ('assis f<T>(a:Array<T>):int{return a._length;}assis assis_assis():int{let a:Array<int>=[1];return f::<int>(a);}', 'campo privado'),
            ('assis f(v:int):int{return v;}assis assis_assis():int{val g:pure assis(int):int=f;return 0;}', 'não é possível usar'),
            ('ASSIS C<T>{private let v:T;}assis assis_assis():int{let c:C<int>=new C<int>();print(c.v);return 0;}', 'campo privado'),
            ('assis consumir(own a:Array<int>):void{}assis assis_assis():int{own a:Array<int>=[1];consumir(move(a));print(a[0]);return 0;}', 'movido ou liberado'),
            ('safe assis assis_assis():int{let p:*int=alloc<int>(1);return 0;}', 'safe exige own/borrow')]:
            result = subprocess.run([compiler, 'check', 'package-check.assis', '--stdin', '--diagnostics=json'], input=source.encode(), capture_output=True, timeout=30)
            assert result.returncode == 1 and message in json.loads(result.stderr)['message'], result.stderr.decode()
with zipfile.ZipFile(root / 'dist' / f'AssisScript-{version}-windows-linux.zip') as archive:
    assert archive.testzip() is None
    for platform_name in ['windows','linux']:
        report=json.loads(archive.read(f'AssisScript/benchmarks/resultados/evolucao-alpha9-{platform_name}.json'))
        for name,digest in report['sourceHashes'].items():
            archive_name='AssisScript/'+name.replace(chr(92),'/')
            assert hashlib.sha256(archive.read(archive_name)).hexdigest()==digest, ('fonte de medição divergente',name)
    sums = archive.read('AssisScript/SHA256SUMS').decode().splitlines()
    for entry in sums:
        expected, name = entry.split('  ', 1)
        assert hashlib.sha256(archive.read('AssisScript/' + name)).hexdigest() == expected, name
print(f'ASSIS: VSIX offline com {len(catalog["libraries"])} bibliotecas e release com {len(sums)} hashes verificados.')
