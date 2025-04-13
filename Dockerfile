FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3-tk \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Set environment variables for InfluxDB
ENV INFLUXDB_URL=http://influxdb:8086
ENV INFLUXDB_TOKEN=my-super-secret-auth-token
ENV INFLUXDB_ORG=calculator
ENV INFLUXDB_BUCKET=calculator_logs

# Command to run the application
CMD ["python", "calculator.py"] 