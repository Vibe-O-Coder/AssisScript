# Executa os binários reais no Windows x64. Não altera o PATH do usuário.
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$assis = Join-Path $root 'bin\assis.exe'
$setup = Join-Path $root 'bin\assis-setup.exe'
$utf8 = [System.Text.UTF8Encoding]::new($false)
$isolatedRoot = Join-Path ([IO.Path]::GetTempPath()) ('assisscript-test-' + [Guid]::NewGuid().ToString('N'))
[void][IO.Directory]::CreateDirectory($isolatedRoot)
$script:count = 0

function Quote-WindowsArgument([string]$Value) {
    $escaped = [regex]::Replace($Value, '(\\*)"', '$1$1\"')
    $escaped = [regex]::Replace($escaped, '(\\+)$', '$1$1')
    return '"' + $escaped + '"'
}
function Run-Process {
    param([string]$File, [string[]]$Arguments = @(), [string]$Directory = $root, [bool]$NoTools = $false)
    $info = New-Object Diagnostics.ProcessStartInfo
    $info.FileName = $File
    $info.Arguments = (($Arguments | ForEach-Object { Quote-WindowsArgument $_ }) -join ' ')
    $info.WorkingDirectory = $Directory
    $info.UseShellExecute = $false
    $info.RedirectStandardOutput = $true
    $info.RedirectStandardError = $true
    $info.StandardOutputEncoding = $utf8
    $info.StandardErrorEncoding = $utf8
    $info.CreateNoWindow = $true
    if ($NoTools) { $info.EnvironmentVariables['PATH'] = 'C:\AssisScript-Tools-Unavailable' }
    $process = New-Object Diagnostics.Process
    $process.StartInfo = $info
    try {
        [void]$process.Start()
        $stdout = $process.StandardOutput.ReadToEndAsync()
        $stderr = $process.StandardError.ReadToEndAsync()
        if (-not $process.WaitForExit(15000)) { $process.Kill(); $process.WaitForExit(); throw ('Timeout de teste: ' + $File) }
        $process.WaitForExit()
        return [pscustomobject]@{ Code = $process.ExitCode; Out = $stdout.Result; Err = $stderr.Result }
    } finally { $process.Dispose() }
}
function Assert-True([bool]$Condition, [string]$Message) {
    if (-not $Condition) { throw ('FALHA: ' + $Message) }
}
function Assert-Code($Result, [int]$Expected, [string]$Message) {
    Assert-True ($Result.Code -eq $Expected) ($Message + ': status ' + $Result.Code + ', esperado ' + $Expected + '. ' + $Result.Err)
    $script:count++
}

