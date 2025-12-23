#!/bin/bash

# Case Whisperer Backend Startup Script

echo "🏛️  Starting Case Whisperer Backend..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📚 Installing dependencies..."
pip install -r requirements.txt

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚙️  Creating .env file from example..."
    cp .env.example .env
    echo "📝 Please edit .env file with your configuration"
fi

# Check for Tesseract
if ! command -v tesseract &> /dev/null; then
    echo "⚠️  Warning: Tesseract OCR not found!"
    echo "   Please install Tesseract:"
    echo "   - Ubuntu/Debian: sudo apt-get install tesseract-ocr"
    echo "   - macOS: brew install tesseract"
    echo "   - Windows: Download from GitHub releases"
fi

# Start the server
echo "🚀 Starting FastAPI server..."
python run.py