# Use official Python base image
FROM python:3.11-slim
# Install system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*
# Set workdir
WORKDIR /app
# Copy files
COPY v3_api_demo.py .
COPY requirements.txt .
COPY README.md .
# Install deps
RUN pip install --no-cache-dir -r requirements.txt
# Expose Gradio port
EXPOSE 7860
# Environment var for Gemini key – you must set it when running
ENV GOOGLE_API_KEY="YOUR_API_KEY_HERE"
# Run
CMD ["python", "v3_api_demo.py"]
