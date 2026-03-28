# Use the official, lightweight Python 3.12 image
FROM python:3.12-slim

# Create a non-root user for security
RUN useradd -m -s /bin/bash sandboxuser

# Set the working directory inside the container
WORKDIR /app

# Copy requirements and install them (done first for caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the core Python scripts and the datasets folder
COPY api.py execution_engine.py backend_config.py ./
COPY datasets/ ./datasets/

# Create the /runs directory for output artifacts
RUN mkdir runs

# CRITICAL SECURITY: Transfer ownership of the /app folder to the non-root user
RUN chown -R sandboxuser:sandboxuser /app

# Switch from the root OS user to our restricted sandbox user
USER sandboxuser

# Expose port 8000 for the FastAPI server
EXPOSE 8000

# Start the server bound to 0.0.0.0 so it can receive traffic from outside the container
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]