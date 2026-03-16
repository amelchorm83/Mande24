param(
    [string]$Owner = "amelchorm83",
    [string]$Repo = "Mande24",
    [string]$Branch = "main",
    [string]$Token = "",
    [string[]]$CheckContexts = @("stagea-smoke", "StageA Smoke CI / stagea-smoke")
)

$ErrorActionPreference = "Stop"

if (-not $Token) {
    $Token = $env:GH_TOKEN
}
if (-not $Token) {
    $Token = $env:GITHUB_TOKEN
}
if (-not $Token) {
    throw "Missing token. Provide -Token or set GH_TOKEN/GITHUB_TOKEN with repo admin permissions."
}

$uri = "https://api.github.com/repos/$Owner/$Repo/branches/$Branch/protection"
$headers = @{
    Authorization = "Bearer $Token"
    Accept = "application/vnd.github+json"
    "X-GitHub-Api-Version" = "2022-11-28"
}

$payload = @{
    required_status_checks = @{
        strict = $true
        contexts = $CheckContexts
    }
    enforce_admins = $false
    required_pull_request_reviews = @{
        dismiss_stale_reviews = $false
        require_code_owner_reviews = $false
        required_approving_review_count = 1
    }
    restrictions = $null
    required_linear_history = $false
    allow_force_pushes = $false
    allow_deletions = $false
    block_creations = $false
    required_conversation_resolution = $true
    lock_branch = $false
    allow_fork_syncing = $true
} | ConvertTo-Json -Depth 10

$response = Invoke-RestMethod -Uri $uri -Method Put -Headers $headers -Body $payload
Write-Host "Branch protection updated successfully."
Write-Host ("Required checks: " + (($response.required_status_checks.contexts) -join ", "))
