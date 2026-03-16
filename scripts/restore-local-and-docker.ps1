param(
    [Parameter(Mandatory = $true)]
    [string]$BackupDir,
    [string]$WorkspaceRoot = "",
    [string]$ExtractRoot = "",
    [switch]$SkipProjectExtract,
    [switch]$SkipDockerLoad,
    [switch]$SkipDatabaseRestore
)

$ErrorActionPreference = "Stop"

function Get-EnvValue {
    param(
        [string]$EnvPath,
        [string]$Key,
        [string]$DefaultValue = ""
    )

    if (-not (Test-Path $EnvPath)) {
        return $DefaultValue
    }

    $line = Get-Content $EnvPath | Where-Object { $_ -match "^$Key=" } | Select-Object -First 1
    if (-not $line) {
        return $DefaultValue
    }

    return ($line -split "=", 2)[1]
}

function Try-LoadImageTar {
    param([string]$TarPath)
    if (Test-Path $TarPath) {
        docker load -i $TarPath | Out-Null
        return $true
    }
    return $false
}

$backupDirResolved = (Resolve-Path $BackupDir).Path

if ([string]::IsNullOrWhiteSpace($WorkspaceRoot)) {
    if ($PSScriptRoot) {
        $WorkspaceRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
    } else {
        $WorkspaceRoot = (Get-Location).Path
    }
}

$workspaceRootResolved = (Resolve-Path $WorkspaceRoot).Path

if ([string]::IsNullOrWhiteSpace($ExtractRoot)) {
    $ExtractRoot = Join-Path (Split-Path $backupDirResolved -Parent) "restores"
}

$timestamp = Split-Path $backupDirResolved -Leaf
$manifest = New-Object System.Collections.Generic.List[string]
$manifest.Add("Restore source: $backupDirResolved")
$manifest.Add("Timestamp: $timestamp")
$manifest.Add("")

if (-not $SkipProjectExtract) {
    $zip = Get-ChildItem $backupDirResolved -Filter "*_*.zip" | Select-Object -First 1
    if ($zip) {
        $extractDir = Join-Path $ExtractRoot ("restored_" + $timestamp)
        New-Item -ItemType Directory -Path $extractDir -Force | Out-Null
        Expand-Archive -Path $zip.FullName -DestinationPath $extractDir -Force
        $manifest.Add("Project extracted to: $extractDir")
    } else {
        $manifest.Add("Project zip not found. Skipped extract.")
    }
}

if (-not $SkipDockerLoad) {
    $webTar = Join-Path $backupDirResolved ("web_image_backup_" + $timestamp + ".tar")
    $apiTar = Join-Path $backupDirResolved ("api_image_backup_" + $timestamp + ".tar")
    $combinedTar = Join-Path $backupDirResolved ("docker_images_backup_" + $timestamp + ".tar")

    $loaded = $false
    $webLoaded = Try-LoadImageTar -TarPath $webTar
    $apiLoaded = Try-LoadImageTar -TarPath $apiTar
    if ($webLoaded -or $apiLoaded) {
        $loaded = $true
    }

    if (-not $loaded -and (Test-Path $combinedTar)) {
        docker load -i $combinedTar | Out-Null
        $loaded = $true
    }

    if ($loaded) {
        $webBackupTag = "mande24_independent-web:backup-$timestamp"
        $apiBackupTag = "mande24_independent-api:backup-$timestamp"

        docker image inspect $webBackupTag *> $null
        docker image inspect $apiBackupTag *> $null

        docker tag $webBackupTag "mande24_independent-web:latest"
        docker tag $apiBackupTag "mande24_independent-api:latest"

        $manifest.Add("Docker images loaded and retagged to latest.")
    } else {
        $manifest.Add("Docker image tar not found. Skipped docker load.")
    }
}

if (-not $SkipDatabaseRestore) {
    $sqlPath = Join-Path $backupDirResolved ("postgres_all_" + $timestamp + ".sql")
    if (Test-Path $sqlPath) {
        $envPath = Join-Path $workspaceRootResolved ".env"
        $pgUser = Get-EnvValue -EnvPath $envPath -Key "POSTGRES_USER" -DefaultValue "postgres"
        $pgPassword = Get-EnvValue -EnvPath $envPath -Key "POSTGRES_PASSWORD" -DefaultValue ""

        $pgContainer = docker ps --filter "name=^/mande24-postgres$" --format "{{.Names}}"
        if (-not $pgContainer) {
            throw "Postgres container mande24-postgres is not running."
        }

        if ([string]::IsNullOrWhiteSpace($pgPassword)) {
            Get-Content -Path $sqlPath | docker exec -i $pgContainer psql -U $pgUser -d postgres | Out-Null
        } else {
            Get-Content -Path $sqlPath | docker exec -i -e PGPASSWORD=$pgPassword $pgContainer psql -U $pgUser -d postgres | Out-Null
        }

        $manifest.Add("Database restored from: $sqlPath")
    } else {
        $manifest.Add("Database dump not found. Skipped database restore.")
    }
}

$restoreManifest = Join-Path $backupDirResolved "restore_manifest.txt"
$manifest | Out-File -FilePath $restoreManifest -Encoding utf8

Write-Host "Restore completed from: $backupDirResolved"
Write-Host "Manifest: $restoreManifest"
