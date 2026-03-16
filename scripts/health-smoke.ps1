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
        [hashtable]$Headers = @{},
        [Microsoft.PowerShell.Commands.WebRequestSession]$WebSession = $null
    )

    $requestArgs = @{
        Uri             = $Url
        Headers         = $Headers
        UseBasicParsing = $true
    }
    if ($WebSession) {
        $requestArgs.WebSession = $WebSession
    }
    $response = Invoke-WebRequest @requestArgs
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
        [hashtable]$Headers = @{},
        [Microsoft.PowerShell.Commands.WebRequestSession]$WebSession = $null
    )

    $requestArgs = @{
        Uri                = $Url
        Method             = "Post"
        Body               = $Body
        Headers            = $Headers
        MaximumRedirection = 0
        UseBasicParsing    = $true
    }
    if ($WebSession) {
        $requestArgs.WebSession = $WebSession
    }

    try {
        $response = Invoke-WebRequest @requestArgs
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
        [hashtable]$Headers = @{},
        [Microsoft.PowerShell.Commands.WebRequestSession]$WebSession = $null
    )

    $response = Assert-Redirect -Name $Name -Url $Url -Body $Body -Headers $Headers -WebSession $WebSession
    $location = $response.Headers['Location']
    if ($location -match "kind=error") {
        throw "$Name returned error redirect: $location"
    }
    return $response
}

