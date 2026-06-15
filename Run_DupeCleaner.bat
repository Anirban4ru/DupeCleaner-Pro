@echo off
title Launching DupeCleaner Pro...

:: Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not added to your system's PATH!
    echo Please install Python 3 from python.org to run this application.
    pause
    exit /b
)

:: Check if virtual environment exists
if not exist ".venv\Scripts\activate" (
    echo [SETUP] First-time setup detected. Creating a virtual environment...
    python -m venv .venv
    
    echo [SETUP] Activating virtual environment...
    call .venv\Scripts\activate
    
    echo [SETUP] Installing required dependencies...
    pip install -r requirements.txt
    
    echo [SETUP] Setup complete!
) else (
    :: Just activate if it already exists
    call .venv\Scripts\activate
)

:: Launch the application using pythonw (so no annoying background terminal stays open)
start pythonw app.py
exit
