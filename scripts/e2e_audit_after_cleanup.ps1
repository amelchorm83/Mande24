$ErrorActionPreference = "Stop"

<#
Master audit for Mande24 Independent.
Covers: smoke availability, business e2e flow, negative and role guard checks.
Usage: .\scripts\e2e_audit_after_cleanup.ps1
#>

$baseApi = "http://localhost:8000"
$baseWeb = "http://localhost:3000"
$session = New-Object Microsoft.PowerShell.Commands.WebRequestSession
$results = New-Object System.Collections.Generic.List[string]

function Add-Result([string]$message) {
    $results.Add($message)
    Write-Output $message
}

function Get-FirstMatchValue([string]$text, [string]$pattern) {
    $m = [regex]::Match($text, $pattern)
    if ($m.Success) {
        return $m.Groups[1].Value
    }
    return $null
}

function Check-Url([string]$url) {
    try {
        $resp = Invoke-WebRequest -UseBasicParsing -WebSession $session -Uri $url -MaximumRedirection 5 -TimeoutSec 20
        Add-Result "PASS smoke $([int]$resp.StatusCode) $url"
    } catch {
        if ($_.Exception.Response) {
            Add-Result "FAIL smoke $([int]$_.Exception.Response.StatusCode) $url"
        } else {
            Add-Result "FAIL smoke ??? $url -> $($_.Exception.Message)"
        }
    }
}

Add-Result "INFO section=smoke"
$smokeApi = @(
    "$baseApi/",
    "$baseApi/ERPMande24",
    "$baseApi/ERPMande24/guides/new",
    "$baseApi/ERPMande24/guides",
    "$baseApi/ERPMande24/deliveries",
    "$baseApi/ERPMande24/catalogs/services",
    "$baseApi/ERPMande24/catalogs/stations",
    "$baseApi/ERPMande24/catalogs/riders",
    "$baseApi/ERPMande24/catalogs/clients",
    "$baseApi/ERPMande24/users",
    "$baseApi/ERPMande24/commissions/riders",
    "$baseApi/ERPMande24/commissions/stations",
    "$baseApi/docs",
    "$baseApi/openapi.json"
)

$smokeWeb = @(
    "$baseWeb/",
    "$baseWeb/servicios",
    "$baseWeb/mandaditos",
    "$baseWeb/cobertura",
    "$baseWeb/nosotros",
    "$baseWeb/noticias",
    "$baseWeb/contacto",
    "$baseWeb/client",
    "$baseWeb/rider",
    "$baseWeb/station",
    "$baseWeb/auth"
)

foreach ($url in ($smokeApi + $smokeWeb)) {
    Check-Url $url
}

Add-Result "INFO section=e2e_business"
try {
    Invoke-WebRequest -UseBasicParsing -WebSession $session -Method Post -Uri "$baseApi/ERPMande24/operator/select" -Body @{
        user_email = "e2e.audit@mande24.local"
        user_id = "E2E-AUDIT"
        return_to = "/ERPMande24/guides/new"
    } -MaximumRedirection 5 | Out-Null
    Add-Result "PASS setup operator context"
} catch {
    Add-Result "FAIL setup operator context: $($_.Exception.Message)"
}

$serviceId = $null
$stationId = $null
$guideCode = $null
$deliveryId = $null

try {
    $newGuide = Invoke-WebRequest -UseBasicParsing -WebSession $session -Uri "$baseApi/ERPMande24/guides/new"
    $serviceId = Get-FirstMatchValue $newGuide.Content 'name="service_id"[\s\S]*?<option value="([a-f0-9]{32})"'
    $stationId = Get-FirstMatchValue $newGuide.Content 'name="station_id"[\s\S]*?<option value="([a-f0-9]{32})"'
    if ($serviceId -and $stationId) {
        Add-Result "PASS parsed ids service=$serviceId station=$stationId"
    } else {
        Add-Result "FAIL cannot parse service/station ids"
    }
} catch {
    Add-Result "FAIL open guides/new: $($_.Exception.Message)"
}

if ($serviceId -and $stationId) {
    try {
        $stamp = Get-Date -Format "yyyyMMddHHmmss"
        $created = Invoke-WebRequest -UseBasicParsing -WebSession $session -Method Post -Uri "$baseApi/ERPMande24/guides/create" -Body @{
            customer_name = "QA E2E $stamp"
            destination_name = "Destino QA $stamp"
            service_id = $serviceId
            station_id = $stationId
        } -MaximumRedirection 5

        $guideMatch = [regex]::Match($created.Content, 'Guia\s+(M24-[0-9]{8}-[A-Z0-9]{6})\s+creada con delivery\s+([a-f0-9]{32})')
        if ($guideMatch.Success) {
            $guideCode = $guideMatch.Groups[1].Value
            $deliveryId = $guideMatch.Groups[2].Value
            Add-Result "PASS guide created code=$guideCode delivery=$deliveryId"
        } else {
            Add-Result "FAIL could not confirm guide creation from response"
        }
    } catch {
        Add-Result "FAIL create guide: $($_.Exception.Message)"
    }
}

