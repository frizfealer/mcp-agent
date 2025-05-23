# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set environment variables for unbuffered I/O and ensure /app is on PYTHONPATH
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Set the working directory in the container
WORKDIR /app

# Copy all application files
COPY . /app/

# List contents to verify structure during build
RUN echo "Contents of /app:" && ls -la /app && echo "\nContents of /app/src:" && ls -la /app/src

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Create a startup script for debugging
RUN echo '#!/bin/bash\n\
    echo "=== STARTUP DEBUG INFO ==="\n\
    echo "Current directory: $(pwd)"\n\
    echo "Contents of /app:"\n\
    ls -la /app/\n\
    echo "Contents of /app/src:"\n\
    ls -la /app/src/\n\
    echo "Checking if gradio_app.py exists:"\n\
    if [ -f "/app/src/gradio_app.py" ]; then\n\
    echo "✓ gradio_app.py found"\n\
    else\n\
    echo "✗ gradio_app.py NOT found"\n\
    exit 1\n\
    fi\n\
    echo "Starting application..."\n\
    exec python -u src/gradio_app.py\n\
    ' > /app/startup.sh && chmod +x /app/startup.sh

# Expose the port the app runs on
EXPOSE 8080

# Define the command to run the application
CMD ["/app/startup.sh"]
