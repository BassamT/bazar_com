# order_service/Dockerfile

FROM python:3.10-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Define environment variable defaults for flexibility
ENV DATABASE orders.db
ENV PORT 5002

# Expose the port, defaulting to the value in the PORT environment variable
EXPOSE ${PORT}

# Run the application with unbuffered output for real-time logging
CMD ["python", "-u", "app.py"]
