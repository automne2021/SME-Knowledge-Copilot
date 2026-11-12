# Windows PowerShell 5.1 launcher. ASCII source is intentional for Windows encoding compatibility.
[CmdletBinding()]
param(
    [ValidateSet('Start', 'Stop', 'Status', 'Check', 'Run')][string]$Action = 'Start',
    [switch]$NoBrowser,
    [switch]$NoAI,
    [ValidateRange(15, 240)][int]$TimeoutSeconds = 90,
    [ValidateSet('api', 'worker', 'frontend')][string]$Service,
    [string]$Instance,
    [string]$Configuration
)

$ErrorActionPreference = 'Stop'
$RepoRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$ScriptFile = Join-Path $PSScriptRoot 'web-dev.ps1'
$ShellExe = Join-Path $PSHOME 'powershell.exe'
$PythonExe = Join-Path $RepoRoot 'backend\.venv\Scripts\python.exe'
$ViteFile = Join-Path $RepoRoot 'frontend\node_modules\vite\bin\vite.js'
$CacheRoot = Join-Path $RepoRoot '.cache\web-dev'
$StateFile = Join-Path $CacheRoot 'state.json'
$WebUrl = 'http://127.0.0.1:5173/'
$ApiUrl = 'http://127.0.0.1:8000/api/v1/health'
$script:RunLog = $null
$script:AIMode = if ($NoAI) { 'disabled' } else { 'env' }

function Write-Step([string]$Message) {
    Write-Host $Message
    if ($script:RunLog) { Add-Content -LiteralPath $script:RunLog -Value ((Get-Date -Format 's') + ' ' + $Message) -Encoding UTF8 }
}

function Set-LocalProfile {
    # Read LLM settings from the project's dotenv files, not stale parent-shell overrides.
    foreach ($name in @('LLM_BASE_URL', 'LLM_MODEL', 'LLM_API_KEY', 'LLM_FREE_TIER_CONFIRMED', 'LLM_QUOTA_CONFIRMED')) {
        Remove-Item -LiteralPath ('Env:' + $name) -ErrorAction SilentlyContinue
    }
    if ($NoAI) {
        # Empty values are removed on PS 5.1 and could fall back to a real dotenv key.
        $env:LLM_API_KEY = 'disabled-by-web-launcher'
        $env:LLM_FREE_TIER_CONFIRMED = 'false'
        $env:LLM_QUOTA_CONFIRMED = 'false'
    }
    $env:SME_WEB_AI_MODE = $script:AIMode
    $env:HF_HUB_OFFLINE = '1'
    $env:TRANSFORMERS_OFFLINE = '1'
    $env:HF_HUB_DISABLE_TELEMETRY = '1'
    $env:PYTHONDONTWRITEBYTECODE = '1'
    $env:PYTHONIOENCODING = 'utf-8'
    [Console]::OutputEncoding = [Text.UTF8Encoding]::new($false)
}

function Get-ConfigurationStamp {
    # No key values are written to state, logs or command lines. Changes trigger a restart.
    $parts = @('web-launcher-v2', $script:AIMode)
    foreach ($file in @((Join-Path $RepoRoot '.env'), (Join-Path $RepoRoot 'backend\.env'))) {
        if (Test-Path -LiteralPath $file -PathType Leaf) { $parts += (Get-FileHash -LiteralPath $file -Algorithm SHA256).Hash }
        else { $parts += 'missing' }
    }
    $hasher = [Security.Cryptography.SHA256]::Create()
    try { return ([BitConverter]::ToString($hasher.ComputeHash([Text.Encoding]::UTF8.GetBytes(($parts -join '|'))))).Replace('-', '').ToLowerInvariant() }
    finally { $hasher.Dispose() }
}

function Find-Node {
    $command = Get-Command node.exe -ErrorAction SilentlyContinue
    if (-not $command) { throw 'Node.js is missing from PATH. Restore the project environment first.' }
    return $command.Source
}

