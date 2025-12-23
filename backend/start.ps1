# PowerShell script to start Case Whisperer Backend with Tesseract
Write-Host "🏛️ Starting Case Whisperer Backend..." -ForegroundColor Cyan

# Activate virtual environment
& "venv\Scripts\Activate.ps1"

# Add Tesseract to PATH for this session
$env:PATH += ";C:\Program Files\Tesseract-OCR"

# Verify Tesseract is available
try {
    $tesseractVersion = & tesseract --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Tesseract found - CAPTCHA solving enabled" -ForegroundColor Green
        Write-Host "🚀 Starting backend server..." -ForegroundColor Cyan
        
        # Start the server
        python run.py
    } else {
        throw "Tesseract not working"
    }
} catch {
    Write-Host "❌ Tesseract not found! Please check installation." -ForegroundColor Red
    Write-Host "   Expected location: C:\Program Files\Tesseract-OCR\tesseract.exe" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}