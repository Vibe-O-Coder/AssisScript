"""Create checksums and a source/binary release, excluding local test profiles."""
from pathlib import Path
import hashlib
import zipfile
import json

root = Path(__file__).resolve().parent.parent
dist = root / "dist"
dist.mkdir(exist_ok=True)
version = json.loads((root / 'vscode-assisscript/package.json').read_text(encoding='utf-8'))['version']
output = dist / f"AssisScript-{version}-windows-linux.zip"

def included(file):
    relative = file.relative_to(root)
    if not file.is_file() or any(part in {"build", ".git", "__pycache__", "node_modules"} for part in relative.parts):
        return False
    if relative.parts[0] == "dist":
        return file.name == f"assisscript-{version}.vsix"
    return file.name != "SHA256SUMS"

files = sorted(file for file in root.rglob("*") if included(file))
sums = "".join(f"{hashlib.sha256(file.read_bytes()).hexdigest()}  {file.relative_to(root).as_posix()}\n" for file in files)
(root / "SHA256SUMS").write_text(sums, encoding="utf-8", newline="\n")
with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
    for file in files + [root / "SHA256SUMS"]:
        archive.write(file, "AssisScript/" + file.relative_to(root).as_posix())
print(output)
