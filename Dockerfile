# Use a lightweight Python image
FROM python:3.12-slim

# Set working directory inside container
WORKDIR /app

# Copy only requirements first (for Docker cache)
COPY stage-3/requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy all files from stage-3 into container
COPY stage-3/ .


EXPOSE 8000

# Run the FastAPI app
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
