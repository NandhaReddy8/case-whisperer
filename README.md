# Case Whisperer 🏛️

> **Professional Legal Case Management System with Automated eCourt Integration**

A comprehensive web application for tracking and managing Indian legal cases with automated data fetching from eCourts, CAPTCHA solving, and Google Calendar integration.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![React](https://img.shields.io/badge/react-18+-blue.svg)
![FastAPI](https://img.shields.io/badge/fastapi-0.100+-green.svg)

## ✨ Features

### 🤖 **Automated eCourt Integration**
- **Smart CAPTCHA Solving**: AI-powered CAPTCHA resolution using OpenCV + Tesseract
- **Multi-Search Support**: CNR, Case Number, Diary Number, Party Name searches
- **Real-time Data Sync**: Automatic case status updates from government servers
- **Retry Logic**: Robust error handling with intelligent retry mechanisms

### 📅 **Google Calendar Integration**
- **Automatic Event Creation**: Hearing dates sync to Google Calendar
- **Smart Reminders**: 1-day and 1-week advance notifications
- **Duplicate Prevention**: Intelligent event management
- **Optional Integration**: Works with or without calendar sync

### 🎨 **Professional Frontend**
- **Modern UI**: Built with React, TypeScript, and Tailwind CSS
- **Law Firm Theme**: Professional design with legal industry aesthetics
- **Responsive Design**: Works seamlessly on desktop and mobile
- **Real-time Updates**: Live case status updates and notifications

### ⚡ **Powerful Backend**
- **FastAPI Framework**: High-performance async API
- **Background Scheduler**: Automated 3 AM daily case refreshes
- **SQLite Database**: Lightweight, reliable data storage
- **Comprehensive Logging**: Detailed operation tracking

## 🚀 Quick Start

### Prerequisites
- **Python 3.8+** - [Download](https://www.python.org/downloads/)
- **Node.js 16+** - [Download](https://nodejs.org/)
- **Tesseract OCR** - [Installation Guide](#tesseract-installation)

### 1. Clone Repository
```bash
git clone https://github.com/yourusername/case-whisperer.git
cd case-whisperer
```

### 2. Backend Setup
```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Start backend (with Tesseract PATH)
# Windows PowerShell:
$env:PATH += ";C:\Program Files\Tesseract-OCR"; python run.py
# Windows CMD:
set PATH=%PATH%;C:\Program Files\Tesseract-OCR && python run.py
```

### 3. Frontend Setup
```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

### 4. Access Application
- **Frontend**: http://localhost:8080
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## 🔧 Installation Guides

### Tesseract Installation

#### Windows
1. Download from [GitHub Releases](https://github.com/UB-Mannheim/tesseract/wiki)
2. Install `tesseract-ocr-w64-setup-5.5.1.exe`
3. **Important**: Check "Add to PATH" during installation
4. Verify: `tesseract --version`

#### macOS
```bash
brew install tesseract
```

#### Ubuntu/Debian
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr tesseract-ocr-eng
```

### Google Calendar Setup (Optional)
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create project and enable Google Calendar API
3. Create OAuth 2.0 credentials
4. Download `credentials.json` to backend directory
5. First run will prompt for authorization

## 📖 Usage

### Adding Cases
1. Click "Add New Case" in the dashboard
2. Choose search type (CNR, Case Number, etc.)
3. Enter case details
4. Enable calendar sync if desired
5. Click "Search & Add Case"
6. CAPTCHA is solved automatically!

### Managing Cases
- **View Details**: Click on any case to see full information
- **Refresh Data**: Manual or automatic updates from eCourt
- **Calendar Sync**: Toggle Google Calendar integration
- **Case History**: View complete case timeline

### Automated Features
- **Daily Refresh**: Cases update automatically at 3 AM
- **Change Detection**: Only updates when case data changes
- **Error Handling**: Graceful handling of eCourt server issues
- **Retry Logic**: Automatic retries for failed requests

## 🏗️ Architecture

```
case-whisperer/
├── backend/                 # FastAPI Backend
│   ├── app/
│   │   ├── api/routes/     # REST API endpoints
│   │   ├── core/           # Configuration & database
│   │   ├── lib/            # eCourt integration
│   │   ├── models/         # Pydantic data models
│   │   └── services/       # Business logic
│   ├── requirements.txt    # Python dependencies
│   └── run.py             # Server startup
│
├── frontend/               # React Frontend
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── pages/         # Page components
│   │   ├── lib/           # API client & utilities
│   │   └── types/         # TypeScript definitions
│   └── package.json       # Node dependencies
│
└── reference/              # Working implementation reference
```

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/health` | Health check |
| `POST` | `/api/v1/cases` | Add new case |
| `GET` | `/api/v1/cases` | List all cases |
| `GET` | `/api/v1/cases/{id}` | Get specific case |
| `PUT` | `/api/v1/cases/{id}` | Update case |
| `DELETE` | `/api/v1/cases/{id}` | Delete case |
| `POST` | `/api/v1/cases/{id}/refresh` | Refresh case data |
| `POST` | `/api/v1/cases/search` | Search without adding |

## ⚙️ Configuration

### Backend (.env)
```env
DATABASE_URL=sqlite:///./cases.db
ALLOWED_ORIGINS=http://localhost:8080
GOOGLE_CREDENTIALS_FILE=credentials.json
ECOURT_MAX_RETRIES=3
SCHEDULER_ENABLED=true
REFRESH_HOUR=3
```

### Frontend (.env)
```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

## 🧪 Testing

```bash
# Backend tests
cd backend
pytest

# Frontend tests  
cd frontend
npm test

# API testing
curl http://localhost:8000/api/v1/health
```

## 🚨 Troubleshooting

### Common Issues

**CAPTCHA Solving Fails**
- Ensure Tesseract is installed and in PATH
- Restart backend server with correct PATH
- Check Tesseract version: `tesseract --version`

**eCourt 404 Errors**
- Government servers can be unreliable
- System includes retry logic and fallbacks
- Check server logs for detailed error information

**Calendar Sync Issues**
- Verify Google API credentials
- Check OAuth permissions
- Ensure `credentials.json` is in backend directory

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Indian eCourts System** - Government digital platform
- **Tesseract OCR** - Open-source OCR engine
- **FastAPI** - Modern Python web framework
- **React** - Frontend framework
- **shadcn/ui** - Beautiful UI components

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/case-whisperer/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/case-whisperer/discussions)
- **Documentation**: [Wiki](https://github.com/yourusername/case-whisperer/wiki)

---

**Case Whisperer** - Revolutionizing legal case management with automation and intelligence. 🏛️✨