$ErrorActionPreference = "Stop"

<#
E2E audit for contact fields (landline + WhatsApp) across catalogs and guide print.
Validates:
- Client/Station/Rider creation with phone fields
- Guide creation using created client + station
- Guide detail and printable view include contact fields
Usage:
  .\scripts\e2e_contact_fields_audit.ps1
#>

$baseApi = "http://localhost:8000"
$session = New-Object Microsoft.PowerShell.Commands.WebRequestSession
$results = New-Object System.Collections.Generic.List[string]

function Add-Result([string]$message) {
    $results.Add($message)
    Write-Output $message
}

function Get-FirstMatchValue([string]$text, [string]$pattern) {
    $m = [regex]::Match($text, $pattern)
    if ($m.Success) { return $m.Groups[1].Value }
    return $null
}

function Check-Contains([string]$text, [string]$needle, [string]$label) {
    if ($text -match [regex]::Escape($needle)) {
        Add-Result "PASS $label contains '$needle'"
    } else {
        Add-Result "FAIL $label missing '$needle'"
    }
}

Add-Result "INFO section=bootstrap"

try {
    Invoke-WebRequest -UseBasicParsing -WebSession $session -Method Post -Uri "$baseApi/ERPMande24/role/select" -Body @{ role = "admin"; return_to = "/ERPMande24" } -MaximumRedirection 5 | Out-Null
    Add-Result "PASS setup role admin"
} catch {
    Add-Result "FAIL setup role admin: $($_.Exception.Message)"
}

$stamp = Get-Date -Format "yyyyMMddHHmmss"
$clientName = "QA Contact Client $stamp"
$stationName = "QA Contact Station $stamp"
$riderName = "QA Contact Rider $stamp"
$riderEmail = "qa.contact.$stamp@mande24.local"
$landline = "993100$($stamp.Substring($stamp.Length - 4))"
$whatsapp = "52993100$($stamp.Substring($stamp.Length - 4))"

$stateCode = $null
$municipalityCode = $null
$postalCode = $null
$colonyId = $null
$clientId = $null
$stationId = $null
$riderId = $null
$serviceId = $null
$guideCode = $null

Add-Result "INFO section=create_client"
try {
    $clientsPage = Invoke-WebRequest -UseBasicParsing -WebSession $session -Uri "$baseApi/ERPMande24/catalogs/clients"
    $stateCode = Get-FirstMatchValue $clientsPage.Content 'id="new-client-state"[\s\S]*?<option value="([A-Z0-9]+)"'
    if (-not $stateCode) { throw "No state option found" }

    $muns = Invoke-RestMethod -WebSession $session -Uri "$baseApi/ERPMande24/geo/municipalities?state_code=$([uri]::EscapeDataString($stateCode))"
    if (-not $muns -or $muns.Count -eq 0) { throw "No municipalities for state=$stateCode" }
    $municipalityCode = $muns[0].code

    $pcs = Invoke-RestMethod -WebSession $session -Uri "$baseApi/ERPMande24/geo/postal-codes?municipality_code=$([uri]::EscapeDataString($municipalityCode))"
    if (-not $pcs -or $pcs.Count -eq 0) { throw "No postal codes for municipality=$municipalityCode" }
    $postalCode = $pcs[0].code

    $cols = Invoke-RestMethod -WebSession $session -Uri "$baseApi/ERPMande24/geo/colonies?state_code=$([uri]::EscapeDataString($stateCode))&municipality_code=$([uri]::EscapeDataString($municipalityCode))&postal_code=$([uri]::EscapeDataString($postalCode))"
    if (-not $cols -or $cols.Count -eq 0) { throw "No colonies for selected geo chain" }
    $colonyId = $cols[0].id

    $createClient = Invoke-WebRequest -UseBasicParsing -WebSession $session -Method Post -Uri "$baseApi/ERPMande24/catalogs/clients/create" -Body @{
        display_name = $clientName
        client_kind = "both"
        state_code = $stateCode
        municipality_code = $municipalityCode
        postal_code = $postalCode
        colony_id = $colonyId
        address_line = "Calle QA Contacto"
        landline_phone = $landline
        whatsapp_phone = $whatsapp
        wants_invoice = "false"
        create_portal_access = "false"
        portal_email = ""
        portal_password = ""
    } -MaximumRedirection 5

    if ($createClient.Content -match "Cliente .* creado") {
        Add-Result "PASS client create submitted"
    } else {
        Add-Result "WARN client create response text not explicit"
    }

    $clientsFiltered = Invoke-WebRequest -UseBasicParsing -WebSession $session -Uri "$baseApi/ERPMande24/catalogs/clients?q=$([uri]::EscapeDataString($clientName))"
    Check-Contains $clientsFiltered.Content $clientName "clients filtered"
    Check-Contains $clientsFiltered.Content $landline "clients filtered"
    Check-Contains $clientsFiltered.Content $whatsapp "clients filtered"
    $clientId = Get-FirstMatchValue $clientsFiltered.Content '/ERPMande24/catalogs/clients/([a-f0-9]{32})'
    if ($clientId) {
        Add-Result "PASS client id parsed $clientId"
    } else {
        Add-Result "FAIL client id not found in filtered list"
    }
} catch {
    Add-Result "FAIL create client flow: $($_.Exception.Message)"
}

