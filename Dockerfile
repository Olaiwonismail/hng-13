# Use a lightweight Python image
FROM python:3.12-slim

# Set the working directory inside the container
WORKDIR /app

# Copy only requirements first (for better caching)
COPY stage-2/requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your app
COPY stage-2/ .

# Ensure instance and cache directories exist and are writable
RUN mkdir -p /app/instance /app/cache && chmod -R 777 /app/instance /app/cache

# Set environment variables for Flask
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_ENV=production

# Expose Flask's default port
EXPOSE 5000

# Run the app
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]

