# Use an official Python runtime as a parent image
# We choose a slim image for smaller size, and 3.9 as a common stable version.
FROM python:3.9-slim-buster

# Set the working directory in the container
WORKDIR /app

# Install system dependencies required for building many Python packages
# 'build-essential' provides compilers like gcc
# 'python3-dev' provides Python header files
# Add other -dev packages as needed based on your requirements.txt (e.g., libpq-dev for psycopg2, libjpeg-dev for Pillow)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        python3-dev \
        # Add any other specific libraries your Python packages might need here:
        # e.g., libpq-dev (for PostgreSQL client), libjpeg-dev (for Pillow),
        # libz-dev, libglib2.0-0, libsm6, libxext6, libxrender1 (for some GUI/image libs)
    && rm -rf /var/lib/apt/lists/* # Clean up apt cache to keep image size small

# Copy the requirements file into the working directory
# This step is placed after system dependency installation to leverage Docker's build cache
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the working directory
# The '.' at the end copies everything from the current host directory (where Dockerfile is)
# into the /app directory in the container.
COPY . .

# Expose the port that Gunicorn will listen on
# Your script uses 5000.
EXPOSE 5000

# Define the command to run your application using Gunicorn
# GEMINI_API_KEY will be passed as an environment variable at runtime (e.g., via `docker run -e` or Docker Compose).
# We are redirecting logs to stdout/stderr so Docker can capture them.
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--certfile", "cert.pem", "--keyfile", "key.pem", "app:app"]

# If you want to run without SSL (like your commented out line):
# CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
