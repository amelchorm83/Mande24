param(
    [string]$Repo = "adanmelchorm/Mande24",
    [int]$ApiPort = 8000,
    [int]$WebPort = 3000,
    [switch]$SkipStopExistingTunnels,
    [switch]$TriggerSmoke,
    [switch]$RunGuideFlow
)

$ErrorActionPreference = "Stop"

function Resolve-ToolPath {
    param(
        [string]$CommandName,
        [string[]]$Candidates
    )

    $cmd = Get-Command $CommandName -ErrorAction SilentlyContinue
    if ($cmd) {
        return $cmd.Source
    }

    foreach ($item in $Candidates) {
        if (Test-Path $item) {
            return $item
        }
    }

    throw "No se encontro la herramienta '$CommandName'."
}

function Start-QuickTunnel {
    param(
        [string]$CloudflaredPath,
        [int]$Port,
        [string]$LogPath,
        [string]$ErrorLogPath
    )

    if (Test-Path $LogPath) {
        Remove-Item $LogPath -Force
    }
    if (Test-Path $ErrorLogPath) {
        Remove-Item $ErrorLogPath -Force
    }

    $arguments = "tunnel --url http://localhost:$Port --no-autoupdate"
    $process = Start-Process -FilePath $CloudflaredPath -ArgumentList $arguments -PassThru -WindowStyle Hidden -RedirectStandardOutput $LogPath -RedirectStandardError $ErrorLogPath
    return $process
}

function Read-TunnelUrl {
    param(
        [string[]]$LogPaths,
        [int]$TimeoutSeconds = 45
    )

    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    $pattern = "https://[a-z0-9-]+\.trycloudflare\.com"

    while ((Get-Date) -lt $deadline) {
        foreach ($path in $LogPaths) {
            if (Test-Path $path) {
                $raw = Get-Content -Path $path -Raw -ErrorAction SilentlyContinue
                if ($raw -match $pattern) {
                    return $Matches[0]
                }
            }
        }
        Start-Sleep -Seconds 1
    }

    throw "No se pudo detectar URL de tunel en los logs dentro de $TimeoutSeconds segundos."
}

function Stop-ExistingQuickTunnels {
    param(
        [int[]]$Ports
    )

    $portPatterns = $Ports | ForEach-Object { "http://localhost:$_" }
    $processes = Get-CimInstance Win32_Process -Filter "Name='cloudflared.exe'" -ErrorAction SilentlyContinue
    if (-not $processes) {
        return
    }

    $toStop = @()
    foreach ($proc in $processes) {
        $cmd = $proc.CommandLine
        if (-not $cmd) {
            continue
        }
        if ($cmd -match "tunnel --url" -and ($portPatterns | Where-Object { $cmd -like "*$_*" })) {
            $toStop += $proc
        }
    }

    if ($toStop.Count -eq 0) {
        return
    }

    $ids = $toStop.ProcessId
    Write-Output "[STEP] Cerrando tuneles previos de cloudflared en puertos objetivo: $($ids -join ', ')"
    Stop-Process -Id $ids -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 1
}

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$reportsDir = Join-Path $PSScriptRoot "reports"
New-Item -ItemType Directory -Force -Path $reportsDir | Out-Null

$ghPath = Resolve-ToolPath -CommandName "gh" -Candidates @("C:\Program Files\GitHub CLI\gh.exe")
$cloudflaredPath = Resolve-ToolPath -CommandName "cloudflared" -Candidates @(
    "C:\Users\Lenovo\AppData\Local\Microsoft\WinGet\Packages\Cloudflare.cloudflared_Microsoft.Winget.Source_8wekyb3d8bbwe\cloudflared.exe"
)

Write-Output "[STEP] Validando autenticacion GitHub CLI"
& $ghPath auth status | Out-Null

if (-not $SkipStopExistingTunnels) {
    Stop-ExistingQuickTunnels -Ports @($ApiPort, $WebPort)
}

$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$apiLog = Join-Path $reportsDir "cloudflared-api-$stamp.log"
$webLog = Join-Path $reportsDir "cloudflared-web-$stamp.log"
$apiErrLog = Join-Path $reportsDir "cloudflared-api-$stamp.err.log"
$webErrLog = Join-Path $reportsDir "cloudflared-web-$stamp.err.log"

Write-Output "[STEP] Abriendo tuneles quick (API:$ApiPort, WEB:$WebPort)"
$apiProc = Start-QuickTunnel -CloudflaredPath $cloudflaredPath -Port $ApiPort -LogPath $apiLog -ErrorLogPath $apiErrLog
$webProc = Start-QuickTunnel -CloudflaredPath $cloudflaredPath -Port $WebPort -LogPath $webLog -ErrorLogPath $webErrLog

$apiUrl = Read-TunnelUrl -LogPaths @($apiLog, $apiErrLog)
$webUrl = Read-TunnelUrl -LogPaths @($webLog, $webErrLog)

Write-Output "[OK] STAGING_API_BASE=$apiUrl"
Write-Output "[OK] STAGING_WEB_BASE=$webUrl"

Write-Output "[STEP] Actualizando GitHub Secrets en $Repo"
& $ghPath secret set STAGING_API_BASE --repo $Repo --body $apiUrl | Out-Null
& $ghPath secret set STAGING_WEB_BASE --repo $Repo --body $webUrl | Out-Null
Write-Output "[OK] Secrets actualizados"

if ($TriggerSmoke) {
    Write-Output "[STEP] Disparando workflow Staging Smoke"
    if ($RunGuideFlow) {
        & $ghPath workflow run "staging-smoke.yml" --repo $Repo --ref main -f run_guide_flow=true | Out-Null
    } else {
        & $ghPath workflow run "staging-smoke.yml" --repo $Repo --ref main -f run_guide_flow=false | Out-Null
    }
    Write-Output "[OK] Workflow enviado"
}

Write-Output "[INFO] Procesos cloudflared activos: API PID=$($apiProc.Id), WEB PID=$($webProc.Id)"
Write-Output "[INFO] Logs: $apiLog"
Write-Output "[INFO] Logs: $webLog"
Write-Output "[INFO] Error logs: $apiErrLog"
Write-Output "[INFO] Error logs: $webErrLog"
Write-Output "[INFO] Para cerrar tuneles: Stop-Process -Id $($apiProc.Id),$($webProc.Id)"
