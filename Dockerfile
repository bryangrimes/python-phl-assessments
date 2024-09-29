# Use an official Python runtime as a parent image
FROM python:3.10

# Install required system dependencies for GDAL and GeoPandas
RUN apt-get update && apt-get install -y \
    gdal-bin \
    libgdal-dev \
    python3-gdal \
    && apt-get clean

# Set environment variables for GDAL
ENV CPLUS_INCLUDE_PATH=/usr/include/gdal
ENV C_INCLUDE_PATH=/usr/include/gdal
ENV GDAL_VERSION=3.2.0

# Set environment variables for Streamlit and Python
ENV PYTHONUNBUFFERED=1 \
    STREAMLIT_HOME=/app \
    PORT=8501

# Set working directory
WORKDIR $STREAMLIT_HOME

# Copy the requirements file to the container
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code to the container
COPY . .

# Expose the port the app runs on
EXPOSE $PORT

# Run the application
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
