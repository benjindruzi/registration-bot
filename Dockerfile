# Use an official Python image
FROM python:3.11-slim

# Install Chrome
RUN apt-get update && apt-get install -y wget gnupg \
    && wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
    && apt-get install -y ./google-chrome-stable_current_amd64.deb \
    && rm google-chrome-stable_current_amd64.deb

# Install Chromedriver
RUN pip install --no-cache-dir chromedriver-autoinstaller

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy your script into the container
COPY bot.py /app/bot.py
WORKDIR /app

# Run the script
CMD ["python", "-u", "bot.py"]
