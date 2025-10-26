# Use a lightweight Python image
FROM python:3.12-slim

# Set working directory inside container
WORKDIR /app

# Copy only requirements first (for Docker cache)
COPY stage-2/requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy all files from stage-2 into container
COPY stage-2/ .

# Flask needs writable directories; use /tmp for SQLite + cache
ENV DATABASE_URL="sqlite:////tmp/data.db"
ENV FLASK_ENV=production
ENV PORT=5000

# Expose the port Flask runs on
EXPOSE 5000

# Run the Flask app
CMD ["python", "app.py"]