Add-Result "INFO section=create_station"
try {
    $stationsPage = Invoke-WebRequest -UseBasicParsing -WebSession $session -Uri "$baseApi/ERPMande24/catalogs/stations"
    $zoneId = Get-FirstMatchValue $stationsPage.Content 'name="zone_id"[\s\S]*?<option value="([a-f0-9]{32})"'
    if (-not $zoneId) { throw "No zone option found" }

    $createStation = Invoke-WebRequest -UseBasicParsing -WebSession $session -Method Post -Uri "$baseApi/ERPMande24/catalogs/stations/create" -Body @{
        name = $stationName
        zone_id = $zoneId
        landline_phone = $landline
        whatsapp_phone = $whatsapp
    } -MaximumRedirection 5

    if ($createStation.Content -match "Estacion .* creada") {
        Add-Result "PASS station create submitted"
    } else {
        Add-Result "WARN station create response text not explicit"
    }

    $stationsFiltered = Invoke-WebRequest -UseBasicParsing -WebSession $session -Uri "$baseApi/ERPMande24/catalogs/stations?q=$([uri]::EscapeDataString($stationName))"
    Check-Contains $stationsFiltered.Content $stationName "stations filtered"
    Check-Contains $stationsFiltered.Content $landline "stations filtered"
    Check-Contains $stationsFiltered.Content $whatsapp "stations filtered"
    $stationId = Get-FirstMatchValue $stationsFiltered.Content '/ERPMande24/catalogs/stations/([a-f0-9]{32})'
    if ($stationId) {
        Add-Result "PASS station id parsed $stationId"
    } else {
        Add-Result "FAIL station id not found in filtered list"
    }
} catch {
    Add-Result "FAIL create station flow: $($_.Exception.Message)"
}

Add-Result "INFO section=create_rider"
try {
    $ridersPage = Invoke-WebRequest -UseBasicParsing -WebSession $session -Uri "$baseApi/ERPMande24/catalogs/riders"
    $zoneIdForRider = Get-FirstMatchValue $ridersPage.Content 'name="zone_id"[\s\S]*?<option value="([a-f0-9]{32})"'

    $createRiderBody = @{
        full_name = $riderName
        email = $riderEmail
        password = "RiderPass123"
        zone_id = $zoneIdForRider
        landline_phone = $landline
        whatsapp_phone = $whatsapp
        vehicle_type = "motorcycle"
    }

    $createRider = Invoke-WebRequest -UseBasicParsing -WebSession $session -Method Post -Uri "$baseApi/ERPMande24/catalogs/riders/create" -Body $createRiderBody -MaximumRedirection 5
    if ($createRider.Content -match "Rider creado") {
        Add-Result "PASS rider create submitted"
    } else {
        Add-Result "WARN rider create response text not explicit"
    }

    $ridersFiltered = Invoke-WebRequest -UseBasicParsing -WebSession $session -Uri "$baseApi/ERPMande24/catalogs/riders?q=$([uri]::EscapeDataString($riderEmail))"
    Check-Contains $ridersFiltered.Content $riderEmail "riders filtered"
    Check-Contains $ridersFiltered.Content $landline "riders filtered"
    Check-Contains $ridersFiltered.Content $whatsapp "riders filtered"
    $riderId = Get-FirstMatchValue $ridersFiltered.Content '/ERPMande24/catalogs/riders/([a-f0-9]{32})'
    if ($riderId) {
        Add-Result "PASS rider id parsed $riderId"
    } else {
        Add-Result "FAIL rider id not found in filtered list"
    }
} catch {
    Add-Result "FAIL create rider flow: $($_.Exception.Message)"
}

