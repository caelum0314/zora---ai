@echo off
REM ============================================================
REM  Zora AI 助手启动脚本
REM  切换到项目目录，激活虚拟环境，然后启动主程序。
REM  所有命令行参数（%*）会透传给 main.py。
REM ============================================================
cd /d D:\zora
call .venv\Scripts\activate.bat
python main.py %*
