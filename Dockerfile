FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY main.py .
COPY hvac_insulation_estimator.py .
COPY pydantic_models.py .
COPY pricebook_sample.json .
COPY measurements_template.csv .

# Optional: Copy Streamlit files for dual deployment
# COPY streamlit_app.py .
# COPY .streamlit/ .streamlit/

# Expose Cloud Run port (default 8080)
EXPOSE 8080

# Health check for Cloud Run
HEALTHCHECK CMD curl --fail http://localhost:8080/health

# Run FastAPI with uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
