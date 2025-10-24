@echo off
REM Quick start script for HVAC Insulation Estimator (Windows)

echo.
echo 🏗️  HVAC Insulation Estimator - Starting...
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed. Please install Python 3.10+
    pause
    exit /b 1
)

echo ✓ Python detected
echo.

REM Install requirements
echo 📦 Installing dependencies...
pip install -r requirements.txt

echo ✓ Dependencies installed
echo.
echo 🚀 Starting Streamlit application...
echo    Open your browser to: http://localhost:8501
echo.
echo    Press Ctrl+C to stop the server
echo.

REM Run Streamlit
streamlit run streamlit_app.py