try {
    foreach ($sourceFile in (Get-ChildItem (Join-Path $root 'tests\cases') -Filter '*.assis' | Sort-Object Name)) {
        $stem = $sourceFile.FullName.Substring(0, $sourceFile.FullName.Length - 6)
        $binary = Join-Path $isolatedRoot 'programa.exe'
        $built = Run-Process -File $assis -Arguments @('build', $sourceFile.FullName, '-o', $binary)
        Assert-True ($built.Code -eq 0) ($sourceFile.Name + ' nao compilou: ' + $built.Err)
        $result = Run-Process -File $binary
        $expectedCode = [int]([IO.File]::ReadAllText($stem + '.status', $utf8).Trim())
        Assert-Code $result $expectedCode $sourceFile.Name
        Assert-True ($result.Out -ceq [IO.File]::ReadAllText($stem + '.stdout', $utf8)) ('stdout: ' + $sourceFile.Name)
        Assert-True ($result.Err -ceq [IO.File]::ReadAllText($stem + '.stderr', $utf8)) ('stderr: ' + $sourceFile.Name)
    }
    foreach ($sourceFile in (Get-ChildItem (Join-Path $root 'tests\rejections') -Filter '*.assis' | Sort-Object Name)) {
        $stem = $sourceFile.FullName.Substring(0, $sourceFile.FullName.Length - 6)
        $result = Run-Process -File $assis -Arguments @('check', $sourceFile.FullName)
        Assert-Code $result 1 $sourceFile.Name
        $expected = [IO.File]::ReadAllText($stem + '.message', $utf8).TrimEnd("`r", "`n")
        Assert-True ($result.Err.Contains($expected)) ('diagnostico: ' + $sourceFile.Name)
    }
    $result = Run-Process -File $assis -Arguments @('version')
    Assert-Code $result 0 'version'
    Assert-True ($result.Out.Contains('3.3.0-alpha.10') -and $result.Out.Contains('Windows x64')) 'versao Windows'
    Assert-Code (Run-Process -File $assis -Arguments @('doctor')) 0 'doctor'
    Assert-Code (Run-Process -File $assis -Arguments @('help')) 0 'help'
    Assert-Code (Run-Process -File $assis -Arguments @('comando-inexistente')) 2 'comando invalido'
    Assert-Code (Run-Process -File $assis -Arguments @('check', (Join-Path $isolatedRoot 'ausente.assis'))) 2 'arquivo ausente'
    Assert-Code (Run-Process -File $assis -Arguments @('tokens', (Join-Path $root 'exemplos\01_ola.assis'))) 0 'tokens'

    $folder = Join-Path $isolatedRoot 'projeto com whitespace e ação'
    Assert-Code (Run-Process -File $assis -Arguments @('new', $folder)) 0 'new Unicode'
    $result = Run-Process -File $assis -Arguments @('run') -Directory $folder -NoTools $true
    Assert-Code $result 0 'run sem ferramentas'
    Assert-True ($result.Out.Contains('Assis, mundo. Fodase. 42')) 'saida do projeto'
    Assert-Code (Run-Process -File $assis -Arguments @('new', $folder)) 2 'new preserva pasta existente'
    $sourcePath = Join-Path $folder 'assis.assis'
    $backup = [IO.File]::ReadAllText($sourcePath, $utf8)
    Assert-Code (Run-Process -File $assis -Arguments @('build', $sourcePath, '-o', $sourcePath)) 2 'protecao do fonte'
    Assert-True ([IO.File]::ReadAllText($sourcePath, $utf8) -ceq $backup) 'fonte preservado'
    Assert-Code (Run-Process -File $assis -Arguments @('build', $sourcePath, '-o', $assis)) 2 'protecao do compilador'
    $output = Join-Path $isolatedRoot 'binario com acento ação'
    Assert-Code (Run-Process -File $assis -Arguments @('build', $sourcePath, '-o', $output) -NoTools $true) 0 'build sem ferramentas'
    Assert-True ([IO.File]::Exists($output + '.exe')) 'extensao exe automatica'
    Assert-Code (Run-Process -File ($output + '.exe') -NoTools $true) 0 'executavel independente'
    $loopFile = Join-Path $isolatedRoot 'laco.assis'
    [IO.File]::WriteAllText($loopFile, 'assis assis_assis(): FODase { ASSis (aSsIs) {} }', $utf8)
    Assert-Code (Run-Process -File $assis -Arguments @('run', $loopFile, '--timeout', '0.02')) 124 'timeout'
    Assert-Code (Run-Process -File $assis -Arguments @('run', $loopFile, '--timeout', 'nan')) 2 'timeout invalido'
    Assert-Code (Run-Process -File $assis -Arguments @('run', $sourcePath, '--target', 'linux-x64')) 2 'run exige destino nativo'
    $elf = Join-Path $isolatedRoot 'programa-linux'
    Assert-Code (Run-Process -File $assis -Arguments @('build', $sourcePath, '--target', 'linux-x64', '-o', $elf)) 0 'cross compile Linux'
    $magic = [IO.File]::ReadAllBytes($elf)
    Assert-True ($magic[0] -eq 127 -and $magic[1] -eq 69 -and $magic[2] -eq 76 -and $magic[3] -eq 70) 'cabecalho ELF'

    # Prefixo isolado e --no-path: os testes nao alteram o registro do usuario.
    $prefix = Join-Path $isolatedRoot 'instalacao com ação'
    Assert-Code (Run-Process -File $setup -Arguments @('install', '--prefix', $prefix, '--no-path', '--no-associations')) 0 'instalador'
    $installed = Join-Path $prefix 'bin\assis.exe'
    Assert-True ([IO.File]::Exists((Join-Path $prefix 'docs\WINDOWS.md'))) 'manual instalado'
    Assert-Code (Run-Process -File $installed -Arguments @('version')) 0 'compilador instalado'
    Assert-Code (Run-Process -File $installed -Arguments @('run', (Join-Path $prefix 'exemplos\08_modulos.assis'))) 0 'bibliotecas instaladas'
    Assert-Code (Run-Process -File $installed -Arguments @('run', (Join-Path $prefix 'exemplos\20_valores_e_resultados.assis'), '--safe', '--debug')) 0 'valores instalados'
    Assert-Code (Run-Process -File $installed -Arguments @('run', (Join-Path $prefix 'exemplos\25_recursos_e_unicode.assis'), '--safe', '--debug')) 0 'recursos e unicode instalados'
    Assert-True ([IO.File]::Exists((Join-Path $prefix 'docs\PROGRESSO.json'))) 'metrica instalada'
    $personalDocs = Join-Path $prefix 'docs\pessoal.txt'
    [IO.File]::WriteAllText($personalDocs, 'preservar', $utf8)
    Assert-Code (Run-Process -File $setup -Arguments @('install', '--prefix', $prefix, '--no-path', '--no-associations')) 0 'reinstalacao'
    $personal = Join-Path $prefix 'meu-projeto.txt'
    [IO.File]::WriteAllText($personal, 'preservar', $utf8)
    Assert-Code (Run-Process -File $setup -Arguments @('uninstall', '--prefix', $prefix, '--no-path', '--no-associations')) 0 'desinstalacao'
    Assert-True (-not [IO.File]::Exists($installed)) 'binario removido'
    Assert-True ([IO.File]::Exists($personalDocs)) 'documento pessoal preservado'
    Assert-True ([IO.File]::Exists($personal)) 'projetos preservados'
    Write-Host ('ASSIS: ' + $script:count + ' testes nativos do Windows aprovados.')
} finally {
    $resolvedCleanup = [IO.Path]::GetFullPath($isolatedRoot)
    $allowedCleanup = [IO.Path]::GetFullPath([IO.Path]::GetTempPath()).TrimEnd('\') + '\assisscript-test-'
    if (-not $resolvedCleanup.StartsWith($allowedCleanup, [StringComparison]::OrdinalIgnoreCase)) { throw 'Destino de limpeza fora da pasta temporária de testes.' }
    Remove-Item -LiteralPath $isolatedRoot -Recurse -Force -ErrorAction SilentlyContinue
}
