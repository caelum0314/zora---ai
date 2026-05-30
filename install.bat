@echo off
chcp 65001 >nul

:: Check for admin privileges
net session >nul 2>&1
if errorlevel 1 (
    echo [提示] 需要管理员权限来修改系统 PATH
    echo 正在请求管理员权限...
    powershell -Command "Start-Process '%~f0' -Verb runAs"
    exit /b
)

echo ========================================
echo    Zora AI 助手 - 安装程序
echo ========================================
echo.

:: Get current directory
set "ZORA_HOME=%~dp0"
set "ZORA_HOME=%ZORA_HOME:~0,-1%"

:: Check if already in PATH
echo %PATH% | find /i "%ZORA_HOME%" >nul
if not errorlevel 1 (
    echo [✓] Zora 已在 PATH 中
    goto :create_shortcut
)

:: Add to system PATH
echo [+] 正在添加到系统 PATH: %ZORA_HOME%
setx /M PATH "%PATH%;%ZORA_HOME%" >nul 2>&1
if errorlevel 1 (
    echo [✗] 添加到 PATH 失败
    exit /b 1
)
echo [✓] 已成功添加到系统 PATH

:create_shortcut
echo.
echo [+] 创建 PowerShell 启动脚本...

:: Create PowerShell wrapper for better experience
set "PS_FILE=%ZORA_HOME%\zora.ps1"
echo # Zora AI Assistant Launcher > "%PS_FILE%"
echo $ZoraHome = "%ZORA_HOME%" >> "%PS_FILE%"
echo Set-Location $ZoraHome >> "%PS_FILE%"
echo ^& "$ZoraHome\.venv\Scripts\Activate.ps1" >> "%PS_FILE%"
echo python main.py $args >> "%PS_FILE%"

echo [✓] 已创建 PowerShell 脚本: zora.ps1

:: Create Unix shell script for Git Bash/WSL
echo [+] 创建 Unix shell 脚本...
set "SH_FILE=%ZORA_HOME%\zora.sh"
echo #!/bin/bash > "%SH_FILE%"
echo cd "%ZORA_HOME:\=/%" >> "%SH_FILE%"
echo source .venv/Scripts/activate >> "%SH_FILE%"
echo python main.py "$@" >> "%SH_FILE%"

echo [✓] 已创建 Shell 脚本: zora.sh

echo.
echo ========================================
echo    安装完成！
echo ========================================
echo.
echo 使用方法:
echo   - CMD:      zora
echo   - PowerShell: zora.ps1 或直接运行 zora
echo   - Git Bash: bash zora.sh
echo.
echo 请重新打开终端窗口以使用 'zora' 命令
echo.
pause
