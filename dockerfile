# Use the Python 3.10.12 slim image
FROM python:3.10.12-slim

# Set the working directory in the container
WORKDIR /app

# Copy requirements.txt into the container
COPY requirements.txt .

# Install the required Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project into the container
COPY . .

# Expose the port for the Streamlit app
EXPOSE 8501

# Set environment variables for Streamlit
ENV STREAMLIT_SERVER_PORT 8501
ENV STREAMLIT_SERVER_HEADLESS true
ENV STREAMLIT_SERVER_ENABLE_CORS false

# Run the Streamlit app
CMD ["streamlit", "run", "Spyder_Robo_Streamlit.py"]
