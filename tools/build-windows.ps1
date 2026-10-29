param([string]$Compiler = 'gcc')
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$resolved = (Get-Command $Compiler -ErrorAction Stop).Source
$env:PATH = (Split-Path -Parent $resolved) + ';' + $env:PATH
Push-Location $root
try {
    $flags = @('-O2', '-std=c11', '-Wall', '-Wextra', '-Wpedantic', '-Wno-misleading-indentation', '-municode', '-static', '-static-libgcc', '-s', '-Wl,--no-insert-timestamp')
    New-Item -ItemType Directory -Force build | Out-Null
    $windres = Join-Path (Split-Path -Parent $resolved) 'windres.exe'
    & $windres assets/compiler.rc -O coff -o build/compiler-icon.o
    if ($LASTEXITCODE -ne 0) { throw 'Falha ao gerar ícone do compilador' }
    & $windres assets/installer.rc -O coff -o build/installer-icon.o
    if ($LASTEXITCODE -ne 0) { throw 'Falha ao gerar ícone do instalador' }
    & $resolved @flags src/assisc.c build/compiler-icon.o -o bin/assis.exe
    if ($LASTEXITCODE -ne 0) { throw 'Falha ao compilar assis.exe' }
    & $resolved @flags src/windows_setup.c build/installer-icon.o -lshell32 -ladvapi32 -luser32 -o bin/assis-setup.exe
    if ($LASTEXITCODE -ne 0) { throw 'Falha ao compilar instalador' }
    & .\bin\assis.exe version
} finally { Pop-Location }
