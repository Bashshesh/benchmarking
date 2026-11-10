param([string]$Python = 'python')
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
New-Item -ItemType Directory -Force .tmp | Out-Null
$env:TEMP = (Resolve-Path .tmp).Path
$env:TMP = $env:TEMP
function Invoke-Checked {
    param([string]$Executable, [string[]]$Arguments)
    & $Executable @Arguments
    if ($LASTEXITCODE -ne 0) { throw "Command failed: $Executable" }
}
if (-not (Test-Path '.numpy126/Scripts/python.exe')) {
    Invoke-Checked $Python @('-m','venv','.numpy126')
}
if (-not (Test-Path '.numpy200/Scripts/python.exe')) {
    Invoke-Checked $Python @('-m','venv','.numpy200')
}
Invoke-Checked '.numpy126/Scripts/python.exe' @('-m','pip','install','numpy==1.26.4')
Invoke-Checked '.numpy200/Scripts/python.exe' @('-m','pip','install','numpy==2.0.0')
$oldPython = (Resolve-Path '.numpy126/Scripts/python.exe').Path
$newPython = (Resolve-Path '.numpy200/Scripts/python.exe').Path
Invoke-Checked '.venv/Scripts/python.exe' @('numpy-experiment/run_numpy.py','--old-python',$oldPython,'--new-python',$newPython,'--repeats','20','--loops','100','--warmups','5','--size','100000')
Invoke-Checked '.venv/Scripts/python.exe' @('numpy-experiment/run_numpy.py','--old-python',$oldPython,'--new-python',$oldPython,'--control','--repeats','20','--loops','100','--warmups','5','--size','100000')
Invoke-Checked '.venv/Scripts/python.exe' @('numpy_diagnostic.py','--old-python',$oldPython,'--new-python',$newPython)
