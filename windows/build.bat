@echo off
REM EVE Veles Eyes - Windows Build Script
REM Creates standalone .exe using PyInstaller

echo ==========================================
echo EVE Veles Eyes v2.2 - Windows Build
echo ==========================================
echo.

REM Check if virtual environment exists
if not exist "venv\" (
    echo Creating virtual environment...
    python -m venv venv
    echo.
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate
echo.

REM Install/upgrade dependencies
echo Installing dependencies...
pip install --upgrade pip >nul 2>&1
pip install -r requirements.txt >nul 2>&1
pip install pyinstaller >nul 2>&1
echo Done.
echo.

REM Clean previous builds
echo Cleaning previous builds...
if exist "build\" rmdir /s /q build
if exist "dist\" rmdir /s /q dist
echo.

REM Build executable
echo Building executable...
echo This may take a few minutes...
pyinstaller build.spec
echo.

if exist "dist\EVE-Veles-Eyes.exe" (
    echo ==========================================
    echo Build Complete!
    echo ==========================================
    echo.
    echo Executable created: dist\EVE-Veles-Eyes.exe
    echo Size:
    dir dist\EVE-Veles-Eyes.exe | find "EVE-Veles-Eyes.exe"
    echo.
    echo You can now distribute dist\EVE-Veles-Eyes.exe
    echo.
) else (
    echo ==========================================
    echo Build Failed!
    echo ==========================================
    echo.
    echo Check the output above for errors.
    echo.
)

pause