if ($guideCode) {
    try {
        $guideDetail = Invoke-WebRequest -UseBasicParsing -WebSession $session -Uri "$baseApi/ERPMande24/guides/$guideCode"
        if (-not $deliveryId) {
            $deliveryId = Get-FirstMatchValue $guideDetail.Content '/ERPMande24/deliveries/([a-f0-9]{32})'
        }
        if ([int]$guideDetail.StatusCode -eq 200) {
            Add-Result "PASS guide detail reachable code=$guideCode"
        } else {
            Add-Result "FAIL guide detail status=$([int]$guideDetail.StatusCode)"
        }
    } catch {
        Add-Result "FAIL guide detail request: $($_.Exception.Message)"
    }
}

if ($deliveryId) {
    try {
        Invoke-WebRequest -UseBasicParsing -WebSession $session -Method Post -Uri "$baseApi/ERPMande24/deliveries/stage" -Body @{
            delivery_id = $deliveryId
            stage = "in_transit"
            note = "E2E transit"
        } -MaximumRedirection 5 | Out-Null

        Invoke-WebRequest -UseBasicParsing -WebSession $session -Method Post -Uri "$baseApi/ERPMande24/deliveries/stage" -Body @{
            delivery_id = $deliveryId
            stage = "delivered"
            note = "E2E delivered"
            has_evidence = "on"
            has_signature = "on"
        } -MaximumRedirection 5 | Out-Null

        $deliveryDetail = Invoke-WebRequest -UseBasicParsing -WebSession $session -Uri "$baseApi/ERPMande24/deliveries/$deliveryId"
        if ($deliveryDetail.Content -match "delivered") {
            Add-Result "PASS delivery progressed to delivered id=$deliveryId"
        } else {
            Add-Result "FAIL delivery progression verification failed id=$deliveryId"
        }
    } catch {
        Add-Result "FAIL update delivery stage: $($_.Exception.Message)"
    }
}

$exportPaths = @(
    "/ERPMande24/export/guides.csv",
    "/ERPMande24/export/deliveries.csv",
    "/ERPMande24/export/services.csv",
    "/ERPMande24/export/zones.csv",
    "/ERPMande24/export/stations.csv",
    "/ERPMande24/export/riders.csv",
    "/ERPMande24/export/pricing-rules.csv",
    "/ERPMande24/export/users.csv",
    "/ERPMande24/export/leads.csv",
    "/ERPMande24/export/clients.csv",
    "/ERPMande24/export/commissions-riders.csv",
    "/ERPMande24/export/commissions-stations.csv"
)

foreach ($path in $exportPaths) {
    try {
        $resp = Invoke-WebRequest -UseBasicParsing -WebSession $session -Uri ($baseApi + $path)
        Add-Result "PASS export $path status=$([int]$resp.StatusCode)"
    } catch {
        if ($_.Exception.Response) {
            Add-Result "FAIL export $path status=$([int]$_.Exception.Response.StatusCode)"
        } else {
            Add-Result "FAIL export $path ex=$($_.Exception.Message)"
        }
    }
}

Add-Result "INFO section=negative_and_permissions"

try {
    $resp = Invoke-WebRequest -UseBasicParsing -WebSession $session -Method Post -Uri "$baseApi/ERPMande24/guides/create" -Body @{
        customer_name = "QA NEG"
        destination_name = "QA NEG DEST"
        service_id = ""
        station_id = ""
    } -MaximumRedirection 5
    if ($resp.Content -match "Servicio no encontrado o inactivo|Estacion no encontrada o inactiva|422") {
        Add-Result "PASS negative guide mandatory validation"
    } else {
        Add-Result "WARN negative guide validation response not explicit"
    }
} catch {
    if ($_.Exception.Response -and [int]$_.Exception.Response.StatusCode -in 400, 422) {
        Add-Result "PASS negative guide mandatory validation status=$([int]$_.Exception.Response.StatusCode)"
    } else {
        Add-Result "FAIL negative guide mandatory validation: $($_.Exception.Message)"
    }
}

