param(
    [string]$ApiBase = "http://localhost:8000",
    [string]$WebBase = "http://localhost:3000",
    [switch]$SkipGuideFlow,
    [string]$ReportPath = "",
    [switch]$SkipCleanupSmokeData,
    [switch]$SkipContainerStatus
)

$ErrorActionPreference = "Stop"

function Assert-Status {
    param(
        [string]$Name,
        [string]$Url,
        [int]$Expected = 200,
        [hashtable]$Headers = @{}
    )

    $response = Invoke-WebRequest -Uri $Url -Headers $Headers -UseBasicParsing
    if ($response.StatusCode -ne $Expected) {
        throw "$Name failed. Expected $Expected, got $($response.StatusCode). URL: $Url"
    }
    Write-Host "[OK] $Name -> $($response.StatusCode)"
    return $response
}

function Assert-Redirect {
    param(
        [string]$Name,
        [string]$Url,
        [hashtable]$Body,
        [hashtable]$Headers = @{}
    )

    try {
        $response = Invoke-WebRequest -Uri $Url -Method Post -Body $Body -Headers $Headers -MaximumRedirection 0 -UseBasicParsing
        if ($response.StatusCode -ne 303) {
            throw "$Name expected 303, got $($response.StatusCode)."
        }
        Write-Host "[OK] $Name -> 303 ($($response.Headers['Location']))"
        return $response
    } catch {
        $raw = $_.Exception.Response
        if (-not $raw) {
            throw
        }
        if ([int]$raw.StatusCode -ne 303) {
            throw "$Name expected 303, got $([int]$raw.StatusCode)."
        }
        Write-Host "[OK] $Name -> 303 ($($raw.Headers['Location']))"
        return $raw
    }
}

function Assert-RedirectSuccess {
    param(
        [string]$Name,
        [string]$Url,
        [hashtable]$Body,
        [hashtable]$Headers = @{}
    )

    $response = Assert-Redirect -Name $Name -Url $Url -Body $Body -Headers $Headers
    $location = $response.Headers['Location']
    if ($location -match "kind=error") {
        throw "$Name returned error redirect: $location"
    }
    return $response
}

function Cleanup-SmokeData {
    param(
        [string]$ComposeFilePath,
        [string]$SmokeCustomerName = "Smoke Script"
    )

    $safeName = $SmokeCustomerName.Replace("'", "''")
    $pythonCode = @'
from app.db.session import SessionLocal
from app.db.models import Guide, Delivery

db = SessionLocal()
try:
    guides = db.query(Guide).filter(Guide.customer_name == '__SMOKE_NAME__').all()
    guide_ids = [g.id for g in guides]
    delivery_deleted = 0
    guide_deleted = 0
    if guide_ids:
        delivery_deleted = db.query(Delivery).filter(Delivery.guide_id.in_(guide_ids)).delete(synchronize_session=False)
        guide_deleted = db.query(Guide).filter(Guide.id.in_(guide_ids)).delete(synchronize_session=False)
        db.commit()
    print("SMOKE_GUIDES_FOUND=" + str(len(guide_ids)))
    print("SMOKE_DELIVERIES_DELETED=" + str(delivery_deleted))
    print("SMOKE_GUIDES_DELETED=" + str(guide_deleted))
finally:
    db.close()
'@
    $pythonCode = $pythonCode.Replace("__SMOKE_NAME__", $safeName)
    $pythonBase64 = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($pythonCode))
    $pythonExec = "import base64; exec(base64.b64decode('$pythonBase64').decode('utf-8'))"

    $cleanupOutput = & docker compose -f $ComposeFilePath exec -T api python -c $pythonExec | Out-String
    if ($LASTEXITCODE -ne 0) {
        throw "Cleanup-SmokeData failed: $cleanupOutput"
    }
    Write-Output "[INFO] Smoke cleanup result:"
    Write-Output $cleanupOutput.Trim()
}

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$composeFile = Join-Path $repoRoot "docker-compose.yml"

