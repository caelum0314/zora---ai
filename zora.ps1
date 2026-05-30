# Zora AI Assistant PowerShell Launcher
$ZoraHome = "D:\zora"
$OriginalLocation = Get-Location

try {
    Set-Location $ZoraHome
    & .venv\Scripts\Activate.ps1
    python main.py @args
} finally {
    Set-Location $OriginalLocation
}