$anyDeliveryId = $null
try {
    $deliveries = Invoke-WebRequest -UseBasicParsing -WebSession $session -Uri "$baseApi/ERPMande24/deliveries"
    $anyDeliveryId = Get-FirstMatchValue $deliveries.Content '/ERPMande24/deliveries/([a-f0-9]{32})'
    if ($anyDeliveryId) {
        $bad = Invoke-WebRequest -UseBasicParsing -WebSession $session -Method Post -Uri "$baseApi/ERPMande24/deliveries/stage" -Body @{
            delivery_id = $anyDeliveryId
            stage = "invalid_stage"
            note = "negative test"
        } -MaximumRedirection 5
        if ($bad.Content -match "Etapa no valida") {
            Add-Result "PASS negative invalid stage rejected"
        } else {
            Add-Result "WARN negative invalid stage did not return expected text"
        }

        $rule = Invoke-WebRequest -UseBasicParsing -WebSession $session -Method Post -Uri "$baseApi/ERPMande24/deliveries/stage" -Body @{
            delivery_id = $anyDeliveryId
            stage = "delivered"
            note = "negative delivered without flags"
        } -MaximumRedirection 5
        if ($rule.Content -match "se requiere evidencia y firma") {
            Add-Result "PASS negative delivered evidence/signature enforced"
        } else {
            Add-Result "WARN negative delivered rule did not return expected text"
        }
    } else {
        Add-Result "WARN negative delivery checks skipped (no delivery id)"
    }
} catch {
    Add-Result "FAIL negative delivery checks: $($_.Exception.Message)"
}

try {
    Invoke-WebRequest -UseBasicParsing -WebSession $session -Method Post -Uri "$baseApi/ERPMande24/role/select" -Body @{ role = "rider"; return_to = "/ERPMande24/catalogs/services" } -MaximumRedirection 5 | Out-Null
    $restricted = Invoke-WebRequest -UseBasicParsing -WebSession $session -Method Post -Uri "$baseApi/ERPMande24/catalogs/services/create" -Body @{
        name = "QA NO-PERMIT"
        service_type = "messaging"
    } -MaximumRedirection 5

    if ($restricted.Content -match "Sin permisos") {
        Add-Result "PASS role guard manage-only endpoint blocked for rider"
    } else {
        Add-Result "FAIL role guard manage-only endpoint not blocked"
    }
} catch {
    Add-Result "FAIL role guard manage-only endpoint test: $($_.Exception.Message)"
}

try {
    Invoke-WebRequest -UseBasicParsing -WebSession $session -Method Post -Uri "$baseApi/ERPMande24/role/select" -Body @{ role = "admin"; return_to = "/ERPMande24/users" } -MaximumRedirection 5 | Out-Null
    $users = Invoke-WebRequest -UseBasicParsing -WebSession $session -Uri "$baseApi/ERPMande24/users"
    $userId = Get-FirstMatchValue $users.Content '/ERPMande24/users/([a-f0-9]{32})'
    if ($userId) {
        $r1 = Invoke-WebRequest -UseBasicParsing -WebSession $session -Method Post -Uri "$baseApi/ERPMande24/users/$userId/role" -Body @{ role = "station" } -MaximumRedirection 5
        $r2 = Invoke-WebRequest -UseBasicParsing -WebSession $session -Method Post -Uri "$baseApi/ERPMande24/users/$userId/role" -Body @{ role = "admin" } -MaximumRedirection 5
        if (($r1.StatusCode -eq 200) -and ($r2.StatusCode -eq 200)) {
            Add-Result "PASS concurrency-lite rapid role changes accepted"
        } else {
            Add-Result "FAIL concurrency-lite unexpected status"
        }
    } else {
        Add-Result "WARN concurrency-lite skipped (no user id)"
    }
} catch {
    Add-Result "FAIL concurrency-lite role updates: $($_.Exception.Message)"
}

try {
    Invoke-WebRequest -UseBasicParsing -WebSession $session -Method Post -Uri "$baseApi/ERPMande24/role/select" -Body @{ role = "admin"; return_to = "/ERPMande24" } -MaximumRedirection 5 | Out-Null
    Add-Result "PASS teardown admin role restored"
} catch {
    Add-Result "FAIL teardown admin restore: $($_.Exception.Message)"
}

$passCount = ($results | Where-Object { $_ -like "PASS*" }).Count
$warnCount = ($results | Where-Object { $_ -like "WARN*" }).Count
$failCount = ($results | Where-Object { $_ -like "FAIL*" }).Count

Write-Output "===E2E_AUDIT_MASTER_RESULTS==="
$results
Write-Output ("SUMMARY PASS={0} WARN={1} FAIL={2}" -f $passCount, $warnCount, $failCount)
