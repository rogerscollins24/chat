@echo off
REM LeadPulse Backend Quick Start Script (Windows)

echo.
echo 🚀 LeadPulse Chat System - Backend Startup
echo ==========================================
echo.

REM Check if venv exists
if not exist "venv" (
    echo ❌ Virtual environment not found!
    echo Please run setup first:
    echo   python -m venv venv
    echo   venv\Scripts\activate
    echo   pip install -r requirements.txt
    pause
    exit /b 1
)

REM Activate venv
call venv\Scripts\activate.bat

REM Check if .env exists
if not exist ".env" (
    echo ⚠️  .env file not found!
    echo Creating .env from template...
    copy .env.example .env
    echo ✓ .env created. Please edit it with your database configuration.
    echo.
)

REM Get Python version
python --version

echo ✓ Python installed
echo.
echo Starting FastAPI server...
echo 📍 API will be available at: http://localhost:8000
echo 📚 Docs available at: http://localhost:8000/docs
echo.
echo Press Ctrl+C to stop the server
echo.

REM Start the server
uvicorn main:app --reload --host 0.0.0.0 --port 8000

pause
