@echo off
echo 🏛️ Starting Case Whisperer with Tesseract...

REM Add Tesseract to PATH for this session
set "PATH=%PATH%;C:\Program Files\Tesseract-OCR"

REM Test Tesseract
tesseract --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Tesseract not found!
    pause
    exit /b 1
)

echo ✅ Tesseract found - starting server...
python run.py