param(
    [string]$TaskName = "Mande24WeeklyCommissionClose"
)

$task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if (-not $task) {
    Write-Error "Task '$TaskName' not found. Register it first with register-weekly-close-task.ps1"
    exit 1
}

Start-ScheduledTask -TaskName $TaskName
Start-Sleep -Seconds 2

$info = Get-ScheduledTaskInfo -TaskName $TaskName
Write-Output "Task '$TaskName' triggered."
Write-Output "LastRunTime: $($info.LastRunTime)"
Write-Output "LastTaskResult: $($info.LastTaskResult)"
Write-Output "NextRunTime: $($info.NextRunTime)"
