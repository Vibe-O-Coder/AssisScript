param([string]$Compiler = 'gcc')
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$resolved = (Get-Command $Compiler -ErrorAction Stop).Source
$env:PATH = (Split-Path -Parent $resolved) + ';' + $env:PATH
Push-Location $root
try {
    $flags = @('-O2', '-std=c11', '-Wall', '-Wextra', '-Wpedantic', '-Wno-misleading-indentation', '-municode', '-static', '-static-libgcc', '-s', '-Wl,--no-insert-timestamp')
    & $resolved @flags src/assisc.c -o bin/assis.exe
    if ($LASTEXITCODE -ne 0) { throw 'Falha ao compilar assis.exe' }
    & $resolved @flags src/windows_setup.c -lshell32 -ladvapi32 -luser32 -o bin/assis-setup.exe
    if ($LASTEXITCODE -ne 0) { throw 'Falha ao compilar instalador' }
    & .\bin\assis.exe version
} finally { Pop-Location }