if (-not $ReportPath) {
    $reportsDir = Join-Path $PSScriptRoot "reports"
    New-Item -ItemType Directory -Force -Path $reportsDir | Out-Null
    $ReportPath = Join-Path $reportsDir ("health-smoke-{0}.txt" -f (Get-Date -Format "yyyyMMdd-HHmmss"))
}

$reportDir = Split-Path -Parent $ReportPath
if ($reportDir) {
    New-Item -ItemType Directory -Force -Path $reportDir | Out-Null
}

$transcriptStarted = $false
try {
    Start-Transcript -Path $ReportPath -Force | Out-Null
    $transcriptStarted = $true
} catch {
    Write-Warning "No se pudo iniciar transcript de reporte: $($_.Exception.Message)"
}

try {
    Write-Output "=== Mande24 Health + Smoke Check ==="
    Write-Output "[INFO] Reporte: $ReportPath"

    if (-not $SkipContainerStatus) {
        Write-Output "[STEP] Containers status"
        $composeStatus = & docker compose -f $composeFile ps | Out-String
        Write-Output $composeStatus
    } else {
        Write-Output "[STEP] Containers status skipped by flag"
    }

    Write-Output "[STEP] Base health endpoints"
        Assert-Status -Name "API health" -Url "$ApiBase/api/v1/health" | Out-Null
        Assert-Status -Name "ERP backend UI" -Url "$ApiBase/backend" | Out-Null
        Assert-Status -Name "Portal auth" -Url "$WebBase/auth" | Out-Null
        Assert-Status -Name "Portal client" -Url "$WebBase/client" | Out-Null
        Assert-Status -Name "Portal rider" -Url "$WebBase/rider" | Out-Null
        Assert-Status -Name "Portal station" -Url "$WebBase/station" | Out-Null

    if (-not $SkipGuideFlow) {
        Write-Output "[STEP] Backend guide creation smoke flow"
        $roleHeaders = @{ Cookie = "m24_backend_role=admin" }

        $seedResponse = Invoke-RestMethod -Uri "$ApiBase/backend/demo/seed" -Method Post -Headers $roleHeaders
        if (-not $seedResponse.service_id -or -not $seedResponse.station_id) {
            throw "Seed demo data did not return service_id/station_id."
        }
        Write-Output "[OK] Seed demo data"

        $createBody = @{
            customer_name = "Smoke Script"
            destination_name = "Smoke Dest"
            service_id = $seedResponse.service_id
            station_id = $seedResponse.station_id
        }

        # Keep demo catalogs active so the guide creation smoke flow is deterministic.
        Assert-RedirectSuccess -Name "Activate demo service" -Url "$ApiBase/backend/catalogs/services/$($seedResponse.service_id)/toggle" -Body @{ active = "true" } -Headers $roleHeaders | Out-Null
        Assert-RedirectSuccess -Name "Activate demo station" -Url "$ApiBase/backend/catalogs/stations/$($seedResponse.station_id)/toggle" -Body @{ active = "true" } -Headers $roleHeaders | Out-Null
        Assert-RedirectSuccess -Name "Create backend guide" -Url "$ApiBase/backend/guides/create" -Body $createBody -Headers $roleHeaders | Out-Null

        $guidesQuery = [System.Uri]::EscapeDataString("Smoke Script")
        $guidesPage = Assert-Status -Name "Guides list" -Url "$ApiBase/backend/guides?q=$guidesQuery" -Headers $roleHeaders
        if ($guidesPage.Content -notmatch "Smoke Script") {
            throw "Guides list does not show 'Smoke Script'."
        }
        Write-Output "[OK] Smoke guide appears in guides list"
    }

    if (-not $SkipCleanupSmokeData) {
        Write-Output "[STEP] Cleanup smoke data"
        Cleanup-SmokeData -ComposeFilePath $composeFile
    } else {
        Write-Output "[STEP] Cleanup smoke data skipped by flag"
    }

    Write-Output "=== RESULT: PASS ==="
}
catch {
    Write-Output "=== RESULT: FAIL ==="
    Write-Output "[ERROR] $($_.Exception.Message)"
    throw
}
finally {
    if ($transcriptStarted) {
        Stop-Transcript | Out-Null
    }
    Write-Output "[INFO] Reporte guardado en: $ReportPath"
}
