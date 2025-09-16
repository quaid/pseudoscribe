FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    netcat-openbsd && \
    rm -rf /var/lib/apt/lists/*
COPY docker-requirements.txt .
RUN pip install --no-cache-dir -r docker-requirements.txt
RUN pip install --no-cache-dir python-multipart

# Create a fresh pseudoscribe directory structure with proper permissions
RUN mkdir -p /app/pseudoscribe/api /app/pseudoscribe/infrastructure /app/pseudoscribe/models
RUN chmod -R 755 /app/pseudoscribe

# Copy the application code with proper permissions
COPY --chmod=755 pseudoscribe/__init__.py /app/pseudoscribe/
COPY --chmod=755 pseudoscribe/api/ /app/pseudoscribe/api/
COPY --chmod=755 pseudoscribe/infrastructure/ /app/pseudoscribe/infrastructure/
COPY --chmod=755 pseudoscribe/models/ /app/pseudoscribe/models/
COPY tests/ /app/tests/
COPY setup.py .
COPY alembic.ini .
COPY migrations/ ./migrations/

# Install the package in development mode
RUN pip install -e .[test]

# Copy the debugging script
COPY debug_modules.py /app/
RUN chmod +x /app/debug_modules.py

# Expose the port the app runs on
EXPOSE 8000

# Copy the entry point script
COPY start_api.py .
RUN chmod +x start_api.py

# Command to run the application
# Copy the wait-for-services script
COPY scripts/wait-for-services.sh /app/
RUN chmod +x /app/wait-for-services.sh

CMD ["python", "start_api.py"]