# Only a service supervisor started with this exact script path and a generated instance ID is owned.
# state.json is diagnostic metadata, NEVER authority for killing a process.
function Get-OwnedServices {
    $result = @()
    foreach ($entry in @(Get-CimInstance Win32_Process -Filter "Name = 'powershell.exe'")) {
        $line = [string]$entry.CommandLine
        if ($line.IndexOf($ScriptFile, [StringComparison]::OrdinalIgnoreCase) -lt 0) { continue }
        if ($line -notmatch '(?i)(?:^|\s)-Action\s+"?Run"?(?:\s|$)') { continue }
        $serviceMatch = [regex]::Match($line, '(?i)(?:^|\s)-Service\s+"?(api|worker|frontend)"?(?:\s|$)')
        $instanceMatch = [regex]::Match($line, '(?i)(?:^|\s)-Instance\s+"?([a-f0-9]{32})"?(?:\s|$)')
        $configurationMatch = [regex]::Match($line, '(?i)(?:^|\s)-Configuration\s+"?([a-f0-9]{64})"?(?:\s|$)')
        $mode = if (-not $configurationMatch.Success) { 'legacy-disabled' } elseif ($line -match '(?i)(?:^|\s)-NoAI(?:\s|$)') { 'disabled' } else { 'env' }
        if (-not $serviceMatch.Success -or -not $instanceMatch.Success) { continue }
        try {
            $process = Get-Process -Id $entry.ProcessId -ErrorAction Stop
            if (-not [string]::Equals($process.Path, $ShellExe, [StringComparison]::OrdinalIgnoreCase)) { continue }
            $result += [pscustomobject]@{ Name = $serviceMatch.Groups[1].Value.ToLowerInvariant(); ProcessId = [int]$entry.ProcessId; StartTicks = $process.StartTime.ToUniversalTime().Ticks.ToString(); Instance = $instanceMatch.Groups[1].Value.ToLowerInvariant(); AIMode = $mode; Configuration = $configurationMatch.Groups[1].Value.ToLowerInvariant() }
        } catch { continue } # Process exited while being observed.
    }
    return $result
}

function Test-ChildOf([int]$ProcessId, [int[]]$Roots, [hashtable]$ProcessMap) {
    $cursor = $ProcessId
    for ($step = 0; $step -lt 64 -and $cursor -gt 0; $step++) {
        if ($Roots -contains $cursor) { return $true }
        if (-not $ProcessMap.ContainsKey($cursor)) { return $false }
        $next = [int]$ProcessMap[$cursor].ParentProcessId
        if ($next -eq $cursor) { return $false }
        $cursor = $next
    }
    return $false
}

function Assert-NoConflict($Owned) {
    $map = @{}
    foreach ($entry in @(Get-CimInstance Win32_Process)) { $map[[int]$entry.ProcessId] = $entry }
    $roots = [int[]]@($Owned | ForEach-Object { $_.ProcessId })
    $listeners = @(Get-NetTCPConnection -State Listen -ErrorAction Stop | Where-Object { $_.LocalPort -in @(8000, 5173) })
    foreach ($listener in $listeners) {
        if (-not (Test-ChildOf ([int]$listener.OwningProcess) $roots $map)) {
            throw "Port $($listener.LocalPort) is used by another process (PID $($listener.OwningProcess)). Close that process yourself; this launcher will not stop it."
        }
    }
    foreach ($entry in $map.Values) {
        if ($entry.Name -notmatch '^pythonw?\.exe$') { continue }
        $line = [string]$entry.CommandLine
        if ($line -notmatch '(?i)(?:^|\s)-m\s+(app\.worker|pytest|eval\.)') { continue }
        if (Test-ChildOf ([int]$entry.ProcessId) $roots $map) { continue }
        $parent = $map[[int]$entry.ParentProcessId]
        $local = $line.IndexOf($RepoRoot, [StringComparison]::OrdinalIgnoreCase) -ge 0
        if ($parent) { $local = $local -or ([string]$parent.CommandLine).IndexOf($RepoRoot, [StringComparison]::OrdinalIgnoreCase) -ge 0 }
        if ($local) { throw "A project worker/test/eval process is running outside this launcher (PID $($entry.ProcessId)). Stop it before launching to avoid sharing the development queue." }
    }
}

