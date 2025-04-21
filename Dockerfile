# Use a base image with Python
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy your application code and data into the container
COPY . /app

# Expose the port your Streamlit app runs on (default is 8501)
EXPOSE 8501

# Command to run your Streamlit application
ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.enableCORS=false", "--server.enableXsrfProtection=false"]