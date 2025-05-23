# Use an official Python runtime as a parent image
FROM python:3.9-slim-buster

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the working directory
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the working directory
COPY . .

# Expose the port that Gunicorn will listen on
EXPOSE 5000

# Define the command to run your application using Gunicorn
# This remains the same as Gunicorn will automatically pick up
# the GEMINI_API_KEY from the container's environment variables.
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--certfile", "cert.pem", "--keyfile", "key.pem", "app:app"]

# If you want to run without SSL:
# CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
