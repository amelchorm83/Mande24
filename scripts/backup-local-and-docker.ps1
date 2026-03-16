param(
	[string]$WorkspaceRoot = "",
	[string]$BackupRoot = "",
	[switch]$SkipProjectZip,
	[switch]$SkipDatabase,
	[switch]$SkipDocker
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

function Assert-Command {
	param([string]$Name)
	if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
		throw "Required command not found: $Name"
	}
}

Assert-Command -Name "docker"
Assert-Command -Name "tar"

if ([string]::IsNullOrWhiteSpace($WorkspaceRoot)) {
	if ($PSScriptRoot) {
		$WorkspaceRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
	} else {
		$WorkspaceRoot = (Get-Location).Path
	}
}

$workspaceRootResolved = (Resolve-Path $WorkspaceRoot).Path
$workspaceName = Split-Path $workspaceRootResolved -Leaf
$workspaceParent = Split-Path $workspaceRootResolved -Parent

if ([string]::IsNullOrWhiteSpace($BackupRoot)) {
	$BackupRoot = Join-Path $workspaceParent "backups"
}

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupDir = Join-Path $BackupRoot $timestamp
New-Item -ItemType Directory -Path $backupDir -Force | Out-Null

$manifest = New-Object System.Collections.Generic.List[string]
$manifest.Add("Backup timestamp: $timestamp")
$manifest.Add("Workspace: $workspaceRootResolved")
$manifest.Add("Backup folder: $backupDir")
$manifest.Add("")

if (-not $SkipProjectZip) {
	$zipPath = Join-Path $backupDir ("$workspaceName" + "_" + $timestamp + ".zip")
	tar -a -c -f $zipPath -C $workspaceParent $workspaceName
	$manifest.Add("Project zip: $zipPath")
}

if (-not $SkipDatabase) {
	$envPath = Join-Path $workspaceRootResolved ".env"
	$pgUser = Get-EnvValue -EnvPath $envPath -Key "POSTGRES_USER" -DefaultValue "postgres"
	$pgPassword = Get-EnvValue -EnvPath $envPath -Key "POSTGRES_PASSWORD" -DefaultValue ""

	$pgContainer = docker ps --filter "name=^/mande24-postgres$" --format "{{.Names}}"
	if (-not $pgContainer) {
		throw "Postgres container mande24-postgres is not running."
	}

	$sqlPath = Join-Path $backupDir ("postgres_all_" + $timestamp + ".sql")
	if ([string]::IsNullOrWhiteSpace($pgPassword)) {
		docker exec $pgContainer pg_dumpall -U $pgUser > $sqlPath
	} else {
		docker exec -e PGPASSWORD=$pgPassword $pgContainer pg_dumpall -U $pgUser > $sqlPath
	}

	$manifest.Add("Postgres dump: $sqlPath")
}

if (-not $SkipDocker) {
	$webLatest = "mande24_independent-web:latest"
	$apiLatest = "mande24_independent-api:latest"

	docker image inspect $webLatest *> $null
	docker image inspect $apiLatest *> $null

	$webBackupTag = "mande24_independent-web:backup-$timestamp"
	$apiBackupTag = "mande24_independent-api:backup-$timestamp"

	docker tag $webLatest $webBackupTag
	docker tag $apiLatest $apiBackupTag

	$webTar = Join-Path $backupDir ("web_image_backup_" + $timestamp + ".tar")
	$apiTar = Join-Path $backupDir ("api_image_backup_" + $timestamp + ".tar")
	$combinedTar = Join-Path $backupDir ("docker_images_backup_" + $timestamp + ".tar")

	docker image save -o $webTar $webBackupTag
	docker image save -o $apiTar $apiBackupTag
	docker image save -o $combinedTar $webBackupTag $apiBackupTag

	$manifest.Add("Web image tar: $webTar")
	$manifest.Add("API image tar: $apiTar")
	$manifest.Add("Combined image tar: $combinedTar")
	$manifest.Add("Web image tag: $webBackupTag")
	$manifest.Add("API image tag: $apiBackupTag")
}

$manifest.Add("")
$manifest.Add("Restore helper:")
$manifest.Add("powershell -ExecutionPolicy Bypass -File scripts/restore-local-and-docker.ps1 -BackupDir '$backupDir'")

$manifestPath = Join-Path $backupDir "backup_manifest.txt"
$manifest | Out-File -FilePath $manifestPath -Encoding utf8

Write-Host "Backup complete: $backupDir"
Write-Host "Manifest: $manifestPath"
