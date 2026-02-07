# Case Whisperer 🏛️

> **Professional Legal Case Management System with Automated eCourt Integration**

A comprehensive web application for tracking and managing Indian legal cases with automated data fetching from eCourts, AI-powered CAPTCHA solving, and Google Calendar integration.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![React](https://img.shields.io/badge/react-18+-blue.svg)
![FastAPI](https://img.shields.io/badge/fastapi-0.100+-green.svg)

## ✨ Features

### 🤖 **Advanced eCourt Integration**
- **AI-Powered CAPTCHA Solving**: Automatic CAPTCHA resolution using OpenCV + Tesseract OCR
- **Multiple Search Methods**: CNR, Case Number, Case Type, Act Type, Diary Number, and Party Name searches
- **Real-time Data Sync**: Automatic case status updates from government servers
- **Intelligent Retry Logic**: Robust error handling with exponential backoff
- **Comprehensive Data Extraction**: Parties, hearings, orders, objections, and FIR details
- **Court Validation**: Validates against known court combinations for accuracy

### 📊 **Enhanced Data Management**
- **SQLite Storage Layer**: Efficient local storage with proper indexing and JSON support
- **Change Detection**: Hash-based change detection to avoid unnecessary updates
- **Bulk Operations**: Bulk case refresh with detailed statistics
- **Search & Filter**: Full-text search across cases with advanced filtering
- **Data Export**: Export case data in JSON format (CSV coming soon)
- **Storage Analytics**: Comprehensive statistics and storage insights

### 📅 **Google Calendar Integration**
- **Automatic Event Creation**: Hearing dates sync to Google Calendar
- **Smart Reminders**: 1-day and 1-week advance notifications
- **Duplicate Prevention**: Intelligent event management
- **Optional Integration**: Works seamlessly with or without calendar sync
- **Real-time Updates**: Calendar events update when hearing dates change

### 🎨 **Professional Frontend**
- **Modern UI**: Built with React, TypeScript, and Tailwind CSS
- **Law Firm Theme**: Professional design with legal industry aesthetics
- **Responsive Design**: Works seamlessly on desktop and mobile
- **Real-time Updates**: Live case status updates and notifications
- **Interactive Calendar**: Visual calendar view for upcoming hearings
- **Case Timeline**: Detailed case history with visual timeline

### ⚡ **Powerful Backend**
- **FastAPI Framework**: High-performance async API with automatic documentation
- **Background Scheduler**: Automated daily case refreshes at 3 AM
- **Comprehensive API**: RESTful API with full CRUD operations
- **Error Handling**: Comprehensive error classification and handling
- **Logging**: Detailed operation tracking and debugging support
- **Court Management**: Dynamic court and case type management

### 🔍 **Advanced Search Capabilities**
- **CNR Search**: Direct case lookup using 16-digit CNR numbers
- **Case Number Search**: Search by case type, number, and year
- **Party Name Search**: Find cases by petitioner or respondent names
- **Diary Number Search**: Search using court diary numbers
- **Case Type Search**: Browse cases by specific case types
- **Act Type Search**: Find cases under specific legal acts

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
2. Select your court from the dropdown
3. Choose search type (CNR, Case Number, etc.)
4. Enter case details
5. Enable calendar sync if desired
6. Click "Search & Add Case"
7. CAPTCHA is solved automatically!

### Managing Cases
- **View Details**: Click on any case to see comprehensive information
- **Refresh Data**: Manual or automatic updates from eCourt
- **Calendar Sync**: Toggle Google Calendar integration per case
- **Case History**: View complete case timeline with orders and hearings
- **Search & Filter**: Find cases quickly using various criteria

### Automated Features
- **Daily Refresh**: Cases update automatically at 3 AM
- **Change Detection**: Only updates when case data actually changes
- **Error Handling**: Graceful handling of eCourt server issues
- **Retry Logic**: Automatic retries for failed requests with exponential backoff
- **Storage Optimization**: Efficient data storage with proper indexing

## 🏗️ Architecture

```
case-whisperer/
├── backend/                 # FastAPI Backend
│   ├── app/
│   │   ├── api/routes/     # REST API endpoints
│   │   ├── core/           # Configuration & database
│   │   ├── lib/            # eCourt integration
│   │   │   ├── entities.py # Data models
│   │   │   ├── parsers.py  # HTML parsing
│   │   │   ├── storage.py  # SQLite storage
│   │   │   └── captcha.py  # CAPTCHA solving
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
```

## 🔌 Enhanced API Endpoints

### Core Case Management
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/health` | Health check |
| `POST` | `/api/v1/cases` | Add new case |
| `GET` | `/api/v1/cases` | List all cases with filtering |
| `GET` | `/api/v1/cases/search` | Search cases by various fields |
| `GET` | `/api/v1/cases/{id}` | Get specific case |
| `PUT` | `/api/v1/cases/{id}` | Update case |
| `DELETE` | `/api/v1/cases/{id}` | Delete case |
| `POST` | `/api/v1/cases/{id}/refresh` | Refresh case data |
| `POST` | `/api/v1/cases/refresh/bulk` | Bulk refresh cases |
| `POST` | `/api/v1/cases/search` | Search without adding |

### Court & Case Type Management
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/courts` | Get available courts |
| `GET` | `/api/v1/courts/{state_code}/case-types` | Get case types for court |
| `GET` | `/api/v1/courts/{state_code}/act-types` | Get act types for court |

### Analytics & Export
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/cases/stats` | Get case statistics |
| `GET` | `/api/v1/cases/refresh/status` | Get refresh status |
| `POST` | `/api/v1/cases/export` | Export cases data |

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
- System includes comprehensive retry logic and fallbacks
- Check server logs for detailed error information

**Calendar Sync Issues**
- Verify Google API credentials
- Check OAuth permissions
- Ensure `credentials.json` is in backend directory

**Database Issues**
- SQLite database is created automatically
- Check file permissions in backend directory
- Use storage statistics endpoint to verify data

## 🔄 Data Flow

1. **Case Search**: User searches via frontend → API validates → eCourt client fetches data
2. **CAPTCHA Solving**: Automatic image processing → OCR → Text extraction
3. **Data Parsing**: HTML response → Structured data → Entity validation
4. **Storage**: SQLite database → Indexed storage → Change detection
5. **Calendar Sync**: Hearing dates → Google Calendar API → Event creation
6. **Updates**: Scheduled refresh → Change detection → Notification

## 📊 Performance Features

- **Efficient Storage**: SQLite with proper indexing for fast queries
- **Change Detection**: Hash-based comparison to avoid unnecessary updates
- **Bulk Operations**: Process multiple cases efficiently
- **Caching**: Intelligent caching of frequently accessed data
- **Retry Logic**: Exponential backoff for failed requests
- **Connection Pooling**: Optimized database connections

## 🔒 Security Features

- **Input Validation**: Comprehensive validation of all inputs
- **Error Handling**: Secure error messages without sensitive data exposure
- **Rate Limiting**: Built-in protection against excessive requests
- **CORS Configuration**: Proper cross-origin resource sharing setup
- **Data Sanitization**: Clean and validate all data from external sources

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
- **Tesseract OCR** - Open-source OCR engine for CAPTCHA solving
- **FastAPI** - Modern Python web framework
- **React** - Frontend framework
- **shadcn/ui** - Beautiful UI components
- **Reference Implementation** - Based on proven eCourt integration patterns

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/case-whisperer/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/case-whisperer/discussions)

---

**Case Whisperer** - Revolutionizing legal case management with automation, intelligence, and comprehensive eCourt integration. 🏛️✨