param(
    [string]$ProjectPath = "C:\Users\Lenovo\Documents\myproyect\mande24_independent\apps\api",
    [string]$PythonExe = "C:\Users\Lenovo\AppData\Local\Python\pythoncore-3.14-64\python.exe"
)

Set-Location $ProjectPath
& $PythonExe -m app.scripts.audit_weekly_close
