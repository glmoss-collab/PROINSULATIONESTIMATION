#!/bin/bash
# Quick start script for HVAC Insulation Estimator

echo "🏗️  HVAC Insulation Estimator - Starting..."
echo ""

# Check if Python is installed
if ! command -v python &> /dev/null; then
    echo "❌ Python is not installed. Please install Python 3.10+"
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python --version 2>&1 | awk '{print $2}')
echo "✓ Python $PYTHON_VERSION detected"

# Install requirements if needed
if ! python -c "import streamlit" &> /dev/null; then
    echo "📦 Installing dependencies..."
    pip install -r requirements.txt
fi

echo "✓ Dependencies installed"
echo ""
echo "🚀 Starting Streamlit application..."
echo "   Open your browser to: http://localhost:8501"
echo ""
echo "   Press Ctrl+C to stop the server"
echo ""

# Run Streamlit
streamlit run streamlit_app.py
