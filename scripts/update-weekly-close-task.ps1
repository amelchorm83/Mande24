param(
    [string]$TaskName = "Mande24WeeklyCommissionClose",
    [string]$ProjectPath = "C:\Users\Lenovo\Documents\myproyect\mande24_independent\apps\api",
    [string]$PythonExe = "C:\Users\Lenovo\AppData\Local\Python\pythoncore-3.14-64\python.exe",
    [int]$Hour = 1,
    [int]$Minute = 0
)

$scriptPath = Join-Path $PSScriptRoot "register-weekly-close-task.ps1"
& $scriptPath -TaskName $TaskName -ProjectPath $ProjectPath -PythonExe $PythonExe -Hour $Hour -Minute $Minute
