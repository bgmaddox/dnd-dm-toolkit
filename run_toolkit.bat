@echo off
setlocal enabledelayedexpansion

echo ------------------------------------------
echo    DM Toolkit: Portable Launcher (Windows)
echo ------------------------------------------

:: 1. Check for Python
where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    where py >nul 2>nul
    if !ERRORLEVEL! neq 0 (
        echo ERROR: Python is not installed.
        echo Please download and install Python from: https://www.python.org/downloads/
        start https://www.python.org/downloads/
        pause
        exit /b 1
    ) else (
        set PYTHON_EXE=py
    )
) else (
    set PYTHON_EXE=python
)

:: 2. Setup Virtual Environment
if not exist .venv (
    echo Creating virtual environment...
    %PYTHON_EXE% -m venv .venv
)

:: 3. Activate and Install Requirements
call .venv\Scripts\activate
echo Checking dependencies...
pip install --quiet -r requirements.txt

:: 4. Start Server
echo Starting toolkit...
:: PORTABLE=1 enables dynamic port selection, browser auto-open, and setup wizard
set PORTABLE=1
%PYTHON_EXE% server.py

if %ERRORLEVEL% neq 0 (
    echo.
    echo Server stopped unexpectedly.
    pause
)
