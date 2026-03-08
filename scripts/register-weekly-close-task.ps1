param(
    [string]$TaskName = "Mande24WeeklyCommissionClose",
    [string]$ProjectPath = "C:\Users\Lenovo\Documents\myproyect\mande24_independent\apps\api",
    [string]$PythonExe = "C:\Users\Lenovo\AppData\Local\Python\pythoncore-3.14-64\python.exe",
    [int]$Hour = 1,
    [int]$Minute = 0
)

$actionArgs = "-m app.scripts.close_commissions"
$action = New-ScheduledTaskAction -Execute $PythonExe -Argument $actionArgs -WorkingDirectory $ProjectPath
$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday -At ([datetime]::Today.AddHours($Hour).AddMinutes($Minute).TimeOfDay)
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries

Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Principal $principal -Settings $settings -Force
Write-Output "Task '$TaskName' created/updated."
