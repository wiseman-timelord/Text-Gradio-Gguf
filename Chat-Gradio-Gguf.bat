REM .\Chat-Gradio-Gguf.bat
@echo off
setlocal enabledelayedexpansion

REM display setup
REM mode con: cols=80 lines=25

REM title code
set "TITLE=Chat-Gradio-Gguf"
title %TITLE%

:: DP0 TO SCRIPT BLOCK, DO NOT, MODIFY or MOVE: START
set "ScriptDirectory=%~dp0"
set "ScriptDirectory=%ScriptDirectory:~0,-1%"
cd /d "%ScriptDirectory%"
echo Dp0'd to Script.
:: DP0 TO SCRIPT BLOCK, DO NOT, MODIFY or MOVE: END

REM Check for Administrator privileges
net session >nul 2>&1
if %errorLevel% NEQ 0 (
    echo Error: Admin Required!
    timeout /t 2 >nul
    echo Right Click, Run As Administrator.
    timeout /t 2 >nul
    goto :end_of_script
)
echo Status: Administrator
timeout /t 1 >nul

REM Functions
goto :SkipFunctions

:DisplayTitle
REM cls
echo ===============================================================================
echo "              _________           ________          ________                 "
echo "              \_   ___ \         /  _____/         /  _____/                 "
echo "              /    \  \/  ______/   \  ___  ______/   \  ___                 "
echo "              \     \____/_____/\    \_\  \/_____/\    \_\  \                "
echo "               \______  /        \______  /        \______  /                "
echo "                      \/                \/                \/                 "
echo ===============================================================================
goto :eof

:DisplaySeparator
echo ===============================================================================
goto :eof

:MainMenu
color 0B
call :DisplayTitle
echo     Batch Menu
call :DisplaySeparator
echo.
echo.
echo.
echo.
echo     1. Launch Main Program
echo.
echo     2. Run Install Script
echo.
echo.
echo.
echo.
call :DisplaySeparator
set /p "choice=Selection; Options = 1-2, Exit = X: "

REM Process user input
if /i "%choice%"=="1" (
    color 1B
    call :DisplayTitle
    echo Starting %TITLE%...
    set PYTHONUNBUFFERED=1
    
    REM Activate venv and launch
    call .\venv\Scripts\activate.bat
    python.exe -u .\launcher.py
    
    REM Check for errors
    if errorlevel 1 (
        echo Error launching %TITLE%
        pause
    )
    
    REM Deactivate venv
    deactivate
    set PYTHONUNBUFFERED=0
    pause
    goto MainMenu
)

if /i "%choice%"=="2" (
    cls
    color 1B
    echo Running Installer...
	timeout /t 1 >nul
	cls
	call :DisplaySeparator
	python.exe .\installer.py
    if errorlevel 1 (
        echo Error during installation
    )
    goto MainMenu
)

if /i "%choice%"=="X" (
    cls
    call :DisplayTitle
    echo Closing %TITLE%...
    timeout /t 2 >nul
    goto :end_of_script
)

REM Invalid input handling
echo.
echo Invalid selection. Please try again.
timeout /t 2 >nul
goto MainMenu

:SkipFunctions
goto MainMenu

:end_of_script
pause
cls
color 0B
call :DisplayTitle
echo. 
timeout /t 2 >nul
exit