function Ensure-ErpAdminSession {
    param(
        [string]$ApiBase,
        [Microsoft.PowerShell.Commands.WebRequestSession]$WebSession
    )

    $seed = Invoke-RestMethod -Uri "$ApiBase/ERPMande24/demo/seed" -Method Post
    if (-not $seed.service_id -or -not $seed.station_id) {
        throw "Seed demo data did not return service_id/station_id."
    }

    $smokeEmail = "smoke.erp.admin@mande24.test"
    $smokePassword = "SmokeAdmin123"

    $registerPayload = @{
        email     = $smokeEmail
        full_name = "Smoke ERP Admin"
        password  = $smokePassword
        role      = "admin"
    } | ConvertTo-Json

    $apiLogin = $null
    try {
        $apiLogin = Invoke-RestMethod -Uri "$ApiBase/api/v1/auth/login" -Method Post -ContentType "application/json" -Body (@{ email = $smokeEmail; password = $smokePassword } | ConvertTo-Json)
    } catch {
        $apiLogin = $null
    }

    if (-not $apiLogin -or -not $apiLogin.access_token) {
        try {
            Invoke-RestMethod -Uri "$ApiBase/api/v1/auth/register" -Method Post -ContentType "application/json" -Body $registerPayload | Out-Null
        } catch {
            $errorText = $_.ErrorDetails.Message
            if (-not ($errorText -match "Email already exists")) {
                throw
            }
        }
        $apiLogin = Invoke-RestMethod -Uri "$ApiBase/api/v1/auth/login" -Method Post -ContentType "application/json" -Body (@{ email = $smokeEmail; password = $smokePassword } | ConvertTo-Json)
    }

    if (-not $apiLogin.access_token) {
        throw "API login did not return access_token for smoke admin."
    }

    # Load login page first so session picks up base cookies if needed.
    Invoke-WebRequest -Uri "$ApiBase/ERPMande24/login" -WebSession $WebSession -UseBasicParsing | Out-Null

    $loginBody = @{
        email    = $smokeEmail
        password = $smokePassword
        next     = "/ERPMande24"
    }
    Assert-RedirectSuccess -Name "ERP login" -Url "$ApiBase/ERPMande24/login" -Body $loginBody -WebSession $WebSession | Out-Null

    return $seed
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

function Get-SmokeGeoData {
    param(
        [string]$ApiBase,
        [Microsoft.PowerShell.Commands.WebRequestSession]$WebSession
    )

    $stateCandidates = @("SIN", "TAB", "CAM", "CHP", "CHIS")
    foreach ($stateCode in $stateCandidates) {
        $municipalities = Invoke-RestMethod -Uri "$ApiBase/ERPMande24/geo/municipalities?state_code=$stateCode" -WebSession $WebSession -Method Get
        if (-not $municipalities -or -not $municipalities[0].code) {
            continue
        }

        $municipalityCode = $municipalities[0].code
        $postalCodes = Invoke-RestMethod -Uri "$ApiBase/ERPMande24/geo/postal-codes?municipality_code=$municipalityCode" -WebSession $WebSession -Method Get
        if (-not $postalCodes -or -not $postalCodes[0].code) {
            continue
        }

        $postalCode = $postalCodes[0].code
        $colonies = Invoke-RestMethod -Uri "$ApiBase/ERPMande24/geo/colonies?state_code=$stateCode&municipality_code=$municipalityCode&postal_code=$postalCode" -WebSession $WebSession -Method Get
        if (-not $colonies -or -not $colonies[0].id) {
            continue
        }

        return @{
            state_code = $stateCode
            municipality_code = $municipalityCode
            postal_code = $postalCode
            colony_id = $colonies[0].id
        }
    }

    throw "No se pudieron obtener datos geo para smoke guide flow."
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
        Assert-Status -Name "ERPMande24 UI" -Url "$ApiBase/ERPMande24" | Out-Null
        Assert-Status -Name "Portal auth" -Url "$WebBase/auth" | Out-Null
        Assert-Status -Name "Portal client" -Url "$WebBase/client" | Out-Null
        Assert-Status -Name "Portal rider" -Url "$WebBase/rider" | Out-Null
        Assert-Status -Name "Portal station" -Url "$WebBase/station" | Out-Null

    if (-not $SkipGuideFlow) {
        Write-Output "[STEP] ERPMande24 guide creation smoke flow"
        $erpSession = New-Object Microsoft.PowerShell.Commands.WebRequestSession
        $seedResponse = Ensure-ErpAdminSession -ApiBase $ApiBase -WebSession $erpSession
        $geo = Get-SmokeGeoData -ApiBase $ApiBase -WebSession $erpSession
        Write-Output "[OK] Seed demo data"

        $createBody = @{
            customer_name = "Smoke Script"
            destination_name = "Smoke Dest"
            service_id = $seedResponse.service_id
            station_id = $seedResponse.station_id
            origin_whatsapp_phone = "5511111111"
            origin_email = "smoke.origin@mande24.test"
            origin_state_code = $geo.state_code
            origin_municipality_code = $geo.municipality_code
            origin_postal_code = $geo.postal_code
            origin_colony_id = $geo.colony_id
            origin_address_line = "Calle Smoke Origen 101"
            destination_whatsapp_phone = "5522222222"
            destination_email = "smoke.destino@mande24.test"
            destination_state_code = $geo.state_code
            destination_municipality_code = $geo.municipality_code
            destination_postal_code = $geo.postal_code
            destination_colony_id = $geo.colony_id
            destination_address_line = "Calle Smoke Destino 202"
        }

        # Keep demo catalogs active so the guide creation smoke flow is deterministic.
        Assert-RedirectSuccess -Name "Activate demo service" -Url "$ApiBase/ERPMande24/catalogs/services/$($seedResponse.service_id)/toggle" -Body @{ active = "true" } -WebSession $erpSession | Out-Null
        Assert-RedirectSuccess -Name "Activate demo station" -Url "$ApiBase/ERPMande24/catalogs/stations/$($seedResponse.station_id)/toggle" -Body @{ active = "true" } -WebSession $erpSession | Out-Null
        Assert-RedirectSuccess -Name "Create backend guide" -Url "$ApiBase/ERPMande24/guides/create" -Body $createBody -WebSession $erpSession | Out-Null

        $guidesQuery = [System.Uri]::EscapeDataString("Smoke Script")
        $guidesPage = Assert-Status -Name "Guides list" -Url "$ApiBase/ERPMande24/guides?q=$guidesQuery" -WebSession $erpSession
        if ($guidesPage.Content -notmatch "Smoke Script") {
            throw "Guides list does not show 'Smoke Script'."
        }
        Write-Output "[OK] Smoke guide appears in guides list"
    }

    if ((-not $SkipGuideFlow) -and (-not $SkipCleanupSmokeData)) {
        Write-Output "[STEP] Cleanup smoke data"
        Cleanup-SmokeData -ComposeFilePath $composeFile
    } else {
        Write-Output "[STEP] Cleanup smoke data skipped"
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
