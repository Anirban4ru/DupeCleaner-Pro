@echo off
echo ========================================================
echo   DupeCleaner Pro - Build Script
echo ========================================================
echo.

echo [1/2] Installing required dependencies...
pip install -r requirements.txt

echo.
echo [2/2] Building the standalone application with PyInstaller...
pyinstaller --noconfirm --onedir --windowed --name "DupeCleanerPro" app.py

echo.
echo ========================================================
echo   Build Complete!
echo ========================================================
echo You can find your compiled application inside the "dist\DupeCleanerPro" folder.
echo You can zip this folder and share it with others!
echo.
pause
