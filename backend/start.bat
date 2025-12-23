@echo off
echo 🏛️ Starting Case Whisperer Backend...

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Add Tesseract to PATH
set "PATH=%PATH%;C:\Program Files\Tesseract-OCR"

REM Verify Tesseract is available
tesseract --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Tesseract not found! Please check installation.
    echo    Expected location: C:\Program Files\Tesseract-OCR\tesseract.exe
    pause
    exit /b 1
)

echo ✅ Tesseract found - CAPTCHA solving enabled
echo 🚀 Starting backend server...

REM Start the server
python run.py