function Test-Docker {
    $savedPreference = $ErrorActionPreference
    try {
        $ErrorActionPreference = 'Continue'
        & docker.exe info --format '{{.ServerVersion}}' 1>$null 2>$null
        return $LASTEXITCODE -eq 0
    } finally { $ErrorActionPreference = $savedPreference }
}

function Ensure-Docker {
    if (-not (Get-Command docker.exe -ErrorAction SilentlyContinue)) { throw 'Docker Desktop is not installed or docker.exe is not on PATH.' }
    if (-not (Test-Docker)) {
        $desktop = Join-Path $env:ProgramFiles 'Docker\Docker\Docker Desktop.exe'
        if (-not (Test-Path -LiteralPath $desktop -PathType Leaf)) { throw 'Open Docker Desktop and retry. The Linux engine is not ready.' }
        Write-Step '[WAIT] Starting Docker Desktop...'
        if (-not (Get-Process -Name 'Docker Desktop' -ErrorAction SilentlyContinue)) { Start-Process -FilePath $desktop -WindowStyle Hidden | Out-Null }
        $deadline = [DateTime]::UtcNow.AddSeconds($TimeoutSeconds)
        while (-not (Test-Docker)) {
            if ([DateTime]::UtcNow -ge $deadline) { throw 'Docker did not become ready. Complete any Docker Desktop prompts yourself, then retry.' }
            Start-Sleep -Seconds 2
        }
    }
    Write-Step '[START] Checking PostgreSQL and Qdrant...'
    Push-Location -LiteralPath $RepoRoot
    try {
        # Never pull images, build an image, start the scaffold backend, or remove volumes here.
        $savedPreference = $ErrorActionPreference
        $ErrorActionPreference = 'Continue'
        & docker.exe compose up -d --pull never --no-build --wait --wait-timeout 120 db qdrant 2>&1 | ForEach-Object { Write-Step $_.ToString() }
        $code = $LASTEXITCODE
        $ErrorActionPreference = $savedPreference
        if ($code -ne 0) { throw 'Storage startup failed. Check Docker and the existing images; no image download or volume reset was attempted.' }
    } finally { $ErrorActionPreference = 'Stop'; Pop-Location }
}

function Invoke-Preflight {
    Write-Step '[CHECK] Dependencies, development target and pinned local model cache...'
    $code = @'
import sys
import os
try:
    import uvicorn
    from urllib.parse import urlsplit
    from sqlalchemy.engine import make_url
    from app.core.config import get_settings
    from app.services.embeddings import frozen_profile
    s = get_settings()
    db = make_url(s.database_url)
    if db.host not in ('localhost', '127.0.0.1', '::1') or not db.database or db.database.lower().endswith('_test'):
        raise ValueError('Use the local development database, never a test target.')
    if s.test_database_url and make_url(s.test_database_url).database == db.database:
        raise ValueError('Development and test database names must differ.')
    if urlsplit(s.qdrant_url).hostname not in ('localhost', '127.0.0.1', '::1'):
        raise ValueError('Use a local Qdrant target.')
    if os.environ['SME_WEB_AI_MODE'] == 'disabled':
        if s.llm_free_tier_confirmed or s.llm_quota_confirmed or not s.llm_api_key or s.llm_api_key.get_secret_value() != 'disabled-by-web-launcher':
            raise ValueError('Gemini guard is not active.')
    else:
        from app.services.gemini import BASE_URL, MODEL, GeminiProvider
        invalid = []
        if s.llm_base_url != BASE_URL:
            invalid.append('LLM_BASE_URL (use the fixed Google endpoint from README)')
        if s.llm_model != MODEL:
            invalid.append('LLM_MODEL (use the supported model from README)')
        if not s.llm_api_key or not s.llm_api_key.get_secret_value().strip() or s.llm_api_key.get_secret_value().strip() in ('disabled-by-web-launcher', '<your-key>', 'your-key-here'):
            invalid.append('LLM_API_KEY (set a private key in .env)')
        if not s.llm_free_tier_confirmed:
            invalid.append('LLM_FREE_TIER_CONFIRMED (confirm Free tier before setting true)')
        if not s.llm_quota_confirmed:
            invalid.append('LLM_QUOTA_CONFIRMED (confirm remaining quota before setting true)')
        if invalid:
            print('AI configuration is not ready: ' + '; '.join(invalid) + '. Use start-web.cmd -NoAI for local UI checks.')
            sys.exit(1)
        GeminiProvider(s)  # Constructor validates configuration; no HTTP/model request.
    frozen_profile(s)
except Exception as error:
    print('Preflight failed (' + type(error).__name__ + '). Check dependencies, local dev URLs and the pinned model cache. No secrets are printed.')
    sys.exit(1)
print('Local model/cache verified. AI mode: ' + os.environ['SME_WEB_AI_MODE'] + '. Preflight sent no model requests.')
'@
    Push-Location -LiteralPath (Join-Path $RepoRoot 'backend')
    try {
        $OutputEncoding = [Text.UTF8Encoding]::new($false)
        $code | & $PythonExe -B - 2>&1 | ForEach-Object { Write-Step $_.ToString() }
        if ($LASTEXITCODE -ne 0) { throw 'Preflight failed. Check the listed .env fields or run start-web.cmd -NoAI. Nothing was installed, downloaded, migrated or seeded.' }
    } finally { Pop-Location }
}

