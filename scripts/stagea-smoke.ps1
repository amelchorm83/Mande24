param(
    [string]$ApiBase = "http://localhost:8000",
    [string]$ReportPath = ""
)

$ErrorActionPreference = "Stop"

if (-not $ReportPath) {
    $ReportPath = Join-Path $PSScriptRoot "stagea-smoke-report.json"
}

$adminEmail = "admin1@mande24.local"
$adminPass = "Admin123*"
$riderEmail = "smoke.stagea.rider.api@mande24.test"
$riderPass = "SmokeRider123*"
$base = $ApiBase

$seed = Invoke-RestMethod -Uri "$base/ERPMande24/demo/seed" -Method Post

try {
    Invoke-RestMethod -Uri "$base/api/v1/auth/register" -Method Post -ContentType "application/json" -Body (
        @{ email = $adminEmail; full_name = "Admin Test"; password = $adminPass; role = "admin" } | ConvertTo-Json
    ) | Out-Null
} catch {
}

$adminLogin = Invoke-RestMethod -Uri "$base/api/v1/auth/login" -Method Post -ContentType "application/json" -Body (
    @{ email = $adminEmail; password = $adminPass } | ConvertTo-Json
)
$token = $adminLogin.access_token
$headers = @{ Authorization = "Bearer $token" }

try {
    Invoke-RestMethod -Uri "$base/api/v1/auth/register" -Method Post -ContentType "application/json" -Body (
        @{ email = $riderEmail; full_name = "Smoke Rider API"; password = $riderPass; role = "rider" } | ConvertTo-Json
    ) | Out-Null
} catch {
}

$riderLogin = Invoke-RestMethod -Uri "$base/api/v1/auth/login" -Method Post -ContentType "application/json" -Body (
    @{ email = $riderEmail; password = $riderPass } | ConvertTo-Json
)
$riderUser = Invoke-RestMethod -Uri "$base/api/v1/auth/me" -Headers @{ Authorization = "Bearer $($riderLogin.access_token)" } -Method Get

$riders = Invoke-RestMethod -Uri "$base/api/v1/catalogs/riders" -Headers $headers -Method Get
$existing = $riders | Where-Object { $_.user_id -eq $riderUser.id } | Select-Object -First 1
if (-not $existing) {
    $newRider = Invoke-RestMethod -Uri "$base/api/v1/catalogs/riders" -Headers $headers -Method Post -ContentType "application/json" -Body (
        @{ user_id = $riderUser.id; station_id = $seed.station_id } | ConvertTo-Json
    )
    $riderId = $newRider.id
} else {
    $riderId = $existing.id
}

$muns = Invoke-RestMethod -Uri "$base/ERPMande24/geo/municipalities?state_code=SIN" -Method Get
$mun = $muns[0].code
$pcs = Invoke-RestMethod -Uri "$base/ERPMande24/geo/postal-codes?municipality_code=$mun" -Method Get
$pc = $pcs[0].code
$cols = Invoke-RestMethod -Uri "$base/ERPMande24/geo/colonies?state_code=SIN&municipality_code=$mun&postal_code=$pc" -Method Get
$col = $cols[0].id

$guideReq = @{
    customer_name = "Smoke API StageA"
    destination_name = "Smoke API Dest"
    origin_whatsapp_phone = "5511111111"
    origin_email = "origin@example.com"
    origin_state_code = "SIN"
    origin_municipality_code = $mun
    origin_postal_code = $pc
    origin_colony_id = $col
    origin_address_line = "Calle 1"
    destination_whatsapp_phone = "5522222222"
    destination_email = "dest@example.com"
    destination_state_code = "SIN"
    destination_municipality_code = $mun
    destination_postal_code = $pc
    destination_colony_id = $col
    destination_address_line = "Calle 2"
    requester_role = "origin"
    service_id = $seed.service_id
    station_id = $seed.station_id
    use_station_handoff = $false
} | ConvertTo-Json

$guide = Invoke-RestMethod -Uri "$base/api/v1/guides" -Headers $headers -Method Post -ContentType "application/json" -Body $guideReq
$legs = Invoke-RestMethod -Uri "$base/api/v1/guides/$($guide.guide_code)/route-legs" -Headers $headers -Method Get
$firstLeg = $legs[0]

if (-not $firstLeg) {
    throw "Smoke failed: no route legs returned for guide $($guide.guide_code)."
}
if ($firstLeg.status -ne "planned") {
    throw "Smoke failed: expected first route leg status 'planned', got '$($firstLeg.status)'."
}

$assignReq = @{ rider_id = $riderId; status = "assigned" } | ConvertTo-Json
$assigned = Invoke-RestMethod -Uri "$base/api/v1/guides/route-legs/$($firstLeg.id)/assign" -Headers $headers -Method Patch -ContentType "application/json" -Body $assignReq

if ($assigned.status -ne "assigned") {
    throw "Smoke failed: transition planned -> assigned did not complete. Current status '$($assigned.status)'."
}
if ($assigned.assigned_rider_id -ne $riderId) {
    throw "Smoke failed: assigned rider mismatch. Expected '$riderId', got '$($assigned.assigned_rider_id)'."
}

$health = Invoke-RestMethod -Uri "$base/api/v1/health/commissions" -Headers $headers -Method Get

if ($health.status -ne "ok") {
    throw "Smoke failed: /health/commissions status is '$($health.status)' (expected 'ok')."
}
if ($health.commission_closes.failed -ne 0 -or $health.commission_closes.in_progress -ne 0) {
    throw "Smoke failed: commission close health degraded. failed=$($health.commission_closes.failed), in_progress=$($health.commission_closes.in_progress)."
}

$report = [ordered]@{
    generated_at_utc = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
    api_base = $base
    seed = $seed
    guide = $guide
    route_leg_before = $firstLeg
    route_leg_after = $assigned
    health = $health
    assertions = [ordered]@{
        route_leg_transition_planned_to_assigned = $true
        assigned_rider_matches_requested = $true
        health_status_ok = $true
        commission_health_clean = $true
    }
}

$report | ConvertTo-Json -Depth 10 | Out-File -Encoding utf8 $ReportPath

Write-Host ("SEED=" + ($seed | ConvertTo-Json -Compress))
Write-Host ("GUIDE=" + ($guide | ConvertTo-Json -Compress))
Write-Host ("LEG_BEFORE=" + ($firstLeg | ConvertTo-Json -Compress))
Write-Host ("ASSIGN=" + ($assigned | ConvertTo-Json -Compress))
Write-Host ("HEALTH=" + ($health | ConvertTo-Json -Compress))
Write-Host ("REPORT_PATH=" + $ReportPath)
