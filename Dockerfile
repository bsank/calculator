FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3-tk \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV DISPLAY=:0

# Set environment variables for InfluxDB
ENV INFLUXDB_URL=http://influxdb:8086
ENV INFLUXDB_TOKEN=eoHE0-Zg85yJEU3EO6EVJ4912W2riiU9mFvU_aFAME5Hfg7SisMeXTnG4HvfH0Tnr4traXNGEy7rwjW4WceWBQ==
ENV INFLUXDB_ORG=calculator
ENV INFLUXDB_BUCKET=calculator_logs

# Command to run the calculator
CMD ["python", "calculator.py"] 