function Test-Ready {
    try {
        $apiResponse = Invoke-RestMethod -Uri $ApiUrl -TimeoutSec 3
        if ($apiResponse.data.status -ne 'ok' -or $apiResponse.data.database -ne 'ok') { return $false }
        $frontResponse = Invoke-WebRequest -Uri $WebUrl -UseBasicParsing -TimeoutSec 3
        if ($frontResponse.StatusCode -ne 200 -or $frontResponse.Content -notmatch '<title>SME Knowledge Copilot</title>') { return $false }
        $proxyResponse = Invoke-RestMethod -Uri ($WebUrl + 'api/v1/health') -TimeoutSec 3
        return $proxyResponse.data.status -eq 'ok'
    } catch { return $false }
}

function Save-State([string]$InstanceId, [string]$LogDirectory) {
    $state = [ordered]@{ schemaVersion = 2; root = $RepoRoot; mode = $script:AIMode; configuration = $Configuration; instance = $InstanceId; logDirectory = $LogDirectory; services = @(Get-OwnedServices) }
    $tempFile = Join-Path $CacheRoot 'state.next.json'
    $state | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $tempFile -Encoding UTF8
    Move-Item -LiteralPath $tempFile -Destination $StateFile -Force
}

function Quote-Argument([string]$Value) {
    # Values passed here are script paths and fixed tokens, never user-supplied shell code.
    if ($Value.Contains('"') -or $Value.EndsWith('\')) { throw 'Unsupported process argument.' }
    if ($Value -match '\s') { return '"' + $Value + '"' }
    return $Value
}

function Start-ServiceProcess([string]$Name, [string]$InstanceId, [string]$LogDirectory) {
    $arguments = @('-NoLogo', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $ScriptFile, '-Action', 'Run', '-Service', $Name, '-Instance', $InstanceId, '-Configuration', $Configuration)
    if ($NoAI) { $arguments += '-NoAI' }
    $line = ($arguments | ForEach-Object { Quote-Argument $_ }) -join ' '
    $process = Start-Process -FilePath $ShellExe -ArgumentList $line -WorkingDirectory $RepoRoot -WindowStyle Hidden -RedirectStandardOutput (Join-Path $LogDirectory ($Name + '.out.log')) -RedirectStandardError (Join-Path $LogDirectory ($Name + '.err.log')) -PassThru
    if (-not $process) { throw "Cannot start $Name." }
    Write-Step "[START] $Name supervisor PID $($process.Id)"
}

function Stop-OwnedServices {
    foreach ($name in @('frontend', 'api', 'worker')) {
        foreach ($record in @(Get-OwnedServices | Where-Object { $_.Name -eq $name })) {
            # Revalidate identity immediately before terminating the owned process tree.
            $current = @(Get-OwnedServices | Where-Object { $_.ProcessId -eq $record.ProcessId -and $_.StartTicks -eq $record.StartTicks -and $_.Instance -eq $record.Instance })
            if ($current.Count -ne 1) { continue }
            Write-Step "[STOP] $name (owned supervisor PID $($record.ProcessId))"
            & "$env:SystemRoot\System32\taskkill.exe" /PID $record.ProcessId /T /F 1>$null 2>$null
            if ($LASTEXITCODE -ne 0 -and (Get-Process -Id $record.ProcessId -ErrorAction SilentlyContinue)) { throw "Unable to stop owned $name process. Other processes were not targeted." }
        }
    }
    if (@(Get-OwnedServices).Count -gt 0) { throw 'Some owned service supervisors are still running.' }
    if (Test-Path -LiteralPath $StateFile -PathType Leaf) { Remove-Item -LiteralPath $StateFile -Force }
}

function Open-Web {
    if (-not $NoBrowser) {
        try { Start-Process -FilePath $WebUrl | Out-Null } catch { Write-Step "[INFO] Open $WebUrl in your browser." }
    }
}

# Child supervisors never acquire the launcher lock. Descendants inherit this process-only profile.
if ($Action -eq 'Run') {
    if (-not $Service -or $Instance -notmatch '^[a-f0-9]{32}$' -or $Configuration -notmatch '^[a-f0-9]{64}$') { Write-Host 'Internal service arguments are invalid.'; exit 1 }
    if ($Configuration -ne (Get-ConfigurationStamp)) { Write-Host 'Configuration changed during startup. Run start-web.cmd again.'; exit 1 }
    Set-LocalProfile
    $ErrorActionPreference = 'Continue'
    try {
        if ($Service -eq 'frontend') {
            Set-Location -LiteralPath (Join-Path $RepoRoot 'frontend') -ErrorAction Stop
            $nodePath = Find-Node
            & $nodePath $ViteFile --host 127.0.0.1 --port 5173 --strictPort 2>&1 | ForEach-Object { [Console]::WriteLine($_.ToString()) }
        } else {
            Set-Location -LiteralPath (Join-Path $RepoRoot 'backend') -ErrorAction Stop
            if ($Service -eq 'api') { & $PythonExe -B -m uvicorn app.main:app --host 127.0.0.1 --port 8000 2>&1 | ForEach-Object { [Console]::WriteLine($_.ToString()) } }
            else { & $PythonExe -B -m app.worker 2>&1 | ForEach-Object { [Console]::WriteLine($_.ToString()) } }
        }
        exit $LASTEXITCODE
    } catch { Write-Host "Service startup failed ($($_.Exception.GetType().Name)). See the launcher logs."; exit 1 }
}

if ($Action -eq 'Status') {
    @(Get-OwnedServices) | Select-Object Name, ProcessId, AIMode, Instance | Format-Table
    if (Test-Ready) { Write-Host "Web is responding: $WebUrl" } else { Write-Host 'Web is not ready.' }
    exit 0
}

$lockHandle = $null
$newInstance = $null
try {
    foreach ($directory in @((Join-Path $RepoRoot '.cache'), $CacheRoot)) {
        if (Test-Path -LiteralPath $directory) {
            if ((Get-Item -LiteralPath $directory).Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Launcher cache cannot be a link/junction. Choose a normal project cache directory.' }
        } else { New-Item -ItemType Directory -Path $directory | Out-Null }
    }
    try { $lockHandle = [IO.File]::Open((Join-Path $CacheRoot 'launcher.lock'), [IO.FileMode]::OpenOrCreate, [IO.FileAccess]::ReadWrite, [IO.FileShare]::None) }
    catch [IO.IOException] { Write-Host '[INFO] Another start/stop launcher is running. Wait for it to finish.'; exit 0 }
    $script:RunLog = Join-Path $CacheRoot 'launcher.log'
    Set-LocalProfile
    if ($Action -eq 'Stop') {
        Stop-OwnedServices
        Write-Step '[OK] Launcher-owned web processes stopped. Docker/storage/volumes were kept.'
        exit 0
    }
    Write-Step '[CHECK] SME Knowledge Copilot - local web launcher'
    foreach ($file in @($PythonExe, $ViteFile, (Join-Path $RepoRoot '.env'))) {
        if (-not (Test-Path -LiteralPath $file -PathType Leaf)) { throw "Required file is missing: $file. Restore the project environment; nothing is installed automatically." }
    }
    $null = Find-Node
    $Configuration = Get-ConfigurationStamp
    $owned = @()
    if ($Action -eq 'Start') {
        $owned = @(Get-OwnedServices)
        Assert-NoConflict $owned
        # Do not leave a previously enabled session using withdrawn dotenv confirmations/key.
        if (@($owned | Where-Object { $_.AIMode -ne $script:AIMode -or $_.Configuration -ne $Configuration }).Count -gt 0) {
            Write-Step '[INFO] Mode/dotenv changed. Stopping the old launcher session before validating its replacement.'
            Stop-OwnedServices
            $owned = @()
        }
    }
    Invoke-Preflight
    if ($Configuration -ne (Get-ConfigurationStamp)) { throw 'Configuration changed during preflight. Run the launcher again.' }
    if ($Action -eq 'Check') { Write-Step '[OK] Configuration check only. No services started/stopped and no model requests sent.'; exit 0 }
    Ensure-Docker
    $healthySet = $owned.Count -eq 3 -and @($owned.Name | Select-Object -Unique).Count -eq 3 -and @($owned.Instance | Select-Object -Unique).Count -eq 1 -and @($owned | Where-Object { $_.AIMode -ne $script:AIMode -or $_.Configuration -ne $Configuration }).Count -eq 0
    if ($healthySet -and (Test-Ready)) {
        Write-Step "[OK] Web is already running. No duplicate processes were started: $WebUrl"
        Open-Web
        exit 0
    }
    if ($owned.Count -gt 0) { Write-Step '[INFO] Restarting launcher-owned services: mode/configuration changed or session unhealthy.'; Stop-OwnedServices }
    Assert-NoConflict @()
    $newInstance = [Guid]::NewGuid().ToString('N')
    $logs = Join-Path $CacheRoot ((Get-Date -Format 'yyyyMMdd-HHmmss') + '-' + $newInstance.Substring(0, 8))
    New-Item -ItemType Directory -Path $logs | Out-Null
    Save-State $newInstance $logs
    foreach ($name in @('api', 'worker', 'frontend')) { Start-ServiceProcess $name $newInstance $logs; Save-State $newInstance $logs }
    Write-Step '[WAIT] Waiting for API, worker and web...'
    $deadline = [DateTime]::UtcNow.AddSeconds($TimeoutSeconds)
    $started = [DateTime]::UtcNow
    while ($true) {
        $current = @(Get-OwnedServices | Where-Object { $_.Instance -eq $newInstance })
        if ($current.Count -ne 3) { throw "A web service exited. Read logs in $logs" }
        if (([DateTime]::UtcNow - $started).TotalSeconds -ge 3 -and (Test-Ready)) { break }
        if ([DateTime]::UtcNow -ge $deadline) { throw "Web startup timed out. Read logs in $logs" }
        Start-Sleep -Seconds 1
    }
    Save-State $newInstance $logs
    Write-Step "[OK] Web ready: $WebUrl"
    if ($NoAI) { Write-Step '[INFO] Gemini is DISABLED (-NoAI). Chat generation is unavailable.' }
    else { Write-Step '[INFO] Gemini configuration loaded from .env. Free tier/quota are user-confirmed, not independently verified; no paid fallback.' }
    Write-Step '[INFO] Use your private demo credentials from .env.'
    Write-Step "[INFO] Logs: $logs"
    Write-Step '[INFO] Use stop-web.cmd to stop this launcher session.'
    Open-Web
} catch {
    Write-Step ("[ERROR] " + $_.Exception.Message)
    if ($newInstance) {
        try { Stop-OwnedServices } catch { Write-Step '[ERROR] Partial startup cleanup failed. Run stop-web.cmd and check the logs.' }
    }
    exit 1
} finally { if ($lockHandle) { $lockHandle.Dispose() } }
