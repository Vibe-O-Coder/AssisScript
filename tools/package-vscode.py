"""Build an offline VSIX with Python's standard library only."""
from pathlib import Path
import json
import zipfile
from xml.sax.saxutils import escape

root = Path(__file__).resolve().parent.parent
extension = root / "vscode-assisscript"
package = json.loads((extension / "package.json").read_text(encoding="utf-8"))
version = package["version"]
output = root / "dist" / f"assisscript-{version}.vsix"
output.parent.mkdir(exist_ok=True)
manifest = f'''<?xml version="1.0" encoding="utf-8"?>
<PackageManifest Version="2.0.0" xmlns="http://schemas.microsoft.com/developer/vsx-schema/2011">
<Metadata><Identity Language="en-US" Id="{package['name']}" Version="{version}" Publisher="{package['publisher']}"/>
<DisplayName>{escape(package['displayName'])}</DisplayName><Description xml:space="preserve">{escape(package['description'])}</Description><Tags>AssisScript,language,IntelliSense</Tags><Categories>Programming Languages</Categories><GalleryFlags>Public</GalleryFlags><Properties><Property Id="Microsoft.VisualStudio.Code.Engine" Value="{package['engines']['vscode']}"/><Property Id="Microsoft.VisualStudio.Code.ExtensionDependencies" Value=""/><Property Id="Microsoft.VisualStudio.Code.ExtensionPack" Value=""/></Properties></Metadata>
<Installation><InstallationTarget Id="Microsoft.VisualStudio.Code"/></Installation><Dependencies/>
<Assets><Asset Type="Microsoft.VisualStudio.Code.Manifest" Path="extension/package.json" Addressable="true"/></Assets>
</PackageManifest>'''
content_types = '''<?xml version="1.0" encoding="utf-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="json" ContentType="application/json"/><Default Extension="js" ContentType="application/javascript"/><Default Extension="md" ContentType="text/markdown"/><Default Extension="assis" ContentType="text/plain"/><Default Extension="pillow" ContentType="text/plain"/><Default Extension="png" ContentType="image/png"/><Default Extension="ico" ContentType="image/x-icon"/><Default Extension="ebnf" ContentType="text/plain"/><Default Extension="exe" ContentType="application/octet-stream"/><Default Extension="vsixmanifest" ContentType="text/xml"/><Override PartName="/extension/bin/assis" ContentType="application/octet-stream"/></Types>'''
content_types = content_types.replace('</Types>', '<Default Extension="txt" ContentType="text/plain"/><Default Extension="sh" ContentType="text/plain"/><Default Extension="pkg" ContentType="text/plain"/><Default Extension="lock" ContentType="text/plain"/><Override PartName="/extension/LICENSE" ContentType="text/plain"/><Override PartName="/extension/docs/LICENSE" ContentType="text/plain"/></Types>')
with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
    archive.writestr("extension.vsixmanifest", manifest)
    archive.writestr("[Content_Types].xml", content_types)
    for file in sorted(extension.rglob("*")):
        if file.is_file() and "test" not in file.relative_to(extension).parts:
            archive.write(file, "extension/" + file.relative_to(extension).as_posix())
    for name in ["assis", "assis.exe"]:
        source = root / "bin" / name
        if not source.is_file():
            raise FileNotFoundError(source)
        info = zipfile.ZipInfo("extension/bin/" + name)
        info.create_system = 3
        info.external_attr = 0o100755 << 16
        info.compress_type = zipfile.ZIP_DEFLATED
        archive.writestr(info, source.read_bytes())
    for file in sorted((root / "stdlib").glob("*")):
        if file.is_file():
            archive.write(file, "extension/stdlib/" + file.name)
    for file in sorted((root / "docs").rglob("*")):
        if file.is_file():
            archive.write(file, "extension/docs/" + file.relative_to(root/'docs').as_posix())
    for name in ['LICENSE', 'THIRD_PARTY_NOTICES.md', 'README.en.md', 'README.pt-BR.md', 'README.es.md']:
        archive.write(root/name, 'extension/'+name)
    for name in ["nativo-3.2.md", "nativo-3.2.json"]:
        archive.write(root / "benchmarks" / "resultados" / name, "extension/benchmarks/resultados/" + name)
    for file in sorted((root / 'benchmarks/resultados').glob('funcional-alpha-*')):
        if file.suffix in {'.md', '.json'}:
            archive.write(file, 'extension/benchmarks/resultados/' + file.name)
    for file in sorted((root / 'benchmarks/resultados').glob('generics-alpha-*')):
        if file.suffix in {'.md', '.json'}:
            archive.write(file, 'extension/benchmarks/resultados/' + file.name)
    for file in sorted((root / 'benchmarks/resultados').glob('funcoes-alpha-*')):
        if file.suffix in {'.md', '.json'}:
            archive.write(file, 'extension/benchmarks/resultados/' + file.name)
    for file in sorted((root / 'benchmarks/resultados').glob('classes-alpha-*')):
        if file.suffix in {'.md', '.json'}:
            archive.write(file, 'extension/benchmarks/resultados/' + file.name)
    for file in sorted((root / 'benchmarks/resultados').glob('colecoes-ast-alpha-*')):
        if file.suffix in {'.md', '.json'}:
            archive.write(file, 'extension/benchmarks/resultados/' + file.name)
    for file in sorted((root / 'benchmarks/resultados').glob('ownership-alpha-*')):
        if file.suffix in {'.md', '.json'}:
            archive.write(file, 'extension/benchmarks/resultados/' + file.name)
    for file in sorted((root / 'benchmarks/resultados').glob('valores-io-alpha-*')):
        if file.suffix in {'.md', '.json'}:
            archive.write(file, 'extension/benchmarks/resultados/' + file.name)
    for file in sorted((root / 'benchmarks/resultados').glob('evolucao-alpha8-*')):
        if file.suffix in {'.md', '.json'}:
            archive.write(file, 'extension/benchmarks/resultados/' + file.name)
    for file in sorted((root / 'benchmarks/resultados').glob('evolucao-alpha9-*')):
        if file.suffix in {'.md', '.json'}:
            archive.write(file, 'extension/benchmarks/resultados/' + file.name)
    for pattern in ['evolucao-alpha10-*', 'optimization-alpha10-*', 'evolucao-alpha11-*', 'optimization-alpha11-*', 'soak-alpha11-*', 'optimization-alpha12-*', 'soak-alpha12-*', 'evolucao-alpha12-*', 'optimization-alpha13-*', 'soak-alpha13-*', 'evolucao-alpha13-*', 'backend-alpha15-*', 'optimization-alpha15-*', 'soak-alpha15-*']:
        for file in sorted((root/'benchmarks/resultados').glob(pattern)):
            if file.suffix in {'.md', '.json'}:
                archive.write(file, 'extension/benchmarks/resultados/'+file.name)
    for file in sorted((root / 'benchmarks/resultados').glob('investigacao-alpha8-*')):
        if file.suffix in {'.md', '.json'}:
            archive.write(file, 'extension/benchmarks/resultados/' + file.name)
    archive.write(root / 'tools/assis-lsp.js', 'extension/tools/assis-lsp.js')
    for file in sorted((root / "exemplos").rglob("*")):
        if file.is_file() and file.suffix in {".assis", ".pillow", ".pkg", ".lock"}:
            archive.write(file, "extension/exemplos/" + file.relative_to(root / "exemplos").as_posix())
    archive.write(root / "README.md", "extension/README.md")
print(output)
