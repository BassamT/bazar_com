# order_service/Dockerfile

FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Expose the port
EXPOSE ${PORT}

CMD ["python", "app.py"]