Add-Result "INFO section=create_guide_and_print"
if ($clientId -and $stationId) {
    try {
        $newGuide = Invoke-WebRequest -UseBasicParsing -WebSession $session -Uri "$baseApi/ERPMande24/guides/new"
        $serviceId = Get-FirstMatchValue $newGuide.Content 'name="service_id"[\s\S]*?<option value="([a-f0-9]{32})"'
        if (-not $serviceId) { throw "No active service found" }

        # New stations do not have tariff by default; create one for guide generation.
        $pricingCreate = Invoke-WebRequest -UseBasicParsing -WebSession $session -Method Post -Uri "$baseApi/ERPMande24/catalogs/pricing-rules/create" -Body @{
            service_id = $serviceId
            station_id = $stationId
            price = "199.00"
            currency = "MXN"
        } -MaximumRedirection 5
        if ($pricingCreate.Content -match "Tarifa creada|Ya existe tarifa") {
            Add-Result "PASS pricing rule ready for service+station"
        } else {
            Add-Result "WARN pricing create response not explicit"
        }

        $created = Invoke-WebRequest -UseBasicParsing -WebSession $session -Method Post -Uri "$baseApi/ERPMande24/guides/create" -Body @{
            customer_name = "QA Contact Customer"
            destination_name = "QA Contact Destination"
            origin_client_id = $clientId
            destination_client_id = $clientId
            origin_wants_invoice = "false"
            service_id = $serviceId
            station_id = $stationId
        } -MaximumRedirection 5

        if ($created.Content -match "No existe tarifa activa") {
            throw "Guide creation blocked by missing pricing rule"
        }

        $guideMatch = [regex]::Match($created.Content, 'Guia\s+(M24-[0-9]{8}-[A-Z0-9]{6})\s+creada')
        if ($guideMatch.Success) {
            $guideCode = $guideMatch.Groups[1].Value
        } else {
            $guidesFiltered = Invoke-WebRequest -UseBasicParsing -WebSession $session -Uri "$baseApi/ERPMande24/guides?q=$([uri]::EscapeDataString($clientName))"
            $guideCode = Get-FirstMatchValue $guidesFiltered.Content '/ERPMande24/guides/(M24-[0-9]{8}-[A-Z0-9]{6})'
        }
        if (-not $guideCode) { throw "Guide code not found after creation" }
        Add-Result "PASS guide created code=$guideCode"

        $guideDetail = Invoke-WebRequest -UseBasicParsing -WebSession $session -Uri "$baseApi/ERPMande24/guides/$guideCode"
        Check-Contains $guideDetail.Content "Contactos Operativos" "guide detail"
        Check-Contains $guideDetail.Content "Telefono fijo" "guide detail"
        Check-Contains $guideDetail.Content "WhatsApp" "guide detail"

        $printPage = Invoke-WebRequest -UseBasicParsing -WebSession $session -Uri "$baseApi/ERPMande24/guides/$guideCode/print"
        Check-Contains $printPage.Content "Contactos Operativos" "guide print"
        Check-Contains $printPage.Content "Telefono fijo" "guide print"
        Check-Contains $printPage.Content "WhatsApp" "guide print"
        Check-Contains $printPage.Content $landline "guide print"
        Check-Contains $printPage.Content $whatsapp "guide print"
        Add-Result "PASS printable guide validated code=$guideCode"
    } catch {
        Add-Result "FAIL create guide/print flow: $($_.Exception.Message)"
    }
} else {
    Add-Result "FAIL create guide/print flow skipped (missing clientId or stationId)"
}

$passCount = ($results | Where-Object { $_ -like "PASS*" }).Count
$warnCount = ($results | Where-Object { $_ -like "WARN*" }).Count
$failCount = ($results | Where-Object { $_ -like "FAIL*" }).Count

Write-Output "===E2E_CONTACT_FIELDS_RESULTS==="
$results
Write-Output ("SUMMARY PASS={0} WARN={1} FAIL={2}" -f $passCount, $warnCount, $failCount)

if ($failCount -gt 0) {
    exit 1
}
